import re


class CommandParser:

    def __init__(self):
        self.callbacks = {
            "switch": None,
            "login": None,
            "clear_all": None,
            "history": None,
            "exit": None,
            "helpme": None,
        }
        self.valid_commands = [
            "chatgpt", "claude", "perplexity",
            "login", "clear-all", "history",
            "help", "helpme", "exit",
        ]

    def set_callbacks(
        self, switch=None, login=None, clearAll=None, history=None, exit=None
    ):
        if switch:
            self.callbacks["switch"] = switch
        if login:
            self.callbacks["login"] = login
        if clearAll:
            self.callbacks["clear_all"] = clearAll
        if history:
            self.callbacks["history"] = history
        if exit:
            self.callbacks["exit"] = exit

    def parse_command(self, command_text):
        command_text = command_text.strip()

        match = re.match(r"/([a-zA-Z0-9_-]+)\s*(.*)", command_text)
        if not match:
            return "Unknown command format. Use /command [args]"

        command = match.group(1).lower()
        args = match.group(2).strip() if match.group(2) else ""

        if command not in self.valid_commands:
            return "Unknown command. Use /helpme to see available commands"

        if command in ["chatgpt", "claude", "perplexity"]:
            if self.callbacks["switch"]:
                return self.callbacks["switch"](command)
            return f"Switching to {command}..."

        elif command == "login":
            if self.callbacks["login"]:
                return self.callbacks["login"](args)
            return "Login functionality not implemented"

        elif command == "clear-all":
            if self.callbacks["clear_all"]:
                return self.callbacks["clear_all"]()
            return "Clear all functionality not implemented"

        elif command == "history":
            if self.callbacks["history"]:
                return self.callbacks["history"]()
            return "History functionality not implemented"

        elif command == "help" or command == "helpme":
            return self._help_text()

        elif command == "exit":
            if self.callbacks["exit"]:
                return self.callbacks["exit"]()
            return "Exit functionality not implemented"

    def _help_text(self):
        lines = [
            ("/chatgpt", "Switch to ChatGPT service"),
            ("/claude", "Switch to Claude service"),
            ("/perplexity", "Switch to Perplexity service"),
            ("/login [provider]", "Login to provider (chatgpt/claude/perplexity)"),
            ("/history", "Show conversation history"),
            ("/clear-all", "Clear chat and history"),
            ("/helpme", "Show this help message"),
            ("/exit", "Exit the widget"),
        ]
        max_cmd = max(len(cmd) for cmd, _ in lines)
        return "\n".join(f"  {cmd:<{max_cmd + 2}}{desc}" for cmd, desc in lines)
