
import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView,
                               QApplication, QStyle, QMenu, QPushButton, QFileDialog, QTabWidget, QProgressBar)
from PySide6.QtCore import Qt, QTimer, Slot, QSize, Signal, QEvent, QMimeData, QUrl
from PySide6.QtGui import QIcon, QFont, QAction, QDrag, QKeySequence
import ctypes
import unicodedata

try:
    from .history_manager import HistoryManager
except ImportError:
    from history_manager import HistoryManager

try:
    from .search_engine import SearchWorker, CountWorker
except ImportError:
    from search_engine import SearchWorker, CountWorker

def apply_dark_title_bar(window):
    """
    Applies Windows dark title bar using ctypes.
    """
    try:
        hwnd = window.winId()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_int(DWMWA_USE_IMMERSIVE_DARK_MODE),
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except Exception as e:
        print(f"Failed to apply dark title bar: {e}")

class DraggableTreeWidget(QTreeWidget):
    """
    QTreeWidget with drag support to external applications (Explorer, etc).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        # self.setAcceptDrops(True) # If we wanted to accept drops too
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

    def startDrag(self, supportedActions):
        items = self.selectedItems()
        if not items:
            return

        urls = []
        for item in items:
            # Retrieve full path stored in data(0, UserRole)
            path = item.data(0, Qt.UserRole)
            if path and os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))
        
        if not urls:
            return

        mime_data = QMimeData()
        mime_data.setUrls(urls)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Execute drag operation
        drag.exec(Qt.CopyAction)

class SearchWidget(QWidget):
    """
    Independent widget for a single search session.
    """
    def __init__(self, start_dir=None, history_manager=None, parent=None):
        super().__init__(parent)
        self.home_dir = os.path.expanduser("~") # v21.11 Fallback
        self.start_dir = start_dir or self.home_dir
        self.history_manager = history_manager
        self.worker = None

        self.init_ui()
        self.setup_logic()
        
        # v21.4: Track last search query to prevent redundant searches
        self.last_query = None

        # Initial Status
        # If we have a status bar callback or signal, we can use it.
        # But here self.status_label is local to this widget? 
        # Actually standard tabbed apps have one global status bar.
        # For simplicity, let's put a status label in the bottom of this widget.
        self.status_label.setText(f"Root: {self.start_dir}")

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 1. Top Area (Button + Search Bar)
        from PySide6.QtWidgets import QToolButton
        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout)
        
        self.dir_button = QToolButton()
        self.dir_button.setText("Dir")
        self.dir_button.setToolTip(f"Change Search Directory\nCurrent: {self.start_dir}")
        self.dir_button.setFixedWidth(60)
        self.dir_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.dir_button.setStyleSheet("""
            QToolButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #555;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover { background-color: #4c4c4c; }
            QToolButton:pressed { background-color: #2c2c2c; }
            QToolButton::menu-indicator { image: none; } /* Hide default arrow to use custom look */
        """)
        self.dir_button.clicked.connect(self.select_directory)
        
        # History Menu
        self.history_menu = QMenu(self)
        self.history_menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        self.history_menu.aboutToShow.connect(self.populate_history_menu)
        self.dir_button.setMenu(self.history_menu)
        
        self.top_layout.addWidget(self.dir_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search... (Space=AND, |=OR, -exclude, *.py=Wildcard)")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.top_layout.addWidget(self.search_input)
        
        # 2. Result List
        self.result_tree = DraggableTreeWidget()
        self.result_tree.setHeaderLabels(["Name", "Path", "Size", "Date"])
        
        # v21.1 Usability: Allow resizing and set better defaults
        header = self.result_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        
        self.result_tree.setColumnWidth(0, 250) # Name
        self.result_tree.setColumnWidth(1, 400) # Path
        self.result_tree.setColumnWidth(2, 80)  # Size
        self.result_tree.setColumnWidth(3, 120) # Date

        # Enable sorting
        self.result_tree.setSortingEnabled(True)
        self.result_tree.sortByColumn(0, Qt.AscendingOrder)  # Default sort by Name
        self.result_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.result_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.result_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # v21.1 Usability: Enter key to open file
        # We handle this event specifically for the tree widget context
        self.result_tree.installEventFilter(self)
        
        self.layout.addWidget(self.result_tree)
        
        # 3. Progress Bar (Indeterminate by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #2d2d2d; }
            QProgressBar::chunk { background-color: #007acc; }
        """)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # 4. Local Status Label (optional, or use main window's)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        self.layout.addWidget(self.status_label)

    def setup_logic(self):
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)
        self.debounce_timer.timeout.connect(self.start_search)
        
        # v21.1 Usability: Auto-focus search box on startup/tab switch
        QTimer.singleShot(0, self.search_input.setFocus)

    def eventFilter(self, source, event):
        if source == self.result_tree and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Open currently selected item
                item = self.result_tree.currentItem()
                if item:
                    self.on_item_double_clicked(item, 0)
                return True
            
            # v21.4 Usability: Ctrl+C to copy files
            if event.matches(QKeySequence.Copy):
                self.copy_selected_files()
                return True
                
        return super().eventFilter(source, event)

    def on_search_text_changed(self):
        query = self.search_input.text().strip()
        if not query:
            self.result_tree.clear()
            self.status_label.setText("Ready")
            return
        self.debounce_timer.start()

    def start_search(self):
        query = self.search_input.text().strip()
        if not query: return
        
        # v21.4 Usability: Prevent re-search if query effectively hasn't changed (e.g. trailing space)
        if hasattr(self, 'last_query') and self.last_query == query:
            return

        # Initialize cache variables and generation ID if not present
        if not hasattr(self, 'master_results'):
            self.master_results = []
            self.master_query = ""
            self.is_master_search_complete = False
            
        # v21.6 Stability: Generation ID to prevent race conditions (signal ghosts)
        if not hasattr(self, 'current_search_id'):
            self.current_search_id = 0

        # v21.8 Hybrid Search: Live Filtering
        # If we are already searching (worker running) or finished searching,
        # and the new query is a refinement of the *base* search we started,
        # then just update the view filter instead of restarting.
        
        # We need to know what the "base query" was for the current worker.
        # Let's assume master_query represents the query used to start the worker.
        
        if not hasattr(self, 'current_search_id'):
            self.current_search_id = 0

        is_hybrid_filter = False

        # v21.10 Fix: Case-insensitive check for hybrid filtering
        # To avoid restarting if user changes case (e.g. "Log" -> "log error")
        # AND Handle full-width/half-width insensitivity
        try:
            master_norm = unicodedata.normalize('NFKC', self.master_query).lower() if self.master_query else ""
            query_norm = unicodedata.normalize('NFKC', query).lower()
        except Exception as e:
            # Fallback if unicodedata fails (e.g. import error?)
            print(f"Normalization error: {e}")
            master_norm = self.master_query.lower() if self.master_query else ""
            query_norm = query.lower()
        
        # Scenario A: Search Finished (Existing Logic) -> Refine results from cache
        if self.is_master_search_complete and master_norm:
             if query_norm.startswith(master_norm):
                 is_hybrid_filter = True
                 
        # Scenario B: Search Running (New Hybrid Logic) -> Refine stream
        elif self.worker and self.worker.isRunning() and master_norm:
            # If user types "log" -> "logg" -> "logge", we don't want to restart.
            # We only restart if they delete characters beyond the base query or change it entirely.
            if query_norm.startswith(master_norm):
                 is_hybrid_filter = True

        # **v21.4 Enhancement: Return to base query**
        if query_norm == master_norm:
            is_hybrid_filter = True

        if is_hybrid_filter:
            # --- Hybrid Filter Mode ---
            if hasattr(self, 'estimated_total') and self.estimated_total > 0:
                self.status_label.setText(f"Filtering '{query}' ... ({len(self.master_results)} / ~{self.estimated_total} items scanned)")
            else:
                self.status_label.setText(f"Filtering '{query}' ({len(self.master_results)} scanned)...")
            
            self.last_query = query
            
            # Re-draw tree with new filter from ALL results computed so far
            self.update_results_view(query)
            return

        # --- Full Search Restart ---
        
        # v21.6 Stability: Disconnect old worker signals to prevent contamination
        if self.worker:
            try:
                self.worker.results_found.disconnect()
                self.worker.progress_update.disconnect()
                self.worker.finished.disconnect()
            except Exception:
                pass # Already disconnected or not connected
            
            if self.worker.isRunning():
                self.worker.stop()
                self.worker.wait()
        
        # Increment generation ID for the new search
        self.current_search_id += 1
        current_id = self.current_search_id
        
        # Reset Master Cache for new base search
        self.master_results = []
        self.master_query = query
        self.is_master_search_complete = False
        
        self.last_query = query
        self.result_tree.clear()
        self.status_label.setText(f"Searching for '{query}' in {self.start_dir} ...")
        self.progress_bar.setRange(0, 0) # Start indeterminate
        self.progress_bar.show()
        
        self.worker = SearchWorker(self.start_dir, query)
        # Pass current_id via lambda or partial to bind it to the slot
        # Using lambda to capture current_id
        self.worker.results_found.connect(lambda results: self.add_results_batch(results, current_id))
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.start()
        
        # v21.11 History Tracking
        if self.history_manager:
            self.history_manager.add_visit(self.start_dir)

        # v21.9 Progress Visualization: Start separate counting thread
        if hasattr(self, 'count_worker') and self.count_worker:
            if self.count_worker.isRunning():
                self.count_worker.stop()
                self.count_worker.wait()
        
        self.estimated_total = 0
        self.count_worker = CountWorker(self.start_dir)
        self.count_worker.count_updated.connect(self.on_count_updated)
        self.count_worker.finished_counting.connect(self.on_count_finished)
        self.count_worker.start()
        
    def on_count_updated(self, count):
        """Update the estimated total items."""
        self.estimated_total = count
        if self.estimated_total > 0:
            # Switch to determinate progress if we have a count
            self.progress_bar.setRange(0, self.estimated_total)
            
    def on_count_finished(self, count):
        """Final count obtained."""
        self.estimated_total = count
        self.progress_bar.setRange(0, self.estimated_total)

    def update_progress(self, count):
        """Update status with scanned count."""
        # Update progress bar value
        self.progress_bar.setValue(count)
        
        # Update text
        if self.estimated_total > 0:
            # Show "123 / ~5000"
            self.status_label.setText(f"Searching for '{self.master_query}' ... ({count} / ~{self.estimated_total} items scanned)")
        else:
            # Fallback to just count
            self.status_label.setText(f"Searching for '{self.master_query}' ... ({count} items scanned)")

    def add_results_batch(self, results, search_id):
        """
        v21.3 Optimization: Handle batch of results.
        results: list of (name, full_path, size, mtime)
        v21.6 Stability: Check search_id to drop old results.
        v21.8 Hybrid Search: Store in master, then filter for view.
        """
        # Generation Check: Drop if this result belongs to an old search
        if search_id != self.current_search_id:
            return

        # Always add to master cache
        if hasattr(self, 'master_results'):
            self.master_results.extend(results)
            
        # Add to view ONLY if it matches CURRENT query (Hybrid Filter)
        current_query = self.search_input.text().strip()
        parsed = SearchWorker.parse_query(current_query)
        
        items = []
        for name, full_path, size, mtime in results:
            # Check match against current UI query, NOT just the worker's query
            if SearchWorker.is_match(name, parsed):
                item = QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, full_path)
                # Size: human-readable with sorting support
                item.setText(2, self.format_size(size))
                item.setData(2, Qt.UserRole, size)  # Store raw value for sorting
                # Date: human-readable with sorting support
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                item.setText(3, date_str)
                item.setData(3, Qt.UserRole, mtime)  # Store raw value for sorting
                item.setData(0, Qt.UserRole, full_path)
                items.append(item)
            
        if items:
            self.result_tree.addTopLevelItems(items)

    def update_results_view(self, query):
        """
        v21.8 Hybrid Search: Re-populates the tree from master_results based on query.
        """
        self.result_tree.clear()
        parsed = SearchWorker.parse_query(query)
        
        items = []
        # Batch creation for UI responsiveness if master_results is huge?
        # For now, simple loop.
        for res in self.master_results:
            name, full_path, size, mtime = res
            if SearchWorker.is_match(name, parsed):
                item = QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, full_path)
                item.setText(2, self.format_size(size))
                item.setData(2, Qt.UserRole, size)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                item.setText(3, date_str)
                item.setData(3, Qt.UserRole, mtime)
                item.setData(0, Qt.UserRole, full_path)
                items.append(item)
        
        if items:
            self.result_tree.addTopLevelItems(items)
        
        if self.is_master_search_complete:
             if hasattr(self, 'estimated_total') and self.estimated_total > 0:
                 self.status_label.setText(f"Found {len(items)} items (Filtered). (Scanned {self.estimated_total} items)")
             else:
                 self.status_label.setText(f"Found {len(items)} items (Filtered).")
        else:
             # Still searching
             if hasattr(self, 'estimated_total') and self.estimated_total > 0:
                 self.status_label.setText(f"Filtering '{query}' ... ({len(self.master_results)} / ~{self.estimated_total} items scanned)")
             else:
                 self.status_label.setText(f"Filtering '{query}' ... ({len(self.master_results)} scanned)")

    def format_size(self, size_bytes):
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.0f} {unit}" if unit == 'B' else f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def on_search_finished(self):
        self.progress_bar.hide()
        # Mark master search as complete so we can filter next time
        self.is_master_search_complete = True
        
        # v21.9: Stop counting if still running
        if hasattr(self, 'count_worker') and self.count_worker:
            if self.count_worker.isRunning():
                self.count_worker.stop()
                self.count_worker.wait()
        
        count = self.result_tree.topLevelItemCount()
        # Show total scanned if available
        if hasattr(self, 'estimated_total') and self.estimated_total > 0:
             self.status_label.setText(f"Found {count} items. (Scanned {self.estimated_total} items)")
        else:
             self.status_label.setText(f"Found {count} items.")

    def on_item_double_clicked(self, item, column):
        path = item.data(0, Qt.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)

    def show_context_menu(self, pos):
        item = self.result_tree.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        
        path = item.data(0, Qt.UserRole)
        
        open_act = QAction("Open", self)
        open_act.triggered.connect(lambda: os.startfile(path))
        menu.addAction(open_act)
        
        # v21.4 Usability: Copy File (Ctrl+C support via clipboard)
        copy_file_act = QAction("Copy File", self)
        copy_file_act.triggered.connect(self.copy_selected_files)
        menu.addAction(copy_file_act)
        
        copy_path_act = QAction("Copy Path", self)
        copy_path_act.triggered.connect(lambda: QApplication.clipboard().setText(path))
        menu.addAction(copy_path_act)

        copy_dir_act = QAction("Copy Folder Path", self)
        copy_dir_act.triggered.connect(lambda: QApplication.clipboard().setText(os.path.dirname(path)))
        
        # Add 'Open Folder' action
        open_folder_act = QAction("Open Folder", self)
        open_folder_act.triggered.connect(lambda: os.startfile(os.path.dirname(path)))
        menu.addAction(open_folder_act)
        
        menu.addAction(copy_dir_act)
        
        menu.exec(self.result_tree.mapToGlobal(pos))
        
    def copy_selected_files(self):
        """Copy selected files to clipboard so they can be pasted in Filer."""
        items = self.result_tree.selectedItems()
        if not items: return
        
        urls = []
        for item in items:
            path = item.data(0, Qt.UserRole)
            if path and os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))
        
        if urls:
            mime = QMimeData()
            mime.setUrls(urls)
            QApplication.clipboard().setMimeData(mime)
            self.status_label.setText(f"Copied {len(urls)} files to clipboard.")

    def select_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Folder", self.start_dir)
        if new_dir:
            self.start_dir = new_dir
            self.dir_button.setToolTip(f"Change Search Directory\nCurrent: {self.start_dir}")
            
            # v21.4: Reset last_query since directory changed
            if hasattr(self, 'last_query'):
                self.last_query = None
                
            self.result_tree.clear()
            self.status_label.setText(f"Ready. Root: {self.start_dir}")
            if self.search_input.text():
                self.start_search()
            
            # Request Tab Rename - Find QTabWidget in parent hierarchy
            widget = self
            tabs = None
            while widget:
                parent = widget.parent()
                if isinstance(parent, QTabWidget):
                    tabs = parent
                    break
                widget = parent
            
            if tabs:
                idx = tabs.indexOf(self)
                if idx != -1:
                    name = os.path.basename(new_dir) or new_dir
                    tabs.setTabText(idx, name)
            
            # Record in history immediately on directory selection
            if self.history_manager:
                self.history_manager.add_visit(new_dir)

    def populate_history_menu(self):
        """Dynamic population of Recent/Frequent folders."""
        self.history_menu.clear()
        if not self.history_manager: return
        
        # 1. Select New Folder (Normal Action)
        select_act = QAction("📁 Select Folder...", self)
        select_act.triggered.connect(self.select_directory)
        self.history_menu.addAction(select_act)
        self.history_menu.addSeparator()
        
        # 2. Recent Folders
        recent = self.history_manager.get_recent()
        if recent:
            self.history_menu.addSection("Recent Folders")
            for path in recent:
                name = os.path.basename(path) or path
                act = QAction(f"🕒 {name}", self)
                act.setToolTip(path)
                act.triggered.connect(lambda checked, p=path: self.set_search_directory(p))
                self.history_menu.addAction(act)
        
        # 3. Frequent Folders
        frequent = self.history_manager.get_frequent()
        if frequent:
            self.history_menu.addSection("Frequent Folders")
            for path in frequent:
                name = os.path.basename(path) or path
                act = QAction(f"⭐ {name}", self)
                act.setToolTip(path)
                act.triggered.connect(lambda checked, p=path: self.set_search_directory(p))
                self.history_menu.addAction(act)
        
        # 4. Filer Favorites
        favorites = self.history_manager.get_filer_favorites()
        if favorites:
            self.history_menu.addSection("ChainFlow Filer Favorites")
            for path in favorites:
                name = os.path.basename(path) or path
                act = QAction(f"📌 {name}", self)
                act.setToolTip(path)
                act.triggered.connect(lambda checked, p=path: self.set_search_directory(p))
                self.history_menu.addAction(act)

    def set_search_directory(self, path):
        """Force specific directory as search root."""
        if os.path.exists(path) and os.path.isdir(path):
            self.start_dir = path
            self.dir_button.setToolTip(f"Change Search Directory\nCurrent: {self.start_dir}")
            
            # Reset results and last query
            self.last_query = None
            self.result_tree.clear()
            self.status_label.setText(f"Ready. Root: {self.start_dir}")
            
            # Update Tab Name
            widget = self
            tabs = None
            while widget:
                parent = widget.parent()
                if isinstance(parent, QTabWidget):
                    tabs = parent
                    break
                widget = parent
            
            if tabs:
                idx = tabs.indexOf(self)
                if idx != -1:
                    name = os.path.basename(path) or path
                    tabs.setTabText(idx, name)
            
            # Update history
            if self.history_manager:
                self.history_manager.add_visit(path)
            
            # Start search if there's a query
            if self.search_input.text():
                self.start_search()

    def update_history_tracking(self):
        """Update history when search starts successfully."""
        if self.history_manager:
            self.history_manager.add_visit(self.start_dir)


