import os
import sys
import json
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QWidget, QLabel, QApplication,
                               QTreeView, QListWidget, QListWidgetItem, QMenu, QFileSystemModel,
                               QToolButton, QStyle, QFileIconProvider, QAbstractItemView, QSizePolicy, QSpacerItem, QSplitter)
from PySide6.QtCore import Qt, QDir, QUrl, QSize, QFileInfo, QEvent
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from core.global_model import get_global_file_system_model

class DragDropListWidget(QListWidget):
    """
    ドラッグ＆ドロップでお気に入りを登録・並び替えできるカスタムリスト
    """
    def __init__(self, parent_nav):
        super().__init__()
        self.nav = parent_nav
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # 外部（TreeView等）からのドロップ：お気に入り登録
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.exists(path): # ファイルも許可
                    self.nav.add_favorite(path)
            event.acceptProposedAction()
        else:
            # 内部での移動
            super().dropEvent(event)
            self.nav.refresh_item_labels() # v6.9 並べ替え後にホットキー表示を更新
            self.nav.save_favorites() # 並び替えを保存

class SectionHeader(QToolButton):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setText(f"  {title}")
        self.setCheckable(True)
        self.setChecked(False)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setArrowType(Qt.RightArrow)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QToolButton { 
                border: none; background-color: #252526; color: #ccc; 
                text-align: left; padding: 5px; font-weight: bold; 
                border-bottom: 1px solid #333; font-size: 10px;
            }
            QToolButton:hover { background-color: #3e3e3e; }
            QToolButton:checked { background-color: #37373d; color: #fff; }
        """)
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        # QToolButton.clicked sends 'checked' state if checkable, but here we manually manage the arrow
        # We rely on the external connection to toggle visibility, and here we just toggle the arrow.
        self.setArrowType(Qt.DownArrow if self.isChecked() else Qt.RightArrow)

    def set_active_style(self, active):
        if active:
            # アクティブ時は少し強調（境界線など）
            self.setStyleSheet("""
                QToolButton { 
                    border: none; background-color: #094771; color: #fff; 
                    text-align: left; padding: 5px; font-weight: bold; 
                    border-bottom: 1px solid #007acc; font-size: 10px;
                }
                QToolButton:hover { background-color: #007acc; }
                QToolButton:checked { background-color: #094771; color: #fff; }
            """)
        else:
            self.setStyleSheet("""
                QToolButton { 
                    border: none; background-color: #252526; color: #ccc; 
                    text-align: left; padding: 5px; font-weight: bold; 
                    border-bottom: 1px solid #333; font-size: 10px;
                }
                QToolButton:hover { background-color: #3e3e3e; }
                QToolButton:checked { background-color: #37373d; color: #fff; }
            """)

class NavigationPane(QFrame):
    def __init__(self, parent_filer=None):
        super().__init__()
        self.parent_filer = parent_filer
        self.setMinimumWidth(0) # v9.2
        self.setObjectName("Sidebar")
        self.active_state = False # v6.8

        # favorites.json path
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fav_file = os.path.join(base_dir, "favorites.json")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter to allow resizing of ALL sections
        self.nav_splitter = QSplitter(Qt.Vertical)
        self.nav_splitter.setHandleWidth(1) # Minimize gap
        # ハンドルは通常見えないが、ホバーで青くなる
        self.nav_splitter.setStyleSheet("""
            QSplitter::handle { background: #252526; } 
            QSplitter::handle:hover { background: #007acc; }
        """)
        
        # --- 1. STANDARD SECTION ---
        self.std_container = QWidget()
        std_layout = QVBoxLayout(self.std_container)
        std_layout.setContentsMargins(0,0,0,0)
        std_layout.setSpacing(0)
        
        self.std_header = SectionHeader("STANDARD")
        self.std_header.setChecked(True) # Default Open
        self.std_header.setArrowType(Qt.DownArrow)
        
        self.std_list = QListWidget()
        self.std_list.setFrameStyle(QFrame.NoFrame)
        self.std_list.setStyleSheet("""
            QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; }
            QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #094771; color: white; }
            QListWidget::item:hover { background-color: #2a2d2e; }
        """)
        self.populate_standard_items()
        self.std_list.itemClicked.connect(self.on_std_clicked)
        self.std_header.clicked.connect(lambda checked: self.toggle_section(self.std_list))
        
        std_layout.addWidget(self.std_header)
        std_layout.addWidget(self.std_list)
        self.nav_splitter.addWidget(self.std_container) # idx 0

        # --- 2. FAVORITES SECTION ---
        self.fav_container = QWidget()
        fav_layout = QVBoxLayout(self.fav_container)
        fav_layout.setContentsMargins(0,0,0,0)
        fav_layout.setSpacing(0)

        self.fav_header = SectionHeader("FAVORITES")
        self.fav_header.setChecked(True) # Default Open
        self.fav_header.setArrowType(Qt.DownArrow)
        
        self.fav_list = DragDropListWidget(self)
        self.fav_list.setObjectName("FavList")
        self.fav_list.setFrameStyle(QFrame.NoFrame)
        self.fav_list.setStyleSheet("""
            QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; }
            QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #094771; color: white; }
            QListWidget::item:hover { background-color: #2a2d2e; }
        """)
        self.fav_list.itemClicked.connect(self.on_fav_clicked)
        self.fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_list.customContextMenuRequested.connect(self.open_fav_menu)
        
        self.fav_header.clicked.connect(lambda checked: self.toggle_section(self.fav_list))
        
        fav_layout.addWidget(self.fav_header)
        fav_layout.addWidget(self.fav_list)
        self.nav_splitter.addWidget(self.fav_container) # idx 1

        # --- 3. DRIVES SECTION ---
        self.drv_container = QWidget()
        drv_layout = QVBoxLayout(self.drv_container)
        drv_layout.setContentsMargins(0,0,0,0)
        drv_layout.setSpacing(0)

        self.drv_header = SectionHeader("DRIVES")
        self.drv_header.setChecked(False) # Default Closed
        self.drv_header.setArrowType(Qt.RightArrow)
        
        # Drive Tree Setup
        # v19 Performance Fix: Use Global Shared Model
        self.model = get_global_file_system_model()
        # self.model.setRootPath("") # Global model already set
        # self.model.setFilter(...) # Global model already set default filters
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))
        for i in range(1, 4): self.tree.hideColumn(i)
        self.tree.setHeaderHidden(True)
        self.tree.setFrameStyle(QFrame.NoFrame)
        self.tree.clicked.connect(self.on_tree_clicked)
        self.tree.setAcceptDrops(True)
        self.tree.setDragEnabled(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDrop)
        self.tree.setStyleSheet("""
            QTreeView { background: transparent; color: #bbb; border: none; }
            QTreeView::item { height: 25px; }
            QTreeView::item:hover { background-color: #2a2d2e; }
            QTreeView::item:selected { background-color: #094771; }
        """)
        self.tree.setVisible(False)
        self.drv_header.clicked.connect(lambda checked: self.toggle_section(self.tree))
        
        drv_layout.addWidget(self.drv_header)
        drv_layout.addWidget(self.tree)
        self.nav_splitter.addWidget(self.drv_container) # idx 2

        # --- 4. HELP / CHEAT SHEET SECTION --- (v16.2: Disabled for now, shortcuts need review)
        # self.help_container = QWidget()
        # help_layout = QVBoxLayout(self.help_container)
        # help_layout.setContentsMargins(0,0,0,0)
        # help_layout.setSpacing(0)
        # self.help_header = SectionHeader("HELP")
        # self.help_header.setChecked(True) 
        # self.help_header.setArrowType(Qt.DownArrow)
        # self.help_list = QListWidget()
        # self.help_list.setFrameStyle(QFrame.NoFrame)
        # self.help_list.setStyleSheet(...)
        # self.help_list.setFocusPolicy(Qt.NoFocus)
        # self.populate_cheat_sheet()
        # self.help_header.clicked.connect(lambda checked: self.toggle_section(self.help_list))
        # help_layout.addWidget(self.help_header)
        # help_layout.addWidget(self.help_list)
        # self.nav_splitter.addWidget(self.help_container) # idx 3

        # --- 4. SPACER SECTION (Important for bottom alignment) ---
        self.spacer = QWidget()
        self.spacer.setAttribute(Qt.WA_TransparentForMouseEvents) # マウスイベントを無視
        self.nav_splitter.addWidget(self.spacer) # idx 3 (was 4)
        
        layout.addWidget(self.nav_splitter)
        
        # リサイズ制御のためにサイズポリシー設定
        self.nav_splitter.setCollapsible(0, False)
        self.nav_splitter.setCollapsible(1, False)
        self.nav_splitter.setCollapsible(2, False)
        self.nav_splitter.setCollapsible(3, False) # Spacer

        # 初期伸長設定
        self.nav_splitter.setStretchFactor(0, 0)
        self.nav_splitter.setStretchFactor(1, 1) # Favorites takes main space
        self.nav_splitter.setStretchFactor(2, 0)
        self.nav_splitter.setStretchFactor(3, 0) # Spacer
        
        # イベントフィルター登録
        self.std_list.installEventFilter(self)
        self.fav_list.installEventFilter(self)
        self.tree.installEventFilter(self)
        
        self.load_favorites()

    def populate_cheat_sheet(self):
        self.help_list.clear()
        shortcuts = [
            ("New File", "Ctrl+N"),
            ("New Folder", "Ctrl+Shift+N"),
            ("Command Palette", "Ctrl+P"),
            ("Quick Look", "Space"),
            ("Rename", "Enter"),
            ("Go Up", "Backspace"),
            ("History Back", "Alt+Left"),
            ("History Fwd", "Alt+Right"),
            ("Focus Filter", "Ctrl+F"),
            ("Show Hints", "Alt (Hold)"),
        ]
        
        for action, key in shortcuts:
            # Format: 'Action ... Key'
            # Calculate padding for alignment? Monospace helps.
            text = f"{action:<15} {key}"
            item = QListWidgetItem(text)
            self.help_list.addItem(item)
            
        # Adjust height
        self.help_list.setFixedHeight(len(shortcuts) * 20 + 15)

    def toggle_section(self, widget):
        # ウィジェットの可視性を切り替え
        is_visible = widget.isVisible()
        widget.setVisible(not is_visible)
        
        container = widget.parentWidget()
        idx = self.nav_splitter.indexOf(container)
        sizes = self.nav_splitter.sizes()
        current_h = sizes[idx]
        
        # ヘッダー高さ計算
        header_h = container.layout().itemAt(0).widget().sizeHint().height()
        if header_h < 20: header_h = 30
        
        if not is_visible: # Opening
            container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # 展開サイズ
            expand = 150
            if widget == self.std_list:
                expand = self.std_list.count() * 25 + 10
            # v16.2: help_list disabled
            # elif widget == self.help_list:
            #     expand = self.help_list.count() * 20 + 15
            
            # Spacer(最後)から奪うか、Neighborsから奪う
            # 基本はSpacer(idx=4)があればそこから奪うと上がずれない
            donor_idx = len(sizes) - 1
            if sizes[donor_idx] < expand:
                # Spacerに余裕がないなら、一番大きいところから奪う
                max_h = 0
                for i, h in enumerate(sizes):
                    if i != idx and h > max_h:
                        max_h = h
                        donor_idx = i
            
            sizes[idx] += expand
            if donor_idx != idx:
                sizes[donor_idx] -= expand
            
            self.nav_splitter.setSizes(sizes)
                
        else: # Closing
            container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            
            diff = current_h - header_h
            if diff > 0:
                sizes[idx] = header_h
                # 余りを全てSpacer(最後)に流す -> これで全体が上に詰まる
                spacer_idx = len(sizes) - 1
                sizes[spacer_idx] += diff
                self.nav_splitter.setSizes(sizes)

    def populate_standard_items(self):
        self.std_list.clear()
        home = os.path.expanduser("~")
        
        items = [
            ("Desktop", os.path.join(home, "Desktop")),
            ("Downloads", os.path.join(home, "Downloads")),
            ("Documents", os.path.join(home, "Documents")),
            ("Pictures", os.path.join(home, "Pictures")),
            ("Music", os.path.join(home, "Music")),
            ("Videos", os.path.join(home, "Videos")),
        ]
        
        # v22.1 Performance: QFileIconProvider を使わず固定ラベルで表示（Shell API呼出を排除）
        icon_labels = {
            "Desktop": "🖥️",
            "Downloads": "📥",
            "Documents": "📄",
            "Pictures": "🖼️",
            "Music": "🎵",
            "Videos": "🎬",
        }
        
        for name, path in items:
            if os.path.exists(path):
                label = icon_labels.get(name, "📁")
                item = QListWidgetItem(f"{label} {name}")
                item.setToolTip(path)
                self.std_list.addItem(item)
        
        # 固定高さは解除（リサイズできるように）
        self.std_list.setFixedHeight(16777215) # QWIDGETSIZE_MAX

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Enter:
            if not (QApplication.keyboardModifiers() & Qt.ControlModifier):
                if self.parent_filer:
                    self.parent_filer.set_active_pane(None)
                self.set_active(True)

        # Shift+Wheel Resizing Logic
        if event.type() == QEvent.Wheel and (event.modifiers() & Qt.ShiftModifier):
            self.handle_wheel_resize(watched, event)
            return True

        return super().eventFilter(watched, event)

    def handle_wheel_resize(self, watched, event):
        # ホイール回転量
        delta = event.angleDelta().y()
        change = 20 if delta > 0 else -20
        if delta == 0: return

        # ターゲット判定
        idx = -1
        if watched == self.std_list: idx = 0
        elif watched == self.fav_list: idx = 1
        elif watched == self.tree: idx = 2
        # v16.2: help_list は無効化済みのため除外
        
        if idx == -1: return

        sizes = self.nav_splitter.sizes()
        if idx < len(sizes):
            target_idx = idx
            
            # リサイズ時、どこから吸い取るか？
            # 拡大時 -> Spacerから吸うのが理想（他を圧迫しない）
            # 縮小時 -> Spacerに吐き出すのが理想
            # しかし操作感としては「下の要素」との境界を動かす感覚に近いのがShift+Scroll
            
            # ここではシンプルに「次の要素」とやりとりする
            # ただし最後(Spacer)とのやりとりを優先すると自然かも
            
            neighbor_idx = idx + 1
            if neighbor_idx >= len(sizes): neighbor_idx = idx - 1 # 自分が最後なら上と
            
            # Spacer(4)があるなら、それをクッションにする
            spacer_idx = 4
            if spacer_idx < len(sizes) and idx != spacer_idx:
                neighbor_idx = spacer_idx

            if neighbor_idx < 0: return

            new_target_h = max(30, sizes[target_idx] + change)
            diff = new_target_h - sizes[target_idx]
            
            if sizes[neighbor_idx] - diff > 0: # Spacerなら0になってもいい
                sizes[target_idx] = new_target_h
                sizes[neighbor_idx] -= diff
                self.nav_splitter.setSizes(sizes)
            event.accept()

    def enterEvent(self, event):
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            return
        if self.parent_filer:
            self.parent_filer.set_active_pane(None)
        self.set_active(True)
        super().enterEvent(event)

    def set_active(self, active):
        self.active_state = active
        self.std_header.set_active_style(active)
        self.fav_header.set_active_style(active)
        self.drv_header.set_active_style(active)
        
        border = "2px solid #007acc" if active else "2px solid transparent"
        bg_sel = "#007acc" if active else "#094771"
        
        base_style = """
            QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; border-left: %s; }
            QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
            QListWidget::item:selected { background-color: %s; color: white; }
            QListWidget::item:hover { background-color: #2a2d2e; }
        """ % (border, bg_sel)
        
        self.std_list.setStyleSheet(base_style)
        self.fav_list.setStyleSheet(base_style)
        
        tree_style = """
            QTreeView { background: transparent; color: #bbb; border: none; border-left: %s; }
            QTreeView::item { height: 25px; }
            QTreeView::item:hover { background-color: #2a2d2e; }
            QTreeView::item:selected { background-color: %s; }
        """ % (border, bg_sel)
        self.tree.setStyleSheet(tree_style)

    def on_std_clicked(self, item):
        path = item.toolTip()
        if os.path.exists(path):
            self.open_path(path)

    def on_fav_clicked(self, item):
        path = item.toolTip()
        if os.path.exists(path):
            self.open_path(path)

    def on_tree_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path): self.open_path(path)

    def open_path(self, path):
        self.parent_filer.set_active_pane(None)
        self.set_active(True)
        
        if os.path.isdir(path):
            self.parent_filer.reset_flow_from(path)
        else:
            if os.name == 'nt':
                try:
                    import subprocess
                    cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
                    subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
                except Exception:
                    pass
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # --- Favorites Logic (Legacy Support) ---

    def load_favorites(self):
        self.fav_list.clear()
        if os.path.exists(self.fav_file):
            try:
                with open(self.fav_file, "r", encoding="utf-8") as f:
                    paths = json.load(f)
                    for p in paths:
                        self.add_fav_item(p)
                self.refresh_item_labels()
            except: pass

    def save_favorites(self):
        paths = []
        for i in range(self.fav_list.count()):
            paths.append(self.fav_list.item(i).toolTip())
        try:
            with open(self.fav_file, "w", encoding="utf-8") as f:
                json.dump(paths, f, ensure_ascii=False, indent=2)
        except: pass

    def add_favorite(self, path):
        for i in range(self.fav_list.count()):
            if self.fav_list.item(i).toolTip() == path:
                return
        self.add_fav_item(path)
        self.refresh_item_labels()
        self.save_favorites()

    def add_fav_item(self, path):
        item = QListWidgetItem("")
        item.setToolTip(path)
        self.fav_list.addItem(item)

    def remove_fav_item(self, item):
        self.fav_list.takeItem(self.fav_list.row(item))
        self.refresh_item_labels()
        self.save_favorites()

    def refresh_item_labels(self):
        hotkeys = ["Q", "A", "Z", "W", "S", "X", "E", "D", "C"]
        for i in range(self.fav_list.count()):
            item = self.fav_list.item(i)
            path = item.toolTip()
            name = os.path.basename(path) or path
            prefix = "📁 " if os.path.isdir(path) else "📄 "
            
            hk_prefix = ""
            if i < len(hotkeys):
                hk_prefix = f"[{hotkeys[i].lower()}] "
            
            item.setText(f"{hk_prefix}{prefix}{name}")

    def open_fav_menu(self, pos):
        item = self.fav_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        remove_act = QAction("Remove from Favorites", self)
        remove_act.triggered.connect(lambda: self.remove_fav_item(item))
        menu.addAction(remove_act)
        menu.exec(self.fav_list.mapToGlobal(pos))
