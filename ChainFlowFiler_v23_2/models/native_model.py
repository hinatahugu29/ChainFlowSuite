import os
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, Signal
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QFileIconProvider

try:
    import chainflow_core
except ImportError:
    chainflow_core = None

class ScanWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, root_path, sort_type, ascending, show_hidden):
        super().__init__()
        self.root_path = root_path
        self.sort_type = sort_type
        self.ascending = ascending
        self.show_hidden = show_hidden

    def run(self):
        try:
            if chainflow_core:
                items = chainflow_core.list_directory_native(
                    self.root_path,
                    self.sort_type,
                    self.ascending,
                    self.show_hidden
                )
                self.finished.emit(items)
            else:
                self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))

class NativeFileModel(QAbstractTableModel):
    """
    V23.1 Fully Native File Model.
    Replaces QFileSystemModel with a lightweight list-based model fed by Rust asynchronously.
    """
    
    # Static Icon Map (Shared among all panes for memory efficiency)
    _ICON_MAP = {}
    _FOLDER_ICON = None
    _DEFAULT_ICON = None
    _FILE_ICON_PROVIDER = QFileIconProvider()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_path = ""
        self.items = [] # List of (name, path, is_dir, size, mtime)
        self.sort_type = 0 # 0:Name, 1:Ext, 2:Size, 3:Date
        self.ascending = True
        self.show_hidden = False
        self.display_mode = 0 # 0:All, 1:Dirs Only, 2:Files Only
        self.search_text = ""
        self.marked_paths = set()
        
        self._worker = None # Current scan worker
        
        # Initialize global icon map if first time
        if not NativeFileModel._ICON_MAP:
            self._init_icons()

    @classmethod
    def _init_icons(cls):
        """Pre-render colored category icons into memory. Zero OS hits after this."""
        from PySide6.QtGui import QPainter, QPixmap
        
        cls._FOLDER_ICON = cls._FILE_ICON_PROVIDER.icon(QFileIconProvider.Folder)
        base_file_icon = cls._FILE_ICON_PROVIDER.icon(QFileIconProvider.File)
        
        # Helper to create a tinted version of the base icon
        def get_tinted_icon(color_name):
            pix = base_file_icon.pixmap(16, 16)
            painter = QPainter(pix)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(pix.rect(), QColor(color_name))
            painter.end()
            return QIcon(pix)

        cls._FILE_ICON = base_file_icon
        
        # Pre-assign Category Icons (Distinct colors for high visibility)
        cls._CAT_ICONS = {
            "PDF":  get_tinted_icon("#ff4444"), # Red
            "XLS":  get_tinted_icon("#2ca44e"), # Green
            "DOC":  get_tinted_icon("#007acc"), # Blue
            "TXT":  get_tinted_icon("#888888"), # Gray
            "CODE": get_tinted_icon("#ff8800"), # Orange
            "IMG":  get_tinted_icon("#a371f7"), # Purple
            "ZIP":  get_tinted_icon("#f1e05a"), # Yellow
            "EXE":  get_tinted_icon("#ff0000"), # Sharp Red
        }

        # Extensions to Category Map
        cls._EXT_TO_CAT = {
            ".pdf": "PDF",
            ".xlsx": "XLS", ".xls": "XLS", ".csv": "XLS",
            ".docx": "DOC", ".doc": "DOC",
            ".txt": "TXT", ".md": "TXT", ".log": "TXT",
            ".py": "CODE", ".js": "CODE", ".html": "CODE", ".css": "CODE", ".ahk": "CODE", ".rs": "CODE",
            ".png": "IMG", ".jpg": "IMG", ".jpeg": "IMG", ".gif": "IMG", ".bmp": "IMG", ".webp": "IMG",
            ".zip": "ZIP", ".7z": "ZIP", ".rar": "ZIP", ".tar": "ZIP", ".gz": "ZIP",
            ".exe": "EXE", ".dll": "EXE", ".msi": "EXE", ".bat": "EXE",
        }

    def _get_icon_for_file(self, name):
        """Pure memory-to-UI mapping. The fastest path possible."""
        ext = os.path.splitext(name)[1].lower()
        cat = self._EXT_TO_CAT.get(ext)
        if cat:
            return self._CAT_ICONS[cat]
        return self._FILE_ICON

    def setRootPath(self, path):
        if not path: return
        self.root_path = os.path.normpath(path)
        self.refresh()

    def refresh(self):
        """Asynchronous re-scan starting from a background thread."""
        if not self.root_path or not os.path.exists(self.root_path): return
        if not chainflow_core: return

        # Terminate previous worker if running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()

        self._worker = ScanWorker(
            self.root_path,
            self.sort_type,
            self.ascending,
            self.show_hidden
        )
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.error.connect(lambda e: print(f"Native Scan Error: {e}"))
        self._worker.start()

    def _on_scan_finished(self, items):
        self.beginResetModel()
        
        # Apply Display Mode (Filter in Python for responsiveness)
        if self.display_mode == 1: # Dirs Only
            self.items = [i for i in items if i[2]]
        elif self.display_mode == 2: # Files Only
            self.items = [i for i in items if not i[2]]
        else:
            self.items = items
            
        # Apply Search Filter
        if self.search_text:
            q = self.search_text.lower()
            self.items = [i for i in self.items if q in i[0].lower()]
            
        self.endResetModel()

    def updateMarkedCache(self):
        """v23.2: Placeholder for marking cache updates.
        Currently not needed as we use the shared reference directly,
        but required for compatibility with FilePane.refresh_all_views_in_tab.
        """
        pass

    # --- QAbstractItemModel Overrides ---

    def rowCount(self, parent=QModelIndex()):
        return len(self.items) if not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return 4 # Name, Path, Size, Date

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None

        row = index.row()
        col = index.column()
        # Rust: (name, path, is_dir, size, mtime)
        name, path, is_dir, size, mtime = self.items[row]

        if role == Qt.DisplayRole:
            if col == 0: return name
            if col == 1: return path
            if col == 2: return "" if is_dir else self.format_size(size)
            if col == 3: return self.format_date(mtime)

        if role == Qt.EditRole:
            if col == 0: return name

        if role == Qt.DecorationRole and col == 0:
            if is_dir:
                return self._FOLDER_ICON
            return self._get_icon_for_file(name)

        if role == Qt.BackgroundRole:
            p_norm = os.path.normcase(os.path.abspath(path))
            if p_norm in self.marked_paths:
                return QColor(150, 40, 40) # Bright Wine Red
            return None

        if role == Qt.UserRole: # The full path for open operation
            return path
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            titles = ["Name", "Path", "Size", "Date"]
            return titles[section] if section < len(titles) else None
        return None

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:,.0f} {unit}" if unit == 'B' else f"{size_bytes:,.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:,.1f} TB"

    def format_date(self, timestamp):
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except: return str(timestamp)

    # Helper for View
    def get_item_data(self, row):
        if 0 <= row < len(self.items):
            return self.items[row]
        return None

    def find_path_row(self, path):
        """Find the row index of a given absolute path. Case-insensitive normalization."""
        p_norm = os.path.normcase(os.path.abspath(path))
        for i, item in enumerate(self.items):
            # item: (name, path, is_dir, size, mtime)
            if os.path.normcase(os.path.abspath(item[1])) == p_norm:
                return i
        return -1

    # --- Interaction Overrides ---

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        
        row = index.row()
        col = index.column()
        # Rust: (name, path, is_dir, size, mtime)
        is_dir = self.items[row][2]
        
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        
        # Only Name (col 0) is editable
        if col == 0:
            f |= Qt.ItemIsEditable
        
        if is_dir:
            f |= Qt.ItemIsDropEnabled
            
        return f

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
            
        row = index.row()
        col = index.column()
        
        if col == 0: # Rename
            old_name, old_path, is_dir, size, mtime = self.items[row]
            new_name = value.strip()
            if not new_name or new_name == old_name:
                return False
                
            parent_dir = os.path.dirname(old_path)
            new_path = os.path.join(parent_dir, new_name)
            
            try:
                if os.path.exists(new_path) and new_path.lower() != old_path.lower():
                    # Name collision (unless it's just a case change on Windows)
                    return False
                    
                os.rename(old_path, new_path)
                # v23.1: Trigger async refresh to update the list and sort order
                self.refresh()
                return True
            except Exception as e:
                print(f"Rename Error: {e}")
                return False
        return False

    def mimeData(self, indexes):
        from PySide6.QtCore import QMimeData, QUrl
        mime = QMimeData()
        urls = []
        seen_rows = set()
        for idx in indexes:
            if idx.isValid() and idx.row() not in seen_rows:
                seen_rows.add(idx.row())
                path = self.items[idx.row()][1]
                urls.append(QUrl.fromLocalFile(os.path.abspath(path)))
        mime.setUrls(urls)
        return mime

    def supportedDragActions(self):
        return Qt.CopyAction | Qt.MoveAction | Qt.LinkAction

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction
