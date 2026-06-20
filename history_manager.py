"""
History manager for storing and retrieving conversation history.
"""

import json
import os
from datetime import datetime


class HistoryManager:
    """Manages conversation history."""

    def __init__(self, history_file="history.json"):
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self):
        """Load history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't save

    def add_entry(self, query, response, service):
        """Add a new entry to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'service': service
        }
        self.history.append(entry)
        self.save_history()

    def get_history(self):
        """Get all history entries."""
        return self.history.copy()

    def clear(self):
        """Clear all history."""
        self.history = []
        self.save_history()

    def get_recent(self, count=10):
        """Get recent history entries."""
        return self.history[-count:] if self.history else []
