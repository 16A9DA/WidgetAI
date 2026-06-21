from PySide6.QtCore import QObject, Signal


LOGIN_URLS = {
    "chatgpt": "https://chatgpt.com/auth/login",
    "claude": "https://claude.ai/login",
    "perplexity": "https://www.perplexity.ai/account/login",
}


class LoginManager(QObject):

    login_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self._states = {"chatgpt": False, "claude": False, "perplexity": False}

    def is_logged_in(self, service):
        return self._states.get(service, False)

    def mark_logged_in(self, service, value=True):
        if service not in self._states:
            return
        if self._states[service] == value:
            return
        self._states[service] = value
        self.login_changed.emit(service, value)

    def logout(self, service):
        if service not in self._states:
            return
        self.mark_logged_in(service, False)

    def login_url(self, service):
        return LOGIN_URLS.get(service)