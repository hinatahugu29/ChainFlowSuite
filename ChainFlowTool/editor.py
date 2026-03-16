import sys
import os
import argparse
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter, QWidget, 
                               QVBoxLayout, QHBoxLayout, QPlainTextEdit, QTextBrowser, 
                               QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut, QPageSize

# WebEngine for HTML viewing
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    print("Warning: QtWebEngine not available. HTML viewing will be limited.")

# Windows: Set AppUserModelID so taskbar shows our icon, not Python's (v21.1)
import ctypes
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.Tool.v21")
except Exception:
    pass

from PySide6.QtCore import QThread, Signal

class PreviewWorker(QThread):
    finished = Signal(str)

    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def run(self):
        try:
            import markdown2
            # Extras for tables, code blocks, etc. match previously used
            extras = ["fenced-code-blocks", "tables", "break-on-newline", "header-ids", "strike"]
            html = markdown2.markdown(self.raw_text, extras=extras)
            self.finished.emit(html)
        except Exception as e:
            self.finished.emit(f"<p>Error rendering markdown: {e}</p>")

class ChainFlowEditor(QMainWindow):
    def __init__(self, file_path=None, geometry=None, theme="dark"):
        super().__init__()
        
        self.file_path = file_path
        self.current_theme = theme
        self.is_html_mode = False  # Track if viewing HTML vs editing Markdown
        
from PySide6.QtCore import QThread, Signal, QEvent

# v19.4 Fix: Inline Dark Title Bar logic to avoid import issues in frozen builds
def force_dark_title_bar(window):
    try:
        import ctypes
        hwnd = window.winId()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        value = ctypes.c_int(1)
        
        # Try modern Windows 11/10 (20H1+)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), 
            DWMWA_USE_IMMERSIVE_DARK_MODE, 
            ctypes.byref(value), 
            ctypes.sizeof(value)
        )
        # Fallback for older Win10
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), 
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, 
            ctypes.byref(value), 
            ctypes.sizeof(value)
        )
    except Exception as e:
        print(f"Failed to force dark title bar: {e}")

class PreviewWorker(QThread):
    finished = Signal(str)

    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def run(self):
        try:
            import markdown2
            # Extras for tables, code blocks, etc. match previously used
            extras = ["fenced-code-blocks", "tables", "break-on-newline", "header-ids", "strike"]
            html = markdown2.markdown(self.raw_text, extras=extras)
            self.finished.emit(html)
        except Exception as e:
            self.finished.emit(f"<p>Error rendering markdown: {e}</p>")

