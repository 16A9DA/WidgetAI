import re


class CommandParser:

    def __init__(self):
        self.callbacks = {
            "switch_service": None,
            "login": None,
            "clear_all": None,
            "show_history": None,
        }

    def set_callbacks(
        self, switch_service=None, login=None, clear_all=None, show_history=None
    ):
        if switch_service:
            self.callbacks["switch_service"] = switch_service
        if login:
            self.callbacks["login"] = login
        if clear_all:
            self.callbacks["clear_all"] = clear_all
        if show_history:
            self.callbacks["show_history"] = show_history

    def parse_command(self, command_text):
        command_text = command_text.strip()

        match = re.match(r"/(\w+)(?:\s+(.*))?", command_text)
        if not match:
            return "Unknown command format. Use /command [args]"

        command = match.group(1).lower()
        args = match.group(2) if match.group(2) else ""

        if command in ["chatgpt", "claude", "perplexity"]:
            if self.callbacks["switch_service"]:
                return self.callbacks["switch_service"](command)
            return f"Switching to {command}..."

        elif command == "login":
            if self.callbacks["login"]:
                return self.callbacks["login"]()
            return "Login functionality not implemented"

        elif command == "clear-all":
            if self.callbacks["clear_all"]:
                return self.callbacks["clear_all"]()
            return "Clear all functionality not implemented"

        elif command == "history":
            if self.callbacks["show_history"]:
                return self.callbacks["show_history"]()
            return "History functionality not implemented"

        elif command == "helpme":
            return (
                "Available commands: /chatgpt, /claude, /perplexity, /login, /history, /clear-all, /helpme\n"
                "/chatgpt - Switch to ChatGPT service\n"
                "/claude - Switch to Claude service\n"
                "/perplexity - Switch to Perplexity service\n"
                "/login - Login to current service\n"
                "/history - Show conversation history\n"
                "/clear-all - Clear chat and history\n"
                "/helpme - Show this help message"
            )

        else:
            return f"Unknown command: {command}. Available commands: /chatgpt, /claude, /perplexity, /login, /history, /clear-all, /helpme"
