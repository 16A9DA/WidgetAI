import json
import os
from datetime import datetime

DEFAULT_PATH = os.path.expanduser("~/.wiai/history.json")
MAX_ENTRIES = 200


class HistoryManager:

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.entries = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return []

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.entries[-MAX_ENTRIES:], f, indent=2)
        except IOError:
            pass

    def add(self, provider: str, query: str, response: str):
        self.entries.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "provider": provider,
            "query": query,
            "response": response,
        })
        self.entries = self.entries[-MAX_ENTRIES:]
        self._save()

    def recent(self, count: int = 10):
        return self.entries[-count:]

    def clear(self):
        self.entries = []
        self._save()
