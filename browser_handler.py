import time
from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView


class BrowserHandler(QObject):

    response_ready = Signal(str)

    SERVICE_URLS = {
        "chatgpt": "https://chatgpt.com/",
        "claude": "https://claude.ai/chats",
        "perplexity": "https://www.perplexity.ai/",
    }

    def __init__(self, login_manager):
        super().__init__()
        self.login_manager = login_manager
        self.browsers = {}
        self.active_service = None
        self._pending_query = None
        self._known_response_count = 0
        self._poll_timer = None
        self._query_started_at = None

        self._init_browsers()

    def _init_browsers(self):
        for service, url in self.SERVICE_URLS.items():
            view = QWebEngineView()
            view.setVisible(False)
            view.resize(1280, 800)
            view.load(QUrl(url))
            self.browsers[service] = view

        self.set_active_service("chatgpt")

    def set_active_service(self, service):
        if service in self.browsers:
            self.active_service = service
            view = self.browsers[service]
            if view.url() and view.url().toString() != self.SERVICE_URLS[service]:
                view.load(QUrl(self.SERVICE_URLS[service]))
            return True
        return False

    def show_active_browser(self):
        if self.active_service and self.active_service in self.browsers:
            view = self.browsers[self.active_service]
            view.setVisible(True)
            view.show()
            view.raise_()
            view.activateWindow()

    def send_query(self, query):
        if not self.active_service:
            return False

        view = self.browsers[self.active_service]
        url = view.url().toString()

        if not self.SERVICE_URLS[self.active_service].split("/")[2] in url:
            view.loadFinished.connect(lambda ok, s=self.active_service: self._run_inject(s, query))
        else:
            self._inject_query(view, query)

        self._pending_query = query
        self._query_started_at = time.time()
        self._start_response_polling()
        return True

    def _run_inject(self, service, query):
        if service in self.browsers and query:
            self._inject_query(self.browsers[service], query)

    def _inject_query(self, view, query):
        js = self._build_inject_js(query)
        view.page().runJavaScript(js)

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
            input.value = input.tagName === 'TEXTAREA' ? '{escaped}' : input.innerText;

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
        if not self.active_service:
            return

        view = self.browsers[self.active_service]
        js = self._build_extract_js()
        view.page().runJavaScript(js, self._on_response_extracted)

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

            const html = last.innerHTML || '';
            const text = (last.innerText || last.textContent || '').trim();
            if (text.length < 10) return { found: false };

            return {
                found: true,
                text: text,
                html: html,
                count: els.length,
            };
        })();
        """

    def shutdown(self):
        if self._poll_timer:
            self._poll_timer.stop()
        for view in self.browsers.values():
            view.stop()
            view.close()
        self.browsers.clear()
