from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QApplication,
)
from core.commands import parse_command


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WidgetAI")
        self.setFixedSize(320, 220)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)


        mono_font = QFont("Menlo")
        mono_font.setStyleHint(QFont.Monospace)

        self.title_label = QLabel("Welcome {Username}")
        self.title_label.setFont(QFont("San Francisco", 15))

        self.command_label = QLabel("Type (/):")
        self.command_label.setFont(QFont("San Francisco", 12))

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("/chatgpt explain this code")
        self.command_input.setFont(QFont("San Francisco", 12))
        self.command_input.returnPressed.connect(self.handle_command)

        self.note_label = QLabel(
            "Note: Prompt router mode.\nType a chatbot command and your message."
        )
        self.note_label.setFont(QFont("San Francisco", 9))

        self.footer_label = QLabel("Built: {github link}")
        self.footer_label.setFont(QFont("San Francisco",8 ))

        layout.addWidget(self.title_label)
        layout.addWidget(self.command_label)
        layout.addWidget(self.command_input)
        layout.addWidget(self.note_label)
        layout.addStretch()
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def handle_command(self):
        user_text = self.command_input.text().strip()
        result = parse_command(user_text)

        if not result.is_valid:
            self.note_label.setText(result.error)
            return

        self.note_label.setText(
            f"Target: {result.target}\nPrompt: {result.prompt}"
            )


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
                # padding: px 10px;
                font-size: 12px;
            }

            QLineEdit:focus {
                border: 1px solid #6c63ff;
            }
        """)
