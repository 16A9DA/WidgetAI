import sys
from datetime import datetime
from html import escape

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QLabel,
)

import providers
from browser_handler import BrowserHandler
from command_parser import CommandParser
from history_manager import HistoryManager
from login_manager import LoginManager

WIDTH = 460
COMPACT_H = 88          
EXPANDED_H = 520
EXPANDED_MIN_H = 220

STYLE = """
QWidget#root { background: #0b0e14; }
QLabel { background: transparent; }
QTextEdit {
    background: #0d1117; color: #c9d1d9;
    border: 1px solid #1f262d; border-radius: 3px;
    selection-background-color: #264f78; padding: 6px;
}
QLineEdit {
    background: #161b22; color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 3px; padding: 7px;
}
QLineEdit:focus { border: 1px solid #58a6ff; }
QLineEdit:read-only { color: #6e7681; }
"""


class WIAIWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("WIAI")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet(STYLE)
        self.resize(WIDTH, COMPACT_H)

        self.history = HistoryManager()
        self.logins = LoginManager()
        self.parser = CommandParser()
        self.browser = BrowserHandler(self.logins)

        self.active = "chatgpt"
        self._busy = False
        self._expanded = False
        self._pending_query = None

        self._build_ui()
        self._wire()
        self._collapse()
        self._refresh_status()

    def _build_ui(self):
        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(11)
        self.setFont(mono)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 8)
        root.setSpacing(6)

        top = QHBoxLayout()
        self.clock = self._label("--:--:--", "#8b949e")
        self.provider_lbl = self._label("chatgpt", "#58a6ff")
        self.login_lbl = self._label("…", "#8b949e")
        top.addWidget(self.clock)
        top.addStretch()
        top.addWidget(self.provider_lbl)
        top.addWidget(self._label("·", "#30363d"))
        top.addWidget(self.login_lbl)
        root.addLayout(top)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(self.font())
        root.addWidget(self.output, 1)

        self.input = QLineEdit()
        self.input.setFont(self.font())
        self.input.setPlaceholderText("type a prompt or /help …")
        self.input.returnPressed.connect(self._submit)
        root.addWidget(self.input)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick)
        self._clock_timer.start(1000)
        self._tick()

    def _label(self, text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: 10pt;")
        return lbl

    def _wire(self):
        self.parser.bind(
            switch=self._switch, login=self._login,
            history=self._show_history, clear_all=self._clear_all,
            debug=self._debug, exit=self._exit,
        )
        self.browser.response_ready.connect(self._on_response)
        self.browser.login_state_changed.connect(self._on_login_state)
        self.browser.login_page_loaded.connect(self._on_login_page)
        self.browser.debug_ready.connect(self._sys)
        self.logins.login_changed.connect(lambda *_: self._refresh_status())

    def _expand(self):
        if self._expanded:
            return
        self._expanded = True
        self.setMaximumHeight(16777215)
        self.setMinimumHeight(EXPANDED_MIN_H)
        self.output.show()
        self.resize(self.width(), EXPANDED_H)

    def _collapse(self):
        self._expanded = False
        self.output.hide()
        self.setMinimumHeight(0)
        self.resize(self.width(), COMPACT_H)
        self.setFixedHeight(COMPACT_H)   

    def _line(self, tag, text, color):
        self._expand()
        ts = datetime.now().strftime("%H:%M:%S")
        self.output.append(
            f"<span style='color:#6e7681'>[{ts}]</span> "
            f"<span style='color:{color};font-weight:bold'>{escape(tag)}</span> "
            f"<span style='color:#c9d1d9;white-space:pre-wrap'>{escape(text)}</span>"
        )
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

    def _sys(self, text):
        self._line("sys", text, "#8b949e")

    def _you(self, text):
        self._line("you", text, "#c9d1d9")

    def _ai(self, text):
        self._line(self.active, text, "#7ee787")

    def _tick(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def _refresh_status(self):
        self.provider_lbl.setText(self.active)
        if self.logins.is_logged_in(self.active):
            self.login_lbl.setText("logged in")
            self.login_lbl.setStyleSheet("color:#7ee787;font-size:10pt;")
        else:
            self.login_lbl.setText("not logged in")
            self.login_lbl.setStyleSheet("color:#f85149;font-size:10pt;")

    def _set_busy(self, busy):
        self._busy = busy
        self.input.setReadOnly(busy)
        self.input.setPlaceholderText("waiting for response …" if busy
                                      else "type a prompt or /help …")
        if not busy:
            self.input.setFocus()

    def _submit(self):
        text = self.input.text().strip()
        if not text or self._busy:
            return
        self.input.clear()
        self._you(text)

        if self.parser.is_command(text):
            result = self.parser.parse(text)
            if result:
                self._sys(result)
            return
        self._send(text)

    def _send(self, query):
        if not self.logins.is_logged_in(self.active):
            self._sys(f"not logged in — run /login {self.active} first")
            return
        self._pending_query = query
        self._sys(f"→ {self.active}")
        self._set_busy(True)
        if not self.browser.send_query(self._with_context(query)):
            self._sys("error: could not dispatch query")
            self._set_busy(False)

    def _with_context(self, query):
        recent = self.history.recent(3)
        if not recent:
            return query
        lines = ["Previous context (for continuity):"]
        for e in recent:
            q = (e.get("query", "") or "").splitlines()[0][:80]
            a = (e.get("response", "") or "")[:120].replace("\n", " ")
            lines.append(f"- [{e.get('provider')}] {q} => {a}")
        return "\n".join(lines) + f"\n\nCurrent question:\n{query}"

    def _on_response(self, text):
        text = (text or "").strip()
        if text.startswith("Error:"):
            self._sys(text.lower())
        else:
            self._ai(text)
            if self._pending_query:
                self.history.add(self.active, self._pending_query, text)
        self._pending_query = None
        self._set_busy(False)

    def _on_login_state(self, key, logged_in):
        self._sys(f"{key}: {'logged in' if logged_in else 'logged out'}")
        self._refresh_status()

    def _on_login_page(self, key, ok):
        if not ok:
            self._sys(f"{key}: login page failed to load — try again")

    def _switch(self, key):
        if key == self.active:
            return f"already on {key}"
        self.active = key
        self.browser.set_active(key)
        self._refresh_status()
        return f"switched to {key}"

    def _login(self, arg):
        key = (arg or self.active).lower().strip()
        if not providers.exists(key):
            return "usage: /login [chatgpt|claude|perplexity]"
        if key != self.active:
            self.active = key
            self.browser.set_active(key)
            self._refresh_status()
        self.browser.begin_login(key)
        return f"opened login window for {key} — sign in there; the widget stays open"

    def _show_history(self):
        entries = self.history.recent(10)
        if not entries:
            return "no history yet"
        self._expand()
        self.output.append("<span style='color:#58a6ff'>─── recent history ───</span>")
        for e in entries:
            q = (e.get("query", "") or "").splitlines()[0][:70]
            a = (e.get("response", "") or "")[:90].replace("\n", " ")
            self.output.append(
                f"<span style='color:#d29922'>[{escape(e.get('provider','?'))}]</span> "
                f"<span style='color:#c9d1d9'>{escape(q)}</span> "
                f"<span style='color:#6e7681'>= {escape(a)}…</span>"
            )
        return ""

    def _clear_all(self):
        self.history.clear()
        self.output.clear()
        self._collapse()
        return ""

    def _debug(self):
        self.browser.run_debug()
        return "running extraction probe on the active page…"

    def _exit(self):
        QTimer.singleShot(0, self.close)
        return ""

    def closeEvent(self, event):
        self.browser.shutdown()
        super().closeEvent(event)
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WIAI")
    app.setQuitOnLastWindowClosed(False)  
    widget = WIAIWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
