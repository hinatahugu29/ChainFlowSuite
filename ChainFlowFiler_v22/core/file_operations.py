"""
core/file_operations.py
v14.1 Refactoring: ファイル操作の共通ユーティリティ

重複していたファイル操作ロジックを統合し、一貫した動作とエラーハンドリングを提供する。
"""
import os
import subprocess
import sys
import unicodedata
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


def open_with_system(path: str) -> bool:
    """OSのデフォルトアプリケーションでファイル/フォルダを開く
    
    Args:
        path: 開くファイルまたはフォルダのパス
        
    Returns:
        bool: 成功した場合True
    """
    try:
        if os.name == 'nt':
            # Windows: 作業ディレクトリを対象ファイルの場所に設定
            # これによりショートカットやエクスプローラーからの起動と同等の挙動を確保
            cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
            subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
        else:
            # macOS/Linux: Qt経由で開く
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        return True
    except Exception as e:
        print(f"[file_operations.open_with_system] Error: {e}")
        return False


def reveal_in_explorer(path: str) -> bool:
    """エクスプローラーで対象を選択した状態で開く
    
    Args:
        path: 表示するファイルまたはフォルダのパス
        
    Returns:
        bool: 成功した場合True
    """
    try:
        abs_path = os.path.abspath(path)
        if os.name == 'nt':
            subprocess.Popen(f'explorer /select,"{abs_path}"')
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', abs_path])
        else:
            # Linux: 親フォルダを開く
            subprocess.Popen(['xdg-open', os.path.dirname(abs_path)])
        return True
    except Exception as e:
        print(f"[file_operations.reveal_in_explorer] Error: {e}")
        return False


def open_terminal(path: str) -> bool:
    """指定パスでターミナルを開く
    
    Args:
        path: ターミナルを開く作業ディレクトリ
        
    Returns:
        bool: 成功した場合True
    """
    try:
        # フォルダかファイルかを判定
        target_dir = path if os.path.isdir(path) else os.path.dirname(path)
        
        if os.name == 'nt':
            # Windows Terminal または CMD を開く
            subprocess.Popen(f'start cmd /K "cd /d {target_dir}"', shell=True)
        elif sys.platform == 'darwin':
            # macOS
            subprocess.Popen(['open', '-a', 'Terminal', target_dir])
        else:
            # Linux
            subprocess.Popen(['x-terminal-emulator', '--working-directory', target_dir])
        return True
    except Exception as e:
        print(f"[file_operations.open_terminal] Error: {e}")
        return False


def normalize_path(path: str) -> str:
    """パスを正規化（OSに依存しない形式に統一）
    
    Args:
        path: 正規化するパス
        
    Returns:
        str: 正規化されたパス
    """
    return os.path.normpath(os.path.abspath(path))


def same_path(path1: str, path2: str) -> bool:
    """2つのパスが実質的に同じか判定（正規化・大文字小文字考慮）
    
    Args:
        path1: 比較するパス1
        path2: 比較するパス2
        
    Returns:
        bool: 同一パスならTrue
    """
    if not path1 or not path2:
        return False
    # Unicode正規化 (NFC) を行い、濁点などの表記揺れを吸収
    path1 = unicodedata.normalize('NFC', path1)
    path2 = unicodedata.normalize('NFC', path2)
    # Windowsではnormcaseで小文字化される
    p1 = os.path.normcase(os.path.normpath(os.path.abspath(path1)))
    p2 = os.path.normcase(os.path.normpath(os.path.abspath(path2)))
    return p1 == p2


def is_office_file(path: str) -> bool:
    """Office形式のファイルかどうかを判定
    
    Args:
        path: 判定するファイルパス
        
    Returns:
        bool: Office形式の場合True
    """
    office_exts = ('.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt')
    return path.lower().endswith(office_exts)


def is_archive_file(path: str) -> bool:
    """アーカイブ形式のファイルかどうかを判定
    
    Args:
        path: 判定するファイルパス
        
    Returns:
        bool: アーカイブ形式の場合True
    """
    archive_exts = ('.zip', '.7z', '.rar', '.tar', '.gz', '.bz2')
    return path.lower().endswith(archive_exts)
