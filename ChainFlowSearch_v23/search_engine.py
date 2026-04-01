import os
import fnmatch
import unicodedata
import sys
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker

# v23.0 Native Search Engine Integration
_HAVE_NATIVE_CORE = False
try:
    # 実行環境に合わせてパスを追加
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, "native", "target", "release")
    if target_path not in sys.path:
        sys.path.append(target_path)
    
    import chainflow_search_core
    _HAVE_NATIVE_CORE = True
except ImportError:
    # 開発用配置案
    pass

class SearchWorker(QThread):
    """
    Background worker for recursive file scanning.
    Emits signals as files are found.
    """
    # Signal arguments: name, full_path, size_bytes, modified_time
    # v21.3 Optimization: Emit a list of tuples to reduce signal overhead
    # Each tuple: (name, full_path, size, mtime)
    results_found = Signal(list)
    finished_scanning = Signal()
    progress_update = Signal(int) # Number of items scanned so far

    def __init__(self, root_path, search_query, search_mode="name", parent=None):
        super().__init__(parent)
        self.root_path = root_path
        # Normalize to NFKC to handle full-width/half-width insensitivity
        self.search_query = unicodedata.normalize('NFKC', search_query).lower()
        self.search_mode = search_mode # "name" or "content" (content not implemented yet)
        self.parsed_query = self._parse_query(self.search_query)
        self._is_running = True
        self.mutex = QMutex()

    def stop(self):
        """Thread-safe stop request."""
        with QMutexLocker(self.mutex):
            self._is_running = False

    def run(self):
        """Main scanning loop using native Rust core or fallback to os.scandir."""
        if not self.root_path or not os.path.exists(self.root_path):
            self.finished_scanning.emit()
            return

        # --- v23.0 Native Engine Path ---
        if _HAVE_NATIVE_CORE:
            try:
                # Rust側に探索を委譲
                # Rustは並列で動き、結果が見つかるたびにcallback(実態はシグナルemit)を叩く
                chainflow_search_core.start_native_search(
                    self.root_path,
                    self.search_query,
                    batch_size=50,
                    callback=lambda results: self.results_found.emit(results)
                )
                self.finished_scanning.emit()
                return
            except Exception as e:
                print(f"Native search failed, falling back to Python: {e}")
        
        # --- Legacy Python Path (Fallback) ---
        scanned_count = 0
        batch_buffer = []
        # v21.4 Optimization: Use smaller batch size to show results immediately (feeling of "real-time")
        BATCH_SIZE = 10
        
        # v21.7 Smart Scan: Ignore list
        IGNORED_DIRS = {
            'node_modules', '.git', '.venv', '__pycache__', 
            'dist', 'build', '.idea', '.vscode', 'venv', 'env'
        }

        # v21.4 Optimization: Use stack-based iteration with os.scandir
        # This avoids the overhead of os.walk and allows using entry.stat()
        # which is cached from the directory listing on Windows/SMB.
        stack = [self.root_path]

        try:
            while stack:
                # Check for stop request at directory level
                with QMutexLocker(self.mutex):
                    if not self._is_running:
                        break
                
                try:
                    current_dir = stack.pop()
                except IndexError:
                    break

                # v21.5 Smart Search: Collect entries first, then sort dirs by mtime
                dirs_to_visit = []
                files_to_process = []

                try:
                    with os.scandir(current_dir) as it:
                        for entry in it:
                            try:
                                # Filter: Skip hidden (.) and system ($) directories/files
                                if entry.name.startswith('.') or entry.name.startswith('$'):
                                    continue
                                
                                if entry.is_dir(follow_symlinks=False):
                                    # v21.7 Smart Scan: Skip ignored directories
                                    if entry.name in IGNORED_DIRS:
                                        continue

                                    try:
                                        dir_stat = entry.stat(follow_symlinks=False)
                                        dirs_to_visit.append((entry.path, dir_stat.st_mtime))
                                    except OSError:
                                        # stat failed -> treat as oldest (priority=lowest)
                                        dirs_to_visit.append((entry.path, 0))
                                
                                elif entry.is_file(follow_symlinks=False):
                                    files_to_process.append(entry)

                            except (OSError, PermissionError):
                                pass
                                
                except (OSError, PermissionError):
                    continue

                # --- Priority Sort: Newest directory first ---
                # Stack is LIFO: last pushed = first popped.
                # Sort ASCENDING by mtime so newest ends up on top of stack.
                dirs_to_visit.sort(key=lambda x: x[1]) 
                for dir_path, _ in dirs_to_visit:
                    stack.append(dir_path)

                # --- Process files in current directory ---
                with QMutexLocker(self.mutex):
                    if not self._is_running:
                        break

                for entry in files_to_process:
                    try:
                        if self._is_match(entry.name, self.parsed_query):
                            stat = entry.stat(follow_symlinks=False)
                            size = stat.st_size
                            mtime = stat.st_mtime
                            full_path = entry.path
                            
                            batch_buffer.append((entry.name, full_path, size, mtime))
                            
                            if len(batch_buffer) >= BATCH_SIZE:
                                self.results_found.emit(batch_buffer)
                                batch_buffer = []

                        scanned_count += 1
                        if scanned_count % 500 == 0:
                            self.progress_update.emit(scanned_count)

                    except (OSError, PermissionError):
                        pass

            # Emit remaining buffered items
            if batch_buffer:
                self.results_found.emit(batch_buffer)

        except Exception as e:
            print(f"Search error: {e}")

        self.finished_scanning.emit()

    @staticmethod
    def parse_query(query):
        """
        Parses the query string into a structure for AND/OR logic.
        Structure: List of Lists of strings.
        Outer list is OR (any of these lists must match).
        Inner list is AND (all of these terms must match).
        Example: "py | txt log" -> [['py'], ['txt', 'log']]
        """
        if not query:
            return []
        
        # 1. Split by OR operator '|'
        or_groups = query.split('|')
        parsed = []
        for group in or_groups:
            # 2. Split by AND operator ' ' (whitespace)
            terms = [t.strip() for t in group.split() if t.strip()]
            if terms:
                parsed.append(terms)
        return parsed

    @staticmethod
    def is_match(filename, parsed_query):
        """
        Checks if filename matches the parsed query.
        """
        # Normalize filename to NFKC to match normalized query
        filename_norm = unicodedata.normalize('NFKC', filename)
        filename_lower = filename_norm.lower()
        
        if not parsed_query:
            return True # Or False if we want to enforce a query. But empty query usually filtered before.

        # OR Logic: Match if ANY of the AND groups match
        for and_group in parsed_query:
            # AND Logic: Match if ALL terms in group match
            group_match = True
            for term in and_group:
                # v21.11 Fix: Normalize and lower the term to ensure case-insensitivity
                # The query terms should be normalized to NFKC and lower-cased.
                term_norm = unicodedata.normalize('NFKC', term).lower()
                
                # Check for negation
                is_negative = term_norm.startswith('-') and len(term_norm) > 1
                search_term = term_norm[1:] if is_negative else term_norm
                
                # Check for wildcards
                term_matches = False
                if '*' in search_term or '?' in search_term:
                    if fnmatch.fnmatch(filename_lower, search_term):
                        term_matches = True
                else:
                    if search_term in filename_lower:
                        term_matches = True
                
                # Apply logic
                if is_negative:
                    if term_matches:
                        group_match = False # Found excluded term -> fail group
                        break
                else:
                    if not term_matches:
                        group_match = False # Missing required term -> fail group
                        break
            
            if group_match:
                return True # Found a matching OR group
        
        return False
    
    # Keep instance methods for compatibility but wrapping static ones
    def _parse_query(self, query):
        return SearchWorker.parse_query(query)

    def _is_match(self, filename, parsed_query):
        return SearchWorker.is_match(filename, parsed_query)

