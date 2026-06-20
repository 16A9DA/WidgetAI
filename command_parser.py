"""
Command parser for handling slash commands.
"""

import re


class CommandParser:
    """Parses and executes slash commands."""

    def __init__(self):
        self.callbacks = {
            'switch_service': None,
            'login': None,
            'clear_all': None,
            'show_history': None
        }

    def set_callbacks(self, switch_service=None, login=None, clear_all=None, show_history=None):
        """Set callback functions for commands."""
        if switch_service:
            self.callbacks['switch_service'] = switch_service
        if login:
            self.callbacks['login'] = login
        if clear_all:
            self.callbacks['clear_all'] = clear_all
        if show_history:
            self.callbacks['show_history'] = show_history

    def parse_command(self, command_text):
        """Parse a command text and execute the appropriate action."""
        command_text = command_text.strip()

        # Match command format: /command [args]
        match = re.match(r'/(\w+)(?:\s+(.*))?', command_text)
        if not match:
            return "Unknown command format. Use /command [args]"

        command = match.group(1).lower()
        args = match.group(2) if match.group(2) else ""

        # Handle commands
        if command in ['chatgpt', 'claude', 'perplexity']:
            if self.callbacks['switch_service']:
                return self.callbacks['switch_service'](command)
            return f"Switching to {command}..."

        elif command == 'login':
            if self.callbacks['login']:
                return self.callbacks['login']()
            return "Login functionality not implemented"

        elif command == 'clear-all':
            if self.callbacks['clear_all']:
                return self.callbacks['clear_all']()
            return "Clear all functionality not implemented"

        elif command == 'history':
            if self.callbacks['show_history']:
                return self.callbacks['show_history']()
            return "History functionality not implemented"

        else:
            return f"Unknown command: {command}. Available commands: /chatgpt, /claude, /perplexity, /login, /clear-all, /history"

