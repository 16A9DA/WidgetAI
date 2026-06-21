import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

from browser_handler import BrowserHandler
from command_parser import CommandParser
from history_manager import HistoryManager
from login_manager import LoginManager


class QueryWorker(QThread):

    finished = Signal(str)

    def __init__(self, browser_handler, query):
        super().__init__()
        self.browser_handler = browser_handler
        self.query = query

    def run(self):

        try:
            self.browser_handler.send_query(self.query)

            if self.browser_handler.wait_for_response(timeout_ms=15000):
                response = self.browser_handler.get_response()
                if not response:
                    response = "Error: No response received from service"
            else:
                response = "Error: Timeout waiting for response from service"

            self.finished.emit(response)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")


class WIWIWidget(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WIAI Widget")
        self.setGeometry(100, 100, 350, 500)
        self.setMinimumSize(300, 400)
        self.setMaximumSize(800, 600)

        self.history_manager = HistoryManager()
        self.login_manager = LoginManager()
        self.command_parser = CommandParser()
        self.browser_handler = BrowserHandler(self.login_manager)

        self.active_service = "chatgpt"
        self.current_query = None

        self.setup_ui()

        self.command_parser.set_callbacks(
            switch=self.switch_service,
            login=self.handle_login,
            clearAll=self.clear_all,
            history=self.show_history,
            exit=self.handle_exit,
        )

        self.check_login_status()

    def setup_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        logo_help_layout = QHBoxLayout()
        self.logo_label = QLabel("WIAI")
        self.logo_label.setStyleSheet("""
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 24px;
                font-weight: bold;
                color: #FF6B6B;
                background-color: #1A1A2E;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(60, 60)

        self.help_label = QLabel("Type /helpme for available commands")
        self.help_label.setStyleSheet("""
            QLabel {
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                color: #888;
                padding: 8px;
            }
        """)
        self.help_label.setAlignment(Qt.AlignVCenter)

        logo_help_layout.addWidget(self.logo_label)
        logo_help_layout.addWidget(self.help_label)
        logo_help_layout.addStretch()
        layout.addLayout(logo_help_layout)

        status_layout = QHBoxLayout()
        self.status_label = QLabel(f"Active Service: {self.active_service.title()}")
        self.login_status_label = QLabel("Checking login status...")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.login_status_label)
        layout.addLayout(status_layout)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText(
            "Welcome to WIAI Widget! Type your query or use commands like /chatgpt, /claude, /perplexity, /login, /history, /clear-all, /helpme"
        )
        self.chat_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #16213E;
                color: #EAF4F4;
                border: 1px solid #0F3460;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                padding: 8px;
                background-color: #0F3460;
                color: #EAF4F4;
                border: 1px solid #16213E;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #FF6B6B;
                background-color: #16213E;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                padding: 8px 16px;
                background-color: #FF6B6B;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
            QPushButton:pressed {
                background-color: #E53935;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def send_message(self):

        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()

        self.chat_display.append(f"<b>You:</b> {text}")

        if text.startswith("/"):
            self.handle_command(text)
        else:
            self.process_query(text)

    def handle_command(self, command_text):

        response = self.command_parser.parse_command(command_text)
        if response:
            self.chat_display.append(f"<b>System:</b> {response}")

    def process_query(self, query):

        if not self.login_manager.is_logged_in(self.active_service):
            self.chat_display.append(
                f"<b>System:</b> Please login first using /login command"
            )
            return

        # Build shared memory context from recent history
        full_query = self._build_contextual_query(query)

        self.chat_display.append("<b>System:</b> Processing...")
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.current_query = query

        self.worker = QueryWorker(self.browser_handler, full_query)
        self.worker.finished.connect(self.query_finished)
        self.worker.start()

    def _build_contextual_query(self, query):
        """Inject recent history as shared memory/context."""
        history = self.history_manager.get_history()
        if not history:
            return query

        # Get last 3 entries from any provider as context
        recent = history[-3:]
        if not recent:
            return query

        context_lines = ["Previous context:"]
        for entry in recent:
            service = entry.get("service", "unknown")
            q = entry.get("query", "")
            r = entry.get("response", "")
            r_short = (r[:80] + "...") if len(r) > 80 else r
            context_lines.append(f"  [{service}] {q} -> {r_short}")

        if context_lines:
            context_lines.append("Current question:")
            return "\n".join(context_lines) + "\n" + query
        return query

    def query_finished(self, response):

        self.chat_display.append(
            f"<b>{self.active_service.title()}:</b> {response}"
        )
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        self.history_manager.add_entry(self.current_query, response, self.active_service)

    def switch_service(self, service):

        self.active_service = service
        self.browser_handler.set_active_service(service)
        self.status_label.setText(f"Active Service: {self.active_service.title()}")
        self.check_login_status()
        return f"Switched to {service.title()}"

    def handle_login(self, provider=""):
        # If provider is specified, use it; otherwise use active service
        target = provider.lower().strip() if provider.strip() else self.active_service

        if target not in ["chatgpt", "claude", "perplexity"]:
            return f"Unknown provider '{provider}'. Use: chatgpt, claude, perplexity"

        # Update active service if a different provider was specified
        if target != self.active_service:
            self.active_service = target
            self.browser_handler.set_active_service(target)
            self.status_label.setText(f"Active Service: {self.active_service.title()}")

        self.login_manager.login(target)
        return f"Login window opened for {target.title()}. Complete login in the browser window."

    def clear_all(self):
        self.history_manager.clear()
        self.chat_display.clear()
        self.chat_display.setPlaceholderText(
            "Welcome to WIAI Widget! Type your query or use commands like /chatgpt, /claude, /perplexity, /login, /history, /clear-all, /helpme"
        )
        return "Chat and history cleared."

    def show_history(self):
        history = self.history_manager.get_history()
        if not history:
            return "No history available"

        lines = []
        for entry in history[-10:]:
            service = entry.get("service", "unknown")
            query = entry.get("query", "")
            response = entry.get("response", "")
            # Truncate long responses for display
            short_response = (response[:120] + "...") if len(response) > 120 else response
            lines.append(f"[{service}] - {query} = {short_response}")

        return "\n".join(lines)

    def handle_exit(self):
        self.close()
        return ""

    def check_login_status(self):

        is_logged_in = self.login_manager.is_logged_in(self.active_service)
        if is_logged_in:
            self.login_status_label.setText("✓ Logged in")
            self.login_status_label.setStyleSheet("color: green;")
        else:
            self.login_status_label.setText("✗ Not logged in")
            self.login_status_label.setStyleSheet("color: red;")


    def closeEvent(self, event):
        """Ensure clean shutdown."""
        if hasattr(self, "worker") and self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()


def main():

    app = QApplication(sys.argv)
    widget = WIWIWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
