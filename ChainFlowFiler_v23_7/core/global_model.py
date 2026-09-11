from PySide6.QtWidgets import QFileSystemModel, QFileIconProvider
from PySide6.QtCore import QDir

from .file_operations import is_network_path

_global_fs_model = None
_icon_provider = None  # モデルより長く生存させる必要があるため保持する


class NetworkAwareIconProvider(QFileIconProvider):
    """v23.8: ネットワークパスに対してシェルAPIの「種類」取得を回避するプロバイダ。

    QFileSystemModel は内部の収集スレッドで、列挙する全エントリに対して
    QFileIconProvider.type() を呼ぶ。既定実装は Windows のシェル API
    (SHGetFileInfo) を叩くため、SMB 共有では往復コストが極端に大きい。

    実測（社内共有 Z: の未アクセスファイル200件）:
        os.stat                    0.26 ms/件
        QFileIconProvider.type()  46.01 ms/件   ← 約177倍
        （ネットワーク上のフォルダに対しては 0.18 ms/件と安いので対象外）

    未訪問フォルダにファイルが50件あれば、これだけで約2.3秒かかる計算になる。
    ローカルパスでは既定の挙動（Windows の種類名）をそのまま使い、
    ネットワークパスのときだけ拡張子から組み立てた文字列を返す。
    """

    def type(self, info):
        try:
            if is_network_path(info.absoluteFilePath()):
                if info.isDir():
                    return "File Folder"
                suffix = info.suffix()
                return (suffix.upper() + " File") if suffix else "File"
        except Exception:
            pass
        return super().type(info)

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
        # v23.4: ショートカットをプロキシ側で特別扱いするために自動解決を無効化
        _global_fs_model.setResolveSymlinks(False)
        # v23.8: ネットワーク上での「種類」取得コストを避ける（上のクラス注記を参照）
        global _icon_provider
        _icon_provider = NetworkAwareIconProvider()
        _global_fs_model.setIconProvider(_icon_provider)
        # ルートから監視を開始（必要に応じて遅延させる手もあるが、通常はこれでOK）
        _global_fs_model.setRootPath(QDir.rootPath())
        # 右クリック操作（削除・リネームなど）のためにRead/Write可能にする
        _global_fs_model.setReadOnly(False)
        
    return _global_fs_model
