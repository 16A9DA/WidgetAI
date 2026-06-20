#!/usr/bin/env python3
"""
WIWI Widget - A terminal-callable widget that provides access to
ChatGPT, Claude, and Perplexity without needing individual APIs.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

# Import our custom modules
from browser_handler import BrowserHandler
from command_parser import CommandParser
from history_manager import HistoryManager
from login_manager import LoginManager


class QueryWorker(QThread):
    """Worker thread to handle queries without blocking the GUI."""
    finished = Signal(str)

    def __init__(self, browser_handler, query):
        super().__init__()
        self.browser_handler = browser_handler
        self.query = query

    def run(self):
        """Execute the query in a separate thread."""
        try:
            response = self.browser_handler.send_query(self.query)
            self.finished.emit(response)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")


class WIWIWidget(QMainWindow):
    """Main application window for the WIWI widget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WIWI Widget")
        self.setGeometry(100, 100, 800, 600)

        # Initialize managers
        self.history_manager = HistoryManager()
        self.login_manager = LoginManager()
        self.command_parser = CommandParser()
        self.browser_handler = BrowserHandler(self.login_manager)

        # Current active service
        self.active_service = "chatgpt"  # Default service

        # Setup UI
        self.setup_ui()

        # Setup command parser callbacks
        self.command_parser.set_callbacks(
            switch_service=self.switch_service,
            login=self.handle_login,
            clear_all=self.clear_all,
            show_history=self.show_history
        )

        # Check login status on startup
        self.check_login_status()

    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel(f"Active Service: {self.active_service.title()}")
        self.login_status_label = QLabel("Checking login status...")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.login_status_label)
        layout.addLayout(status_layout)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Welcome to WIWI Widget! Type your query or use commands like /chatgpt, /claude, /perplexity, /login, /history, /clear-all")
        layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def send_message(self):
        """Handle sending a message."""
        text = self.input_field.text().strip()
        if not text:
            return

        # Clear input field
        self.input_field.clear()

        # Add user message to chat
        self.chat_display.append(f"<b>You:</b> {text}")

        # Check if it's a command
        if text.startswith('/'):
            self.handle_command(text)
        else:
            # Regular query - send to active service
            self.process_query(text)

    def handle_command(self, command_text):
        """Handle slash commands."""
        response = self.command_parser.parse_command(command_text)
        if response:
            self.chat_display.append(f"<b>System:</b> {response}")

    def process_query(self, query):
        """Process a regular query through the active service."""
        # Check if we're logged in
        if not self.login_manager.is_logged_in(self.active_service):
            self.chat_display.append(f"<b>System:</b> Please login first using /login command")
            return

        # Show processing indicator
        self.chat_display.append("<b>System:</b> Processing...")
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)

        # Start worker thread
        self.worker = QueryWorker(self.browser_handler, query)
        self.worker.finished.connect(self.query_finished)
        self.worker.start()

    def query_finished(self, response):
        """Handle the finished query."""
        self.chat_display.append(f"<b>{self.active_service.title()}:</b> {response}")
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        # Add to history
        self.history_manager.add_entry(query, response, self.active_service)

    def switch_service(self, service):
        """Switch the active service."""
        self.active_service = service
        self.status_label.setText(f"Active Service: {self.active_service.title()}")
        return f"Switched to {service.title()}"

    def handle_login(self):
        """Handle login request."""
        self.login_manager.login(self.active_service)
        return f"Please complete login for {self.active_service.title()} in the opened window"

    def clear_all(self):
        """Clear all history."""
        self.history_manager.clear()
        self.chat_display.clear()
        self.chat_display.append("<b>System:</b> History cleared")
        return "History cleared"

    def show_history(self):
        """Show conversation history."""
        history = self.history_manager.get_history()
        if not history:
            return "No history available"

        history_text = "<b>Conversation History:</b><br>"
        for entry in history[-10:]:  # Show last 10 entries
            history_text += f"<b>{entry['service'].title()}:</b> {entry['query']} → {entry['response']}<br><br>"

        return history_text

    def check_login_status(self):
        """Check and update login status."""
        is_logged_in = self.login_manager.is_logged_in(self.active_service)
        if is_logged_in:
            self.login_status_label.setText("✓ Logged in")
            self.login_status_label.setStyleSheet("color: green;")
        else:
            self.login_status_label.setText("✗ Not logged in")
            self.login_status_label.setStyleSheet("color: red;")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    widget = WIWIWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()