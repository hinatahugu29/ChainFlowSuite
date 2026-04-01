
import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout,
                               QScrollArea, QSizePolicy, QApplication, QGraphicsOpacityEffect, QPushButton, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor, QPalette

class QuickLookWindow(QWidget):
    def __init__(self, parent=None):
        # WindowStaysOnTopHint: 常に最前面
        # WindowDoesNotAcceptFocus: フォーカスを奪わない（リスト操作を継続できる）
        # v17.1 Fix: HTMLプレビューのスクロール操作のため、フォーカスを受け取る設定に変更
        flags = Qt.Tool | Qt.FramelessWindowHint 
        super().__init__(parent, flags) 
        
        self.setWindowTitle("Quick Look")
        self.resize(1000, 800) # v17.0 HTML用に少し大きく
        
        # Debug Logger
        self.debug_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "quicklook_debug.log")
        self.log("Initialized")
        
        self.setup_ui()
        
    def log(self, message):
        # v16.2: Debug logging disabled for production
        # To re-enable, uncomment the block below:
        # try:
        #     with open(self.debug_log_path, "a", encoding="utf-8") as f:
        #         import datetime
        #         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #         f.write(f"[{timestamp}] {message}\n")
        # except: pass
        pass

    def setup_ui(self):
        # 背景を半透明の黒っぽくする（ガラス効果風）
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # メインレイアウト（角丸のコンテナを作る）
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(30, 30, 30, 0.98);
                border: 1px solid #454545;
                border-radius: 12px;
            }
            QLabel { color: #ddd; }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(1, 1, 1, 1) # コンテンツはギリギリまで
        self.container_layout.setSpacing(0)
        
        # ヘッダー（ファイル名表示）
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(40)
        self.header_widget.setStyleSheet("""
            background-color: transparent;
            border-bottom: 1px solid #454545;
        """)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.header_label = QLabel("FileName.txt")
        self.header_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; border: none;")
        
        self.copy_btn = QPushButton("Copy Content")
        self.copy_btn.setFixedSize(100, 24)
        self.copy_btn.setStyleSheet(self._btn_style())
        self.copy_btn.clicked.connect(self.copy_content)
        self.copy_btn.hide() # 初期状態は隠す（テキスト系のみ表示）

        # PDF Export Button (v17.0)
        self.pdf_btn = QPushButton("Export PDF")
        self.pdf_btn.setFixedSize(80, 24)
        self.pdf_btn.setStyleSheet(self._btn_style())
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.pdf_btn.hide()

        # Edit/Save Buttons (v15.0)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedSize(60, 24)
        self.edit_btn.setCheckable(True)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #333; color: #ccc; border: 1px solid #555; border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { background-color: #444; color: #fff; border-color: #666; }
            QPushButton:checked { background-color: #007acc; color: #fff; border-color: #0098ff; }
        """)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.edit_btn.hide()

        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(60, 24)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; color: #fff; border: 1px solid #2c974b; border-radius: 4px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2c974b; }
        """)
        self.save_btn.clicked.connect(self.save_content)
        self.save_btn.hide()

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.pdf_btn)
        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.copy_btn)
        
        self.container_layout.addWidget(self.header_widget)

        # コンテンツエリア
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0,0,0,0)
        
        # 各種ビューア
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.hide()
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.text_edit.hide() # 初期状態

        # v18.0: WebEngine removed for lightweight build
        
        self.info_label = QLabel() # 非対応ファイル用
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; color: #888;")
        self.info_label.hide()
        
        self.content_layout.addWidget(self.image_label)
        self.content_layout.addWidget(self.text_edit)
        self.content_layout.addWidget(self.info_label)
        
        self.container_layout.addWidget(self.content_area)
        self.main_layout.addWidget(self.container)
        
        # アニメーション用
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(150) # 高速に
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        
        # v14.1 Fix: RuntimeWarningを防ぐため、静的接続 + 状態チェック方式に変更
        self.anim.finished.connect(self._on_anim_finished)

    def _btn_style(self):
        return """
            QPushButton {
                background-color: #333;
                color: #ccc;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #444;
                color: #fff;
                border-color: #666;
            }
        """

    def show_file(self, path, edit_mode=False):
        self.log(f"show_file: {path} (edit={edit_mode})")
        if not path or not os.path.exists(path):
            self.log("Path not found/empty")
            return
        
        self._current_path = path  # 保存用に保持
            
        try:
            self.header_label.setText(os.path.basename(path))
            
            # リセット
            self.image_label.hide()
            self.text_edit.hide()
            self.info_label.hide()
            self.copy_btn.hide()
            self.edit_btn.hide()
            self.save_btn.hide()
            self.pdf_btn.hide()  # v18: Always hidden (no WebEngine)
            
            # Editボタンの状態リセット
            if self.edit_btn.isChecked():
                self.edit_btn.setChecked(False)
                self.toggle_edit_mode() # スタイル戻す
            
            # フォルダの場合
            if os.path.isdir(path):
                self.log("Type: Folder")
                try:
                    items = len(os.listdir(path))
                    self.show_info(f"📁 Folder\n\nContains {items} items.")
                except:
                    self.show_info("📁 Folder\n\n(Access Denied)")
                return

            ext = os.path.splitext(path)[1].lower()
            self.log(f"Type: File ({ext})")
            
            # v18.0: HTML files are displayed as text (WebEngine removed)
            # Users can use ChainFlowTool for rich HTML viewing

            # 画像
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg']:
                self._current_pixmap = QPixmap(path)
                if not self._current_pixmap.isNull():
                    view_w = self.width() - 40
                    view_h = self.height() - 80
                    scaled_pix = self._current_pixmap.scaled(view_w, view_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pix)
                    self.image_label.show()
                    self.copy_btn.show() # 画像表示時もコピーボタン有効
                    return

            # テキスト / コード
            # v7.6 .ahk support added
            # v18.0: HTML/HTM added as text files (no rich rendering)
            # v18.0: HTML files - Prompt to open ChainFlowTool
            # v18.0/v19.0: HTML/PDF files - Prompt to open ChainFlowTool
            if ext in ['.html', '.htm', '.pdf']:
                file_type = "PDF" if ext == '.pdf' else "HTML"
                self.info_label.setText(f"{file_type} Preview Available\n\nClick 'Edit' to open in ChainFlowTool\nfor high-fidelity preview.")
                self.info_label.show()
                self.edit_btn.show()
                if not self.edit_btn.isChecked():
                    self.edit_btn.setChecked(True)
                return

            text_exts = ['.txt', '.md', '.py', '.json', '.js', '.css', '.csv', '.xml', '.yaml', '.yml', '.ini', '.log', '.bat', '.sh', '.cpp', '.h', '.java', '.ahk']
            if ext in text_exts:
                try:
                    content = ""
                    for enc in ['utf-8', 'shift-jis', 'latin-1']:
                        try:
                            with open(path, 'r', encoding=enc) as f:
                                content = f.read(10000)
                            break
                        except: continue
                    
                    # 空ファイルでも編集可能にする
                    # if content: (条件を緩和)
                    
                    self.text_edit.setPlainText(content)
                    self.text_edit.show()
                    self.copy_btn.show() # テキスト表示時はコピーボタン有効
                    
                    # 編集ボタン有効化
                    self.edit_btn.show()
                    
                    # 自動編集モード
                    if edit_mode:
                        self.edit_btn.setChecked(True)
                        self.toggle_edit_mode()
                    elif not content:
                        # コンテンツがない場合、明示的にInfoを消す（もし残っていたら）
                        self.info_label.hide()
                    return
                except Exception as e:
                    self.log(f"Text read error: {e}")
                    self.show_info(f"Error reading file:\n{e}")
                    return
            
            # その他 (PDFなど非対応ファイル)
            size_str = "Unknown size"
            try:
                # PermissionErrorなどで落ちないように
                size_str = f"{os.path.getsize(path):,} bytes"
            except Exception as e:
                self.log(f"Getsize error: {e}")
                size_str = f"Error getting size: {e}"
            
            self.show_info(f"Preview not available for '{ext}' files.\n\nSize: {size_str}")

        except Exception as e:
            # 最悪のケース
            self.log(f"CRITICAL ERROR in show_file: {e}")
            print(f"QuickLook Error: {e}", file=sys.stderr)
            self.show_info(f"System Error:\n{str(e)}")

    def export_pdf(self):
        """v18.0: PDF Export removed (use ChainFlowTool)"""
        pass

    def copy_content(self):
        """現在表示中のコンテンツをクリップボードにコピー"""
        feedback = False
        
        # テキストの場合
        if self.text_edit.isVisible():
            QApplication.clipboard().setText(self.text_edit.toPlainText())
            feedback = True
            
        # 画像の場合
        elif self.image_label.isVisible() and hasattr(self, '_current_pixmap') and not self._current_pixmap.isNull():
            QApplication.clipboard().setPixmap(self._current_pixmap)
            feedback = True

        if feedback:
            # フィードバック
            orig_text = self.copy_btn.text()
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(1000, lambda: self.copy_btn.setText(orig_text))

    def show_info(self, text):
        self.log(f"Show Info: {text.replace(chr(10), ' ')}")
        self.info_label.setText(text)
        self.info_label.show()

    def popup(self, center_pos=None):
        """アニメーション付きで表示"""
        if self.isVisible() and self.anim.state() == QPropertyAnimation.Running and self.anim.endValue() == 1:
            return

        self.log("popup")
        
        # v14.1 Fix: disconnect不要

        if center_pos:
            # ウィンドウの中心を指定位置に合わせる
            geo = self.geometry()
            geo.moveCenter(center_pos)
            self.setGeometry(geo)
            
            # v17.0 画面外にはみ出さないように補正（大きくなったので重要）
            screen = QApplication.primaryScreen().availableGeometry()
            curr = self.geometry()
            if not screen.contains(curr):
                if curr.right() > screen.right(): curr.moveRight(screen.right() - 20)
                if curr.bottom() > screen.bottom(): curr.moveBottom(screen.bottom() - 20)
                if curr.left() < screen.left(): curr.moveLeft(screen.left() + 20)
                if curr.top() < screen.top(): curr.moveTop(screen.top() + 20)
                self.setGeometry(curr)
                
        self.show()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1)
        self.anim.start()

    def fade_out(self):
        """アニメーション付きで非表示（終了後にhide）"""
        if not self.isVisible() or self.anim.state() == QPropertyAnimation.Running and self.anim.endValue() == 0:
            return
            
        self.log("fade_out")

        # v14.1 Fix: disconnect/connect不要
        
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0)
        self.anim.start()

    def _on_anim_finished(self):
        """v14.1 アニメーション終了時のハンドラ"""
        # フェードアウト（不透明度0へ向かうアニメーション）が完了したときだけhideする
        if self.anim.endValue() == 0:
            self.hide()
            # v18.0: No WebEngine to clean up

    # --- v15.0 Quick Edit Features ---
    def toggle_edit_mode(self):
        """編集モードの切り替え (v16.0: Launch External Editor)"""
        # Close QuickLook (Fade out)
        self.fade_out()
        
        # Launch Satellite Editor via MainWindow
        if self.parent() and hasattr(self.parent(), 'launch_editor'):
            # 少し待ってから起動（アニメーションと被らないように）
            QTimer.singleShot(150, lambda: self.parent().launch_editor(self._current_path))
        else:
            self.log("Error: Parent has no launch_editor method")

    def save_content(self):
        """編集内容を保存"""
        if not hasattr(self, '_current_path') or not self._current_path:
            return
            
        try:
            content = self.text_edit.toPlainText()
            # 文字コードは一旦UTF-8固定（簡易版のため）
            # 必要なら元のエンコードを保持するロジックが必要だが、新規作成はUTF-8なので一旦OK
            with open(self._current_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Feedback
            orig_text = self.save_btn.text()
            self.save_btn.setText("Saved!")
            QTimer.singleShot(1000, lambda: self.save_btn.setText(orig_text))
            
            self.log(f"Saved file: {self._current_path}")
            
        except Exception as e:
            self.log(f"Save error: {e}")
            self.header_label.setText(f"Error: {e}")

    def keyPressEvent(self, event):
        # QuickLook自体にフォーカスがある場合、SpaceやEscで閉じる
        # v15.0: 編集モード時はSpaceで閉じないようにする
        if self.edit_btn.isChecked():
            # 編集モード中
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_S:
                self.save_content()
                return
            elif event.key() == Qt.Key_Escape:
                # ユーザー要望機能: Escで即座にウィンドウを閉じる
                self.fade_out()
                return
        else:
            # View Mode
            if event.key() == Qt.Key_Space or event.key() == Qt.Key_Escape:
                self.fade_out()
                return
            elif event.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
                # v17.1 Forward navigation keys to parent logic if possible
                if self.parent() and hasattr(self.parent(), 'hovered_pane') and self.parent().hovered_pane:
                     # Send exact key event to the active pane's view
                     # Note: We need to target the internal QTreeView usually
                     pane = self.parent().hovered_pane
                     # pane has 'views' list [(view, proxy, root, ...), ...]
                     # Try to send to the focused view or the last active one
                     # If the pane is highlighted, let's assume its first view is primary for now or use pane.get_current_view() if avail
                     # But simple 'sendEvent' to the pane widget itself might not work if it doesn't handle keyPress.
                     # The pane is usually QFrame. The views are QTreeView.
                     # Let's try sending to pane, hoping it propagates or pane handles it? 
                     # Actually, MainWindow dispatch_shortcut uses `run_on_hovered`.
                     # Let's try to find the view.
                     
                     target = None
                     if hasattr(pane, 'views') and pane.views:
                         target = pane.views[0][0] # First view
                     
                     if target:
                         QApplication.sendEvent(target, event)
                         # The selection change in TreeView should trigger MainWindow's logic if connected?
                         # Usually standard QTreeView selection change doesn't auto-update QuickLook unless explicitly connected.
                         # But user just wants to navigate. If they navigate, they might expect QL to update.
                         # Existing QL logic: MainWindow.update_preview() is called? 
                         # MainWindow calls update_preview()? 
                         # Let's check update_preview usage in MainWindow later if it doesn't update.
                         # For now, just forwarding the key is the goal.
                         
                         # Also, if we forward the key, we should RETURN so we don't call super() double handling?
                         return

        super().keyPressEvent(event)

    def wheelEvent(self, event):
        # v18.0: Simplified (no WebEngine)
        super().wheelEvent(event)

    def eventFilter(self, obj, event):
        # v18.0: Simplified (no WebEngine)
        return super().eventFilter(obj, event)

    # v18.0: WebEngine helper methods removed

