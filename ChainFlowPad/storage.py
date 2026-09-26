import json
import os

class StorageManager:
    """
    Handles persistence for ChainFlowPad.
    Saves and loads tab states (content, title, order).
    """
    def __init__(self, storage_path=None):
        if storage_path is None:
            # Default: Current Dir (Portable)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage_path = os.path.join(base_dir, ".scratch_session.json")
        else:
            self.storage_path = storage_path

    def save_state(self, tabs_data):
        """
        tabs_data: list of dicts [{"title": str, "content": str, "active": bool}]
        """
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({"tabs": tabs_data}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self):
        """
        Returns list of tab data or default if missing/corrupt.
        """
        if not os.path.exists(self.storage_path):
            return []
            
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("tabs", [])
        except Exception as e:
            print(f"Error loading state: {e}")
            return []
