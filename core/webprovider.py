from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from .allproviders import get_provider


class WebProviderWindow(QWidget):
    def __init__(self, url: str, prompt: str, parent=None):
        super().__init__(parent)

        self.url = url
        self.prompt = prompt
        self.provider = get_provider(self.url)

        if not self.provider:
            raise ValueError(f"No provider found for URL: {self.url}")

        self.last_response = ""
        self.same_count = 0
        self.max_same_count = 3
        self.poll_interval_ms = 2000
        self.is_finished = False

        self.setWindowTitle(f"{self.provider.name.title()} - Web Provider")
        self.resize(1200, 900)

        self.setup_ui()
        self.setup_browser()
        self.setup_timers()

        self.browser.loadFinished.connect(self.on_load_finished)
        self.browser.setUrl(QUrl(self.url))

    def setup_ui(self):
        self.status_label = QLabel(f"Loading {self.url}")
        self.status_label.setWordWrap(True)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("AI response will appear here...")

        self.reload_button = QPushButton("Reload")
        self.inject_button = QPushButton("Inject Prompt")
        self.submit_button = QPushButton("Submit")
        self.poll_button = QPushButton("Poll Once")
        self.stop_button = QPushButton("Stop Polling")

        self.reload_button.clicked.connect(self.reload_page)
        self.inject_button.clicked.connect(self.inject_prompt)
        self.submit_button.clicked.connect(self.submit_prompt)
        self.poll_button.clicked.connect(self.poll_response)
        self.stop_button.clicked.connect(self.stop_polling)

        button_row = QHBoxLayout()
        button_row.addWidget(self.reload_button)
        button_row.addWidget(self.inject_button)
        button_row.addWidget(self.submit_button)
        button_row.addWidget(self.poll_button)
        button_row.addWidget(self.stop_button)

        self.browser = QWebEngineView()

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addLayout(button_row)
        layout.addWidget(self.browser, 3)
        layout.addWidget(self.output_box, 2)

    def setup_browser(self):
        self.page = self.browser.page()

    def setup_timers(self):
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_response)

    def on_load_finished(self, ok: bool):
        if not ok:
            self.status_label.setText("Page failed to load.")
            return

        self.status_label.setText(
            f"Loaded {self.url} with provider: {self.provider.name}"
        )

        QTimer.singleShot(2000, self.inject_prompt)

    def reload_page(self):
        self.status_label.setText("Reloading page...")
        self.last_response = ""
        self.same_count = 0
        self.is_finished = False
        self.stop_polling()
        self.browser.setUrl(QUrl(self.url))

    def inject_prompt(self):
        if self.is_finished:
            return

        self.status_label.setText("Injecting prompt...")
        script = self.provider.inject_script(self.prompt)
        self.page.runJavaScript(script, self.after_injection)

    def after_injection(self, result):
        self.status_label.setText(f"Prompt injected: {result}")
        QTimer.singleShot(1200, self.submit_prompt)

    def submit_prompt(self):
        if self.is_finished:
            return

        self.status_label.setText("Submitting prompt...")
        script = self.provider.submit_script()
        self.page.runJavaScript(script, self.after_submit)

    def after_submit(self, result):
        self.status_label.setText(f"Submit result: {result}")
        self.start_polling()

    def start_polling(self):
        if self.poll_timer.isActive():
            self.poll_timer.stop()

        self.status_label.setText("Polling for response...")
        self.poll_timer.start(self.poll_interval_ms)

    def stop_polling(self):
        if self.poll_timer.isActive():
            self.poll_timer.stop()
        self.status_label.setText("Polling stopped.")

    def poll_response(self):
        if self.is_finished:
            return

        script = self.provider.extract_script()
        self.page.runJavaScript(script, self.handle_poll_result)

    def handle_poll_result(self, result):
        text = (result or "").strip()

        if not text:
            self.status_label.setText("Waiting for response...")
            return

        self.output_box.setPlainText(text)

        if text == self.last_response:
            self.same_count += 1
        else:
            self.last_response = text
            self.same_count = 0

        self.status_label.setText(
            f"Response length: {len(text)} chars | Stable checks: {self.same_count}/{self.max_same_count}"
        )

        if self.same_count >= self.max_same_count:
            self.finish_response()

    def finish_response(self):
        self.is_finished = True
        self.stop_polling()
        self.status_label.setText("Response captured successfully.")

    def get_response(self) -> str:
        return self.output_box.toPlainText().strip()