class CountWorker(QThread):
    """
    Worker thread to quickly estimate/count total files for progress bar.
    """
    count_updated = Signal(int) # Emits total count found so far
    finished_counting = Signal(int)

    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.root_path = root_path
        self._is_running = True
        self.mutex = QMutex()
        
        # Share the same ignore list
        self.IGNORED_DIRS = {
            'node_modules', '.git', '.venv', '__pycache__', 
            'dist', 'build', '.idea', '.vscode', 'venv', 'env'
        }

    def stop(self):
        with QMutexLocker(self.mutex):
            self._is_running = False

    def run(self):
        count = 0
        stack = [self.root_path]
        
        # Report implicit bulk updates to avoid flooding event loop
        last_report_count = 0
        REPORT_INTERVAL = 1000

        try:
            while stack:
                with QMutexLocker(self.mutex):
                    if not self._is_running:
                        break
                
                try:
                    current_dir = stack.pop()
                except IndexError:
                    break
                
                try:
                    with os.scandir(current_dir) as it:
                        for entry in it:
                            if entry.name.startswith('.') or entry.name.startswith('$'):
                                continue
                                
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name in self.IGNORED_DIRS:
                                    continue
                                stack.append(entry.path)
                                # directory counts as 1 item? No, SearchWorker counts files.
                                # count += 1 
                            elif entry.is_file(follow_symlinks=False):
                                count += 1
                                
                    if count - last_report_count > REPORT_INTERVAL:
                        self.count_updated.emit(count)
                        last_report_count = count

                except (OSError, PermissionError):
                    continue
                    
        except Exception:
            pass
            
        self.finished_counting.emit(count)
