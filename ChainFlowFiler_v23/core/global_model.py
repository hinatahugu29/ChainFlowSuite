from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir

_global_fs_model = None

def get_global_file_system_model():
    """
    アプリケーション全体で共有するQFileSystemModelのシングルトンインスタンスを返す。
    複数のモデルを作ると、それぞれがスレッド監視を行って重くなるため、一つを使い回す。
    """
    global _global_fs_model
    if _global_fs_model is None:
        _global_fs_model = QFileSystemModel()
        # ドライブ表示、隠しファイル表示などの基本フィルタ設定
        _global_fs_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden | QDir.Drives)
        # ルートから監視を開始（必要に応じて遅延させる手もあるが、通常はこれでOK）
        _global_fs_model.setRootPath(QDir.rootPath())
        # 右クリック操作（削除・リネームなど）のためにRead/Write可能にする
        _global_fs_model.setReadOnly(False)
        
    return _global_fs_model
