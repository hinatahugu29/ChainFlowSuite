import os
import sys
import json
from collections import Counter

class HistoryManager:
    """
    Manages search directory history, including recent and frequent folders.
    Also provides access to ChainFlow Filer favorites.
    """
    def __init__(self, history_file="search_history.json"):
        # Resolve history file path relative to the application
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.history_file = os.path.join(base_dir, history_file)
        self.filer_favorites_file = os.path.join(os.path.dirname(base_dir), "favorites.json")
        
        self.recent_limit = 10
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Expecting {"recent": [], "counts": {}}
                    if "recent" not in data: data["recent"] = []
                    if "counts" not in data: data["counts"] = {}
                    return data
            except Exception as e:
                print(f"Failed to load history: {e}")
        return {"recent": [], "counts": {}}

    def save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def add_visit(self, path):
        """Add a directory visit to history."""
        if not path or not os.path.isdir(path):
            return
            
        path = os.path.abspath(path)
        
        # 1. Update Recent
        recent = self.history.get("recent", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.history["recent"] = recent[:self.recent_limit]
        
        # 2. Update Frequency
        counts = self.history.get("counts", {})
        counts[path] = counts.get(path, 0) + 1
        self.history["counts"] = counts
        
        self.save_history()

    def get_recent(self):
        """Return list of recent directories (existing ones only)."""
        return [p for p in self.history.get("recent", []) if os.path.exists(p)]

    def get_frequent(self, limit=10):
        """Return list of frequent directories sorted by access count."""
        counts = self.history.get("counts", {})
        # Filter existing paths
        valid_counts = {p: c for p, c in counts.items() if os.path.exists(p)}
        
        # Sort by count descending, then by path
        sorted_paths = sorted(valid_counts.keys(), key=lambda x: (-valid_counts[x], x))
        return sorted_paths[:limit]

    def get_filer_favorites(self):
        """Try to load favorites from ChainFlow Filer."""
        if os.path.exists(self.filer_favorites_file):
            try:
                with open(self.filer_favorites_file, "r", encoding="utf-8") as f:
                    paths = json.load(f)
                    return [p for p in paths if os.path.exists(p)]
            except Exception:
                pass
        return []
