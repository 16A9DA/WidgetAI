from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QApplication,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WidgetAI")
        self.setFixedSize(620, 420)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 34, 40, 34)
        layout.setSpacing(18)

        mono_font = QFont("Menlo")
        mono_font.setStyleHint(QFont.Monospace)

        self.title_label = QLabel("Welcome {Username}")
        self.title_label.setFont(QFont("Menlo", 24))

        self.command_label = QLabel("Type (/):")
        self.command_label.setFont(QFont("Menlo", 16))

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("/chatgpt explain this code")
        self.command_input.setFont(QFont("Menlo", 18))
        self.command_input.returnPressed.connect(self.handle_command)

        self.note_label = QLabel(
            "Note: Prompt router mode.\nType a chatbot command and your message."
        )
        self.note_label.setFont(QFont("Menlo", 13))
        self.note_label.setWordWrap(True)

        self.footer_label = QLabel("Built: {github link}")
        self.footer_label.setFont(QFont("Menlo", 15))

        layout.addWidget(self.title_label)
        layout.addSpacing(8)
        layout.addWidget(self.command_label)
        layout.addWidget(self.command_input)
        layout.addWidget(self.note_label)
        layout.addStretch()
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def handle_command(self):
        user_text = self.command_input.text().strip()

        if not user_text:
            self.note_label.setText("Please type a command first.")
            return

        self.note_label.setText(f"Captured: {user_text}")

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #050505;
                color: #f2f2f2;
                border: 1px solid #2b2b2b;
            }

            QLabel {
                border: none;
                background: transparent;
            }

            QLineEdit {
                background-color: #0b0b0b;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                padding: 12px 14px;
                font-size: 18px;
            }

            QLineEdit:focus {
                border: 1px solid #6c63ff;
            }
        """)
