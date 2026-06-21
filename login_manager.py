import time
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView


LOGIN_URLS = {
    "chatgpt": "https://chatgpt.com/auth/login",
    "claude": "https://claude.ai/login",
    "perplexity": "https://www.perplexity.com/account/login",
}

LOGGED_IN_INDICATORS = {
    "chatgpt": "[data-testid='profile-button'], button[aria-label='Open profile menu']",
    "claude": "[data-testid='user-menu'], button[aria-label='User menu']",
    "perplexity": "[data-testid='user-menu'], button[aria-label='User menu']",
}


class LoginManager:

    def __init__(self):
        self._states = {"chatgpt": False, "claude": False, "perplexity": False}
        self._login_windows = {}
        self._poll_timers = {}
        self._started_at = {}

    def is_logged_in(self, service):
        return self._states.get(service, False)

    def login(self, service, check_browser=None):
        if service not in self._states:
            return False
        if self._states[service]:
            return True

        if check_browser is not None:
            self._check_browser(service, check_browser)
            return True

        url = LOGIN_URLS.get(service)
        if not url:
            return False

        win = QWebEngineView()
        win.setWindowTitle(f"Login to {service.title()}")
        win.resize(1024, 768)
        win.load(QUrl(url))
        win.show()
        self._login_windows[service] = win
        self._started_at[service] = time.time()

        timer = QTimer()
        timer.setInterval(2000)
        timer.timeout.connect(lambda s=service: self._poll(s))
        timer.start()
        self._poll_timers[service] = timer
        return True

    def _check_browser(self, service, view):
        sel = LOGGED_IN_INDICATORS[service]
        self._run_login_check(service, view, sel)

    def _poll(self, service):
        win = self._login_windows.get(service)
        if not win or not win.page():
            return
        sel = LOGGED_IN_INDICATORS[service]
        self._run_login_check(service, win, sel)

        elapsed = time.time() - self._started_at.get(service, time.time())
        if elapsed > 600:
            self._fail(service)

    def _run_login_check(self, service, view, selector):
        def _cb(result):
            if result:
                self._mark_logged_in(service)

        js = f"""
        (function() {{
            const sel = "{selector}";
            try {{
                if (document.querySelector(sel)) return true;
            }} catch (e) {{}}
            const path = window.location.pathname;
            if (path.includes('/login') || path.includes('/auth')) return false;
            if (path.length > 1) return true;
            return false;
        }})();
        """
        view.page().runJavaScript(js, _cb)

    def _mark_logged_in(self, service):
        if self._states.get(service):
            return
        self._states[service] = True
        timer = self._poll_timers.pop(service, None)
        if timer:
            timer.stop()
        win = self._login_windows.pop(service, None)
        if win:
            win.close()

    def _fail(self, service):
        timer = self._poll_timers.pop(service, None)
        if timer:
            timer.stop()
        win = self._login_windows.pop(service, None)
        if win:
            win.close()

    def logout(self, service):
        self._states[service] = False
        if service in self._poll_timers:
            self._poll_timers[service].stop()
            del self._poll_timers[service]
        if service in self._login_windows:
            self._login_windows[service].close()
            del self._login_windows[service]