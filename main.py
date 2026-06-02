import sys
from PySide6.QtWidgets import QApplication
from core.webprovider import WebProviderWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WidgetAI")

    window = WebProviderWindow(
        "https://chatgpt.com",
        "Explain random forest in very simple words."
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
