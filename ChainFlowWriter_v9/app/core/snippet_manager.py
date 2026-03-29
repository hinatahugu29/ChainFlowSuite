import json
import os
import uuid
from datetime import datetime

class SnippetManager:
    def __init__(self, data_dir="snippets_data"):
        self.data_dir = data_dir
        self.json_path = os.path.join(self.data_dir, "snippets.json")
        self.thumbnail_dir = os.path.join(self.data_dir, "thumbnails")
        self.snippets = []
        self._ensure_dirs()
        self.load_snippets()

    def _ensure_dirs(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    def load_snippets(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.snippets = json.load(f)
            except Exception as e:
                print(f"Error loading snippets: {e}")
                self.snippets = []
        else:
            self.snippets = []

    def save_snippets(self):
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.snippets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving snippets: {e}")

    def add_snippet(self, title, tags, content, thumbnail_filename=None):
        snippet_id = str(uuid.uuid4())
        new_snippet = {
            "id": snippet_id,
            "title": title,
            "tags": tags,
            "content": content,
            "thumbnail": thumbnail_filename,
            "created_at": datetime.now().isoformat()
        }
        self.snippets.append(new_snippet)
        self.save_snippets()
        return snippet_id

    def delete_snippet(self, snippet_id):
        """Removes a snippet from the list and deletes its thumbnail file."""
        for i, s in enumerate(self.snippets):
            if s.get("id") == snippet_id:
                # 1. Delete thumbnail file if it exists
                thumb_file = s.get("thumbnail")
                if thumb_file:
                    thumb_path = os.path.join(self.thumbnail_dir, thumb_file)
                    try:
                        if os.path.exists(thumb_path):
                            os.remove(thumb_path)
                    except Exception as e:
                        print(f"Error deleting thumbnail file: {e}")

                # 2. Remove from list
                self.snippets.pop(i)
                self.save_snippets()
                return True
        return False

    def get_snippet(self, snippet_id):
        """Retrieves a single snippet by its UUID."""
        for s in self.snippets:
            if s.get("id") == snippet_id:
                return s
        return None

    def get_all_snippets(self):
        return self.snippets


