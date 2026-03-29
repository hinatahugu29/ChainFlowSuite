import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QFileDialog, QMessageBox, QLabel,
    QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QFont, QIcon, QShowEvent

try:
    from .ui_utils import apply_dark_title_bar
except ImportError:
    # Fallback or stub if running standalone without Filer structure (unlikely for this file)
    def apply_dark_title_bar(win): pass

try:
    from pypdf import PdfWriter
except ImportError:
    PdfWriter = None

class DragDropListWidget(QListWidget):
    """ドラッグ＆ドロップで順番を入れ替え、さらに外部ファイルも受け入れられるリストウィジェット"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)  # 外部ドロップを許可
        self.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 5px;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                border-radius: 3px;
                margin-bottom: 2px;
                padding: 6px;
                border: 1px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
                border: 1px solid #007acc;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".pdf"):
                    self.add_pdf(file_path)
        else:
            super().dropEvent(event)

    def add_pdf(self, file_path):
        # 重複チェック（ツールチップ＝フルパスで判定）
        items = [self.item(i).toolTip() for i in range(self.count())]
        if file_path not in items:
            display_name = os.path.basename(file_path)
            self.addItem(display_name)
            self.item(self.count()-1).setToolTip(file_path)

class PDFMergerWindow(QMainWindow):
    def __init__(self, parent=None, initial_files=None):
        super().__init__(parent)
        if PdfWriter is None:
            QMessageBox.critical(self, "Error", "pypdf library is not installed.\nPlease run: pip install pypdf")
            self.close()
            return

        self.init_ui()
        
        # 初期ファイルがあれば追加
        if initial_files:
            for f in initial_files:
                if os.path.exists(f) and f.lower().endswith('.pdf'):
                    self.file_list.add_pdf(f)

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def init_ui(self):
        self.setWindowTitle("PDF Merger")
        self.resize(600, 500)
        
        # メインウィジェットとレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # スタイルシート設定（ChainFlowFiler共通テーマに合わせる）
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #252526;
            }
            QPushButton#actionButton {
                background-color: #0e639c; /* VSCode Blue */
                border: 1px solid #1177bb;
            }
            QPushButton#actionButton:hover {
                background-color: #1177bb;
            }
            QPushButton#dangerButton {
                background-color: #8a3b3b;
            }
            QPushButton#dangerButton:hover {
                background-color: #a14545;
            }
        """)

        # タイトル
        title_label = QLabel("PDF Merger")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Drag & Drop to reorder files")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #888888; margin-bottom: 5px;")
        main_layout.addWidget(subtitle_label)

        # ファイルリスト
        self.file_list = DragDropListWidget()
        main_layout.addWidget(self.file_list)

        # ボタンコントロール（上部）
        top_button_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add PDFs...")
        self.btn_add.clicked.connect(self.add_files)
        top_button_layout.addWidget(self.btn_add)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        top_button_layout.addWidget(self.btn_remove)
        
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_files)
        top_button_layout.addWidget(self.btn_clear)

        main_layout.addLayout(top_button_layout)

        # --------------------------
        # Checkbox for Auto-Close
        # ユーザーの「悩みどころ」に対する解決策：選択可能にする
        self.chk_close = QCheckBox("Close window after successful merge")
        self.chk_close.setChecked(True) # Default to auto-close for efficiency
        self.chk_close.setStyleSheet("QCheckBox { color: #cccccc; margin-top: 10px; margin-bottom: 5px; } QCheckBox::indicator { width: 16px; height: 16px; }")
        main_layout.addWidget(self.chk_close)
        # --------------------------

        # 結合実行ボタン
        self.btn_merge = QPushButton("Merge PDFs")
        self.btn_merge.setObjectName("actionButton")
        self.btn_merge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_merge.clicked.connect(self.merge_pdfs)
        main_layout.addWidget(self.btn_merge)

        # ステータスバー
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("color: #888888; border-top: 1px solid #3d3d3d;")

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if files:
            count = 0
            for file_path in files:
                self.file_list.add_pdf(file_path)
                count += 1
            self.statusBar().showMessage(f"Added {count} files")

    def remove_selected(self):
        items = self.file_list.selectedItems()
        if not items: return
        
        for item in items:
            self.file_list.takeItem(self.file_list.row(item))
        self.statusBar().showMessage(f"Removed {len(items)} files")

    def clear_files(self):
        self.file_list.clear()
        self.statusBar().showMessage("List cleared")

    def merge_pdfs(self):
        count = self.file_list.count()
        if count < 2:
            QMessageBox.warning(self, "Warning", "Need at least 2 PDF files to merge.")
            return

        # 初期ファイル名提案（最初のファイル名 + _merged）
        first_file = self.file_list.item(0).toolTip()
        dir_name = os.path.dirname(first_file)
        base_name = os.path.splitext(os.path.basename(first_file))[0]
        default_save = os.path.join(dir_name, f"{base_name}_merged.pdf")

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF", default_save, "PDF Files (*.pdf)"
        )

        if save_path:
            try:
                self.statusBar().showMessage("Merging...")
                # UI更新のためにイベントループを回す
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()
                
                merger = PdfWriter()
                for i in range(count):
                    file_path = self.file_list.item(i).toolTip()
                    merger.append(file_path)
                
                with open(save_path, "wb") as f:
                    merger.write(f)
                
                merger.close()
                
                reply = QMessageBox.information(self, "Success", f"PDFs merged successfully!\nSaved to:\n{save_path}")
                self.statusBar().showMessage("Merge Completed")
                
                # Auto-close logic
                if self.chk_close.isChecked():
                    self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during merge:\n{str(e)}")
                self.statusBar().showMessage("Merge Failed")
