import os
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFileIconProvider, QApplication

class IconLoaderSignals(QObject):
    """
    Signals for IconLoader.
    Must be a separate QObject because QRunnable is not a QObject.
    """
    icon_loaded = Signal(str, QIcon) # path, icon

class IconWorker(QRunnable):
    """
    Background task to load an icon for a specific path.
    """
    def __init__(self, path, signals, provider):
        super().__init__()
        self.path = path
        self.signals = signals
        self.provider = provider

    def run(self):
        # Using the shared provider instance
        from PySide6.QtCore import QFileInfo
        info = QFileInfo(self.path)
        icon = self.provider.icon(info)
        
        if icon.isNull():
            return

        # Emit the result back to the main thread
        # Note: Sending QIcon across threads via signal/slot is safe (queued connection handles allow copying).
        self.signals.icon_loaded.emit(self.path, icon)

class IconLoader(QObject):
    """
    Singleton-like manager for asynchronous icon loading.
    """
    _instance = None
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = IconLoader()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        # Limit the number of concurrent icon fetches to avoid saturating UI thread with updates
        self.thread_pool.setMaxThreadCount(4) 
        
        self.signals = IconLoaderSignals()
        self.signals.icon_loaded.connect(self._on_icon_loaded)
        
        self.provider = QFileIconProvider() # Shared Instance
        self.cache = {}    # path -> QIcon
        self.cache_order = [] # To implement simple FIFO eviction
        self.MAX_CACHE_SIZE = 500
        self.loading = set() # paths currently being loaded (to prevent duplicate requests)
        
        # Default placeholder icon (transparent)
        pix = QPixmap(16, 16)
        pix.fill(Qt.transparent)
        self.default_icon = QIcon(pix)

    def get_icon(self, path):
        """
        Request an icon for the given path.
        Returns:
            (QIcon, bool): The icon to display, and a boolean indicating if it is the final icon (True) or a placeholder (False).
        """
        abs_path = os.path.normpath(path)
        
        # Check cache
        if abs_path in self.cache:
            return self.cache[abs_path], True
            
        # Check if already loading
        if abs_path not in self.loading:
            self.loading.add(abs_path)
            worker = IconWorker(abs_path, self.signals, self.provider)
            self.thread_pool.start(worker)
            
        return self.default_icon, False

    def _on_icon_loaded(self, path, icon):
        """Slot called when a worker finishes loading an icon."""
        if path in self.loading:
            self.loading.remove(path)
        
        # Cache Management with FIFO eviction
        if path not in self.cache:
            if len(self.cache_order) >= self.MAX_CACHE_SIZE:
                oldest = self.cache_order.pop(0)
                if oldest in self.cache:
                    del self.cache[oldest]
            
            self.cache[path] = icon
            self.cache_order.append(path)
        else:
            self.cache[path] = icon

# Global Accessor
_loader = None

def get_icon_loader():
    global _loader
    if _loader is None:
        _loader = IconLoader.instance()
    return _loader
