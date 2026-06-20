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
            # Start sending the query
            self.browser_handler.send_query(self.query)

            # Wait for response to be ready (with timeout)
            if self.browser_handler.wait_for_response(timeout_ms=15000):  # 15 second timeout
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
        self.setWindowTitle("WIWI Widget")
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
            switch_service=self.switch_service,
            login=self.handle_login,
            clear_all=self.clear_all,
            show_history=self.show_history,
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
            "Welcome to WIWI Widget! Type your query or use commands like /chatgpt, /claude, /perplexity, /login, /history, /clear-all, /helpme"
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

        self.chat_display.append("<b>System:</b> Processing...")
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.current_query = query

        self.worker = QueryWorker(self.browser_handler, query)
        self.worker.finished.connect(self.query_finished)
        self.worker.start()

    def query_finished(self, response):

        self.chat_display.append(f"<b>{self.active_service.title()}:</b> {response}")
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        self.history_manager.add_entry(self.current_query, response, self.active_service)

    def switch_service(self, service):

        self.active_service = service
        self.status_label.setText(f"Active Service: {self.active_service.title()}")
        return f"Switched to {service.title()}"

    def handle_login(self):

        self.login_manager.login(self.active_service)
        return f"Please complete login for {self.active_service.title()} in the opened window"

    def clear_all(self):

        self.history_manager.clear()
        self.chat_display.clear()
        return "History cleared"

    def show_history(self):

        history = self.history_manager.get_history()
        if not history:
            return "No history available"

        history_text = "<b>Conversation History:</b><br>"
        for entry in history[-10:]:
            history_text += f"<b>{entry['service'].title()}:</b> {entry['query']} → {entry['response']}<br><br>"

        return history_text

    def handle_exit(self):
        self.close()
        return "Exiting application..."

    def check_login_status(self):

        is_logged_in = self.login_manager.is_logged_in(self.active_service)
        if is_logged_in:
            self.login_status_label.setText("✓ Logged in")
            self.login_status_label.setStyleSheet("color: green;")
        else:
            self.login_status_label.setText("✗ Not logged in")
            self.login_status_label.setStyleSheet("color: red;")


def main():

    app = QApplication(sys.argv)
    widget = WIWIWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
