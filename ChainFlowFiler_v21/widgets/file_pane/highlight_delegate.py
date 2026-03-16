"""
v14.0 Ancestral Highlight用デリゲート
v14.1 Refactoring: file_pane.py から分離
v14.2 Fix: same_path を使用した大文字小文字を区別しない比較
"""
import os
from PySide6.QtWidgets import QStyledItemDelegate, QApplication
from PySide6.QtGui import QColor

from core import same_path


class HighlightDelegate(QStyledItemDelegate):
    """Ancestral Highlight用デリゲート - 選択パスの祖先/子孫をハイライト表示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_path = None
        self._norm_highlighted_path = None

    def set_highlight_path(self, path):
        if path:
            self.highlighted_path = path
            # v19.2 Optimization: 描画ループ内での計算を避けるため、事前に正規化しておく
            # normcase for Windows (case-insensitive)
            self._norm_highlighted_path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        else:
            self.highlighted_path = None
            self._norm_highlighted_path = None

    def paint(self, painter, option, index):
        # そもそもハイライトがない、またはインデックスが無効なら標準描画のみ
        if not self._norm_highlighted_path or not index.isValid():
            super().paint(painter, option, index)
            return

        # Check if window is active (Fix for Highlight Persistence on Alt+Tab)
        if option.widget and option.widget.window() and not option.widget.window().isActiveWindow():
             super().paint(painter, option, index)
             return

        super().paint(painter, option, index)
        
        # v14.3 Fix: 全カラム（名前、サイズ、日付）をハイライト対象にする
        # if index.column() != 0:
        #     return

        model = index.model()
        item_path = None
        
        # モデルからパス取得 (極力高速に)
        if hasattr(model, 'filePath'):
             item_path = model.filePath(index)
        elif hasattr(model, 'mapToSource'):
             source_idx = model.mapToSource(index)
             source_model = model.sourceModel()
             if hasattr(source_model, 'filePath'):
                 item_path = source_model.filePath(source_idx)
        
        if not item_path:
            return
            
        # v19.2 Optimization: ここで same_path を呼ぶと os.path.abspath が高負荷になるため
        # 文字列操作のみで比較する (OSのパス区切り文字の違いなどは normpath で吸収)
        try:
            norm_item_path = os.path.normcase(os.path.normpath(item_path))
        except Exception:
            return # パス変換エラー時はスキップ

        if norm_item_path == self._norm_highlighted_path:
             painter.save()
             
             highlight_color = QColor(255, 200, 50, 100) 
             border_color = QColor(255, 200, 0, 255)
             
             rect = option.rect
             
             # v14.3: 枠線が重なると見栄えが悪いので、カラム位置に応じて調整
             # ただしDelegateからは単純にrect全体を塗る。
             
             painter.fillRect(rect, highlight_color)
             
             pen = painter.pen()
             pen.setColor(border_color)
             pen.setWidth(2)
             painter.setPen(pen)
             
             # 各セルに枠を描く（Excelの範囲選択風）
             painter.drawRect(rect.adjusted(1,1,-1,-1))
             
             painter.restore()

    def createEditor(self, parent, option, index):
        """v21.1: IME対応エディタの作成"""
        from PySide6.QtWidgets import QLineEdit
        editor = QLineEdit(parent)
        # イベントフィルタをインストールしてキーイベントを監視
        editor.installEventFilter(self)
        return editor

    def eventFilter(self, editor, event):
        """v21.1: IME入力中のキーイベント制御"""
        from PySide6.QtCore import QEvent, Qt
        
        if event.type() == QEvent.KeyPress:
            # Case 1: Enter Key
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # IME構成中かチェック
                # Qt.ImCursorPosition != 0 または ImPlatformData がある場合は構成中とみなす
                # ただし環境依存があるため、inputMethodQueryで判定
                if hasattr(editor, 'inputMethodQuery'):
                    attributes = editor.inputMethodQuery(Qt.InputMethodQuery.ImAttributes)
                    # cursor_pos = editor.inputMethodQuery(Qt.InputMethodQuery.ImCursorPosition)
                    
                    # 簡易判定: テキストが存在し、かつ確定していない状態（推測）
                    # 実際には KeyPress 時点でまだ IME イベントが来ていないこともある。
                    # しかし「Enter」が来た時点で、もしIMEがActiveなら、
                    # Qtの標準Delegateはこれを「Commit」として扱ってしまう。
                    
                    # 対策: EnterキーをDelegate側で処理せず、Editorに渡す。
                    # EditorがそれをIME確定として処理すれば、EditingFinishedは飛ばないはず。
                    # もしIMEがなければ、Editorは単に改行などをしようとするか、何もしない。
                    # リネーム確定のためには「IMEでなければCommit」したい。
                    
                    # ここでは "return False" (標準処理) だとCommitされてしまうので、
                    # 自分で条件分岐する必要がある。
                    
                    # Windowsでの経験則: 
                    # IME変換中のEnterは、QEvent.KeyPress としては飛んでこないことが多い（OSが食う）。
                    # しかし、確定の瞬間のEnterが飛んでくることがある。
                    # その場合、QInputMethodEvent が直後に来る。
                    
                    # 安全策: Enterキーは常に「Editorに任せる」ことにして、
                    # Delegateの「EnterでCommit」機能を無効化する。
                    # その代わり、Editorの `editingFinished` シグナルを使ってCommitさせるように
                    # BatchTreeView側などで設定する必要があるが、
                    # QStyledItemDelegateはデフォルトで editingFinished を監視して commitData を呼ぶ。
                    
                    # つまり、「何もしない（Trueを返してイベントを握りつぶし、Editorにも渡さない）」と入力できない。
                    # 「Falseを返す（親＝Delegate処理へ）」とCommitされる。
                    # 「Editorにだけ渡したい」
                    
                    # 解決策:
                    # 1. Editorに直接 keyPressEvent を送る (editor.event(event))
                    # 2. True を返す (DelegateのeventFilterとしては「処理済み」とする)
                    
                    # これにより、Delegate（親クラスのeventFilter）はEnterを検知できずCommitしない。
                    # EditorはEnterを受け取り、IME確定や編集終了処理を行う。
                    # EditingFinishedシグナルが出れば、Delegateがそれを拾ってCommitする。
                    
                    editor.event(event)
                    return True

        return super().eventFilter(editor, event)

    def setEditorData(self, editor, index):
        """v21.1: データ更新時の入力保護"""
        # 編集中にバックグラウンドでアイコンロード(dataChanged)が走ると
        # setEditorDataが呼ばれて入力中の文字が消える（元のファイル名に戻る）問題の修正
        
        # エディタが既に変更されている（ユーザーが何か入力した）なら、
        # モデルからの値を上書きしない。
        if hasattr(editor, 'isModified') and editor.isModified():
             return

        super().setEditorData(editor, index)


