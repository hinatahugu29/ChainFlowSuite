import sys
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QDockWidget, QStackedWidget, QStatusBar
from PySide6.QtCore import Qt, QPointF, QEvent, QSettings
from PySide6.QtGui import QUndoStack, QShortcut, QKeySequence, QIcon
from canvas import DTPScene, DTPView
from panels import TextPanel, ImagePanel, ShapePanel, TablePanel, ShadowPanel
from layer_panel import LayerPanel
from swatch_panel import SwatchPanel

# ─── ChainFlowFiler 統一ダークテーマ ───
DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
    color: #cccccc;
}
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: "Segoe UI", "Yu Gothic UI", sans-serif;
    font-size: 12px;
}
QMenuBar {
    background-color: #252526;
    color: #cccccc;
    border-bottom: 1px solid #3c3c3c;
}
QMenuBar::item:selected {
    background-color: #094771;
}
QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3c3c3c;
}
QMenu::item:selected {
    background-color: #094771;
}
QToolBar {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    spacing: 4px;
    padding: 2px;
}
QToolBar QToolButton {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 4px 8px;
}
QToolBar QToolButton:hover {
    background-color: #3c3c3c;
    border: 1px solid #505050;
}
QToolBar QToolButton:pressed {
    background-color: #094771;
}
QDockWidget {
    color: #cccccc;
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}
QDockWidget::title {
    background-color: #252526;
    padding: 6px;
    border-bottom: 1px solid #3c3c3c;
}
QDockWidget QWidget {
    background-color: #252526;
}
QLabel {
    color: #cccccc;
    background-color: transparent;
}
QPushButton {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 4px 10px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #505050;
    border: 1px solid #6a6a6a;
}
QPushButton:pressed {
    background-color: #094771;
}
QPushButton:checked {
    background-color: #094771;
    border: 1px solid #1177bb;
}
QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 2px 4px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #007acc;
}
QFontComboBox, QComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 2px 4px;
}
QComboBox::drop-down {
    border: none;
    background: #3c3c3c;
}
QCheckBox {
    color: #cccccc;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #505050;
    border-radius: 2px;
    background-color: #3c3c3c;
}
QCheckBox::indicator:checked {
    background-color: #007acc;
    border: 1px solid #007acc;
}
QSlider::groove:horizontal {
    background-color: #3c3c3c;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #007acc;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background-color: #007acc;
    border-radius: 3px;
}
QListWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    outline: none;
}
QListWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #2d2d2d;
}
QListWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #2a2d2e;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    border-top: none;
}
QStatusBar QLabel {
    color: #ffffff;
    background-color: transparent;
    padding: 0 8px;
}
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #686868;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #686868;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
"""


class DTPEditor(QMainWindow):
    def __init__(self, initial_path=None):
        super().__init__()
        
        self.initial_path = initial_path
        
        self.settings = QSettings("ChainFlow", "Designer")
        
        # --- Icon Settings ---
        icon_path = ""
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS logic for PyInstaller
            bundle_dir = sys._MEIPASS
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # Local dev path
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------
        
        self.setWindowTitle("ChainFlow Designer")
        self.resize(1024, 768)
        
        # ダークテーマ適用
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        
        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Scene & View
        self.undo_stack = QUndoStack(self) 
        
        self.scene = DTPScene(self, self.undo_stack)
        self.view = DTPView(self.scene)
        self.view.zoomChanged.connect(self.update_zoom_label)
        self.layout.addWidget(self.view)
        
        # Toolbar
        self.toolbar = self.addToolBar("ツール")
        
        self.action_add_text = self.toolbar.addAction("📝 テキスト")
        self.action_add_text.triggered.connect(self.add_text)
        
        self.toolbar.addSeparator()
        
        self.action_add_rect = self.toolbar.addAction("▭ 矩形")
        self.action_add_rect.triggered.connect(lambda: self.add_shape('rect'))
        
        self.action_add_ellipse = self.toolbar.addAction("○ 楕円")
        self.action_add_ellipse.triggered.connect(lambda: self.add_shape('ellipse'))
        
        self.action_add_line = self.toolbar.addAction("╱ 線")
        self.action_add_line.triggered.connect(lambda: self.add_shape('line'))
        
        self.action_add_table = self.toolbar.addAction("☰ テーブル")
        self.action_add_table.triggered.connect(self.add_table)
        
        self.toolbar.addSeparator()
        
        self.action_save = self.toolbar.addAction("💾 保存")
        self.action_save.triggered.connect(self.save_project)
        
        self.action_open = self.toolbar.addAction("📂 開く")
        self.action_open.triggered.connect(self.load_project)
        
        self.action_export_pdf = self.toolbar.addAction("📄 PDF出力")
        self.action_export_pdf.triggered.connect(self.export_pdf)
        
        self.action_export_image = self.toolbar.addAction("🖼️ 画像出力")
        self.action_export_image.triggered.connect(self.export_image)
        
        # Menu
        file_menu = self.menuBar().addMenu("ファイル")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addSeparator()
        file_menu.addAction(self.action_export_pdf)
        file_menu.addAction(self.action_export_image)
        
        # Align Menu
        align_menu = self.menuBar().addMenu("整列")
        
        self.action_align_left = align_menu.addAction("左揃え")
        self.action_align_left.triggered.connect(lambda: self.align_items('left'))
        
        self.action_align_center_h = align_menu.addAction("水平中央揃え")
        self.action_align_center_h.triggered.connect(lambda: self.align_items('center_h'))
        
        self.action_align_right = align_menu.addAction("右揃え")
        self.action_align_right.triggered.connect(lambda: self.align_items('right'))
        
        align_menu.addSeparator()
        
        self.action_align_top = align_menu.addAction("上揃え")
        self.action_align_top.triggered.connect(lambda: self.align_items('top'))
        
        self.action_align_center_v = align_menu.addAction("垂直中央揃え")
        self.action_align_center_v.triggered.connect(lambda: self.align_items('center_v'))
        
        self.action_align_bottom = align_menu.addAction("下揃え")
        self.action_align_bottom.triggered.connect(lambda: self.align_items('bottom'))
        
        # View Menu
        view_menu = self.menuBar().addMenu("表示")
        
        page_menu = view_menu.addMenu("ページサイズ")
        for size_name in DTPScene.PAGE_SIZES:
            action = page_menu.addAction(size_name)
            action.triggered.connect(lambda checked, n=size_name: self._change_page_size(n))
        
        page_menu.addSeparator()
        self.action_landscape = page_menu.addAction("横向き")
        self.action_landscape.setCheckable(True)
        self.action_landscape.toggled.connect(self._toggle_landscape)
        
        view_menu.addSeparator()
        
        self.action_snap = view_menu.addAction("グリッドスナップ")
        self.action_snap.setCheckable(True)
        self.action_snap.toggled.connect(self._toggle_snap)
        
        # Undo/Redo Actions
        self.action_undo = self.undo_stack.createUndoAction(self, "元に戻す")
        self.action_undo.setShortcut("Ctrl+Z")
        self.action_redo = self.undo_stack.createRedoAction(self, "やり直し")
        self.action_redo.setShortcut("Ctrl+Y")
        
        self.action_copy = self.toolbar.addAction("コピー")
        self.action_copy.setShortcut("Ctrl+C")
        self.action_copy.triggered.connect(lambda: self.view.copy_selection())
        
        self.action_paste = self.toolbar.addAction("貼り付け")
        self.action_paste.setShortcut("Ctrl+V")
        self.action_paste.triggered.connect(lambda: self.view.paste_from_clipboard())
        
        self.toolbar.addSeparator()
        
        self.action_group = self.toolbar.addAction("G グループ化")
        self.action_group.setShortcut("Ctrl+G")
        self.action_group.triggered.connect(self.group_items)
        self.action_group.setEnabled(False)

        self.action_ungroup = self.toolbar.addAction("U グループ解除")
        self.action_ungroup.setShortcut("Ctrl+Shift+G")
        self.action_ungroup.triggered.connect(self.ungroup_items)
        self.action_ungroup.setEnabled(False)
        
        self.toolbar.addSeparator()
        
        self.action_lock = self.toolbar.addAction("🔒 ロック")
        self.action_lock.setShortcut("Ctrl+L")
        self.action_lock.triggered.connect(self.lock_items)
        self.action_lock.setEnabled(False)

        self.action_unlock_all = self.toolbar.addAction("🔓 全てロック解除")
        self.action_unlock_all.setShortcut("Ctrl+Shift+L")
        self.action_unlock_all.triggered.connect(self.unlock_all_items)
        
        # Edit Menu
        edit_menu = self.menuBar().addMenu("編集")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_copy)
        edit_menu.addAction(self.action_paste)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_group)
        edit_menu.addAction(self.action_ungroup)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_lock)
        edit_menu.addAction(self.action_unlock_all)

        self.toolbar.addAction(self.action_undo)
        self.toolbar.addAction(self.action_redo)

        # Property Panel (Right Dock)
        self.dock = QDockWidget("プロパティ", self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        
        self.panel_stack = QStackedWidget()
        self.dock.setWidget(self.panel_stack)
        
        self.text_panel = TextPanel()
        self.image_panel = ImagePanel()
        self.shape_panel = ShapePanel()
        self.table_panel = TablePanel()
        self.shadow_panel = ShadowPanel()
        
        # Pass undo stack to panels
        self.text_panel.set_undo_stack(self.undo_stack)
        self.image_panel.set_undo_stack(self.undo_stack)
        self.shape_panel.set_undo_stack(self.undo_stack)
        self.table_panel.set_undo_stack(self.undo_stack)
        self.shadow_panel.set_undo_stack(self.undo_stack)
        
        # Helper method to combine item panel with shadow panel
        def create_panel_container(main_panel):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0,0,0,0)
            layout.addWidget(main_panel)
            # Add a dynamically inserted shadow panel Placeholder or handle it differently
            # Actually, since QStackedWidget is used, we can just insert the ShadowPanel
            # into each container. But an instance of a widget can only have ONE parent.
            # So creating a container and moving the single shadow panel per selection is better.
            return container

        self.panel_stack.addWidget(QWidget()) # Index 0: Empty placeholder
        
        self.text_container = create_panel_container(self.text_panel)
        self.image_container = create_panel_container(self.image_panel)
        self.shape_container = create_panel_container(self.shape_panel)
        self.table_container = create_panel_container(self.table_panel)
        self.group_container = create_panel_container(QWidget()) # Empty for now, but will hold shadow
        
        self.panel_stack.addWidget(self.text_container) # Index 1
        self.panel_stack.addWidget(self.image_container) # Index 2
        self.panel_stack.addWidget(self.shape_container) # Index 3
        self.panel_stack.addWidget(self.table_container) # Index 4
        self.panel_stack.addWidget(self.group_container) # Index 5
        
        self.layer_dock = QDockWidget("レイヤー", self)
        self.layer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.layer_panel = LayerPanel(self.scene, undo_stack=self.undo_stack)
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.layer_dock)
        
        # Swatch Panel (Bottom Right Dock)
        self.swatch_dock = QDockWidget("スウォッチ", self)
        self.swatch_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.swatch_panel = SwatchPanel(self.scene, undo_stack=self.undo_stack)
        self.swatch_dock.setWidget(self.swatch_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.swatch_dock)
        
        # Connect signal
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.undo_stack.indexChanged.connect(self._on_undo_redo)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.coord_label = QLabel("X: 0  Y: 0")
        self.zoom_label = QLabel("Zoom: 100%")
        self.selection_label = QLabel("選択: 0")
        
        self.status_bar.addWidget(self.coord_label)
        self.status_bar.addWidget(self.zoom_label)
        self.status_bar.addPermanentWidget(self.selection_label)
        
        # Mouse tracking for coordinate display
        self.view.setMouseTracking(True)
        self.view.viewport().setMouseTracking(True)
        self.view.mouseMoveSignal = None
        self.view.installEventFilter(self)
        
        # File management
        self._current_file = None
        self._modified = False
        self.undo_stack.indexChanged.connect(self._on_modified)
        self._update_title()
        
        # Shortcuts
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_project_quick)
        
        reset_zoom_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        reset_zoom_shortcut.activated.connect(self.view.reset_zoom)
        
        # 起動時にページ全体を表示
        from PySide6.QtCore import QTimer
        def initial_fit():
             # DTPソフトらしく、100%で用紙の中央を表示する
             self.view.reset_zoom()
             
             # centerOn はシーン座標を指定する
             # 用紙の中心は (w/2, h/2)
             w = self.scene._w_px
             h = self.scene._h_px
             self.view.centerOn(w/2, h/2)
             
             self.update_zoom_label(self.view.transform().m11())
             
        QTimer.singleShot(100, initial_fit)


    def eventFilter(self, obj, event):
        if obj == self.view and event.type() == QEvent.MouseMove:
            pos = self.view.mapToScene(event.pos())
            self.coord_label.setText(f"X: {pos.x():.0f}  Y: {pos.y():.0f}")
        return super().eventFilter(obj, event)
    
    def _on_modified(self, idx=None):
        self._modified = True
        self._update_title()
    
    def _update_title(self):
        name = "Untitled"
        if self._current_file:
            import os
            name = os.path.basename(self._current_file)
        mark = "* " if self._modified else ""
        self.setWindowTitle(f"{mark}{name} - ChainFlow Designer")

    def showEvent(self, event):
        """ウィンドウ表示時にダークタイトルバーを適用"""
        try:
            from ui_utils import apply_dark_title_bar
            apply_dark_title_bar(self)
        except Exception as e:
            print(f"Failed to apply dark title bar in showEvent: {e}")
        super().showEvent(event)

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes to prevent white flash on maximize/restore
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            try:
                from ui_utils import apply_dark_title_bar
                apply_dark_title_bar(self)
            except:
                pass
        super().changeEvent(event)

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        self.selection_label.setText(f"選択: {len(items)}")
        
        from items import DTPGroupItem
        
        # Group action toggle
        self.action_group.setEnabled(len(items) > 1)
        
        # Ungroup action toggle
        can_ungroup = any(isinstance(i, DTPGroupItem) for i in items)
        self.action_ungroup.setEnabled(can_ungroup)
        
        # Lock action toggle
        self.action_lock.setEnabled(len(items) > 0)

        if not items:
            self.panel_stack.setCurrentIndex(0)
            for panel in [self.text_panel, self.image_panel, self.shape_panel, self.table_panel]:
                panel.current_item = None
            return
            
        item = items[0]
        from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem
        
        if isinstance(item, DTPTextItem):
            self.panel_stack.setCurrentWidget(self.text_container)
            self.text_container.layout().addWidget(self.shadow_panel)
            self.text_panel.set_item(item)
            self.shadow_panel.set_item(item)
        elif isinstance(item, DTPImageItem):
            self.panel_stack.setCurrentWidget(self.image_container)
            self.image_container.layout().addWidget(self.shadow_panel)
            self.image_panel.set_item(item)
            self.shadow_panel.set_item(item)
        elif isinstance(item, DTPShapeItem):
            self.panel_stack.setCurrentWidget(self.shape_container)
            self.shape_container.layout().addWidget(self.shadow_panel)
            self.shape_panel.set_item(item)
            self.shadow_panel.set_item(item)
        elif isinstance(item, DTPTableItem):
            self.panel_stack.setCurrentWidget(self.table_container)
            self.table_container.layout().addWidget(self.shadow_panel)
            self.table_panel.set_item(item)
            self.shadow_panel.set_item(item)
        elif isinstance(item, DTPGroupItem):
            self.panel_stack.setCurrentWidget(self.group_container)
            self.group_container.layout().addWidget(self.shadow_panel)
            self.shadow_panel.set_item(item)
        else:
            self.panel_stack.setCurrentIndex(0)

    def add_text(self):
        from items import DTPTextItem
        from commands import AddItemCommand
        
        item = DTPTextItem("New Text")
        command = AddItemCommand(self.scene, item, QPointF(100, 100))
        self.undo_stack.push(command)
        
        item.setSelected(True)
        item.setFocus()
        
    def group_items(self):
        items = self.scene.selectedItems()
        if len(items) > 1:
            from commands import GroupCommand
            command = GroupCommand(self.scene, items)
            self.undo_stack.push(command)

    def ungroup_items(self):
        items = self.scene.selectedItems()
        from items import DTPGroupItem
        from commands import UngroupCommand
        
        groups = [i for i in items if isinstance(i, DTPGroupItem)]
        if not groups: return
        
        if len(groups) > 1:
            self.undo_stack.beginMacro("複数グループ解除")
            for group in groups:
                cmd = UngroupCommand(self.scene, group)
                self.undo_stack.push(cmd)
            self.undo_stack.endMacro()
        else:
            cmd = UngroupCommand(self.scene, groups[0])
            self.undo_stack.push(cmd)
            
    def lock_items(self):
        items = self.scene.selectedItems()
        if not items: return
        self.undo_stack.beginMacro("Lock Items")
        from commands import LockChangeCommand
        for item in items:
            self.undo_stack.push(LockChangeCommand(item, True))
        self.undo_stack.endMacro()
        self.scene.clearSelection()

    def unlock_all_items(self):
        locked_items = [i for i in self.scene.items() if getattr(i, 'locked', False)]
        if not locked_items: return
        self.undo_stack.beginMacro("Unlock All")
        from commands import LockChangeCommand
        for item in locked_items:
            self.undo_stack.push(LockChangeCommand(item, False))
        self.undo_stack.endMacro()
        
    def export_pdf(self):
        from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        from PySide6.QtCore import QStandardPaths
        
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        file_path, _ = QFileDialog.getSaveFileName(self, "PDFエクスポート", desktop_path, "PDF Files (*.pdf)")
        
        if not file_path:
            return

        # Option Dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("PDFエクスポート設定")
        layout = QVBoxLayout(dialog)
        
        chk_grid = QCheckBox("グリッド線を描画する")
        chk_grid.setChecked(False) # Default: Off
        
        chk_border = QCheckBox("ページ枠線を描画する")
        chk_border.setChecked(True) # Default: On
        
        layout.addWidget(chk_grid)
        layout.addWidget(chk_border)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            self.scene.export_pdf(file_path, 
                                  draw_grid=chk_grid.isChecked(), 
                                  draw_border=chk_border.isChecked())

    def export_image(self):
        from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QCheckBox, QLabel, QSpinBox, QHBoxLayout, QDialogButtonBox
        from PySide6.QtCore import QStandardPaths
        
        desktop_path = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        file_path, _ = QFileDialog.getSaveFileName(self, "画像エクスポート", desktop_path, "Image Files (*.png *.jpg *.jpeg)")
        
        if not file_path:
            return

        # Option Dialog for DPI
        dialog = QDialog(self)
        dialog.setWindowTitle("画像エクスポート設定")
        layout = QVBoxLayout(dialog)
        
        dpi_layout = QHBoxLayout()
        dpi_label = QLabel("解像度 (DPI):")
        dpi_spin = QSpinBox()
        dpi_spin.setRange(72, 1200)
        dpi_spin.setValue(300)
        dpi_spin.setSingleStep(50)
        dpi_layout.addWidget(dpi_label)
        dpi_layout.addWidget(dpi_spin)
        
        chk_grid = QCheckBox("グリッド線を描画する")
        chk_grid.setChecked(False) # Default: Off
        
        chk_border = QCheckBox("ページ枠線を描画する")
        chk_border.setChecked(False) # Default: Off for images usually
        
        layout.addLayout(dpi_layout)
        layout.addWidget(chk_grid)
        layout.addWidget(chk_border)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            self.scene.export_image(file_path, 
                                    dpi=dpi_spin.value(),
                                    draw_grid=chk_grid.isChecked(), 
                                    draw_border=chk_border.isChecked())

    def add_table(self):
        from items import DTPTableItem
        from commands import AddItemCommand
        
        item = DTPTableItem(3, 3)
        command = AddItemCommand(self.scene, item, QPointF(100, 100))
        self.undo_stack.push(command)
        item.setSelected(True)

    def add_shape(self, shape_type):
        from items import DTPShapeItem
        from commands import AddItemCommand
        
        item = DTPShapeItem(shape_type)
        command = AddItemCommand(self.scene, item, QPointF(100, 100))
        self.undo_stack.push(command)
        item.setSelected(True)

    def save_project_quick(self):
        """Ctrl+S: 上書き保存。未保存なら名前をつけて保存。"""
        if self._current_file:
            from file_io import save_project_to
            save_project_to(self.scene, self._current_file)
            self._modified = False
            self._update_title()
        else:
            self.save_project()
    
    def save_project(self):
        from file_io import save_project
        # Use initial_path if current_file is not set
        initial_dir = self.initial_path if not self._current_file else None
        path = save_project(self.scene, self, initial_dir=initial_dir)
        if path:
            self._current_file = path
            self._modified = False
            self._update_title()

    def load_project(self):
        from file_io import load_project
        path = load_project(self.scene, self, initial_dir=self.initial_path)
        if path:
            self._current_file = path
            self._modified = False
            self._update_title()

    def align_items(self, align_type):
        items = self.scene.selectedItems()
        if not items:
            return
            
        from commands import AlignItemsCommand
        command = AlignItemsCommand(self.scene, items, align_type)
        self.undo_stack.push(command)

    def _change_page_size(self, name):
        self.scene.set_page_size(name, self.action_landscape.isChecked())
        # DO NOT auto-fit. Keep current zoom level.
        # self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        # self.update_zoom_label(self.view.transform().m11())
    
    def _toggle_landscape(self, checked):
        self.scene.set_page_size(self.scene._page_name, checked)
        # DO NOT auto-fit. Keep current zoom level.
        # self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        # self.update_zoom_label(self.view.transform().m11())

    def update_zoom_label(self, scale):
        self.zoom_label.setText(f"Zoom: {scale*100:.0f}%")
    
    def _toggle_snap(self, checked):
        self.scene.snap_enabled = checked
    
    def _on_layer_update(self):
        """Undo/Redo や操作後にレイヤーリストを更新"""
        self.layer_panel.refresh_list()
    
    def _on_undo_redo(self, idx=None):
        """Undo/Redo発生時にレイヤーリスト＋プロパティパネルを更新"""
        self.layer_panel.refresh_list()
        items = self.scene.selectedItems()
        if items:
            item = items[0]
            from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem
            if isinstance(item, DTPTextItem):
                self.text_panel._update_ui_from_item(item)
            elif isinstance(item, DTPImageItem):
                self.image_panel._update_ui_from_item(item)
            elif isinstance(item, DTPShapeItem):
                self.shape_panel._update_ui_from_item(item)
            elif isinstance(item, DTPTableItem):
                self.table_panel._update_ui_from_item(item)
