import os
import time
from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView


SERVICE_URLS = {
    "chatgpt": "https://chatgpt.com/",
    "claude": "https://claude.ai/chats",
    "perplexity": "https://www.perplexity.ai/",
}

LOGIN_URLS = {
    "chatgpt": "https://chatgpt.com/auth/login",
    "claude": "https://claude.ai/login",
    "perplexity": "https://www.perplexity.ai/account/login",
}

LOGGED_IN_DOMAINS = {
    "chatgpt": ["chatgpt.com"],
    "claude": ["claude.ai"],
    "perplexity": ["perplexity.ai"],
}

LOGIN_PATH_FRAGMENTS = ("/login", "/auth", "/signin", "/signup")


class BrowserHandler(QObject):

    response_ready = Signal(str)
    login_state_changed = Signal(str, bool)

    def __init__(self, login_manager):
        super().__init__()
        self.login_manager = login_manager
        self.browsers = {}
        self.active_service = None
        self._pending_query = None
        self._poll_timer = None
        self._query_started_at = None
        self._login_timers = {}
        self._login_started_at = {}

        self._setup_profile()
        self._init_browsers()

    def _setup_profile(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        cache_path = os.path.expanduser("~/.wiai/profile")
        os.makedirs(cache_path, exist_ok=True)
        profile.setCachePath(cache_path)
        profile.setPersistentStoragePath(cache_path)

    def _init_browsers(self):
        for service, url in SERVICE_URLS.items():
            view = QWebEngineView()
            view.resize(1280, 800)
            view.setVisible(False)
            view.load(QUrl(url))
            self.browsers[service] = view

        self.set_active_service("chatgpt")

    def set_active_service(self, service):
        if service not in self.browsers:
            return False

        for s, v in self.browsers.items():
            if s != service and v.isVisible():
                v.hide()

        self.active_service = service
        view = self.browsers[service]
        url = view.url().toString()
        target = SERVICE_URLS[service]
        if not url or url == "about:blank" or url.split("/")[2] != target.split("/")[2]:
            view.load(QUrl(target))
        return True

    def _active_view(self):
        if self.active_service and self.active_service in self.browsers:
            return self.browsers[self.active_service]
        return None

    def begin_login(self, service):
        view = self.browsers.get(service)
        if not view:
            return False
        if service != self.active_service:
            self.set_active_service(service)
        url = self.login_manager.login_url(service)
        if not url:
            return False
        view.show()
        view.raise_()
        view.setVisible(True)
        view.load(QUrl(url))
        self.login_manager.mark_logged_in(service, False)

        if service in self._login_timers:
            self._login_timers[service].stop()

        timer = QTimer()
        timer.setInterval(1500)
        timer.timeout.connect(lambda s=service: self._poll_login(s))
        timer.start()
        self._login_timers[service] = timer
        self._login_started_at[service] = time.time()
        return True

    def _poll_login(self, service):
        view = self.browsers.get(service)
        if not view or not view.page():
            return

        def _cb(result):
            self._on_login_checked(service, result)

        js = self._login_check_js(service)
        view.page().runJavaScript(js, _cb)

        elapsed = time.time() - self._login_started_at.get(service, time.time())
        if elapsed > 900:
            self._stop_login_poll(service)

    def _on_login_checked(self, service, is_logged_in):
        if is_logged_in:
            self.login_manager.mark_logged_in(service, True)
            self._stop_login_poll(service)
            view = self.browsers.get(service)
            if view and service != self.active_service:
                view.hide()
            self.login_state_changed.emit(service, True)

    def _login_check_js(self, service):
        login_path = " || ".join(
            [f"path.includes('{frag}')" for frag in LOGIN_PATH_FRAGMENTS]
        )
        return f"""
        (function() {{
            const path = window.location.pathname;
            if ({login_path}) return false;
            if (path.length > 1 && !path.startsWith('/auth')) return true;
            try {{
                const main = document.querySelector('main, [role="main"], nav, button[aria-haspopup="menu"]');
                if (main) return true;
            }} catch (e) {{}}
            return false;
        }})();
        """

    def send_query(self, query):
        view = self._active_view()
        if not view or not self.active_service:
            return False
        url = view.url().toString()
        if not url or url == "about:blank":
            view.loadFinished.connect(lambda ok, v=view, q=query: self._inject_query(v, q))
        else:
            self._inject_query(view, query)

        self._pending_query = query
        self._query_started_at = time.time()
        self._start_response_polling()
        return True

    def _inject_query(self, view, query):
        view.page().runJavaScript(self._build_inject_js(query))

    def _build_inject_js(self, query):
        escaped = (
            query.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "")
        )

        return f"""
        (function() {{
            const url = window.location.href;
            let input = null;
            let submitBtn = null;

            if (url.includes('claude.ai')) {{
                input = document.querySelector('div[contenteditable="true"]');
                submitBtn = document.querySelector('button[aria-label*="Send" i]');
            }} else if (url.includes('chatgpt.com') || url.includes('chat.openai.com')) {{
                input = document.querySelector('textarea#prompt-textarea, textarea[placeholder*="Ask" i]');
                submitBtn = document.querySelector('button[data-testid="send-button"]');
            }} else if (url.includes('perplexity.ai')) {{
                input = document.querySelector('textarea[placeholder*="Ask" i], textarea');
                submitBtn = document.querySelector('button[aria-label*="Submit" i]');
            }} else {{
                input = document.querySelector('textarea, div[contenteditable="true"]');
                submitBtn = document.querySelector('button[type="submit"], button[aria-label*="Send" i]');
            }}

            if (!input) return 'no-input';

            input.focus();
            if (input.tagName === 'TEXTAREA') {{
                input.value = '';
            }} else {{
                input.innerHTML = '';
                const p = document.createElement('p');
                p.textContent = '{escaped}';
                input.appendChild(p);
            }}
            if (input.tagName === 'TEXTAREA') input.value = '{escaped}';

            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));

            if (submitBtn && submitBtn.offsetParent !== null) {{
                submitBtn.click();
                return 'submitted';
            }}

            const ev = new KeyboardEvent('keydown', {{
                key: 'Enter', code: 'Enter', keyCode: 13,
                bubbles: true, cancelable: true,
            }});
            input.dispatchEvent(ev);
            return 'enter-sent';
        }})();
        """

    def _start_response_polling(self):
        if self._poll_timer:
            self._poll_timer.stop()
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(1500)
        self._poll_timer.timeout.connect(self._poll_response)
        self._poll_timer.start()

    @Slot()
    def _poll_response(self):
        view = self._active_view()
        if not view:
            return
        view.page().runJavaScript(self._build_extract_js(), self._on_response_extracted)

    def _on_response_extracted(self, result):
        if not result or not isinstance(result, dict):
            return
        if not result.get("found"):
            if time.time() - (self._query_started_at or time.time()) > 60:
                self._poll_timer and self._poll_timer.stop()
                self.response_ready.emit("Error: Timeout waiting for response")
            return

        text = (result.get("text") or "").strip()
        if len(text) < 10:
            return
        if any(t in text.lower() for t in ("thinking", "generating", "loading")):
            return

        self._poll_timer and self._poll_timer.stop()
        self.response_ready.emit(text)

    def _build_extract_js(self):
        return """
        (function() {
            const url = window.location.href;
            let candidates = [];

            if (url.includes('claude.ai')) {
                candidates = document.querySelectorAll('[data-testid="chat-assistant-message"], .font-claude-message');
            } else if (url.includes('chatgpt.com') || url.includes('chat.openai.com')) {
                candidates = document.querySelectorAll('[data-message-author-role="assistant"] .markdown');
            } else if (url.includes('perplexity.ai')) {
                candidates = document.querySelectorAll('.answer, [data-testid="copilot-response"], .prose');
            } else {
                candidates = document.querySelectorAll('[data-message-author-role="assistant"], .assistant-message');
            }

            const els = Array.from(candidates);
            const last = els[els.length - 1];
            if (!last) return { found: false };

            const text = (last.innerText || last.textContent || '').trim();
            if (text.length < 10) return { found: false };

            return { found: true, text: text };
        })();
        """

    def show_active_browser(self):
        view = self._active_view()
        if view:
            view.show()
            view.raise_()
            view.activateWindow()

    def hide_active_browser(self):
        view = self._active_view()
        if view:
            view.hide()

    def shutdown(self):
        if self._poll_timer:
            self._poll_timer.stop()
        for timer in self._login_timers.values():
            timer.stop()
        for view in self.browsers.values():
            view.stop()
            view.close()
        self.browsers.clear()