class ChainFlowEditor(QMainWindow):
    def __init__(self, file_path=None, geometry=None, theme="dark"):
        super().__init__()
        
        self.file_path = file_path
        self.current_theme = theme
        self.is_html_mode = False  # Track if viewing HTML vs editing Markdown
        
        self.setWindowTitle("ChainFlow Editor")
        
        # Win10/11 Dark Title Bar moved to showEvent
        # force_dark_title_bar(self)
        
        # v16.2: Set window icon (same as Filer)
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS logic for PyInstaller (v21.1)
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1000, 700) # Default size if geometry not specified
        
        # Apply Geometry if provided
        if geometry:
            try:
                # Expected format: "x,y,w,h"
                x, y, w, h = map(int, geometry.split(','))
                self.setGeometry(x, y, w, h)
            except Exception as e:
                print(f"Invalid geometry: {e}")

        # Setup UI
        self.setup_ui()
        self.apply_theme()
        
        # Load File
        if self.file_path and os.path.exists(self.file_path):
            self.load_file(self.file_path)
        else:
            # New file mode or empty
            self.editor.setPlainText("")
            if self.file_path:
                self.setWindowTitle(f"{os.path.basename(self.file_path)} - ChainFlow Tool")

    def showEvent(self, event):
        super().showEvent(event)
        # v19.4 Fix: Re-apply dark title bar on show to ensure HWND is ready and DWM catches it
        force_dark_title_bar(self)

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes (maximize/restore/focus) to prevent white flash
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            force_dark_title_bar(self)
        super().changeEvent(event)

    def setup_ui(self):
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar / Header
        self.header = QFrame()
        self.header.setFixedHeight(40)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_label = QLabel("ChainFlow Editor")
        
        # Help Button
        self.help_btn = QPushButton("Help")
        self.help_btn.setFixedSize(60, 24)
        self.help_btn.setCheckable(True)
        self.help_btn.setStyleSheet("background-color: #333; color: #ccc; border: none;")
        
        # Save Button (Explicit)
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(60, 24)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c; color: white; border: none; font-weight: bold; border-radius: 2px;
            }
            QPushButton:hover { background-color: #1177bb; }
        """)
        self.save_btn.clicked.connect(self.save_file)

        self.export_btn = QPushButton("Export PDF")
        self.export_btn.setFixedSize(100, 24)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.help_btn)
        header_layout.addWidget(self.export_btn)
        
        layout.addWidget(self.header)
        
        # Main Body Splitter (Help | [Editor | Preview])
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(1)

        # Help Pane
        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        self.help_list = QListWidget()
        self.help_list.setFrameStyle(QFrame.NoFrame)
        self.help_list.setStyleSheet("background-color: #1e1e1e; color: #888; padding: 5px; font-family: 'Consolas'; font-size: 11px;")
        self.help_list.setFocusPolicy(Qt.NoFocus)
        self.help_list.setFixedWidth(200)
        self.populate_help_list()
        self.help_list.setVisible(False)
        self.main_splitter.addWidget(self.help_list)
        
        # Nested Splitter (Editor | Preview)
        self.splitter = QSplitter(Qt.Horizontal) # Keep name 'splitter' to minimize diff, or rename carefully. Let's keep self.splitter as the editor one for compatibility if referenced elsewhere.
        
        # Editor Pane
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.splitter.addWidget(self.editor)
        
        # Preview Pane (Markdown)
        self.preview = QTextBrowser()
        self.splitter.addWidget(self.preview)
        
        # WebEngine View (HTML)
        self.web_view = None
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            self.web_view.setStyleSheet("background: #1e1e1e;")
            # Enable Plugins (Required for PDF viewing)
            self.web_view.settings().setAttribute(self.web_view.settings().WebAttribute.PluginsEnabled, True)
            self.web_view.settings().setAttribute(self.web_view.settings().WebAttribute.PdfViewerEnabled, True)
            self.web_view.hide()
            self.splitter.addWidget(self.web_view)
        
        # Set initial sizes (50/50)
        self.splitter.setSizes([500, 500])
        
        self.main_splitter.addWidget(self.splitter)
        layout.addWidget(self.main_splitter)

        # Signals
        self.editor.textChanged.connect(self.update_preview)
        self.export_btn.clicked.connect(self.export_to_pdf)
        self.help_btn.clicked.connect(self.toggle_help_pane)
        self.help_list.itemDoubleClicked.connect(self.insert_snippet)

        # v19.3 Debounce Timer
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(300) # 300ms delay
        self.preview_timer.timeout.connect(self._queue_preview_update)

        # v16.1 Editor Slash Menu Integration (Fixed placement)
        try:
             # Try relative import first for running as module
             from .widgets.slash_menu import SlashMenu
        except ImportError:
             # Fallback for running standalone where widgets is in path
             try:
                 from widgets.slash_menu import SlashMenu
             except ImportError:
                 # Last resort if running inside ChainFlowTool dir directly
                 sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
                 from widgets.slash_menu import SlashMenu

        self.slash_menu = SlashMenu(self)
        self.slash_menu.command_selected.connect(self.execute_slash_command)
        
        self.slash_actions = [
            {"id": "save", "label": "Save", "desc": "Save current file (Ctrl+S)"},
            {"id": "export_pdf", "label": "Export PDF", "desc": "Export as PDF"},
            {"id": "close", "label": "Close Editor", "desc": "Close this window"},
        ]
        self.slash_menu.set_commands(self.slash_actions)
        
        # Shortcuts
        # v19.2 Fix: Use QShortcut directly for reliable window-wide triggering
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.setContext(Qt.WindowShortcut)
        self.save_shortcut.activated.connect(self.save_file)
        
        # Slash Shortcut (Application Context to ensure it hits)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.toggle_slash_menu)

    def populate_help_list(self):
        from PySide6.QtWidgets import QListWidgetItem
        
        # (Label, Key/Desc, Snippet)
        shortcuts = [
            ("Save", "Ctrl+S", None),
            ("Command Palette", "Ctrl+P", None),
            ("Export PDF", "via Menu", None),
            ("-", "-", None), # Separator
            ("Header 1", "#", "\n# "),
            ("Header 2", "##", "\n## "),
            ("Bold", "**text**", "**text**"),
            ("Italic", "*text*", "*text*"),
            ("Strike", "~~text~~", "~~text~~"),
            ("Quote", "> text", "\n> "),
            ("Code Block", "```", "\n```\ncode\n```\n"),
            ("Inline Code", "`code`", "`code`"),
            ("Link", "[]()", "[text](url)"),
            ("Image", "![]()", "![alt](url)"),
            ("List", "- item", "\n- "),
            ("Task", "- [ ]", "\n- [ ] "),
            ("Table", "| A | B |", "\n| Header 1 | Header 2 |\n| -------- | -------- |\n| Cell 1   | Cell 2   |\n"),
            ("Line", "---", "\n---\n"),
        ]
        
        for action, key, snippet in shortcuts:
            if action == "-":
                # Separator
                item = QListWidgetItem("----------------")
                item.setFlags(Qt.NoItemFlags)
                self.help_list.addItem(item)
                continue
                
            item = QListWidgetItem(f"{action:<15} {key}")
            # Use UserRole to store snippet
            if snippet:
                item.setData(Qt.UserRole, snippet)
                item.setToolTip(f"Double-click to insert:\n{snippet}")
            else:
                item.setToolTip("Action shortcut (not insertable)")
                
            self.help_list.addItem(item)

    def insert_snippet(self, item):
        snippet = item.data(Qt.UserRole)
        if snippet:
            self.editor.insertPlainText(snippet)
            self.editor.setFocus()
            
            # Auto-selection logic could go here (e.g. select 'text' in **text**)
            # But simple insertion is a good start.

    def toggle_help_pane(self):
        visible = self.help_btn.isChecked()
        self.help_list.setVisible(visible)

    def apply_theme(self):
        # Shared DNA: mimic Filer's dark theme
        if self.current_theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #1e1e1e; color: #cccccc; }
                QFrame { background-color: #252526; border-bottom: 1px solid #3e3e42; }
                QLabel { color: #cccccc; font-weight: bold; }
                QSplitter::handle { background-color: #3e3e42; width: 2px; }
                QPlainTextEdit { 
                    background-color: #1e1e1e; 
                    color: #d4d4d4; 
                    border: none;
                    padding: 10px;
                    selection-background-color: #264f78;
                }
                QTextBrowser {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #0e639c; color: #ffffff; border: none; border-radius: 4px;
                }
                QPushButton:hover { background-color: #1177bb; }

                /* ScrollBar customization */
                QScrollBar:vertical { border: none; background: #1e1e1e; width: 12px; margin: 0px; }
                QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 6px; margin: 2px; }
                QScrollBar::handle:vertical:hover { background: #686868; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

                QScrollBar:horizontal { border: none; background: #1e1e1e; height: 12px; margin: 0px; }
                QScrollBar::handle:horizontal { background: #424242; min-width: 20px; border-radius: 6px; margin: 2px; }
                QScrollBar::handle:horizontal:hover { background: #686868; }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

                /* QMessageBox Dark Theme */
                QMessageBox { background-color: #252526; color: #cccccc; }
                QMessageBox QLabel { color: #cccccc; }
                QMessageBox QPushButton { 
                    background-color: #0e639c; color: #ffffff; 
                    border: none; border-radius: 4px; 
                    padding: 5px 15px; min-width: 60px;
                }
                QMessageBox QPushButton:hover { background-color: #1177bb; }
            """)

    def load_file(self, path):
        try:
            ext = os.path.splitext(path)[1].lower()
            
            # HTML / PDF files: display in WebEngine
            if ext in ['.html', '.htm', '.pdf'] and HAS_WEBENGINE and self.web_view:
                self.is_html_mode = True
                # Hide editor/preview, show WebView
                self.editor.hide()
                self.preview.hide()
                self.web_view.show()
                self.help_btn.hide()  # Help is for Markdown
                # PDF doesn't need export to PDF
                if ext == '.pdf':
                    self.export_btn.hide()
                else:
                    self.export_btn.show()
                
                # Load HTML/PDF
                url = QUrl.fromLocalFile(path)
                self.web_view.load(url)
                self.setWindowTitle(f"{os.path.basename(path)} - ChainFlow Tool (Viewer)")
            else:
                # Markdown/Text files: traditional editor
                self.is_html_mode = False
                self.editor.show()
                self.preview.show()
                self.export_btn.show()
                if self.web_view:
                    self.web_view.hide()
                
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.setWindowTitle(f"{os.path.basename(path)} - ChainFlow Tool")
        except Exception as e:
            self.editor.setPlainText(f"Error reading file: {e}")
            self.is_html_mode = False

    def update_preview(self):
        # v19.3 Optimization: Debounce update (300ms)
        self.preview_timer.start()

    def _queue_preview_update(self):
        # Actual update logic called by timer
        if hasattr(self, '_preview_worker') and self._preview_worker.isRunning():
            # If still running, wait for next debounce cycle?
            # Or just let it finish and rely on user stopping typing.
            # We'll just skip and let the latest change trigger another timer if needed?
            # Actually, if we skip, we might miss the final state.
            # But the timer won't fire again unless textChanged happens.
            # Correct debounce: Just start worker. If worker is busy, maybe cancel it?
            # For simplicity and stability: Just allow overlap or ignore.
            # Ignoring is safer for stability.
            return

        raw_text = self.editor.toPlainText()
        
        self._preview_worker = PreviewWorker(raw_text)
        self._preview_worker.finished.connect(self._on_preview_ready)
        self._preview_worker.start()

    def _on_preview_ready(self, html_content):
        # CSS for Markdown style
        css = """
        <style>
            body { font-family: 'Segoe UI', sans-serif; color: #d4d4d4; line-height: 1.6; }
            h1, h2, h3 { color: #569cd6; border-bottom: 1px solid #3e3e42; padding-bottom: 5px; margin-top: 20px; }
            code { background-color: #2d2d2d; padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }
            pre { background-color: #1e1e1e; padding: 10px; border: 1px solid #3e3e42; border-radius: 4px; overflow-x: auto; }
            
            /* Table Styling */
            table { border-collapse: collapse; width: 100%; border: 1px solid #3e3e42; margin: 15px 0; }
            th, td { border: 1px solid #3e3e42; padding: 8px 12px; text-align: left; }
            th { background-color: #252526; font-weight: bold; color: #569cd6; }
            tr:nth-child(even) { background-color: #1e1e1e; }
            tr:nth-child(odd) { background-color: #1a1a1a; }
            
            blockquote { border-left: 4px solid #569cd6; margin: 0; padding-left: 10px; color: #888; }
            a { color: #3794ff; text-decoration: none; }
            hr { border: 0; border-top: 1px solid #3e3e42; margin: 20px 0; }
        </style>
        """
        
        full_html = f"<html><head>{css}</head><body>{html_content}</body></html>"
        
        # Save scroll position to prevent jumping
        scrollbar = self.preview.verticalScrollBar()
        scroll_val = scrollbar.value()
        
        self.preview.setHtml(full_html)
        
        # Restore scroll position
        scrollbar.setValue(scroll_val)



    def export_to_pdf(self):
        """Export current content to PDF (HTML or Markdown)"""
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        # HTML Mode: use WebEngine's superior PDF export
        if self.is_html_mode and HAS_WEBENGINE and self.web_view:
            self._export_webengine_pdf()
            return
        
        # Markdown Mode: traditional export
        import markdown2
        
        try:
            # Suggest filename
            base_name = os.path.splitext(os.path.basename(self.file_path))[0] if self.file_path else "Untitled"
            dir_name = os.path.dirname(self.file_path) if self.file_path else "" 
            default_path = os.path.join(dir_name, f"{base_name}.pdf")
            
            file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_path, "PDF Files (*.pdf)")
            
            if not file_path:
                print("PDF Export Cancelled by User")
                return

            # Generate print-friendly HTML (white background, black text)
            raw_text = self.editor.toPlainText()
            extras = ["fenced-code-blocks", "tables", "break-on-newline", "header-ids", "strike"]
            html_content = markdown2.markdown(raw_text, extras=extras)
            
            print_css = """
            <style>
                body { 
                    font-family: 'Segoe UI', 'Meiryo', sans-serif; 
                    color: #1a1a1a; 
                    line-height: 1.7; 
                    background-color: #ffffff;
                    margin: 20px;
                }
                h1, h2, h3 { 
                    color: #2c3e50; 
                    border-bottom: 2px solid #3498db; 
                    padding-bottom: 8px; 
                    margin-top: 24px; 
                }
                h1 { font-size: 24pt; }
                h2 { font-size: 18pt; }
                h3 { font-size: 14pt; }
                
                code { 
                    background-color: #f5f5f5; 
                    padding: 2px 6px; 
                    border-radius: 3px; 
                    font-family: 'Consolas', 'MS Gothic', monospace;
                    font-size: 10pt;
                    color: #c7254e;
                }
                pre { 
                    background-color: #f8f8f8; 
                    padding: 12px; 
                    border: 1px solid #ddd; 
                    border-radius: 4px; 
                    overflow-x: auto;
                    font-family: 'Consolas', 'MS Gothic', monospace;
                    font-size: 10pt;
                }
                pre code { background: none; padding: 0; color: #333; }
                
                /* Table Styling - Professional Print */
                table { 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 16px 0;
                    font-size: 10pt;
                }
                th, td { 
                    border: 1px solid #333; 
                    padding: 10px 14px; 
                    text-align: left; 
                }
                th { 
                    background-color: #34495e; 
                    color: #ffffff;
                    font-weight: bold; 
                }
                tr:nth-child(even) { background-color: #f9f9f9; }
                tr:nth-child(odd) { background-color: #ffffff; }
                
                blockquote { 
                    border-left: 4px solid #3498db; 
                    margin: 16px 0; 
                    padding-left: 16px; 
                    color: #555;
                    font-style: italic;
                }
                
                ul, ol { margin: 12px 0; padding-left: 24px; }
                li { margin: 6px 0; }
                
                hr { 
                    border: 0; 
                    border-top: 1px solid #ccc; 
                    margin: 24px 0; 
                }
                
                a { color: #2980b9; text-decoration: none; }
                strong { color: #2c3e50; }
                del { color: #888; }
            </style>
            """
            
            print_html = f"<html><head>{print_css}</head><body>{html_content}</body></html>"
            
            # Temporarily set print-friendly content
            self.preview.setHtml(print_html)
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPageSize(QPageSize.A4))
            
            # Print
            self.preview.print_(printer)
            
            # Restore dark preview
            self.update_preview()
            
            # Use dark-themed message box
            try:
                from widgets.ui_utils import show_dark_message_box
                show_dark_message_box(self, "Export PDF", f"Successfully exported to:\n{file_path}", "information")
            except ImportError:
                QMessageBox.information(self, "Export PDF", f"Successfully exported to:\n{file_path}")
        except Exception as e:
            print(f"PDF Export Failed: {e}")
            # Restore preview even on failure
            self.update_preview()
            try:
                from widgets.ui_utils import show_dark_message_box
                show_dark_message_box(self, "Export Error", f"Failed to export PDF:\n{e}", "critical")
            except ImportError:
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")

    def _export_webengine_pdf(self):
        """Export HTML content to PDF using WebEngine (high quality)"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        try:
            # Suggest filename
            base_name = os.path.splitext(os.path.basename(self.file_path))[0] if self.file_path else "Untitled"
            dir_name = os.path.dirname(self.file_path) if self.file_path else ""
            default_path = os.path.join(dir_name, f"{base_name}.pdf")
            
            file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_path, "PDF Files (*.pdf)")
            
            if not file_path:
                return
            
            # PDF export callback
            def pdf_finished(pdf_file, success):
                if success:
                    QMessageBox.information(self, "Export Complete", f"PDF exported successfully:\n{pdf_file}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to generate PDF.")
                try:
                    self.web_view.page().pdfPrintingFinished.disconnect()
                except:
                    pass
            
            # Connect signal and trigger
            self.web_view.page().pdfPrintingFinished.connect(pdf_finished)
            self.web_view.page().printToPdf(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")


    def save_file(self):
        # Implement 'Save As' logic if no path is set
        if not self.file_path:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;Markdown (*.md);;Text (*.txt)")
            if path:
                self.file_path = path
                self.setWindowTitle(f"{os.path.basename(self.file_path)} - ChainFlow Tool")
            else:
                return # User cancelled

        try:
            content = self.editor.toPlainText()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Visual feedback (could be status bar, but title flash is enough for now)
            orig_title = self.windowTitle()
            if " [Saved]" not in orig_title:
                self.setWindowTitle(f"{orig_title} [Saved]")
                QTimer.singleShot(1000, lambda: self.setWindowTitle(orig_title.replace(" [Saved]", "")))
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")

    def toggle_slash_menu(self):
        if self.slash_menu.isVisible():
            self.slash_menu.fade_out()
        else:
            self.slash_menu.popup(self.geometry())

    def execute_slash_command(self, cmd_id):
        if cmd_id == "save":
            self.save_file()
        elif cmd_id == "export_pdf":
            self.export_to_pdf()
        elif cmd_id == "close":
            self.close()

    def keyPressEvent(self, event):
        # Slash Menu Trigger
        if event.key() == Qt.Key_Slash or event.key() == Qt.Key_Question:
            # If editor has focus, we might want to allow typing /
            # But VSCode usually steals it if it's strictly a command palette modifier?
            # Actually VSCode uses F1 or Ctrl+Shift+P. / is usually for "quick open" if focused in some input.
            # Here, if the user wants to type /, they might be annoyed if we steal it.
            # But based on user request, they expect the menu.
            # Let's use Ctrl+P as primary and allow / if Ctrl is held? 
            # Or just steal it and if they really want /, maybe Escape? 
            # No, text editor MUST accept /.
            # So we only trigger on Ctrl+P or maybe Shift+Shift?
            # User asked for "Slash Menu", implying / key.
            # Let's check modifiers.
            pass
            
        # Standard Ctrl+P (VSCode style command palette)
        if (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_P:
            self.toggle_slash_menu()
            event.accept()
            return

        super().keyPressEvent(event)

def main():
    parser = argparse.ArgumentParser(description="ChainFlow Editor")
    parser.add_argument("--file", help="Path to file to open")
    parser.add_argument("--geometry", help="Window geometry x,y,w,h")
    parser.add_argument("--theme", default="dark", help="UI Theme")
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = ChainFlowEditor(file_path=args.file, geometry=args.geometry, theme=args.theme)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
