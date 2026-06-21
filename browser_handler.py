import json
import os
import time

from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot, Qt
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView

import providers

PROFILE_DIR = os.path.expanduser("~/.wiai/profile")
RESPONSE_TIMEOUT = 90
STABLE_POLLS = 2
POLL_MS = 1500


class BrowserHandler(QObject):

    response_ready = Signal(str)
    login_state_changed = Signal(str, bool)
    login_page_loaded = Signal(str, bool)
    debug_ready = Signal(str)

    def __init__(self, login_manager):
        super().__init__()
        self.login_manager = login_manager
        self.active = None
        self.views = {}

        self._poll_timer = None
        self._query_started = 0.0
        self._last_text = ""
        self._stable = 0

        self._login_timers = {}
        self._login_started = {}

        self._setup_profile()
        self._init_views()

    def _setup_profile(self):
        os.makedirs(PROFILE_DIR, exist_ok=True)
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        profile.setCachePath(PROFILE_DIR)
        profile.setPersistentStoragePath(PROFILE_DIR)

    def _init_views(self):
        for key in providers.ORDER:
            view = QWebEngineView()
            view.setWindowTitle(f"WIAI · {providers.get(key).label} login")
            view.setAttribute(Qt.WA_DeleteOnClose, False)
            view.resize(1100, 800)
            view.hide()
            view.load(QUrl(providers.get(key).chat_url))
            self.views[key] = view
        self.set_active("chatgpt")

    def set_active(self, key: str) -> bool:
        if key not in self.views:
            return False
        self.active = key
        view = self.views[key]
        target = providers.get(key).chat_url
        if not _same_host(view.url().toString(), target):
            view.load(QUrl(target))
        return True

    def _view(self):
        return self.views.get(self.active)

    def begin_login(self, key: str) -> bool:
        view = self.views.get(key)
        if not view:
            return False
        self.set_active(key)

        view.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        view.page().loadFinished.connect(
            lambda ok, k=key: self.login_page_loaded.emit(k, bool(ok))
        )
        view.load(QUrl(self.login_manager.login_url(key)))
        view.show()
        view.raise_()
        view.activateWindow()

        self.login_manager.mark(key, False)
        self._start_login_poll(key)
        return True

    def _start_login_poll(self, key):
        if key in self._login_timers:
            self._login_timers[key].stop()
        timer = QTimer(self)
        timer.setInterval(POLL_MS)
        timer.timeout.connect(lambda k=key: self._poll_login(k))
        timer.start()
        self._login_timers[key] = timer
        self._login_started[key] = time.time()

    def _poll_login(self, key):
        view = self.views.get(key)
        if not view or not view.page():
            return
        view.page().runJavaScript(
            _login_check_js(providers.get(key)),
            lambda ok, k=key: self._on_login_checked(k, ok),
        )
        if time.time() - self._login_started.get(key, 0) > 900:
            self._stop_login_poll(key)

    def _on_login_checked(self, key, logged_in):
        if not logged_in:
            return
        self.login_manager.mark(key, True)
        self._stop_login_poll(key)
        view = self.views.get(key)
        if view:
            view.hide()
        self.login_state_changed.emit(key, True)

    def _stop_login_poll(self, key):
        timer = self._login_timers.pop(key, None)
        if timer:
            timer.stop()

    def send_query(self, text: str) -> bool:
        view = self._view()
        if not view:
            return False
        provider = providers.get(self.active)
        self._inject(view, provider, text)
        self._query_started = time.time()
        self._last_text = ""
        self._stable = 0
        self._start_response_poll()
        return True

    def _inject(self, view, provider, text):
        view.page().runJavaScript(_inject_js(provider, text))

    def _start_response_poll(self):
        if self._poll_timer:
            self._poll_timer.stop()
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(POLL_MS)
        self._poll_timer.timeout.connect(self._poll_response)
        self._poll_timer.start()

    @Slot()
    def _poll_response(self):
        view = self._view()
        if not view:
            return
        view.page().runJavaScript(
            _extract_js(providers.get(self.active)), self._on_extracted
        )

    def _on_extracted(self, result):
        if time.time() - self._query_started > RESPONSE_TIMEOUT:
            self._finish("Error: timed out waiting for a response")
            return
        if not isinstance(result, dict) or not result.get("found"):
            return

        text = (result.get("text") or "").strip()
        if len(text) < 1:
            return

        if text == self._last_text:
            self._stable += 1
        else:
            self._last_text = text
            self._stable = 0

        if self._stable >= STABLE_POLLS:
            self._finish(text)

    def _finish(self, text):
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None
        self.response_ready.emit(text)

    def run_debug(self):
        view = self._view()
        if not view:
            self.debug_ready.emit("debug: no active browser view")
            return
        provider = providers.get(self.active)
        view.page().runJavaScript(
            _debug_js(provider), lambda r: self._on_debug(provider, r)
        )

    def _on_debug(self, provider, r):
        if not isinstance(r, dict):
            self.debug_ready.emit("debug: page not ready (no result)")
            return
        lines = [
            f"debug · {provider.key}",
            f"  url:      {r.get('url', '?')}",
            f"  input:    {r.get('input') or 'NOT FOUND, fix input_selectors'}",
            f"  send:     {r.get('submit') or 'NOT FOUND, fix submit_selectors'}",
            f"  response: {r.get('response') or 'NOT FOUND, fix response_selectors'}",
            f"  last reply snippet: {(r.get('text') or '(none)')[:160]}",
        ]
        self.debug_ready.emit("\n".join(lines))

    def show_browser(self):
        view = self._view()
        if view:
            view.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            view.show()
            view.raise_()
            view.activateWindow()

    def shutdown(self):
        for timer in list(self._login_timers.values()):
            timer.stop()
        if self._poll_timer:
            self._poll_timer.stop()
        for view in self.views.values():
            view.stop()
            view.close()
            view.deleteLater()
        self.views.clear()


