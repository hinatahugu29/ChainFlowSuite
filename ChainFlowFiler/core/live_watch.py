"""外部からのファイル変更（コピー・移動・削除等）をリアルタイムにペインへ反映する層。

QFileSystemModel自身の内部監視（QFileSystemWatcher）はQtの非同期ロード機構と
絡み合っていて反映が遅れることがあるため、watchdog（Windowsでは
ReadDirectoryChangesWを直接叩く）で変更を検知し、既存のF5リフレッシュ処理
（file_pane.FilePane.refresh_contents）を即座に呼び出すだけの薄い層にする。

Trayce（Tauri版ファイラ）のwatch.rsと同じ設計:
  - パスごとに参照カウントし、最後の利用者が離れたら監視を止める
  - 変更の種類は問わず「ここが変わった」とだけ伝え、詳細な差分計算はしない
"""
import os
from collections import defaultdict

from PySide6.QtCore import QObject, Signal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core import logger


class _Dispatcher(QObject):
    """watchdogのワーカースレッドからQtのメインスレッドへ橋渡しするための器。

    Signalはスレッドをまたいで安全にemitできる（Qtが自動的にキューイングする）ので、
    ここを経由すればUI側のコードはメインスレッドで動いていると信じてよい。
    """
    path_changed = Signal(str)


_dispatcher = _Dispatcher()
_observer = None
_handles = {}       # 正規化パス -> watchdog ObservedWatch
_refcount = defaultdict(int)


class _NudgeHandler(FileSystemEventHandler):
    """このディレクトリ配下で何かが起きたら、そのディレクトリ自身の変化として伝える。"""
    def __init__(self, norm_path):
        super().__init__()
        self._norm_path = norm_path

    def on_any_event(self, event):
        _dispatcher.path_changed.emit(self._norm_path)


def _ensure_observer():
    global _observer
    if _observer is None:
        _observer = Observer()
        _observer.start()
    return _observer


def acquire(path):
    """このディレクトリの監視を開始する（既に見ているなら参照数を増やすだけ）。"""
    if not path or not os.path.isdir(path):
        return
    norm = os.path.normcase(os.path.normpath(path))
    _refcount[norm] += 1
    if norm in _handles:
        return

    try:
        observer = _ensure_observer()
        handler = _NudgeHandler(norm)
        # v1: 直下だけ見る。再帰にすると深い階層で大量のイベントが飛んでくる
        # （Trayceのwatch.rsと同じ判断）。
        watch = observer.schedule(handler, path, recursive=False)
        _handles[norm] = watch
    except Exception as e:
        # ネットワークドライブなど、ReadDirectoryChangesWが使えない/失敗する場所もある。
        # その場合はリアルタイム反映を諦め、従来通りF5手動更新に任せる。
        logger.log_debug(f"[live_watch] {path} を監視できません: {e}")
        _refcount[norm] -= 1


def release(path):
    """監視をやめる。他にも見ている者がいれば参照数を減らすだけ。"""
    if not path:
        return
    norm = os.path.normcase(os.path.normpath(path))
    if norm not in _refcount:
        return
    _refcount[norm] -= 1
    if _refcount[norm] > 0:
        return
    del _refcount[norm]
    watch = _handles.pop(norm, None)
    if watch is not None and _observer is not None:
        try:
            _observer.unschedule(watch)
        except Exception:
            pass


def connect(slot):
    """path_changedシグナルにスロットを接続するヘルパー（テスト・型ヒント用）。"""
    _dispatcher.path_changed.connect(slot)


def disconnect(slot):
    try:
        _dispatcher.path_changed.disconnect(slot)
    except (TypeError, RuntimeError):
        pass
