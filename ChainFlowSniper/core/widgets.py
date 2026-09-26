from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QListWidget, QListWidgetItem, QApplication
from PySide6.QtCore import Qt, Signal, QSize

class ExtractionItemWidget(QWidget):
    def __init__(self, text, is_html=False, preview_text=None, parent=None):
        super().__init__(parent)
        self.is_html = is_html
        self._full_text = text  # HTML原文またはプレーンテキスト
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 8, 10, 8)
        
        # HTMLバッジ付きヘッダー
        if is_html:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 4)
            badge = QLabel("HTML")
            badge.setObjectName("htmlBadge")
            badge.setFixedHeight(16)
            header.addWidget(badge)
            header.addStretch()
            self.layout.addLayout(header)
        
        # 表示テキスト（HTMLの場合はタグ除去済みプレビュー）
        display_text = preview_text if preview_text else text
        self.label = QLabel(display_text)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents) # クリックを親に透過
        self.layout.addWidget(self.label)
        
        self.is_expanded = False
        self.label.setMaximumHeight(100)
        self.setMinimumHeight(30) # 最低30pxを保証
        
    def get_full_text(self):
        """保持している全文を取得（HTMLの場合はHTML原文）"""
        return self._full_text
        
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.label.setMaximumHeight(16777215) # マックス解除
        else:
            self.label.setMaximumHeight(100)
        self.updateGeometry()

class ClipboardPopup(QDialog):
    closed = Signal(list)

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sniper Extraction List")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(300, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("extractionList")
        for text in items:
            self.add_item(text)
            
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

    def on_item_clicked(self, item):
        widget = self.list_widget.itemWidget(item)
        text = widget.get_full_text() if widget else item.text()
        if text:
            QApplication.clipboard().setText(text)

    def on_item_double_clicked(self, item):
        widget = self.list_widget.itemWidget(item)
        if widget and hasattr(widget, "toggle_expand"):
            widget.toggle_expand()
            item.setSizeHint(widget.sizeHint())

    def add_item(self, text):
        item = QListWidgetItem(text)
        # 透明なテキストを保持（検索やコピー用）
        item.setForeground(Qt.transparent) 
        self.list_widget.addItem(item)
        
        widget = ExtractionItemWidget(text)
        widget.adjustSize()
        height = max(widget.sizeHint().height(), 40)
        item.setSizeHint(QSize(100, height))
        
        self.list_widget.setItemWidget(item, widget)
        self.list_widget.scrollToBottom()

    def closeEvent(self, event):
        items_data = []
        for i in range(self.list_widget.count()):
            items_data.append(self.list_widget.item(i).text())
        self.closed.emit(items_data)
        super().closeEvent(event)
