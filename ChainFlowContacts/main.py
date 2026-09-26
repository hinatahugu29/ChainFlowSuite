import sys
import os
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QTreeView, QSplitter, 
                               QHeaderView, QFileDialog, QMessageBox, QPushButton)
from PySide6.QtGui import QKeySequence, QShortcut

from data_manager import ContactManager
from ui_components import ContactTableModel, ContactDetailForm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow Contacts 📂👤")
        self.resize(950, 600)

        # データ管理クラスの初期化
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")
        self.manager = ContactManager(filepath=db_path)

        self.setup_ui()
        self.setup_shortcuts()
        self.load_styles()

        # 初期データの読み込みと表示
        self.perform_search()

    def setup_ui(self):
        # メニューバーの設定
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル")
        
        new_action = file_menu.addAction("新規連絡先")
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.on_new_contact)
        
        file_menu.addSeparator()
        
        import_action = file_menu.addAction("CSVインポート...")
        import_action.triggered.connect(self.on_import_csv)
        
        export_action = file_menu.addAction("CSVエクスポート...")
        export_action.triggered.connect(self.on_export_csv)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("終了")
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)

        # メインのウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 上部：検索バー ＋ 新規登録ボタン
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("横断検索... (大文字小文字/全半角区別なし、スペースで複数ワードAND検索)")
        self.search_bar.textChanged.connect(self.perform_search)
        top_layout.addWidget(self.search_bar, 1)

        self.btn_new = QPushButton("＋ 新規登録 (Ctrl+N)")
        self.btn_new.setObjectName("newButton")
        self.btn_new.clicked.connect(self.on_new_contact)
        top_layout.addWidget(self.btn_new)

        main_layout.addLayout(top_layout)

        # 中央：左右に分割するスプリッター
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        # 左ペイン：リストエリア
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        self.table_model = ContactTableModel(self)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.table_model)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        
        # ヘッダーのリサイズモード設定
        header = self.tree_view.header()
        header.setStretchLastSection(True)
        
        # リスト選択変更時のシグナル接続
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Eキーでのトグルをハンドルするためにイベントフィルタを設置
        self.tree_view.installEventFilter(self)

        left_layout.addWidget(self.tree_view)
        splitter.addWidget(left_widget)

        # 右ペイン：詳細入力フォームエリア
        self.detail_form = ContactDetailForm()
        self.detail_form.save_requested.connect(self.on_save_contact)
        self.detail_form.delete_requested.connect(self.on_delete_contact)
        self.detail_form.cancel_requested.connect(self.on_cancel_edit)
        
        splitter.addWidget(self.detail_form)

        # 初期スプリッター比率 (リスト 55%, フォーム 45%)
        splitter.setSizes([520, 410])

    def setup_shortcuts(self):
        """キーボードショートカットを登録する。"""
        # Ctrl + N: 新規作成
        QShortcut(QKeySequence("Ctrl+N"), self, self.on_new_contact)
        
        # Ctrl + S: 保存
        QShortcut(QKeySequence("Ctrl+S"), self, self.detail_form.on_save)
        
        # Esc または Ctrl + F: 検索バーにフォーカス
        QShortcut(QKeySequence("Esc"), self, self.focus_search)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)

    def load_styles(self):
        """style.qss を読み込んで適用する。"""
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def eventFilter(self, obj, event):
        """Eキー押下によるカラム表示切り替えをハンドルするイベントフィルタ。"""
        if obj == self.tree_view and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_E:
                self.table_model.toggle_columns()
                # ヘッダーの幅を適切に調整
                self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
                return True
        return super().eventFilter(obj, event)

    def perform_search(self):
        """検索を実行してリストモデルを更新する。"""
        query = self.search_bar.text()
        results = self.manager.search(query)
        self.table_model.set_contacts(results)
        
        # カラム幅の自動調整
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 検索結果の1件目を自動選択（利便性向上のため）
        if results:
            self.tree_view.setCurrentIndex(self.table_model.index(0, 0))
        else:
            self.detail_form.clear_form()

    def on_selection_changed(self, selected, deselected):
        """リスト選択変更時に詳細フォームに情報を展開する。"""
        indexes = selected.indexes()
        if indexes:
            # 0列目のインデックスからUserRoleでデータ取得
            row_idx = indexes[0].row()
            contact = self.table_model.contacts[row_idx]
            self.detail_form.load_contact(contact)
        else:
            self.detail_form.clear_form()

    def on_save_contact(self, data):
        """連絡先の保存処理。"""
        if data.get("id"):
            # 更新
            self.manager.update_contact(data["id"], data)
        else:
            # 新規追加
            new_contact = self.manager.add_contact(data)
            # 作成した連絡先に選択を移動させるために再検索
            self.perform_search()
            # リストから新規追加したアイテムを選択
            for idx, c in enumerate(self.table_model.contacts):
                if c["id"] == new_contact["id"]:
                    self.tree_view.setCurrentIndex(self.table_model.index(idx, 0))
                    break
            return

        self.perform_search()

    def on_delete_contact(self, contact_id):
        """連絡先の削除処理。"""
        self.manager.delete_contact(contact_id)
        self.perform_search()

    def on_cancel_edit(self):
        """編集キャンセル時、選択を維持するか検索にフォーカスを戻す。"""
        self.focus_search()

    def on_import_csv(self):
        """CSVインポート処理を実行。"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "CSVファイルのインポート", "", "CSVファイル (*.csv);;すべてのファイル (*.*)"
        )
        if not filepath:
            return

        # 重複レコード時の処理について確認するダイアログ
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("インポートオプション")
        msg_box.setText("既存の重複データ（同じ会社名・氏名）を検出した際の処理を選択してください。")
        msg_box.setIcon(QMessageBox.Question)
        
        btn_overwrite = msg_box.addButton("上書き更新", QMessageBox.YesRole)
        btn_skip = msg_box.addButton("スキップして新規追加", QMessageBox.NoRole)
        btn_cancel = msg_box.addButton("キャンセル", QMessageBox.RejectRole)
        
        msg_box.exec()
        clicked_btn = msg_box.clickedButton()
        
        if clicked_btn == btn_cancel:
            return
        
        overwrite = (clicked_btn == btn_overwrite)
        
        res = self.manager.import_from_csv(filepath, overwrite_duplicates=overwrite)
        
        if res is None:
            QMessageBox.critical(self, "エラー", "CSVファイルの読み込みに失敗したか、無効な書式です。")
        else:
            success, dup = res
            status_text = "上書き" if overwrite else "スキップ"
            QMessageBox.information(
                self, "完了", 
                f"インポート完了:\n新規追加: {success} 件\n重複 ({status_text}): {dup} 件"
            )
            self.perform_search()

    def on_export_csv(self):
        """CSVエクスポート処理を実行。"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "CSVファイルのエクスポート", "contacts.csv", "CSVファイル (*.csv)"
        )
        if not filepath:
            return
            
        success = self.manager.export_to_csv(filepath)
        if success:
            QMessageBox.information(self, "完了", "CSVファイルのエクスポートが完了しました。")
        else:
            QMessageBox.critical(self, "エラー", "CSVファイルのエクスポートに失敗しました。")

    def on_new_contact(self):
        """新規追加モードへ移行する。"""
        self.tree_view.clearSelection()
        self.detail_form.clear_form()
        self.detail_form.focus_first()

    def focus_search(self):
        """検索バーにフォーカスを当て、テキストを全選択する。"""
        self.search_bar.setFocus()
        self.search_bar.selectAll()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
