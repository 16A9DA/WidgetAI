from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
import threading
import time


class LoginManager:

    def __init__(self):
        self.login_states = {"chatgpt": False, "claude": False, "perplexity": False}
        self.visible_browsers = {}

    def is_logged_in(self, service):

        return self.login_states.get(service, False)

    def login(self, service):
        if service not in ["chatgpt", "claude", "perplexity"]:
            return False

        if self.is_logged_in(service):
            return True

        login_browser = QWebEngineView()
        login_browser.setWindowTitle(f"Login to {service.title()}")
        login_browser.resize(1024, 768)

        login_urls = {
            "chatgpt": "https://chat.openai.com/auth/login",
            "claude": "https://claude.ai/login",
            "perplexity": "https://www.perplexity.ai/account/login",
        }

        url = login_urls.get(service, f"https://{service}.com/login")
        login_browser.load(QUrl(url))
        login_browser.show()

        self.visible_browsers[service] = login_browser

        def simulate_login_delay():
            time.sleep(5)
            self.login_states[service] = True
            print(f"Simulated login successful for {service}")
            # In real app, we'd close the visible browser here

        login_thread = threading.Thread(target=simulate_login_delay)
        login_thread.daemon = True
        login_thread.start()

        return True

    def logout(self, service):

        if service in self.login_states:
            self.login_states[service] = False
        if service in self.visible_browsers:
            self.visible_browsers[service].close()
            del self.visible_browsers[service]
