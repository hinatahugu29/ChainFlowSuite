"""
v14.0 Ancestral Highlight用デリゲート
v14.1 Refactoring: file_pane.py から分離
v14.2 Fix: same_path を使用した大文字小文字を区別しない比較
"""
import os
from PySide6.QtWidgets import QStyledItemDelegate, QApplication
from PySide6.QtGui import QColor

from PySide6.QtCore import Qt, QEvent
from core import same_path


class HighlightDelegate(QStyledItemDelegate):
    """Ancestral Highlight用デリゲート - 選択パスの祖先/子孫をハイライト表示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted_path = None
        self._norm_highlighted_path = None
        self.marked_paths = set() # v23.2: バッチマーク用共有参照

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

        # v23.2: バッチマーク（赤色）の描画を先に行う
        item_path = index.data(Qt.UserRole)
        if item_path:
            p_norm = os.path.normcase(os.path.abspath(item_path))
            if p_norm in self.marked_paths:
                painter.save()
                mark_color = QColor(180, 50, 50, 80) # 視認性の高い赤（半透明）
                painter.fillRect(option.rect, mark_color)
                painter.restore()

        super().paint(painter, option, index)
        
        # v14.3 Fix: 全カラム（名前、サイズ、日付）をハイライト対象にする
        # if index.column() != 0:
        #     return

        model = index.model()
        item_path = None
        
        # モデルからパス取得 (Native v23.1: UserRole優先)
        item_path = index.data(Qt.UserRole)
        
        # フォールバック (標準モデルやサイドバー用)
        if not item_path:
            if hasattr(model, 'filePath'):
                 item_path = model.filePath(index)
            elif hasattr(model, 'mapToSource'):
                 source_idx = model.mapToSource(index)
                 source_model = model.sourceModel()
                 if hasattr(source_model, 'filePath'):
                     item_path = source_model.filePath(source_idx)
        
        if not item_path:
            return
            
        # v19.2 Optimization: 文字列比較を優先。
        # Windows環境を考慮し、最低線限の normcase 比較に留める。
        # normpath はコストがかかるため、絶対に必要ではない限り避ける。
        
        # セルごとに normcase を呼ぶのは重いため、まずは単純比較
        if item_path == self.highlighted_path:
            is_match = True
        else:
            try:
                # self._norm_highlighted_path は set_highlight_path で既に normcase 済み
                norm_item_path = os.path.normcase(item_path)
                is_match = (norm_item_path == self._norm_highlighted_path)
            except Exception:
                is_match = False

        if is_match:
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
        """v23.1: データ更新時の入力保護と、リネーム時の初期選択範囲の制御"""
        if hasattr(editor, 'isModified') and editor.isModified():
             return

        # モデルから現在のテキストを取得 (EditRole)
        text = index.data(Qt.EditRole)
        if text:
            editor.setText(text)
            
            # 標準的なファイラの挙動: 拡張子を除いた名前部分のみを選択する
            path = index.data(Qt.UserRole)
            if path and os.path.isfile(path):
                # 拡張子分離
                name_part, ext_part = os.path.splitext(text)
                
                # .gitignore 等の隠しファイル（.で始まり、他に.がない）の場合は全選択
                if text.startswith('.') and text.count('.') == 1:
                    editor.selectAll()
                elif name_part:
                    editor.setSelection(0, len(name_part))
                else:
                    editor.selectAll()
            else:
                # フォルダ等の場合は全選択
                editor.selectAll()
        else:
            super().setEditorData(editor, index)


