from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QPlainTextEdit,
)

from core.commands import parse_command, get_history
from core.sender import get_target_url
from core.webprovider import WebProviderWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.compact_size = (420, 190)
        self.expanded_size = (420, 520)

        self.setMinimumSize(*self.compact_size)
        self.resize(*self.compact_size)

        self.resize(*self.compact_size)

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.worker_window = None

        self.response_timer = QTimer(self)
        self.response_timer.setInterval(1500)
        self.response_timer.timeout.connect(self.check_response)

        self.setup_ui()
        self.apply_styles()


    def set_compact_mode(self):
        self.resize(*self.compact_size)
        self.output_box.hide()

    def set_expanded_mode(self):
        self.resize(*self.expanded_size)
        self.output_box.show()


    def setup_ui(self):
        layout = QVBoxLayout()
        
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.title_label = QLabel("WidgetAI")
        self.title_label.setFont(QFont("San Francisco", 15))

        self.command_label = QLabel("Type command:")
        self.command_label.setFont(QFont("San Francisco", 12))

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("/chatgpt explain this code")
        self.command_input.setFont(QFont("San Francisco", 12))
        self.command_input.returnPressed.connect(self.handle_command)

        self.status_label = QLabel(
            "Type a chatbot command and your message."
        )
        self.status_label.setFont(QFont("San Francisco", 9))
        self.status_label.setWordWrap(True)

        self.output_box = QPlainTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("Response will appear here...")
        self.output_box.setFont(QFont("Menlo", 10))
        self.output_box.hide()



        self.footer_label = QLabel(
            "Built and instructions: https://github.com/16A9DA/WidgetAI"
        )
        self.footer_label.setFont(QFont("San Francisco", 8))
        self.footer_label.setWordWrap(True)
        


        layout.addWidget(self.title_label)
        layout.addWidget(self.command_label)
        layout.addWidget(self.command_input)
        layout.addWidget(self.status_label)
        layout.addWidget(self.output_box, 1)
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def handle_command(self):
  

        user_text = self.command_input.text().strip()
        result = parse_command(user_text)
        self.set_compact_mode()
        self.status_label.setText(f"Sending prompt to {result.target}...")

        if not result.is_valid:
            self.status_label.setText(result.error)
            return

        if result.target == "exit":
            self.close()
            return

        if result.target == "history":
            items = get_history()

            if not items:
                self.output_box.setPlainText("No history yet.")
                self.status_label.setText("History is empty.")
                return

            lines = [
                f"{item['target']}: {item['prompt']}"
                for item in items[-5:]
            ]
            self.output_box.setPlainText("\n".join(lines))
            self.status_label.setText("Showing recent history.")
            return

        url = get_target_url(result.target)
        if not url:
            self.status_label.setText(f"No sender configured for {result.target}.")
            return

        if self.worker_window is not None:
            self.worker_window.close()
            self.worker_window.deleteLater()
            self.worker_window = None

        self.output_box.setPlainText("")
        
        self.status_label.setText(f"Sending prompt to {result.target}...")

        self.worker_window = WebProviderWindow(url=url, prompt=result.prompt)
        self.worker_window.hide()

        self.response_timer.start()

    def check_response(self):
        if self.worker_window is None:
            self.response_timer.stop()
            return

        response = self.worker_window.get_response()

        if response:
            self.set_expanded_mode()
            self.output_box.setPlainText(response)
            self.status_label.setText("Response received.")


        if response:
            self.output_box.setPlainText(response)
            self.status_label.setText("Response received.")

        if self.worker_window.is_finished:
            self.response_timer.stop()
            final_response = self.worker_window.get_response().strip()

            if final_response:
                self.output_box.setPlainText(final_response)
                self.status_label.setText("Done.")
            else:
                self.status_label.setText("Finished, but no response was captured.")

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0b0b0f;
                color: #f5f5f7;
                border-radius: 26px;
            }

            QLabel {
                border: none;
                background: transparent;
            }

            QLineEdit, QPlainTextEdit {
                background-color: #151518;
                color: #ffffff;
                border: 1px solid #2f2f35;
                border-radius: 18px;
                padding: 10px;
                font-size: 12px;
            }

            QLineEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #7c7cff;
            }

            QPlainTextEdit {
                selection-background-color: #7c7cff;
            }
        """)
