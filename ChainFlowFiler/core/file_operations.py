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

# ==============================================================================
# v23.8: ネットワークパス判定
#
# UIスレッドから os.path.isdir() / os.path.exists() を呼ぶと、対象が到達不能な
# ネットワーク共有だった場合 SMB のタイムアウトまでスレッドが停止する。
# 実測: 到達不能ホストで 26.7 秒、名前解決失敗で 1.1 秒（正常なSMB共有は 3ms）。
# 起動時や終了時にこれを踏むとアプリが固まって見えるため、ネットワーク上の
# パスに対しては I/O を行わずに判定できる手段を用意する。
# ==============================================================================

_DRIVE_TYPE_CACHE = {}
_DRIVE_REMOTE = 4      # DRIVE_REMOTE
_DRIVE_NO_ROOT_DIR = 1 # DRIVE_NO_ROOT_DIR（未接続のマップドライブ等）


def is_network_path(path):
    """パスがネットワーク上（またはドライブ未接続）かを、I/Oを起こさずに判定する。

    - UNC パス（\server\share）は常に True
    - ドライブレターは GetDriveTypeW で判定（ローカルのテーブル参照のみでブロックしない）

    判定できない場合は False（＝従来どおり I/O してよい）を返す。
    """
    if not path:
        return False
    try:
        if path.startswith("\\\\") or path.startswith("//"):
            return True
        drive = os.path.splitdrive(path)[0]
        if not drive or len(drive) < 2:
            return False
        drive = drive.upper()
        cached = _DRIVE_TYPE_CACHE.get(drive)
        if cached is None:
            import ctypes
            cached = ctypes.windll.kernel32.GetDriveTypeW(drive + "\\")
            # DRIVE_NO_ROOT_DIR は「今は繋がっていない」という一時的な状態なので
            # キャッシュしない。セッション中にドライブを割り当て直しても追随できる。
            # GetDriveTypeW 自体はローカルのテーブル参照でブロックしないため、
            # 毎回呼んでも実害はない。
            if cached != _DRIVE_NO_ROOT_DIR:
                _DRIVE_TYPE_CACHE[drive] = cached
        return cached in (_DRIVE_REMOTE, _DRIVE_NO_ROOT_DIR)
    except Exception:
        return False


def looks_like_dir(path):
    """フォルダらしさを判定する。ローカルなら実際に確認し、ネットワークなら推測する。

    ネットワークパスに対して os.path.isdir() を呼ぶと最大数十秒ブロックし得るため、
    その場合は「拡張子が無ければフォルダ」という推測に切り替える。
    表示アイコンの選択のような、外れても実害のない用途に限って使うこと。
    """
    if not path:
        return False
    if is_network_path(path):
        return not os.path.splitext(path)[1]
    try:
        return os.path.isdir(path)
    except Exception:
        return False


def exists_nonblocking(path):
    """存在確認。ネットワークパスはブロックを避けるため、常に True とみなす。

    「消えたパスを弾く」用途向け。ネットワーク上のパスを消してしまうより、
    残しておく方が実害が小さいという判断。
    """
    if not path:
        return False
    if is_network_path(path):
        return True
    try:
        return os.path.exists(path)
    except Exception:
        return False


# ==============================================================================
# ゴミ箱への削除
#
# 従来は QFileSystemModel.remove() を直接呼んでおり、確認ダイアログで Yes を
# 押した瞬間に復元不能な完全削除が走っていた。ファイラーの誤操作で最も痛い
# 部分なので、Windows のシェル API 経由でゴミ箱へ送る。
#
# SHFileOperationW に FOF_ALLOWUNDO を付けると「元に戻す」が効く形で削除される。
# FOF_WANTNUKEWARNING は、サイズ超過やネットワークドライブ等でゴミ箱に入れられず
# 完全削除になってしまう場合に、OS 標準の警告を出させるためのフラグ。
# これを外すと黙って完全削除されるため、必ず付けたままにすること。
# ==============================================================================

_FO_DELETE = 0x0003
_FOF_NOCONFIRMATION = 0x0010
_FOF_ALLOWUNDO = 0x0040
_FOF_WANTNUKEWARNING = 0x4000


def move_to_trash(paths):
    """指定パスをゴミ箱へ送る。

    Args:
        paths: 削除対象パスのリスト

    Returns:
        (ok, detail): ok が False のとき detail にエラー内容を示す文字列が入る。
                      ユーザーが OS の警告でキャンセルした場合も ok=False,
                      detail="cancelled" を返す。
    """
    targets = [os.path.normpath(os.path.abspath(p)) for p in paths if p]
    if not targets:
        return False, "削除対象がありません"

    if os.name != 'nt':
        # Windows 以外は send2trash があれば使う（無ければ失敗として扱い、
        # 呼び出し側に完全削除させない）
        try:
            from send2trash import send2trash
        except ImportError:
            return False, "ゴミ箱への削除に対応していません (send2trash 未インストール)"
        try:
            for p in targets:
                send2trash(p)
            return True, ""
        except Exception as e:
            return False, str(e)

    import ctypes
    from ctypes import wintypes

    class _SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", ctypes.c_wchar_p),
            ("pTo", ctypes.c_wchar_p),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_wchar_p),
        ]

    # pFrom は「NUL 区切り + 末尾二重 NUL」の文字列。c_wchar_p に直接代入すると
    # 最初の NUL で切れてしまうため、バッファを作って cast する。
    # buf は API 呼び出しが終わるまで参照を保持しておく必要がある。
    buf = ctypes.create_unicode_buffer("\0".join(targets) + "\0\0")

    op = _SHFILEOPSTRUCTW()
    op.hwnd = None
    op.wFunc = _FO_DELETE
    op.pFrom = ctypes.cast(buf, ctypes.c_wchar_p)
    op.pTo = None
    op.fFlags = _FOF_ALLOWUNDO | _FOF_NOCONFIRMATION | _FOF_WANTNUKEWARNING
    op.fAnyOperationsAborted = False
    op.hNameMappings = None
    op.lpszProgressTitle = None

    try:
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    except Exception as e:
        return False, str(e)

    if op.fAnyOperationsAborted:
        return False, "cancelled"
    if res != 0:
        # SHFileOperation は GetLastError ではなく独自のコードを返す
        return False, f"削除に失敗しました (code: 0x{res:X})"
    return True, ""
