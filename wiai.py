import sys
from datetime import datetime
from html import escape
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QLabel,
)

from browser_handler import BrowserHandler
from command_parser import CommandParser
from history_manager import HistoryManager
from login_manager import LoginManager


class WIWIWidget(QMainWindow):

    BASE_CSS = """
    QMainWindow { background: #0b0e14; }
    QWidget { color: #c9d1d9; font-family: 'JetBrains Mono', 'Menlo', 'Consolas', monospace; }
    QTextEdit {
        background: #0d1117;
        color: #c9d1d9;
        border: 1px solid #1f262d;
        selection-background-color: #264f78;
        padding: 6px;
        font-size: 11pt;
    }
    QLineEdit {
        background: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 2px;
        padding: 6px;
        font-size: 11pt;
    }
    QLineEdit:focus { border: 1px solid #58a6ff; }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WIAI")
        self.resize(420, 540)
        self.setMinimumSize(360, 360)
        self.setWindowFlags(
            self.windowFlags() | Qt.Tool | Qt.WindowStaysOnTopHint
        )

        self.history_manager = HistoryManager()
        self.login_manager = LoginManager()
        self.command_parser = CommandParser()
        self.browser_handler = BrowserHandler(self.login_manager)

        self.active_service = "chatgpt"
        self.current_query = None
        self._busy = False

        self._setup_ui()
        self._wire_signals()

        self.command_parser.set_callbacks(
            switch=self._switch_service,
            login=self._handle_login,
            clearAll=self._clear_all,
            history=self._show_history,
            exit=self._handle_exit,
        )

        self._update_status()
        self._append_system("WIAI widget ready. Type /helpme for commands.")

    def _setup_ui(self):
        self.setStyleSheet(self.BASE_CSS)
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        top = QHBoxLayout()
        self.clock_label = self._make_label("HH:MM:SS", size=10)
        self.provider_label = self._make_label("chatgpt", size=10, color="#58a6ff")
        self.login_label = self._make_label("checking...", size=10, color="#8b949e")

        top.addWidget(self.clock_label)
        top.addStretch()
        top.addWidget(self.provider_label)
        top.addSpacing(8)
        top.addWidget(self.login_label)
        root.addLayout(top)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Type a prompt or /command...")
        root.addWidget(self.chat_display, 1)

        bottom = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("> _")
        self.input_field.returnPressed.connect(self._on_submit)
        bottom.addWidget(self.input_field)
        root.addLayout(bottom)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start()
        self._tick_clock()

    def _make_label(self, text, size=10, color="#c9d1d9"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: {size}pt; background: transparent;")
        return lbl

    def _wire_signals(self):
        self.browser_handler.response_ready.connect(self._on_response_ready)
        self.browser_handler.login_state_changed.connect(self._on_login_state_changed)
        self.browser_handler.login_url_loaded.connect(self._on_login_url_loaded)

    def _on_login_state_changed(self, service, logged_in):
        self._append_system(f"login state: {service} -> {'logged in' if logged_in else 'logged out'}")
        self._update_status()

    def _on_login_url_loaded(self, service, ok):
        if ok:
            self._append_system(f"login page loaded for {service}; sign in there.")
        else:
            self._append_system(f"login page failed to load for {service}; check the browser window or try again.")

    def _tick_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(now)

    def _set_busy(self, busy):
        self._busy = busy
        self.input_field.setReadOnly(busy)
        if not busy:
            self.input_field.setFocus()

    def _append_system(self, text):
        self._append_line("sys", text, "#8b949e")

    def _append_user(self, text):
        self._append_line("you", text, "#c9d1d9")

    def _append_assistant(self, text):
        self._append_line(self.active_service, text, "#7ee787")

    def _append_line(self, prefix, text, color):
        ts = datetime.now().strftime("%H:%M:%S")
        self.chat_display.append(
            f"<span style='color:#6e7681'>[{ts}]</span> "
            f"<span style='color:{color}; font-weight:bold'>{escape(prefix)}</span> "
            f"<span style='color:#c9d1d9'>{escape(text)}</span>"
        )

    def _update_status(self):
        self.provider_label.setText(self.active_service)
        if self.login_manager.is_logged_in(self.active_service):
            self.login_label.setText("logged in")
            self.login_label.setStyleSheet("color: #7ee787; font-size: 10pt; background: transparent;")
        else:
            self.login_label.setText("not logged in")
            self.login_label.setStyleSheet("color: #f85149; font-size: 10pt; background: transparent;")

    def _on_submit(self):
        text = self.input_field.text().strip()
        if not text or self._busy:
            return
        self.input_field.clear()

        if text.startswith("/"):
            self._append_user(text)
            response = self.command_parser.parse_command(text)
            if response:
                self._append_system(response)
        else:
            self._append_user(text)
            self._process_query(text)

    def _process_query(self, query):
        if not self.login_manager.is_logged_in(self.active_service):
            self._append_system(f"Please login first: /login {self.active_service}")
            return

        self.current_query = query
        full = self._build_contextual_query(query)
        self._append_system(f"-> {self.active_service}")
        self._set_busy(True)

        if not self.browser_handler.send_query(full):
            self._append_system("Error: failed to dispatch query")
            self._set_busy(False)

    def _build_contextual_query(self, query):
        recent = self.history_manager.get_recent(3)
        if not recent:
            return query
        lines = ["Previous context:"]
        for entry in recent:
            svc = entry.get("service", "?")
            q = (entry.get("query", "") or "").splitlines()[0][:80]
            r = (entry.get("response", "") or "")[:100].replace("\n", " ")
            lines.append(f"  [{svc}] Q:{q}  A:{r}")
        lines.append("Current question:")
        return "\n".join(lines) + "\n" + query

    def _on_response_ready(self, response):
        text = (response or "").strip()
        if text.startswith("Error:"):
            self._append_system(text)
        else:
            self._append_assistant(text)

        if self.current_query:
            self.history_manager.add_entry(self.current_query, text, self.active_service)
        self.current_query = None
        self._set_busy(False)

    def _switch_service(self, service):
        if service == self.active_service:
            return f"Already on {service}."
        self.active_service = service
        self.browser_handler.set_active_service(service)
        self._update_status()
        return f"Switched to {service}."

    def _handle_login(self, provider=""):
        target = provider.lower().strip() if provider.strip() else self.active_service
        if target not in ("chatgpt", "claude", "perplexity"):
            return f"Unknown provider '{provider}'. Use: chatgpt | claude | perplexity"
        if target != self.active_service:
            self.active_service = target
            self.browser_handler.set_active_service(target)

        self.browser_handler.begin_login(target)
        self._update_status()
        return f"Login window opened for {target}. Sign in there; you'll stay logged in afterwards."

    def _clear_all(self):
        self.history_manager.clear()
        self.chat_display.clear()
        self._append_system("Cleared chat and history.")
        return ""

    def _show_history(self):
        entries = self.history_manager.get_recent(10)
        if not entries:
            return "No history."
        self.chat_display.append(
            "<span style='color:#58a6ff'>─── history ───</span>"
        )
        for e in entries:
            ts = e.get("timestamp", "")[11:19]
            svc = e.get("service", "?")
            q = (e.get("query", "") or "").splitlines()[0][:80]
            r = (e.get("response", "") or "")[:120].replace("\n", " ")
            self.chat_display.append(
                f"<span style='color:#6e7681'>[{ts}]</span> "
                f"<span style='color:#d29922'>{escape(svc)}</span> "
                f"<span style='color:#c9d1d9'>Q: {escape(q)}</span><br>"
                f"<span style='color:#8b9499'>&nbsp;&nbsp;A: {escape(r)}</span>"
            )
        return ""

    def _handle_exit(self):
        QTimer.singleShot(0, self.close)
        return ""

    def closeEvent(self, event):
        self.browser_handler.shutdown()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WIAI")
    win = WIWIWidget()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()