def _same_host(a: str, b: str) -> bool:
    try:
        return QUrl(a).host() == QUrl(b).host()
    except Exception:
        return False


def _sel_array(selectors):
    return json.dumps(selectors)


def _login_check_js(provider):
    frags = json.dumps(list(providers.LOGIN_PATH_FRAGMENTS))
    return f"""
    (function() {{
        const path = window.location.pathname.toLowerCase();
        const frags = {frags};
        if (frags.some(f => path.includes(f))) return false;
        const shell = document.querySelector('main, [role="main"], nav');
        return !!shell;
    }})();
    """


def _inject_js(provider, text):
    payload = json.dumps(text)
    inputs = _sel_array(provider.input_selectors)
    submits = _sel_array(provider.submit_selectors)
    editable = "true" if provider.contenteditable else "false"
    return f"""
    (function() {{
        const text = {payload};
        const inputSel = {inputs};
        const submitSel = {submits};
        const editable = {editable};

        let input = null;
        for (const s of inputSel) {{ input = document.querySelector(s); if (input) break; }}
        if (!input) return 'no-input';

        input.focus();
        if (editable) {{
            document.execCommand('selectAll', false, null);
            const ok = document.execCommand('insertText', false, text);
            if (!ok) {{
                input.innerHTML = '';
                const p = document.createElement('p');
                p.textContent = text;
                input.appendChild(p);
            }}
        }} else {{
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(input, text);
        }}
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));

        let btn = null;
        for (const s of submitSel) {{
            const b = document.querySelector(s);
            if (b && !b.disabled && b.offsetParent !== null) {{ btn = b; break; }}
        }}
        if (btn) {{ btn.click(); return 'submitted'; }}

        input.dispatchEvent(new KeyboardEvent('keydown', {{
            key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
            bubbles: true, cancelable: true
        }}));
        return 'enter';
    }})();
    """


def _debug_js(provider):
    inputs = _sel_array(provider.input_selectors)
    submits = _sel_array(provider.submit_selectors)
    resps = _sel_array(provider.response_selectors)
    return f"""
    (function() {{
        function firstHit(sels) {{
            for (const s of sels) if (document.querySelector(s)) return s;
            return null;
        }}
        const respSel = firstHit({resps});
        let text = '';
        if (respSel) {{
            const nodes = document.querySelectorAll(respSel);
            const last = nodes[nodes.length - 1];
            if (last) text = (last.innerText || last.textContent || '').trim();
        }}
        return {{
            url: window.location.href,
            input: firstHit({inputs}),
            submit: firstHit({submits}),
            response: respSel,
            text: text
        }};
    }})();
    """


def _extract_js(provider):
    sels = _sel_array(provider.response_selectors)
    return f"""
    (function() {{
        const sels = {sels};
        let nodes = [];
        for (const s of sels) {{
            nodes = document.querySelectorAll(s);
            if (nodes.length) break;
        }}
        const last = nodes[nodes.length - 1];
        if (!last) return {{ found: false }};
        const text = (last.innerText || last.textContent || '').trim();
        if (text.length < 1) return {{ found: false }};
        return {{ found: true, text: text }};
    }})();
    """
