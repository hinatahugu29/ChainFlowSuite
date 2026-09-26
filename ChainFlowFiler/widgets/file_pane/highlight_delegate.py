"""
v14.0 Ancestral Highlight用デリゲート
v14.1 Refactoring: file_pane.py から分離
v14.2 Fix: same_path を使用した大文字小文字を区別しない比較
"""
import os
from PySide6.QtWidgets import QStyledItemDelegate, QApplication
from PySide6.QtGui import QColor

from core import same_path


class EditingDelegate(QStyledItemDelegate):
    """v23.8: リネーム時のIME対応だけを担当する軽量デリゲート。

    paint() を **あえて override しない** ことが唯一にして最大の役割。
    QStyledItemDelegate.paint を Python 側で上書きすると、可視セル1つごとに
    Python↔C++ の往復が発生し、ハイライトが無効なときでもその往復代だけを
    払い続けることになる（32ビュー構成のタブ切替で計測した際、描画時間の
    約半分がこの空振り分だった）。
    通常時はこのクラスを、ハイライト表示中のみ HighlightDelegate を使う。
    """

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
                # v23.4 Fix: IME変換中でなければ、DelegateにEnterを渡してリネームを確定させる
                # 未確定の文字列（PreeditText）があるか確認
                if hasattr(editor, 'inputMethodQuery'):
                    preedit = editor.inputMethodQuery(Qt.ImPreeditText)
                    if not preedit:
                        # 変換中ではない -> 通常の確定（Commit）として扱い、Delegateの標準処理に任せる
                        return False

                # IME変換中の場合は、エディタにイベントを渡して内部確定のみ行わせる
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


class HighlightDelegate(EditingDelegate):
    """Ancestral Highlight用デリゲート - 選択パスの祖先/子孫をハイライト表示

    v23.8: 編集まわりは EditingDelegate に移し、こちらは paint() の上書きに専念する。
    ハイライトが有効な間だけビューに差し込まれる。
    """
    
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
