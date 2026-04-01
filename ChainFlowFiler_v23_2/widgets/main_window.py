import os
import sys
import json
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
                               QTabWidget, QTabBar, QApplication, QMenu, QInputDialog, QLineEdit, QMessageBox)
import subprocess
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon

from .navigation_pane import NavigationPane
from .quick_look import QuickLookWindow
from core.plugin_manager import PluginManager
from .flow_area import FlowArea
from core import same_path
from core.session import SessionManager

class ChainFlowFiler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.plugin_manager = PluginManager()
        self.setWindowTitle("ChainFlow Filer v23.2")
        self.resize(1800, 950)
        
        # Dark Title Bar moved to showEvent for Windows compatibility (v20.0)

        # --- v6.11 Icon Settings ---
        icon_path = ""
        # 1. PyInstallerバンドル内（一時フォルダ）のリソースを探す
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS はPyInstallerが一時的にファイルを展開する場所
            bundle_dir = sys._MEIPASS
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # 2. 通常実行時はスクリプトと同じディレクトリを探す
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------------
        
        self.hovered_pane = None
        self.internal_clipboard = {"paths": [], "mode": "copy"} # v6.2 一括操作用
        self.editor_processes = []  # v16.2 Track spawned editor processes
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Address Bar Area
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(5, 5, 5, 5)
        self.toolbar_layout.setSpacing(5)
        
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter path here...")
        self.address_bar.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #ccc;
                border: 1px solid #555;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                color: #fff;
            }
        """)
        self.address_bar.returnPressed.connect(self.on_address_return)
        self.toolbar_layout.addWidget(self.address_bar)
        
        self.main_layout.addLayout(self.toolbar_layout)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        # self.main_splitter.setChildrenCollapsible(False) # 従来
        self.main_splitter.setChildrenCollapsible(True) # v9.2 サイドバーを完全に消せるようにする
        self.main_layout.addWidget(self.main_splitter)
        
        # 左：ナビゲーション
        self.nav = NavigationPane(self)
        self.main_splitter.addWidget(self.nav)
        
        # 中央：タブ付きフロー領域
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        # タブバーのスタイルなど適宜調整
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2d2d2d; color: #ccc; padding: 5px 10px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; font-weight: bold; }
            QTabBar::tab:hover { background: #3e3e3e; }
        """)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        self.main_splitter.addWidget(self.tab_widget)

        # QuickLook (Hidden by default)
        self.quick_look = QuickLookWindow(self)
        
        # 初期タブ追加
        self.add_new_tab()
        
        # 全体の初期レイアウト比率を設定 (サイドバー, フローエリア)
        self.main_splitter.setSizes([240, 1550])
        
        self.setup_shortcuts()
        self.apply_theme()
        
        # タブバーの拡張
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # セッション復元 (v6.10 Portable対応: 実行ファイルと同階層に保存)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.session_file = os.path.join(base_dir, "session.json")
        self.session_manager = SessionManager(self, self.session_file)
        self.session_manager.load_session()

        from .slash_menu import SlashMenu # v16.0
        self.slash_menu = SlashMenu(self)
        self.slash_menu.command_selected.connect(self.execute_slash_command)

        # Register Commands
        self.slash_commands = [
            {"id": "new_file", "label": "New File", "desc": "Create a new file in current folder"},
            {"id": "new_folder", "label": "New Folder", "desc": "Create a new folder"},
            {"id": "toggle_sidebar", "label": "Toggle Sidebar", "desc": "Show/Hide Navigation Pane"},
            {"id": "copy_path", "label": "Copy Path", "desc": "Copy current path to clipboard"},
            {"id": "launch_editor", "label": "Launch Editor", "desc": "Open integrated editor"},
            {"id": "merge_pdfs", "label": "Merge PDFs", "desc": "Combine multiple PDF files"},
            {"id": "settings", "label": "Settings", "desc": "Open Application Settings"},
            {"id": "reload", "label": "Reload Window", "desc": "Refresh all panes"},
            {"id": "todo", "label": "ToDo List", "desc": "Open ChainFlow ToDo Task Manager"},
            {"id": "search_folder", "label": "Search in Folder", "desc": "Search files in current directory"},
            {"id": "design_canvas", "label": "ChainFlow Designer", "desc": "Design canvas for DTP editing"},
            {"id": "pdf_studio", "label": "Py PDF Studio", "desc": "Launch PDF Studio Application"},
            {"id": "pdf_compare", "label": "ChainFlow PDF Compare", "desc": "Advanced multi-view PDF comparison"},
            {"id": "writer_tool", "label": "Open with ChainFlow Writer", "desc": "Professional Markdown writer"},
            {"id": "sniper_shell", "label": "Sniper Research Shell", "desc": "Information extraction browser station"},
        ]
        self.slash_menu.set_commands(self.slash_commands)
        
        # Shortcut for Slash Menu
        # v16.1 Fix: Use ApplicationShortcut to ensure it triggers globally
        # Added Ctrl+P as a standard Command Palette alternative
        for seq in ["Ctrl+P"]:
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(self.toggle_slash_menu)
        
        # F11 Fullscreen
        fs_shortcut = QShortcut(QKeySequence("F11"), self)
        fs_shortcut.activated.connect(self.toggle_fullscreen)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def toggle_slash_menu(self):
        print("Toggle Slash Menu Triggered")
        if self.slash_menu.isVisible():
            self.slash_menu.fade_out()
        else:
            self.slash_menu.popup(self.geometry())

    def execute_slash_command(self, cmd_id):
        # Dispatcher
        if cmd_id == "new_file":
            self.run_on_hovered(lambda p: p.action_new_file(None, None)) # Hacky args
        elif cmd_id == "new_folder":
            self.run_on_hovered(lambda p: p.action_new_folder())
        elif cmd_id == "toggle_sidebar":
            self.toggle_sidebar()
        elif cmd_id == "copy_path":
            self.run_on_hovered(lambda p: p.action_copy())
        elif cmd_id == "launch_editor":
            # Just launch editor with current path
             if self.hovered_pane:
                 p = self.hovered_pane.get_current_selected_path()
                 if p: self.launch_editor(p)
                 else: self.launch_editor(None) # Empty editor
        elif cmd_id == "reload":
            self.refresh_all_panes()
        elif cmd_id == "todo":
            self.launch_todo()
        elif cmd_id == "settings":
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Settings", "Settings Dialog Placeholder")
        elif cmd_id == "merge_pdfs":
            self.launch_pdf_merger()
        elif cmd_id == "search_folder":
            self.launch_search_tool()
        elif cmd_id == "design_canvas":
            self.launch_designer()
        elif cmd_id == "pdf_studio":
            self.launch_pdf_studio()
        elif cmd_id == "pdf_compare":
            self.launch_pdf_compare()
        elif cmd_id == "writer_tool":
            self.launch_writer()
        elif cmd_id == "sniper_shell":
            self.launch_sniper()

    def launch_pdf_merger(self):
        # 1. Gather selected PDFs from hovered pane (or active pane)
        initial_files = []
        target_pane = self.hovered_pane
        
        # Fallback to active lane's last pane if no hover
        if not target_pane and self.current_flow_area and self.current_flow_area.active_lane:
             panes = self.current_flow_area.active_lane.panes
             if panes: target_pane = panes[-1]

        if target_pane:
            # Check for multiple selection
            try:
                selected_paths = target_pane.get_selected_paths()
                # If nothing selected, maybe just current folder? No, usually expect files for merger.
                # But user said: "無選択→実行...". So it's okay to pass empty.
                if selected_paths:
                    for p in selected_paths:
                        if os.path.isfile(p) and p.lower().endswith('.pdf'):
                            initial_files.append(p)
            except Exception as e:
                print(f"Error gathering files for merger: {e}")

        # 2. Launch Window
        from .pdf_merger import PDFMergerWindow
        # Keep reference to prevent GC
        self.pdf_merger_window = PDFMergerWindow(self, initial_files)
        self.pdf_merger_window.show()

    def launch_pdf_compare(self):
        """v21.0 Launch ChainFlowPDFCompare via PluginManager"""
        print("[DEBUG] launch_pdf_compare called")
        
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "pdf_compare"), None)
        if not tool_def:
            # Fallback define if not in tools.json for some reason
            tool_def = {
                "name": "ChainFlow PDF Compare",
                "id": "pdf_compare",
                "extensions": [".pdf"],
                "executable_path": "../ChainFlowPDFCompare/ChainFlowPDFCompare.exe",
                "script_path": "../ChainFlowPDFCompare/main.py",
                "arguments": ["{FILE_PATH}"]
            }
        
        # Determine target path (current folder or selected file)
        target_path = None
        if self.hovered_pane:
            target_path = self.hovered_pane.get_current_selected_path()
            if not target_path and self.hovered_pane.current_paths:
                target_path = self.hovered_pane.current_paths[0]
        
        if not target_path:
            target_path = os.getcwd()
            
        self.plugin_manager.launch_tool(tool_def, target_path, self)

    def launch_pdf_studio(self):
        """v21.0 Launch ChainFlowPDFStudio via PluginManager"""
        print("[DEBUG] launch_pdf_studio called")
        
        # Dynamic Tool Definition
        # Note: Paths are relative to PluginManager's root_dir (which is ChainFlowFiler_v21/core/../)
        # So we use ../ChainFlowPDFStudio to reach sibling directory
        tool_def = {
            "name": "ChainFlow PDF Studio",
            "id": "pdf_studio",
            "extensions": [],
            # Frozen: dist/ChainFlowFiler/ -> ../ChainFlowPDFStudio/ChainFlowPDFStudio.exe (assuming suite structure)
            "executable_path": "../ChainFlowPDFStudio/ChainFlowPDFStudio.exe", 
            # Dev: ChainFlowFiler_v21/ -> ../ChainFlowPDFStudio/app/main.py (assuming sibling repo)
            "script_path": "../ChainFlowPDFStudio/app/main.py",
            "arguments": []
        }
        
        target_path = os.getcwd()
        self.plugin_manager.launch_tool(tool_def, target_path, self)

    def launch_designer(self):
        """v21.0 Launch ChainFlowDesigner via PluginManager"""
        print("[DEBUG] launch_designer called")
        
        # 1. Find Designer Tool Config
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "designer_tool"), None)
        if not tool_def:
            print("[DEBUG] Designer tool NOT FOUND in tools.json")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Designer Tool", "Designer tool not configured in tools.json")
            return
        
        # 2. Determine Initial Path
        target_path = None
        if self.hovered_pane and hasattr(self.hovered_pane, 'current_paths') and self.hovered_pane.current_paths:
             target_path = self.hovered_pane.current_paths[0]
        elif self.current_flow_area and self.current_flow_area.active_lane:
             lane = self.current_flow_area.active_lane
             if lane.panes:
                 pane = lane.panes[-1]
                 if hasattr(pane, 'current_paths') and pane.current_paths:
                     target_path = pane.current_paths[0]
        
        if not target_path:
            target_path = os.getcwd()

        print(f"[Designer] Initial path: {target_path}")

        # 3. Launch via PluginManager
        result = self.plugin_manager.launch_tool(tool_def, target_path, self)
        print(f"[Designer] Launch result: {result}")

    def launch_writer(self):
        """v21.1 Launch ChainFlowWriter via PluginManager"""
        print("[DEBUG] launch_writer called")
        
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "writer_tool"), None)
        if not tool_def:
            # Fallback define if not in tools.json
            tool_def = {
                "name": "ChainFlow Writer",
                "id": "writer_tool",
                "extensions": [".md"],
                "executable_path": "../ChainFlowWriter/ChainFlowWriter.exe",
                "script_path": "../ChainFlowWriter/main.py",
                "arguments": ["{FILE_PATH}"]
            }
        
        target_path = None
        if self.hovered_pane:
            target_path = self.hovered_pane.get_current_selected_path()
            if not target_path and self.hovered_pane.current_paths:
                target_path = self.hovered_pane.current_paths[0]
        
        if not target_path:
            target_path = os.getcwd()
            
        self.plugin_manager.launch_tool(tool_def, target_path, self)

    def launch_sniper(self):
        """v22.1 Launch Sniper Research Shell via PluginManager"""
        print("[DEBUG] launch_sniper called")
        
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "sniper_shell"), None)
        if not tool_def:
            # Fallback define
            tool_def = {
                "name": "Sniper Research Shell",
                "id": "sniper_shell",
                "extensions": [],
                "executable_path": "../ChainFlowSniper/ChainFlowSniper.exe",
                "script_path": "../ChainFlowSniper/main.py",
                "arguments": ["{FILE_PATH}"]
            }
        
        target_path = None
        if self.hovered_pane:
            target_path = self.hovered_pane.get_current_selected_path()
            if not target_path and self.hovered_pane.current_paths:
                target_path = self.hovered_pane.current_paths[0]
        
        if not target_path:
            target_path = os.getcwd()
            
        self.plugin_manager.launch_tool(tool_def, target_path, self)

    def launch_search_tool(self):
        """v20.0 Launch ChainFlowSearch in current folder"""
        print("[DEBUG] launch_search_tool called")
        
        # 1. Find Search Tool Config
        print(f"[DEBUG] Loaded tools count: {len(self.plugin_manager.tools)}")
        for t in self.plugin_manager.tools:
            print(f"[DEBUG]   - Tool: {t.get('name')} (id={t.get('id')})")
        
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "search_tool"), None)
        if not tool_def:
            print("[DEBUG] Search tool NOT FOUND in tools.json")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Search Tool", "Search tool not configured in tools.json")
            return
        
        print(f"[DEBUG] Search tool found: {tool_def}")

        # 2. Determine Target Directory
        target_path = None
        if self.hovered_pane and hasattr(self.hovered_pane, 'current_paths') and self.hovered_pane.current_paths:
             target_path = self.hovered_pane.current_paths[0]  # First path in the pane
        elif self.current_flow_area and self.current_flow_area.active_lane:
             # Active pane in active lane
             lane = self.current_flow_area.active_lane
             if lane.panes:
                 pane = lane.panes[-1]
                 if hasattr(pane, 'current_paths') and pane.current_paths:
                     target_path = pane.current_paths[0]
        
        if not target_path:
            target_path = os.getcwd()
        
        print(f"[DEBUG] Target path: {target_path}")

        # 3. Launch via PluginManager
        result = self.plugin_manager.launch_tool(tool_def, target_path, self)
        print(f"[DEBUG] launch_tool result: {result}")

    def closeEvent(self, event):
        if hasattr(self, 'session_manager'):
            self.session_manager.save_session()
        
        # v19.0: Terminate all tools launched via PluginManager
        if self.plugin_manager:
            self.plugin_manager.terminate_all()
        
        # v16.2: Terminate any other spawned processes (like ToDo)
        for proc in self.editor_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
        self.editor_processes.clear()
        
        super().closeEvent(event)

    
    def showEvent(self, event):
        # Re-apply dark title bar on show to ensure it takes effect (env dependent)
        try:
            from .ui_utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except Exception as e:
            print(f"showEvent: Failed to apply dark title bar: {e}")
        super().showEvent(event)

    # session_manager への委譲により load_session / save_session は削除されました

    def show_tab_context_menu(self, pos):
        idx = self.tab_widget.tabBar().tabAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        
        # Actions
        new_tab_act = QAction("New Tab", self)
        new_tab_act.triggered.connect(self.add_new_tab)
        menu.addAction(new_tab_act)
        
        if idx >= 0:
            dup_act = QAction("Duplicate Tab", self)
            dup_act.triggered.connect(lambda: self.duplicate_tab(idx))
            
            rename_act = QAction("Rename Tab", self)
            rename_act.triggered.connect(lambda: self.rename_tab(idx))
            
            close_act = QAction("Close Tab", self)
            close_act.triggered.connect(lambda: self.close_tab(idx))
            
            menu.addSeparator()
            menu.addAction(dup_act)
            menu.addAction(rename_act)
            menu.addSeparator()
            menu.addAction(close_act)
            
        menu.exec(self.tab_widget.mapToGlobal(pos))

    def rename_tab(self, index):
        if index < 0: return
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Tab", "Tab Name:", text=current_name)
        if ok and new_name:
            self.tab_widget.setTabText(index, new_name)

    def duplicate_tab(self, index):
        if index < 0: return
        source_area = self.tab_widget.widget(index)
        if isinstance(source_area, FlowArea):
            new_area = source_area.duplicate()
            current_name = self.tab_widget.tabText(index)
            new_idx = self.tab_widget.addTab(new_area, f"{current_name} (Copy)")
            self.tab_widget.setCurrentIndex(new_idx)

    def set_active_pane(self, pane):
        """v6.4 最後にホバーしたペインを永続的にハイライトする管理メソッド"""
        if self.hovered_pane == pane:
            return
            
        # 以前のアクティブペインのハイライトをオフにする
        if self.hovered_pane:
            try:
                self.hovered_pane.highlight(False)
            except RuntimeError: # 削除済みの場合
                pass

        # サイドバーのアクティブ表示もオフにする
        if hasattr(self, 'nav'):
            self.nav.set_active(False)
                
        # 新しいアクティブペインをセットしてハイライト
        self.hovered_pane = pane
        if self.hovered_pane:
            self.hovered_pane.highlight(True)
            # v19.1: アクティブペインのフォルダ名をタブ名に反映
            self.update_current_tab_title()

    def setup_shortcuts(self):
        # --- ペイン基本操作 ---
        QShortcut(QKeySequence("N"), self).activated.connect(self.add_pane_to_hovered_lane)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self.go_up_hovered)
        QShortcut(QKeySequence("F"), self).activated.connect(self.toggle_favorites_focus)
        QShortcut(QKeySequence("."), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.toggle_hidden()))
        QShortcut(QKeySequence("V"), self).activated.connect(self.split_lane_vertically)
        
        # --- QuickLook / Global ---
        QShortcut(QKeySequence("Space"), self).activated.connect(self.toggle_quick_look)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close_quick_look)



        # --- v6.7 統合ショートカット・ディスパッチャ (Q,A,Z,W,S,X,E,D,C) ---
        # これらは「お気に入り欄にフォーカスがあるか」で挙動が変わる
        self.hk_map = {"Q":0, "A":1, "Z":2, "W":3, "S":4, "X":5, "E":6, "D":7, "C":8}
        for key in self.hk_map:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda k=key: self.dispatch_shortcut(k))

        # --- 標準ファイル操作 (v6.2) ---
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_copy()))
        QShortcut(QKeySequence("Ctrl+X"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_cut()))
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_paste()))
        QShortcut(QKeySequence("Delete"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_delete()))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_rename()))
        
        # v10.1 Shift+W: ペイン内のビュー分割を減らす（末尾削除）
        QShortcut(QKeySequence("Shift+W"), self).activated.connect(self.remove_hovered_view)

        # --- タブ・基本システム ---
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.focus_address_bar)
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(self.focus_address_bar)
        
        # --- v9.2 サイドバー開閉 ---
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.toggle_sidebar)

        # --- v13.0 レイアウト均等リセット ---
        QShortcut(QKeySequence("Ctrl+Shift+R"), self).activated.connect(self.reset_layout)

    @property
    def current_flow_area(self) -> FlowArea:
        w = self.tab_widget.currentWidget()
        if isinstance(w, FlowArea):
            return w
        return None

    def add_new_tab(self):
        new_area = FlowArea(self)
        idx = self.tab_widget.addTab(new_area, f"Workspace {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(idx)
        # v19.1: タブ追加直後に動的名前を設定
        self.update_current_tab_title()

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())
    
    def remove_hovered_view(self):
        """Shift+W: ホバー中のペインの一番下のビューを削除"""
        if self.hovered_pane:
            self.hovered_pane.pop_active_view()

    def on_tab_changed(self, index):
        area = self.tab_widget.widget(index)
        if not isinstance(area, FlowArea):
            return
        
        # v21.5 Performance Fix: タブ切替時のペイント一括化
        # 全ビューの描画を一時停止してからアドレスバー等を更新し、
        # 最後に一括で描画を再開することで同期paintの連鎖を回避。
        all_views = []
        for lane in area.lanes:
            for pane in lane.panes:
                for view, _, _, _ in pane.views:
                    view.setUpdatesEnabled(False)
                    all_views.append(view)
        
        lane = area.active_lane
        if lane and lane.panes and lane.panes[0].current_paths:
            self.update_address_bar(lane.panes[0].current_paths[0])
        
        # v19.1: タブ切り替え時に名前を更新
        self.update_current_tab_title()
        
        # 全ビューの描画を再開（一括再描画が走る）
        for view in all_views:
            view.setUpdatesEnabled(True)

    def update_current_tab_title(self):
        """v19.1: 現在のタブのタイトルをアクティブペインのフォルダ名で更新"""
        idx = self.tab_widget.currentIndex()
        if idx == -1:
            return
        
        area = self.tab_widget.widget(idx)
        
        # v21.5 Fix: hovered_paneが現タブに属するかチェック
        # タブ切替直後はhovered_paneが旧タブのペインを指すため、
        # 現タブのFlowAreaに属するペインのみを使用する。
        name = "Workspace"
        pane_in_current_tab = False
        if self.hovered_pane and self.hovered_pane.current_paths:
            # hovered_paneが現タブ内のペインか確認
            if isinstance(area, FlowArea):
                for lane in area.lanes:
                    if self.hovered_pane in lane.panes:
                        pane_in_current_tab = True
                        break
            
            if pane_in_current_tab:
                path = self.hovered_pane.current_paths[0]
                name = os.path.basename(path)
                if not name:
                    name = path.replace("\\", "").replace("/", "")
        
        # フォールバック: hovered_paneが使えない場合は最初のペインから取得
        if not pane_in_current_tab and isinstance(area, FlowArea):
            lane = area.active_lane
            if lane and lane.panes and lane.panes[0].current_paths:
                path = lane.panes[0].current_paths[0]
                name = os.path.basename(path)
                if not name:
                    name = path.replace("\\", "").replace("/", "")
        
        self.tab_widget.setTabText(idx, name)

    def apply_theme(self):
        # VSCode Dark-like Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #cccccc; }
            QWidget { font-family: 'Segoe UI', sans-serif; font-size: 10pt; }
            QTreeView { 
                background-color: #1e1e1e; color: #cccccc; border: none; 
                selection-background-color: #094771; selection-color: #ffffff;
            }
            /* Rename Input Styling: High Contrast */
            QTreeView QLineEdit {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #007acc;
                border-radius: 0px;
                padding: 1px;
                selection-background-color: #264f78;
            }
            QTreeView::item:hover { background-color: #2a2d2e; }
            QTreeView::item:selected:active { background-color: #094771; }
            QTreeView::item:selected:!active { background-color: #37373d; }
            QHeaderView { background-color: #252526; border: none; }
            QHeaderView::section { background-color: #252526; color: #cccccc; border: none; padding: 4px; }
            
            QSplitter::handle { background-color: #333333; }
            QSplitter::handle:item:hover { background-color: #007acc; }

            /* 縦並びレーン間のスプリッター（通常色へ戻す） */
            QSplitter#VerticalFlowSplitter::handle { height: 4px; background: #111; border-top: 1px solid #222; border-bottom: 1px solid #222; }
            QSplitter#VerticalFlowSplitter::handle:hover { background: #333; }

            /* ScrollBar customization: Accent Rounded */
            QScrollBar:vertical {
                border: 1px solid #333;
                background: #252525;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #153b93;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3a62bd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar:horizontal {
                border: 1px solid #333;
                background: #252525;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #153b93;
                min-width: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3a62bd;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }

            QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; }
            QMenu::item:selected { background-color: #094771; }

            /* Fix for White Pane Background (esp. New Pane) */
            QScrollArea { background-color: transparent; border: none; }
            QFrame#Pane { background-color: transparent; } /* Let main window bg show through, or set specific */
            QWidget#PaneHeader { background-color: transparent; }
        """)

        # Windows Dark Title Bar
        try:
            from widgets.ui_utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except ImportError:
            pass

    # --- Delegated Actions ---
    
    def run_on_hovered(self, func):
        if self.hovered_pane:
            func(self.hovered_pane)

    def add_pane_to_hovered_lane(self):
        if self.hovered_pane and hasattr(self.hovered_pane, 'parent_lane'):
            self.hovered_pane.parent_lane.add_pane()
        elif self.current_flow_area and self.current_flow_area.active_lane:
            self.current_flow_area.active_lane.add_pane()

    def remove_hovered_pane(self):
        if self.hovered_pane and hasattr(self.hovered_pane, 'parent_lane'):
            self.hovered_pane.parent_lane.remove_pane(self.hovered_pane)

    def go_up_hovered(self):
        if self.hovered_pane:
            self.hovered_pane.go_up()

    def split_lane_vertically(self):
        if self.current_flow_area:
            self.current_flow_area.split_lane_vertically()

    def reset_flow_from(self, path):
        # ナビゲーションからのリセット。現在のタブに対して適用
        if self.current_flow_area:
            self.current_flow_area.reset_flow_from(path)
        else:
            # タブがない場合は作る（基本ありえないが）
            self.add_new_tab()
            self.current_flow_area.reset_flow_from(path)

    def update_downstream(self, source_pane, paths):
        # ソースペインが属するレーンに委譲
        if hasattr(source_pane, 'parent_lane'):
            source_pane.parent_lane.update_downstream(source_pane, paths)

    def launch_tool(self, file_path):
        """v19.0: Launch external tool via PluginManager, with fallback to SimpleEditor"""
        if not file_path or not os.path.exists(file_path):
            return

        # 1. Find registered tool
        tool = self.plugin_manager.get_tool_for_file(file_path)
        
        success = False
        if tool:
            # Launch via PluginManager
            success = self.plugin_manager.launch_tool(tool, file_path, self)
        
        # 2. Fallback: Simple Internal Editor (if tool launch failed or no tool found)
        # Only fallback for text-editable files
        ext = os.path.splitext(file_path)[1].lower()
        text_exts = ['.txt', '.md', '.py', '.json', '.xml', '.html', '.css', '.js', '.ini', '.log', '.bat', '.sh']
        
        if not success and ext in text_exts:
            from core.simple_editor import SimpleEditor
            # Keep ref to prevent garbage collection
            self.simple_editor_window = SimpleEditor(file_path, self)
            self.simple_editor_window.show()

    # Legacy method name for compatibility with Slash Menu / QuickLook
    def launch_editor(self, file_path):
        """Compatibility wrapper for launch_tool"""
        self.launch_tool(file_path)

    def launch_todo(self):
        """v21.0 Launch ChainFlowToDo via PluginManager"""
        print("[DEBUG] launch_todo called")
        
        tool_def = next((t for t in self.plugin_manager.tools if t.get("id") == "todo_tool"), None)
        if not tool_def:
            print("[DEBUG] ToDo tool NOT FOUND in tools.json")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "ToDo Tool", "ToDo tool not configured in tools.json")
            return
            
        target_path = os.getcwd()
        self.plugin_manager.launch_tool(tool_def, target_path, self)

    def update_preview(self, path):
        try:
            # QuickLookが表示中なら内容を更新する
            if self.quick_look and self.quick_look.isVisible():
                self.quick_look.show_file(path)
        except Exception as e:
            print(f"Error in update_preview: {e}", file=sys.stderr)
            
    def toggle_quick_look(self):
        # 表示中なら閉じる
        if self.quick_look.isVisible():
            self.quick_look.fade_out()
            return

        # ホバー中のペインを取得
        target_pane = self.hovered_pane
        if not target_pane and self.current_flow_area and self.current_flow_area.active_lane:
             panes = self.current_flow_area.active_lane.panes
             if panes: target_pane = panes[-1]
        
        if target_pane:
            path = target_pane.get_current_selected_path()
            if path:
                self.quick_look.show_file(path)
                self.quick_look.popup(self.geometry().center())

    def close_quick_look(self):
        if self.quick_look.isVisible():
            self.quick_look.fade_out()
        else:
            # Escは通常通りフォーカス外しなどとして機能させるためにイベントを無視しない
            # ただし、Shortcutとして登録されているのでEscを押すとここに来る。
            # 他にEscを使いたい場所（FilePaneのクリア検索など）との兼ね合いがある。
            pass


    def add_to_favorites(self, path):
        self.nav.add_favorite(path)

    # --- Address Bar Actions ---

    def toggle_favorites_focus(self):
        """v6.5 Fキーでお気に入り欄とペインのフォーカスを行き来する"""
        fav_list = self.nav.fav_list
        if fav_list.hasFocus():
            self.nav.set_active(False)
            if self.hovered_pane:
                info = self.hovered_pane.get_selection_info()
                if info["view"]:
                    info["view"].setFocus()
        else:
            # 他のペインのハイライトをオフにする（自分をアクティブにする前に）
            if self.hovered_pane:
                self.hovered_pane.highlight(False)
            
            self.nav.set_active(True)
            fav_list.setFocus()
            if fav_list.count() > 0 and not fav_list.currentItem():
                fav_list.setCurrentRow(0)

    def handle_favorites_hotkey(self, index):
        """v6.6 お気に入り欄フォーカス時のクイックジャンプ"""
        if index < self.nav.fav_list.count():
            item = self.nav.fav_list.item(index)
            if item:
                self.nav.on_fav_clicked(item)

    def dispatch_shortcut(self, key):
        """v6.7 お気に入り欄と通常の動作を振り分ける中央ディスパッチャ"""
        # v6.8 お気に入り欄がアクティブ（ホバー含む）な場合
        if self.nav.active_state:
            idx = self.hk_map.get(key)
            if idx is not None:
                self.handle_favorites_hotkey(idx)
        else:
            # 通常（ペイン操作）時
            if key == "Q": self.go_up_hovered()
            elif key == "W": self.remove_hovered_pane()
            elif key == "A": self.run_on_hovered(lambda p: p.toggle_sort(0))
            elif key == "S": self.run_on_hovered(lambda p: p.toggle_sort(1))
            elif key == "X": self.run_on_hovered(lambda p: p.toggle_sort(2))
            elif key == "Z": self.run_on_hovered(lambda p: p.toggle_sort(3))
            elif key == "D": self.run_on_hovered(lambda p: p.cycle_display_mode())
            elif key == "C": self.run_on_hovered(lambda p: p.toggle_compact())
            # E は現在はグローバルアクションなし

    def focus_address_bar(self):
        if self.address_bar.hasFocus():
            # アドレスバーにフォーカスがある場合は最後に触れたペインへ戻す
            if self.hovered_pane:
                info = self.hovered_pane.get_selection_info()
                if info["view"]:
                    info["view"].setFocus()
        else:
            self.address_bar.setFocus()
            self.address_bar.selectAll()

    def on_address_return(self):
        path = self.address_bar.text().strip()
        if path and os.path.exists(path):
            self.reset_flow_from(path)
            self.tab_widget.currentWidget().setFocus() # フォーカスを戻す
        elif path:
             # パスが無効な場合は通知（簡易的に）
             self.address_bar.setStyleSheet(self.address_bar.styleSheet() + "QLineEdit { border-color: #f44; }")

    def update_address_bar(self, path):
        if not self.address_bar.hasFocus():
            # ユーザーが入力中でなければ更新する
            self.address_bar.setText(path)
            # エラースタイルを戻す
            self.address_bar.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ccc;
                    border: 1px solid #555;
                    padding: 4px 10px;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border-color: #007acc;
                    color: #fff;
                }
            """)
            
            # v19.1: タブ名をアドレスバーと完全同期
            idx = self.tab_widget.currentIndex()
            if idx != -1:
                name = os.path.basename(path)
                if not name:  # ドライブルート対策
                    name = path.replace("\\", "").replace("/", "")
                self.tab_widget.setTabText(idx, name)

    def toggle_sidebar(self):
        """v9.2 サイドバーの表示・非表示を切り替える"""
        # 単純に幅0にするだけだとハンドルや最小幅の影響でゴミが残ることがあるため、
        # setVisibleを使って完全に消す。
        
        if self.nav.isVisible():
            # 閉じる
            # 現在の幅を保存しておくと親切だが、今回はシンプルに非表示化のみ
            self.nav.setVisible(False)
        else:
            # 開く
            self.nav.setVisible(True)
            
            # もし幅が潰れていたら復活させる
            sizes = self.main_splitter.sizes()
            if sizes and sizes[0] == 0:
                target_w = 120
                current_total = sum(sizes)
                new_sizes = [target_w, current_total - target_w]
                self.main_splitter.setSizes(new_sizes)

    def reset_layout(self):
        """v13.0 レイアウトを初期状態（均等割り・デフォルト幅）に戻す"""
        # 1. サイドバーのリセット (デフォルト240px程度に)
        if not self.nav.isVisible():
            self.nav.setVisible(True)
            
        current_sizes = self.main_splitter.sizes()
        total_w = sum(current_sizes)
        sidebar_w = 240
        if total_w > sidebar_w:
            self.main_splitter.setSizes([sidebar_w, total_w - sidebar_w])
            
        # 2. フローエリア内の均等割り
        if self.current_flow_area:
            self.current_flow_area.distribute_items()

    def highlight_context(self):
        """v14.0 Altキー押下時に文脈（祖先・子孫）をハイライト表示"""
        active_pane = self.hovered_pane
        
        # v14.1 Fix: ファイルペイン以外にフォーカスがある場合(アドレスバー等)へのフォールバック
        if not active_pane and self.current_flow_area:
            lane = self.current_flow_area.active_lane
            if lane and lane.panes:
                active_pane = lane.panes[-1]

        if not active_pane: 
            return
        
        target_path = None
        
        # フォーカスを持っているViewを優先
        for view, model, root_path, _ in active_pane.views:
            try:
                if view.hasFocus():
                    idx = view.currentIndex()
                    if idx.isValid():
                        target_path = idx.data(Qt.UserRole)
                    else:
                        target_path = root_path
                    break
            except RuntimeError:
                continue
        
        # フォールバック: currentIndexが有効な最初のView
        if not target_path:
            for view, model, _, _ in active_pane.views:
                try:
                    idx = view.currentIndex()
                    if idx.isValid():
                        target_path = idx.data(Qt.UserRole)
                        break
                except RuntimeError:
                    continue
        
        # フォールバック: get_selection_info
        if not target_path:
            info = active_pane.get_selection_info()
            if info.get("paths"):
                target_path = info["paths"][0]
        
        # フォールバック: ペインの表示パス
        if not target_path and active_pane.current_paths:
            target_path = active_pane.current_paths[0]

        if not target_path: 
            return
        
        target_path = os.path.normpath(target_path)
        current_area = self.current_flow_area
        if not current_area: return

        # 1. 上流ハイライト (Ancestors)
        # v14.2 Fix: パス比較の堅牢化とルート判定の修正
        # v14.2 Hotfix: カレントディレクトリ（ターゲット自身）も親ペインでハイライト対象とするため、
        # dirname() ではなくターゲット自身からスタートする。
        ancestor = target_path # os.path.dirname(target_path) から変更
        
        # ルートに到達するまで遡る
        while True:
            # 描画指示
            # v14.2 Fix: ペイン探索を逆順（右→左）に行うことで、
            # 最もアクティブペインに近い（直近の）親ペインを優先的にハイライトさせる。
            # これにより、最上流のペインによる "Deep Match" の横取りを防ぐ。
            
            all_panes = []
            for lane in current_area.lanes:
                all_panes.extend(lane.panes)
                
            # v14.3 Fix: breakを除去し、重複フォルダ（複数のペインが同じ祖先を持つ場合）
            # すべてでハイライトが行われるようにする。
            for pane in reversed(all_panes):
                if pane == active_pane: 
                    continue
                # set_temp_highlight内部で same_path による比較が行われる
                pane.set_temp_highlight(ancestor)
            
            # 次の親へ
            parent = os.path.dirname(ancestor)
            if same_path(parent, ancestor): # これ以上親がないなら終了
                break
            ancestor = parent
            
        # 2. 下流ハイライト (Descendants)
        # ターゲットがフォルダの場合のみ、その中身を表示しているペインを探す
        if os.path.isdir(target_path):
            found_descendant = False
            for lane in current_area.lanes:
                for pane in lane.panes:
                    if pane == active_pane: continue
                    
                    # ペインがこのパスをルートとして表示しているか？
                    if pane.set_view_highlight(target_path):
                        found_descendant = True
                        break

    def clear_context_highlights(self):
        """v14.0 ハイライト解除"""
        current_area = self.current_flow_area
        if not current_area: return

        for lane in current_area.lanes:
            for pane in lane.panes:
                pane.clear_temp_highlight()

    def refresh_all_panes(self):
        """v14.0 F5リフレッシュ: 現在タブの全ペインを再読み込み"""
        current_area = self.current_flow_area
        if not current_area: return

        for lane in current_area.lanes:
            for pane in lane.panes:
                pane.refresh_contents()

    # v16.1 Fix: Manual Key Handling for Slash Menu as QShortcut seems unreliable in this context
    def keyPressEvent(self, event):
        # Debug Log
        # print(f"Key Pressed: {event.key()} Mod: {event.modifiers()}")
        
        # Check for Ctrl+P
        if (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_P:
            print("Manual Key Event: Ctrl+P -> Toggle Menu")
            self.toggle_slash_menu()
            event.accept()
            return

        # v14.0 F5で全ペインリフレッシュ
        if event.key() == Qt.Key_F5:
            self.refresh_all_panes()
            event.accept()
            return
        
        # v14.0 AltキーでContext Highlight
        if event.key() == Qt.Key_Alt:
            self.highlight_context()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self.clear_context_highlights()
        super().keyReleaseEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange:
            # v20.1 Fix: Alt+Tabなどでフォーカスを失った場合、AltキーのReleaseイベントが取れないため
            # 明示的にハイライトを解除する。
            if not self.isActiveWindow():
                self.clear_context_highlights()
            else:
                # v21.1: Re-apply on activation
                try:
                    from .ui_utils import apply_dark_title_bar
                    apply_dark_title_bar(self)
                except: pass
        elif event.type() == QEvent.WindowStateChange:
            # v21.1: Re-apply on maximize/restore to prevent returning to white
            try:
                from .ui_utils import apply_dark_title_bar
                apply_dark_title_bar(self)
            except: pass
        super().changeEvent(event)
