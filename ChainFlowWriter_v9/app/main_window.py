import os
import sys
# ctypes is no longer needed here as apply_dark_title_bar is imported from a utility module
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter,
                               QFileDialog, QMessageBox, QMenu)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QIcon, QAction
from app.widgets.editor_pane import EditorPane
from app.widgets.preview_pane import PreviewPane
from app.widgets.property_pane import PropertyPane
from app.widgets.cheat_sheet_dialog import CheatSheetDialog
from app.widgets.snippet_register_dialog import SnippetRegisterDialog
from app.core.snippet_manager import SnippetManager
from app.core.thumbnail_generator import ThumbnailGenerator
from app.core.paths import get_data_dir
from app.utils.theme import apply_dark_title_bar


class MainWindow(QMainWindow):
    def __init__(self, initial_file=None):
        super().__init__()
        self.setWindowTitle("ChainFlow Writer v9 - Untitled")
        self.resize(1400, 900)
        
        # Icon Setting
        self._set_icon()
        
        self.current_file = None
        
        # Core Managers with Robust Path Management
        snippets_dir = get_data_dir("ChainFlowWriter")
        print(f"Using data directory: {snippets_dir}")
        
        self.snippet_manager = SnippetManager(snippets_dir)
        self.thumbnail_generator = ThumbnailGenerator(self.snippet_manager.thumbnail_dir)
        
        # Connect Thumbnail Generator success signal
        self.thumbnail_generator.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.thumbnail_generator.generation_failed.connect(lambda err: print(f"Thumbnail Error: {err}"))
        
        self.is_modified = False
        
        self._setup_ui()
        self._apply_theme()
        
        # On first run, seed default snippets if none exist
        if not self.snippet_manager.snippets:
            self._seed_default_snippets()
        
        # Determine initial working directory and file to load
        if initial_file:
            # Normalize path (remove extra quotes, trailing slashes)
            norm_path = os.path.abspath(initial_file.strip('"').rstrip('\\/'))
            
            if os.path.exists(norm_path):
                if os.path.isdir(norm_path):
                    # It's a directory: Start as Untitled in THIS directory
                    self.current_file = None
                    self.last_dir = norm_path
                else:
                    # It's a file: Load it and use its parent as last_dir
                    self.current_file = norm_path
                    self.last_dir = os.path.dirname(norm_path)
                    QTimer.singleShot(100, lambda: self._load_file(norm_path))
            else:
                # Path doesn't exist (maybe new file name from CLI?)
                self.last_dir = os.getcwd()
        else:
            # Fallback to Desktop for better UX
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.last_dir = desktop if os.path.exists(desktop) else os.getcwd()
            
        # Push to property pane for initial exports
        self.property_pane.last_dir = self.last_dir

    def _set_icon(self):
        icon_path = ""
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS logic for PyInstaller
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # Local dev path (relative to main.py)
            # app/main_window.py is 2 levels deep from project root
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")

        
    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
        
    def closeEvent(self, event):
        if not self.is_modified:
            event.accept()
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("保存の確認")
        msg_box.setText("ドキュメントは変更されています。")
        msg_box.setInformativeText("変更を保存しますか？")
        msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Save)
        
        # Customize button text to Japanese
        msg_box.button(QMessageBox.Save).setText("保存 (&S)")
        msg_box.button(QMessageBox.Discard).setText("保存しない (&N)")
        msg_box.button(QMessageBox.Cancel).setText("キャンセル")
        
        ret = msg_box.exec()
        
        if ret == QMessageBox.Save:
            if self._on_save_requested():
                event.accept()
            else:
                event.ignore()
        elif ret == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

    def _set_modified(self, modified):
        if self.is_modified == modified:
            return
        self.is_modified = modified
        title = self.windowTitle()
        if modified:
            if not title.endswith(" *"):
                self.setWindowTitle(title + " *")
        else:
            if title.endswith(" *"):
                self.setWindowTitle(title[:-2])
        
    def _setup_ui(self):
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(1)
        
        self.editor_pane = EditorPane()
        self.preview_pane = PreviewPane()
        self.property_pane = PropertyPane()
        
        self.main_splitter.addWidget(self.editor_pane)
        self.main_splitter.addWidget(self.preview_pane)
        self.main_splitter.addWidget(self.property_pane)
        
        self.main_splitter.setSizes([400, 700, 300])
        self.setCentralWidget(self.main_splitter)
        
        # Connect editor to preview and IO
        self.editor_pane.text_changed.connect(self._on_text_changed)
        self.editor_pane.save_requested.connect(self._on_save_requested)
        self.editor_pane.save_as_requested.connect(self._on_save_as_requested)
        self.editor_pane.open_requested.connect(self._on_open_requested)
        
        # Connect editor to cheat sheet workflows
        self.editor_pane.open_cheat_sheet_requested.connect(self._on_open_cheat_sheet)
        self.editor_pane.save_snippet_requested.connect(self._on_save_snippet_requested)
        
        # Connect properties to preview
        self.property_pane.margins_changed.connect(self.preview_pane.update_margins)
        self.property_pane.typography_changed.connect(self.preview_pane.update_typography)
        self.property_pane.page_size_changed.connect(self.preview_pane.update_page_size)
        self.property_pane.page_decor_changed.connect(self.preview_pane.update_page_decor)
        self.property_pane.guides_toggled.connect(self.preview_pane.set_guides_visible)
        
        # PDF書き出しフローの制御（JS側での改ページ除去などの準備を経てから出力する）
        self.property_pane.export_pdf_requested.connect(self._handle_pdf_export)
        self.property_pane.refresh_requested.connect(self._handle_preview_refresh)
        
        # PDF出力完了通知
        self.preview_pane.pdf_export_finished.connect(self._on_pdf_export_finished)
        
        # Connect settings changes to modification tracking
        self.property_pane.margins_changed.connect(lambda: self._set_modified(True))
        self.property_pane.typography_changed.connect(lambda: self._set_modified(True))
        self.property_pane.page_size_changed.connect(lambda: self._set_modified(True))
        self.property_pane.page_decor_changed.connect(lambda: self._set_modified(True))
        
        # Menus & Shortcuts
        self._setup_file_menu()
        self._setup_view_menu()
        
        # Setup initial state
        self.property_pane._emit_margins()
        self.property_pane._emit_typography()
        self.property_pane._emit_page_size()
        self.property_pane._emit_page_decor()

        
    def _setup_file_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル (File)")
        
        act_open = QAction("開く (Open)", self)
        act_open.setShortcut("Ctrl+O")
        act_open.setShortcutContext(Qt.WindowShortcut)
        act_open.triggered.connect(self._on_open_requested)
        file_menu.addAction(act_open)
        self.addAction(act_open)
        
        file_menu.addSeparator()
        
        act_save = QAction("保存 (Save)", self)
        act_save.setShortcut("Ctrl+S")
        act_save.setShortcutContext(Qt.WindowShortcut)
        act_save.triggered.connect(self._on_save_requested)
        file_menu.addAction(act_save)
        self.addAction(act_save)
        
        act_save_as = QAction("名前を付けて保存 (Save As...)", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.setShortcutContext(Qt.WindowShortcut)
        act_save_as.triggered.connect(self._on_save_as_requested)
        file_menu.addAction(act_save_as)
        self.addAction(act_save_as)
        
        file_menu.addSeparator()
        
        act_export = QAction("PDFとして書き出し (Export PDF)...", self)
        act_export.setShortcut("Ctrl+P")
        act_export.setShortcutContext(Qt.WindowShortcut)
        act_export.triggered.connect(self.property_pane._on_export_pdf)
        file_menu.addAction(act_export)
        self.addAction(act_export)
        
        file_menu.addSeparator()
        
        act_exit = QAction("終了 (Exit)", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    def _setup_view_menu(self):
        menubar = self.menuBar()
        # Custom dark styling for the native menubar if possible, but standard is fine for now
        view_menu = menubar.addMenu("表示 (View)")
        
        act_toggle_ed = QAction("エディタを切り替え (Toggle Editor)", self)
        act_toggle_ed.setShortcut("Ctrl+Alt+B")
        act_toggle_ed.setShortcutContext(Qt.WindowShortcut)
        act_toggle_ed.triggered.connect(self._toggle_editor_pane)
        view_menu.addAction(act_toggle_ed)
        self.addAction(act_toggle_ed)
        
        act_toggle_prop = QAction("設定パネルを切り替え (Toggle Settings)", self)
        act_toggle_prop.setShortcut("Ctrl+R")
        act_toggle_prop.setShortcutContext(Qt.WindowShortcut)
        act_toggle_prop.triggered.connect(self._toggle_property_pane)
        view_menu.addAction(act_toggle_prop)
        self.addAction(act_toggle_prop)
        
        view_menu.addSeparator()
        
        act_open_data = QAction("データフォルダを開く (Open Data Folder)", self)
        act_open_data.setShortcut("Ctrl+Shift+O")
        act_open_data.setShortcutContext(Qt.WindowShortcut)
        act_open_data.triggered.connect(self._on_open_data_folder)
        view_menu.addAction(act_open_data)
        self.addAction(act_open_data)
        
        view_menu.addSeparator()
        
        act_focus = QAction("集中モード (Focus Mode)", self)
        act_focus.setShortcut("F11")
        act_focus.setShortcutContext(Qt.WindowShortcut)
        act_focus.triggered.connect(self._toggle_focus_mode)
        view_menu.addAction(act_focus)
        self.addAction(act_focus)

        view_menu.addSeparator()
        
        act_refresh = QAction("プレビューを更新 (Refresh Preview)", self)
        act_refresh.setShortcut("F5")
        act_refresh.setShortcutContext(Qt.WindowShortcut)
        act_refresh.triggered.connect(self._handle_preview_refresh)
        view_menu.addAction(act_refresh)
        self.addAction(act_refresh)
        
    def _toggle_focus_mode(self):
        """Toggle Editor and Property panes to focus on Preview only, or restore them."""
        # Simple implementation: if either is visible, hide both. If both hidden, show both.
        if self.editor_pane.isVisible() or self.property_pane.isVisible():
            self.editor_pane.hide()
            self.property_pane.hide()
        else:
            self.editor_pane.show()
            self.property_pane.show()

    def _on_open_data_folder(self):
        import subprocess
        path = self.snippet_manager.data_dir
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            else:
                # Fallback for other OS if needed
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, path])
        else:
            QMessageBox.information(self, "Info", "Data folder hasn't been created yet.")
        
    def _toggle_editor_pane(self):
        is_visible = self.editor_pane.isVisible()
        self.editor_pane.setVisible(not is_visible)
        # Force splitter to re-layout gracefully
        if not is_visible:
            # If we are showing it again, give it some default width
            self.main_splitter.setSizes([400, 700, 300])

    def _toggle_property_pane(self):
        is_visible = self.property_pane.isVisible()
        self.property_pane.setVisible(not is_visible)
        if not is_visible:
            self.main_splitter.setSizes([400, 700, 300])
        
    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1E1E1E; }
            QSplitter::handle { background-color: #3E3E42; }
            QSplitter::handle:horizontal { width: 1px; }
            
            /* Menu Bar Styling */
            QMenuBar {
                background-color: #1E1E1E;
                color: #B0B0B0;
                border: none;
                border-bottom: 1px solid #3E3E42;
                font-size: 11px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background: #3E3E42;
                color: #FFFFFF;
            }
            QMenu {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #454545;
                font-size: 11px;
            }
            QMenu::item {
                padding: 5px 25px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background: #454545;
                margin: 4px 0px;
            }

            /* Global ScrollBar Style to match VSCode / ChainFlow style */
            QScrollBar:vertical {
                border: none;
                background: #252526;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4F4F4F;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #252526;
                height: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #424242;
                min-width: 20px;
            }
        """)
        
    def _handle_pdf_export(self, path):
        """PDF出力の実行。新設計では PreviewPane 側でクリーンな印刷用コピーが作成されるため、直接呼び出す。"""
        self.preview_pane.export_pdf(path)

    def _handle_preview_refresh(self):
        # ブラウザのリロード処理を実行（右クリックメニューのReloadと同じ効果）
        self.preview_pane.web_view.reload()
        
    def _on_pdf_export_finished(self, success, message):
        """PDF出力の完了通知を受け取り、ユーザーに結果を表示する。"""
        if success:
            QMessageBox.information(self, "PDF Export", message)
        else:
            QMessageBox.critical(self, "PDF Export Error", message)
        
    def _on_text_changed(self, text):
        self.preview_pane.update_preview(text, self.last_dir)
        self._set_modified(True)

    def _on_open_requested(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown", self.last_dir, "Markdown Files (*.md);;All Files (*.*)")
        if not path: return
        self._load_file(path)

    def _on_open_cheat_sheet(self):
        dialog = CheatSheetDialog(self.snippet_manager, self)
        dialog.insert_requested.connect(self.editor_pane._insert_at_cursor)
        dialog.exec()

    def _on_save_snippet_requested(self, raw_content):
        dialog = SnippetRegisterDialog(raw_content, self)
        if dialog.exec():
            data = dialog.get_data()
            title = data["title"] or "Untitled Snippet"
            tags = data["tags"]
            content = data["content"]
            
            # Generate a consistent filename for the thumbnail
            import uuid
            thumb_filename = f"{uuid.uuid4().hex[:8]}.png"
            
            # Save the snippet record immediately
            snippet_id = self.snippet_manager.add_snippet(title, tags, content, thumb_filename)
            
            # Trigger background thumbnail generation
            self.thumbnail_generator.generate_thumbnail(content, thumb_filename)
            
    def _on_thumbnail_ready(self, filename):
        print(f"Thumbnail successfully generated: {filename}")
        # The CheatSheetDialog reloads snippets dynamically on open, 
        # so we don't need to force a UI refresh if it's closed.

        
    def _load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            settings, content = self._parse_frontmatter(text)
            
            # Apply to UI
            if settings:
                self.property_pane.apply_settings(settings)
                
            # Temporarily block signals to avoid preview updates while loading doc
            self.editor_pane.editor.blockSignals(True)
            self.editor_pane.editor.setPlainText(content)
            self.editor_pane.editor.blockSignals(False)
            
            self.current_file = path
            self.last_dir = os.path.dirname(os.path.abspath(path))
            self.property_pane.last_dir = self.last_dir # Sync with PDF export
            self.preview_pane.update_preview(content, self.last_dir)
            self.setWindowTitle(f"ChainFlow Writer v9 - {os.path.basename(path)}")
            self._set_modified(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _on_save_requested(self):
        if not self.current_file:
            return self._on_save_as_requested()
            
        return self._save_to_path(self.current_file)

    def _on_save_as_requested(self):
        default_name = os.path.basename(self.current_file) if self.current_file else "Untitled.md"
        initial_path = os.path.join(self.last_dir, default_name)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown As", initial_path, "Markdown Files (*.md);;All Files (*.*)"
        )
        if not path:
            return False
            
        self.current_file = path
        return self._save_to_path(self.current_file)

    def _save_to_path(self, path):
        content = self.editor_pane.editor.toPlainText()
        settings = self.property_pane.get_settings()
        full_text = self._build_frontmatter(settings) + content
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            self.setWindowTitle(f"ChainFlow Writer v9 - {os.path.basename(path)}")
            self._set_modified(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
            return False
            
    def _parse_frontmatter(self, text):
        import yaml
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                fm_str = parts[1].strip()
                try:
                    data = yaml.safe_load(fm_str)
                    content = parts[2].lstrip()
                    return data or {}, content
                except Exception as e:
                    print(f"Frontmatter parse error: {e}")
        return {}, text
        
    def _build_frontmatter(self, settings):
        lines = ["---"]
        for k, v in settings.items():
            if isinstance(v, str):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f'{k}: {v}')
        lines.append("---")
        # Ensure a trailing newline to separate from markdown text
        return "\n".join(lines) + "\n\n"

    def _seed_default_snippets(self):
        # Default snippets packed into the application logic 
        # to ensure they are available without external files tracking
        defaults = [
            {
                "title": "Warning Block (Callout)",
                "tags": ["callout", "warning", "block"],
                "content": "<div class='warning'>\n**Warning!**\n\nTake note of this important information.\n</div>"
            },
            {
                "title": "Info Block (Callout)",
                "tags": ["callout", "info", "block"],
                "content": "<div class='info'>\n**Tip:**\n\nHere is a helpful tip or contextual note.\n</div>"
            },
            {
                "title": "2-Column Layout (Flex)",
                "tags": ["layout", "columns", "flex"],
                "content": "<div style='display: flex; gap: 20px;'>\n<div style='flex: 1;'>\n\n### Left Column\nContent goes here.\n\n</div>\n<div style='flex: 1;'>\n\n### Right Column\nContent goes here.\n\n</div>\n</div>"
            },
            {
                "title": "Standard Basic Table",
                "tags": ["table", "markdown"],
                "content": "| ID | Name | Role |\n|:---|:---|:---|\n| 1 | Alice | Admin |\n| 2 | Bob | Editor |"
            },
            {
                "title": "Image with Caption",
                "tags": ["image", "caption", "layout"],
                "content": "<div style='text-align: center; margin: 20px 0;'>\n<img src='https://via.placeholder.com/600x300' style='max-width: 100%; border-radius: 8px;'>\n<p style='color: #666; font-size: 0.9em; margin-top: 8px;'><b>図1:</b> 画像の説明文をここに記載します</p>\n</div>"
            },
            {
                "title": "Code with Filename",
                "tags": ["code", "development"],
                "content": "<div style='background: #333; color: #eee; padding: 5px 15px; border-radius: 4px 4px 0 0; font-family: monospace; font-size: 0.8em;'>main.py</div>\n\n```python\ndef hello_world():\n    print(\"Hello from ChainFlow!\")\n```"
            },
            {
                "title": "Critical Alert (Danger)",
                "tags": ["alert", "danger", "warning"],
                "content": "<div style='background-color: #fff0f0; border: 1px solid #ff4d4f; border-left: 5px solid #ff4d4f; padding: 15px; color: #a8071a;'>\n\n**重要:** この操作は取り消せません。実行前に必ずバックアップを確認してください。\n\n</div>"
            },
            {
                "title": "Quote with Author",
                "tags": ["quote", "typography"],
                "content": "<blockquote style='font-style: italic; border-left: 4px solid #0E639C; padding: 10px 20px; background: #f9f9f9;'>\n\"創造性は、知識を無駄にしないための最良の方法だ。\"\n<p style='text-align: right; font-style: normal; color: #555;'>— 著名なクリエイター</p>\n</blockquote>"
            },
            {
                "title": "Gradient Divider",
                "tags": ["divider", "style"],
                "content": "<hr style='border: 0; height: 1px; background-image: linear-gradient(to right, rgba(0,0,0,0), #0E639C, rgba(0,0,0,0)); margin: 30px 0;'>"
            },
            {
                "title": "Simple Progress Bar",
                "tags": ["ui", "progress"],
                "content": "### 進捗状況: 75%\n<div style='width: 100%; background: #eee; border-radius: 10px; height: 12px;'>\n<div style='width: 75%; background: #0E639C; border-radius: 10px; height: 100%;'></div>\n</div>"
            }
        ]

        
        print("Seeding default snippets...")
        import uuid
        for d in defaults:
            thumb_filename = f"default_{uuid.uuid4().hex[:8]}.png"
            self.snippet_manager.add_snippet(d["title"], d["tags"], d["content"], thumb_filename)
            self.thumbnail_generator.generate_thumbnail(d["content"], thumb_filename)


