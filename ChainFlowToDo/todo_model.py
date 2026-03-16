import json
import os
from datetime import datetime

class ToDoModel:
    def __init__(self, storage_path="todo_data.json"):
        self.storage_path = storage_path
        self.data = self.load()

    def load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_category(self, name):
        category = {
            "name": name,
            "items": [],
            "open": True
        }
        self.data.append(category)
        self.save()
        return category

    def delete_category(self, index):
        if 0 <= index < len(self.data):
            self.data.pop(index)
            self.save()

    def add_task(self, cat_index, text, priority="low"):
        if 0 <= cat_index < len(self.data):
            task = {
                "text": text,
                "checked": False,
                "added": datetime.now().strftime("%Y/%m/%d %H:%M"),
                "priority": priority
            }
            self.data[cat_index]["items"].append(task)
            self.save()
            return task
        return None

    def delete_task(self, cat_index, task_index):
        if 0 <= cat_index < len(self.data):
            if 0 <= task_index < len(self.data[cat_index]["items"]):
                self.data[cat_index]["items"].pop(task_index)
                self.save()

    def toggle_task(self, cat_index, task_index):
        if 0 <= cat_index < len(self.data):
            if 0 <= task_index < len(self.data[cat_index]["items"]):
                self.data[cat_index]["items"][task_index]["checked"] = not self.data[cat_index]["items"][task_index]["checked"]
                self.save()
