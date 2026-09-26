import os
import sys
import json

class StorageManager:
    """データの永続化やロードを担当するユーティリティ"""
    
    @staticmethod
    def get_favorites_path():
        if getattr(sys, 'frozen', False):
            # EXE化されている場合、.exe ファイルの真横
            app_root = os.path.dirname(sys.executable)
        else:
            # 開発環境の場合、main.py の親(project_root)
            # core/storage.py の親(core)の親(project_root)
            app_root = os.path.dirname(os.path.dirname(__file__))
            
        return os.path.join(app_root, "favorites.json")
        
    @staticmethod
    def load_favorites():
        fav_path = StorageManager.get_favorites_path()
        if os.path.exists(fav_path):
            try:
                with open(fav_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading favorites: {e}")
        return []

    @staticmethod
    def save_favorites(favorites_data):
        fav_path = StorageManager.get_favorites_path()
        tmp_path = fav_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(favorites_data, f, indent=4, ensure_ascii=False)
            # アトミックに差し替え（書き込み中クラッシュによるJSON破損を防止）
            os.replace(tmp_path, fav_path)
        except Exception as e:
            print(f"Error saving favorites: {e}")
            # 一時ファイルが残っていたら削除
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
