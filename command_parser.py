import re

import providers

COMMANDS = [
    "chatgpt", "claude", "perplexity",
    "login", "history", "clear-all",
    "debug", "help", "helpme", "exit",
]


class CommandParser:

    def __init__(self):
        self.callbacks = {}

    def bind(self, **callbacks):
        self.callbacks.update(callbacks)

    def is_command(self, text: str) -> bool:
        return text.strip().startswith("/")

    def parse(self, text: str) -> str:
        match = re.match(r"/([a-zA-Z0-9_-]+)\s*(.*)", text.strip())
        if not match:
            return "Unknown command. Try /help"

        cmd = match.group(1).lower()
        args = match.group(2).strip()

        if cmd not in COMMANDS:
            return f"Unknown command '/{cmd}'. Try /help"

        if cmd in providers.ORDER:
            return self._call("switch", cmd)
        if cmd == "login":
            return self._call("login", args)
        if cmd == "history":
            return self._call("history")
        if cmd == "clear-all":
            return self._call("clear_all")
        if cmd == "debug":
            return self._call("debug")
        if cmd == "exit":
            return self._call("exit")
        if cmd in ("help", "helpme"):
            return self.help_text()
        return ""

    def _call(self, name, *args):
        cb = self.callbacks.get(name)
        return cb(*args) if cb else ""

    def help_text(self) -> str:
        rows = [
            ("/chatgpt", "switch to ChatGPT"),
            ("/claude", "switch to Claude"),
            ("/perplexity", "switch to Perplexity"),
            ("/login [provider]", "sign in (current provider if omitted)"),
            ("/history", "show recent history"),
            ("/clear-all", "clear output and stored history"),
            ("/debug", "show what extraction finds on the page"),
            ("/help, /helpme", "show this help"),
            ("/exit", "close the widget"),
        ]
        width = max(len(c) for c, _ in rows) + 3
        body = "\n".join(f"{c:<{width}}{d}" for c, d in rows)
        return "commands:\n" + body + "\n(plain text is sent to the active provider)"
