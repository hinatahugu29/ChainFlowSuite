"""
v2: Model/View backing for the search result list.

Replaces the old QTreeWidget + QTreeWidgetItem approach, where every query
change cleared the tree and rebuilt a QTreeWidgetItem per matching result
(O(total matches) per keystroke). Here, all scanned rows live in
SearchResultModel exactly once; SearchFilterProxyModel only decides which
rows are *visible* for the current query. Changing the query just calls
invalidateFilter() - Qt only re-renders the rows actually on screen, so the
cost no longer scales with the number of matches.
"""

import os
from datetime import datetime

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QMimeData, QUrl
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtGui import QDrag

try:
    from .search_engine import SearchWorker
except ImportError:
    from search_engine import SearchWorker


def format_size(size_bytes):
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}" if unit == 'B' else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


class SearchResultModel(QAbstractTableModel):
    """Holds every scanned (name, full_path, size, mtime) row for one search."""

    COLUMNS = ["Name", "Path", "Size", "Date"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []  # list of (name, full_path, size, mtime)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return super().flags(index) | Qt.ItemIsDragEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        name, full_path, size, mtime = self._rows[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return name
            if col == 1:
                return full_path
            if col == 2:
                return format_size(size)
            if col == 3:
                return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        elif role == Qt.UserRole:
            # Always the file path, regardless of which column was clicked -
            # open/copy/drag all just want "which file is this row".
            return full_path
        return None

    def get_row(self, row_idx):
        return self._rows[row_idx]

    def clear(self):
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def append_rows(self, rows):
        if not rows:
            return
        start = len(self._rows)
        end = start + len(rows) - 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._rows.extend(rows)
        self.endInsertRows()


class SearchFilterProxyModel(QSortFilterProxyModel):
    """Filters SearchResultModel rows against the current query, in place."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parsed_query = []
        self._show_none = False
        self.setDynamicSortFilter(True)

    def setParsedQuery(self, parsed_query):
        """Show only rows matching parsed_query (from SearchWorker.parse_query)."""
        self._show_none = False
        self._parsed_query = parsed_query
        self.invalidateFilter()

    def setShowNone(self):
        """Show nothing (used when the search box is emptied) without
        touching the underlying scanned data."""
        self._show_none = True
        self._parsed_query = []
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if self._show_none:
            return False
        model = self.sourceModel()
        name = model.get_row(source_row)[0]
        return SearchWorker.is_match(name, self._parsed_query)

    def lessThan(self, left, right):
        model = self.sourceModel()
        col = left.column()
        l_row = model.get_row(left.row())
        r_row = model.get_row(right.row())

        if col == 2:  # Size
            return l_row[2] < r_row[2]
        if col == 3:  # Date
            return l_row[3] < r_row[3]
        # Name / Path: case-insensitive string compare
        return l_row[col].lower() < r_row[col].lower()


class DraggableTreeView(QTreeView):
    """QTreeView with drag support to external applications (Explorer, etc)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setUniformRowHeights(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def startDrag(self, supportedActions):
        indexes = self.selectionModel().selectedRows(0)
        if not indexes:
            return

        urls = []
        for idx in indexes:
            path = idx.data(Qt.UserRole)
            if path and os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))

        if not urls:
            return

        mime_data = QMimeData()
        mime_data.setUrls(urls)

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)
