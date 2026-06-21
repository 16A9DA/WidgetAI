

from PySide6.QtCore import QObject, Signal

import providers


class LoginManager(QObject):

    login_changed = Signal(str, bool)  

    def __init__(self):
        super().__init__()
        self._states = {key: False for key in providers.ORDER}

    def is_logged_in(self, key: str) -> bool:
        return self._states.get(key, False)

    def mark(self, key: str, value: bool = True):
        if key not in self._states or self._states[key] == value:
            return
        self._states[key] = value
        self.login_changed.emit(key, value)

    def login_url(self, key: str) -> str:
        return providers.get(key).login_url if providers.exists(key) else ""
