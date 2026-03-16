from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton, QLabel, QToolButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class LayerPanel(QWidget):
    """レイヤー管理パネル: アイテムを zValue 順に表示し、選択・並び替えを行う"""
    
    def __init__(self, scene, undo_stack=None, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.undo_stack = undo_stack
        self._syncing = False  # 再帰防止フラグ
        self._item_map = {}   # id(item) -> item
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # ボタン行
        btn_layout = QHBoxLayout()
        
        self.btn_up = QPushButton("▲")
        self.btn_up.setToolTip("前面へ")
        self.btn_up.setFixedWidth(32)
        self.btn_up.clicked.connect(self.move_up)
        btn_layout.addWidget(self.btn_up)
        
        self.btn_down = QPushButton("▼")
        self.btn_down.setToolTip("背面へ")
        self.btn_down.setFixedWidth(32)
        self.btn_down.clicked.connect(self.move_down)
        btn_layout.addWidget(self.btn_down)
        
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setToolTip("更新")
        self.btn_refresh.setFixedWidth(32)
        self.btn_refresh.clicked.connect(self.refresh_list)
        btn_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(btn_layout)
        
        # リスト
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._sync_to_scene)
        layout.addWidget(self.list_widget)
        
        # シーンの選択変更を監視
        self.scene.selectionChanged.connect(self._sync_from_scene)
    
    def _get_item_label(self, item):
        """アイテムの種類に応じた表示名を返す"""
        from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem, DTPGroupItem
        
        if isinstance(item, DTPTextItem):
            text = item.toPlainText()[:15]
            return f"📝 {text}"
        elif isinstance(item, DTPImageItem):
            return "🖼️ Image"
        elif isinstance(item, DTPShapeItem):
            shape_icons = {'rect': '▭', 'ellipse': '○', 'line': '╱'}
            icon = shape_icons.get(item.shape_type, '?')
            return f"{icon} {item.shape_type.capitalize()}"
        elif isinstance(item, DTPTableItem):
            return f"☰ Table ({item._rows}x{item._cols})"
        elif isinstance(item, DTPGroupItem):
            return f"📁 Group ({len([c for c in item.childItems() if type(c).__name__ != 'ResizeHandle'])} items)"
        else:
            return f"? {type(item).__name__}"
    
    def refresh_list(self):
        """シーン内のアイテムを zValue 順にリスト化"""
        self._syncing = True
        self.list_widget.clear()
        
        # 親アイテムのみ抽出（子アイテム・ResizeHandle を除外）
        from items import ResizeHandle
        items = [i for i in self.scene.items() 
                 if i.parentItem() is None and not isinstance(i, ResizeHandle)]
        # zValue 降順（手前が上）
        items.sort(key=lambda x: x.zValue(), reverse=True)
        
        for item in items:
            list_item = QListWidgetItem()
            list_item.setData(Qt.UserRole, id(item))
            self.list_widget.addItem(list_item)
            
            # カスタムウィジェット
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setContentsMargins(2, 2, 2, 2)
            h_layout.setSpacing(4)
            
            # 表示名ラベル
            label = self._get_item_label(item)
            lbl = QLabel(label)
            h_layout.addWidget(lbl, 1)
            
            # 表示/非表示トグル (👁️)
            btn_vis = QToolButton()
            btn_vis.setText("👁️" if item.isVisible() else "🙈")
            btn_vis.setCheckable(True)
            btn_vis.setChecked(item.isVisible())
            btn_vis.setFixedSize(24, 24)
            btn_vis.clicked.connect(lambda checked, i=item, b=btn_vis: self.toggle_visibility(i, b))
            h_layout.addWidget(btn_vis)
            
            # ロック/アンロックトグル (🔒)
            btn_lock = QToolButton()
            is_locked = getattr(item, 'locked', False)
            btn_lock.setText("🔒" if is_locked else "🔓")
            btn_lock.setCheckable(True)
            btn_lock.setChecked(is_locked)
            btn_lock.setFixedSize(24, 24)
            btn_lock.clicked.connect(lambda checked, i=item, b=btn_lock: self.toggle_lock(i, b))
            h_layout.addWidget(btn_lock)
            
            list_item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(list_item, widget)
            
            if item.isSelected():
                list_item.setSelected(True)
        
        # アイテム参照辞書を構築
        self._item_map = {id(i): i for i in items}
        self._syncing = False
    
    def _sync_from_scene(self):
        """シーンの選択をリストに反映"""
        if self._syncing:
            return
        self._syncing = True
        
        try:
            if not self.scene:
                self._syncing = False
                return

            selected_items = self.scene.selectedItems()
            selected_ids = {id(i) for i in selected_items}
            
            for row in range(self.list_widget.count()):
                list_item = self.list_widget.item(row)
                item_id = list_item.data(Qt.UserRole)
                list_item.setSelected(item_id in selected_ids)
        except Exception as e:
            print(f"Layer sync error ignored: {e}")
        finally:
            self._syncing = False
    
    def _sync_to_scene(self):
        """リストの選択をシーンに反映"""
        if self._syncing:
            return
        self._syncing = True
        
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        
        for list_item in self.list_widget.selectedItems():
            item_id = list_item.data(Qt.UserRole)
            item = self._item_map.get(item_id)
            if item:
                item.setSelected(True)
        
        self.scene.blockSignals(False)
        self._syncing = False
    
    def move_up(self):
        """選択アイテムを前面へ（zValue を上げる）"""
        selected = self.list_widget.selectedItems()
        if not selected:
            return
        
        items = []
        for list_item in selected:
            item_id = list_item.data(Qt.UserRole)
            item = self._item_map.get(item_id)
            if item:
                items.append(item)
        
        if items and self.undo_stack:
            from commands import ZValueCommand
            self.undo_stack.push(ZValueCommand(items, 1))
        elif items:
            for item in items:
                item.setZValue(item.zValue() + 1)
        
        self.refresh_list()
    
    def move_down(self):
        """選択アイテムを背面へ（zValue を下げる）"""
        selected = self.list_widget.selectedItems()
        if not selected:
            return
        
        items = []
        for list_item in selected:
            item_id = list_item.data(Qt.UserRole)
            item = self._item_map.get(item_id)
            if item:
                items.append(item)
        
        if items and self.undo_stack:
            from commands import ZValueCommand
            self.undo_stack.push(ZValueCommand(items, -1))
        elif items:
            for item in items:
                item.setZValue(item.zValue() - 1)
        
        self.refresh_list()

    def toggle_visibility(self, item, btn):
        from commands import VisibilityChangeCommand
        new_vis = btn.isChecked()
        if self.undo_stack:
            self.undo_stack.push(VisibilityChangeCommand(item, new_vis))
        else:
            item.setVisible(new_vis)
        btn.setText("👁️" if item.isVisible() else "🙈")
        
    def toggle_lock(self, item, btn):
        from commands import LockChangeCommand
        new_lock = btn.isChecked()
        if self.undo_stack:
            self.undo_stack.push(LockChangeCommand(item, new_lock))
        else:
            item.set_locked(new_lock)
        btn.setText("🔒" if getattr(item, 'locked', False) else "🔓")
