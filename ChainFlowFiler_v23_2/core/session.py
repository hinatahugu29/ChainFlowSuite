"""
v23.2: Refactoring: MainWindow から抽出されたセッション管理モジュール
"""
import json
import os
import sys
from PySide6.QtCore import Qt

class SessionManager:
    def __init__(self, main_window, session_file):
        self.win = main_window
        self.session_file = session_file

    def load_session(self):
        """セッション復元"""
        if not os.path.exists(self.session_file): return
        
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session = json.load(f)
                
            # Geometry
            if "geometry" in session:
                self.win.restoreGeometry(bytes.fromhex(session["geometry"]))
                
            # Splitter State
            if "splitter_state" in session:
                self.win.main_splitter.restoreState(bytes.fromhex(session["splitter_state"]))
            
            # Tabs
            tabs_data = session.get("tabs", [])
            if not tabs_data: return
            
            # 既存タブをクリア
            while self.win.tab_widget.count() > 0:
                widget = self.win.tab_widget.widget(0)
                self.win.tab_widget.removeTab(0)
                if widget: widget.deleteLater()
                
            from widgets.main_window import FlowArea # 回避策としてのインポート
            
            for i, t_data in enumerate(tabs_data):
                area = FlowArea(self.win)
                title = t_data.get("title", "Workspace")
                idx = self.win.tab_widget.addTab(area, title)
                area.restore_state(t_data.get("state", {}))
                
                # ダイナミックネームの適用
                if hasattr(area, 'get_representative_name'):
                    dynamic_name = area.get_representative_name()
                    self.win.tab_widget.setTabText(idx, dynamic_name)
                
            active_tab = session.get("active_tab_index", 0)
            if 0 <= active_tab < self.win.tab_widget.count():
                self.win.tab_widget.setCurrentIndex(active_tab)
                
        except Exception as e:
            print(f"Failed to load session: {e}", file=sys.stderr)
            # フォールバック
            if self.win.tab_widget.count() == 0:
                self.win.add_new_tab()

    def save_session(self):
        """現在の状態を保存"""
        session = {}
        
        # Geometry
        session["geometry"] = self.win.saveGeometry().toHex().data().decode()
        
        # Splitter
        session["splitter_state"] = self.win.main_splitter.saveState().toHex().data().decode()
        
        # Tabs
        tabs_data = []
        for i in range(self.win.tab_widget.count()):
            area = self.win.tab_widget.widget(i)
            # if isinstance(area, FlowArea):
            if hasattr(area, 'get_state'):
                tabs_data.append({
                    "title": self.win.tab_widget.tabText(i),
                    "state": area.get_state()
                })
        session["tabs"] = tabs_data
        session["active_tab_index"] = self.win.tab_widget.currentIndex()
        
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save session: {e}", file=sys.stderr)
