from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QColorDialog, QScrollArea, QGridLayout, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QAction

class SwatchButton(QPushButton):
    """Button representing a single color swatch"""
    colorApplied = Signal(QColor)
    colorRemoved = Signal(QColor)
    
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(QSize(24, 24))
        self.setToolTip(color.name())
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name(QColor.HexArgb)};
                border: 1px solid #505050;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 1px solid #ffffff;
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.colorApplied.emit(self.color)
        elif event.button() == Qt.RightButton:
            # Context menu to delete
            menu = QMenu(self)
            remove_action = QAction("Remove Swatch", self)
            remove_action.triggered.connect(lambda: self.colorRemoved.emit(self.color))
            menu.addAction(remove_action)
            menu.exec(event.globalPos())
        super().mousePressEvent(event)

class SwatchPanel(QWidget):
    """Panel for managing document color swatches"""
    swatchAdded = Signal(QColor)
    swatchRemoved = Signal(QColor)
    
    def __init__(self, scene, undo_stack, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.undo_stack = undo_stack
        self.swatches = [] # List of QColors
        
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        
        # Header controls
        header_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ Add Color")
        self.add_btn.setToolTip("Add current item's color or choose new")
        self.add_btn.clicked.connect(self._add_color)
        
        header_layout.addWidget(QLabel("Swatches:"))
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)
        
        self.layout.addLayout(header_layout)
        
        # Swatch grid area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll_area.setWidget(self.grid_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Default palettes (initial state)
        default_colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff", "#ff00ff", "#000000", "#ffffff"]
        for c in default_colors:
            self._add_color_to_list(QColor(c), emit_signal=False)
            
    def _add_color(self):
        # Default behavior: open color dialog
        initial_color = Qt.white
        items = self.scene.selectedItems()
        if items:
            item = items[0]
            if hasattr(item, '_fill_color'):
                initial_color = item._fill_color
            elif hasattr(item, '_text_color'):
                initial_color = item._text_color
                
        color = QColorDialog.getColor(initial_color, self, "Add Swatch", options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self._add_color_to_list(color)
            
    def _add_color_to_list(self, color, emit_signal=True):
        if isinstance(color, str):
            color = QColor(color)
            
        # Optional: prevent duplicates based on hex name
        if any(c.name(QColor.HexArgb) == color.name(QColor.HexArgb) for c in self.swatches):
            return
            
        self.swatches.append(color)
        self._refresh_grid()
        if emit_signal:
            self.swatchAdded.emit(color)
            
    def remove_swatch(self, color):
        name_to_remove = color.name(QColor.HexArgb)
        self.swatches = [c for c in self.swatches if c.name(QColor.HexArgb) != name_to_remove]
        self._refresh_grid()
        self.swatchRemoved.emit(color)
        
    def set_swatches(self, hex_list):
        """Sets the swatches from a list of hex strings (used on project load)"""
        self.swatches = [QColor(h) for h in hex_list]
        self._refresh_grid()
        
    def get_swatches(self):
        """Returns list of hex strings for saving"""
        return [c.name(QColor.HexArgb) for c in self.swatches]
        
    def _refresh_grid(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Rebuild
        cols = 6  # Fixed number of columns for now, or could be dynamic based on width
        col = 0
        row = 0
        for color in self.swatches:
            btn = SwatchButton(color)
            btn.colorApplied.connect(self._apply_color_to_selection)
            btn.colorRemoved.connect(self.remove_swatch)
            self.grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
                
    def _apply_color_to_selection(self, color):
        items = self.scene.selectedItems()
        if not items:
            return
            
        from commands import PropertyChangeCommand
        
        # For multiple items, begin a macro
        if len(items) > 1:
            self.undo_stack.beginMacro("Apply Swatch Color")
            for item in items:
                self._apply_to_item(item, color)
            self.undo_stack.endMacro()
        else:
            self._apply_to_item(items[0], color)
            
    def _apply_to_item(self, item, color):
        from commands import PropertyChangeCommand
        from items import DTPTextItem, DTPShapeItem, DTPTableItem
        
        # Determine which property to change based on item type
        if isinstance(item, DTPTextItem):
            cmd = PropertyChangeCommand(item, "text_color", color)
            self.undo_stack.push(cmd)
        elif hasattr(item, "_fill_color"):
            cmd = PropertyChangeCommand(item, "fill_color", color)
            self.undo_stack.push(cmd)