class SearchWindow(QMainWindow):
    def __init__(self, start_dir=None):
        super().__init__()
        self.setWindowTitle("ChainFlow Search")
        
        # Initialize History Manager
        self.history_manager = HistoryManager()
        
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

        self.resize(900, 650)
        
        # Dark Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #cccccc; }
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555;
                padding: 8px;
                font-size: 14px;
                border-radius: 4px;
            }
            QLineEdit:focus { border-color: #007acc; }
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
            }
            QTreeWidget::item:hover { background-color: #2a2d2e; }
            QTreeWidget::item:selected { background-color: #094771; color: #ffffff; }
            QHeaderView::section { background-color: #333333; color: #cccccc; border: none; padding: 4px; }
            QStatusBar { background-color: #007acc; color: #ffffff; }
            QTabWidget::pane { border: 1px solid #454545; top: -1px; } 
            QTabBar::tab {
                background: #2d2d2d;
                color: #888;
                padding: 8px 12px;
                border: 1px solid #454545;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #fff;
                border-bottom-color: #1e1e1e;
            }
            QTabBar::tab:hover {
                background: #3e3e3e;
            }
            /* ScrollBar: Accent Rounded (Matching Filer) */
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
        """)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        # tabBarDoubleClicked passes index, ignore it with lambda
        self.tabs.tabBarDoubleClicked.connect(lambda idx: self.add_new_tab())
        
        # Add "+" button to corner
        new_tab_button = QPushButton("+")
        new_tab_button.setToolTip("New Search Tab (Ctrl+T)")
        new_tab_button.setFixedSize(30, 30)
        new_tab_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3e3e3e; color: #fff; border-radius: 4px; }
            QPushButton:pressed { background-color: #2c2c2c; }
        """)
        new_tab_button.clicked.connect(lambda: self.add_new_tab())
        self.tabs.setCornerWidget(new_tab_button, Qt.TopRightCorner)

        self.setCentralWidget(self.tabs)
        
        # Ctrl+T Shortcut to add new tab
        from PySide6.QtGui import QShortcut, QKeySequence
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(lambda: self.add_new_tab())
        
        # Add initial tab
        self.add_new_tab(start_dir)

    def add_new_tab(self, start_dir=None):
        if not start_dir:
            # v21.2 Usability: Inherit path from current active tab if exists
            current_widget = self.tabs.currentWidget()
            if current_widget and hasattr(current_widget, 'start_dir'):
                start_dir = current_widget.start_dir
            else:
                start_dir = self.home_dir if hasattr(self, 'home_dir') else os.getcwd()
            
        search_widget = SearchWidget(start_dir, self.history_manager)
        title = os.path.basename(start_dir) or start_dir
        if not title: title = "Root"
        
        self.tabs.addTab(search_widget, title)
        self.tabs.setCurrentWidget(search_widget)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            # Optionally close window if last tab closed?
            # For now, maybe just clear it or close app?
            # Let's close app if last tab is closed
            self.close()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes to prevent theme breakage
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            apply_dark_title_bar(self)
        super().changeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SearchWindow()
    window.show()
    sys.exit(app.exec())
