from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QPushButton, QTreeView, 
                               QFormLayout, QMessageBox, QAbstractItemView)

class ContactTableModel(QAbstractTableModel):
    """連絡先一覧を表示するためのテーブルモデル。"""
    
    # 表示する列（Eキーでトグル可能にする）
    DEFAULT_COLUMNS = ["会社名", "氏名", "電話番号"]
    ALL_COLUMNS = ["会社名", "氏名", "電話番号", "メールアドレス"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.contacts = []
        self.columns = self.DEFAULT_COLUMNS.copy()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.contacts)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self.columns):
                return self.columns[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.contacts)):
            return None

        contact = self.contacts[index.row()]
        col_name = self.columns[index.column()]

        if role == Qt.DisplayRole:
            if col_name == "会社名":
                return contact.get("company_name", "")
            elif col_name == "氏名":
                return contact.get("name", "")
            elif col_name == "電話番号":
                return contact.get("phone_number", "")
            elif col_name == "メールアドレス":
                return contact.get("email_address", "")
        
        elif role == Qt.UserRole:
            # 行全体のデータを返す
            return contact

        return None

    def set_contacts(self, contacts):
        """表示するデータを差し替える。"""
        self.beginResetModel()
        self.contacts = contacts
        self.endResetModel()

    def toggle_columns(self):
        """表示カラムの簡易表示と詳細表示を切り替える（Eキーに対応）。"""
        self.beginResetModel()
        if self.columns == self.DEFAULT_COLUMNS:
            self.columns = self.ALL_COLUMNS.copy()
        else:
            self.columns = self.DEFAULT_COLUMNS.copy()
        self.endResetModel()


class ContactDetailForm(QWidget):
    """連絡先の詳細表示・編集・新規作成を行うフォームペイン。"""
    
    # 状態変更をメイン側に伝えるシグナル
    save_requested = Signal(dict)       # 保存ボタン押下時 (新規または更新用データ)
    delete_requested = Signal(str)      # 削除ボタン押下時 (ID)
    cancel_requested = Signal()        # キャンセル（新規作成中止等）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)

        # フォーム見出し
        self.header_label = QLabel("詳細情報")
        self.header_label.setObjectName("formHeader")
        layout.addWidget(self.header_label)

        # 入力フォームエリア
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(10)

        self.input_company = QLineEdit()
        self.input_company.setPlaceholderText("例: 株式会社チェインフロー")
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("例: 鈴木 太郎")

        # 郵便番号入力欄 (ハイフンを挟んだ2分割)
        self.input_zip1 = QLineEdit()
        self.input_zip1.setMaxLength(3)
        self.input_zip1.setPlaceholderText("123")
        self.input_zip1.setFixedWidth(50)
        self.input_zip1.setAlignment(Qt.AlignCenter)
        self.input_zip1.textChanged.connect(self.on_zip1_changed)

        self.input_zip2 = QLineEdit()
        self.input_zip2.setMaxLength(4)
        self.input_zip2.setPlaceholderText("4567")
        self.input_zip2.setFixedWidth(65)
        self.input_zip2.setAlignment(Qt.AlignCenter)

        zip_layout = QHBoxLayout()
        zip_layout.setSpacing(5)
        zip_layout.addWidget(self.input_zip1)
        zip_lbl = QLabel("-")
        zip_lbl.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        zip_layout.addWidget(zip_lbl)
        zip_layout.addWidget(self.input_zip2)
        zip_layout.addStretch()

        self.input_phone = QLineEdit()
        self.input_phone.setPlaceholderText("例: 03-1234-5678")

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("例: user@example.com")

        self.input_address = QLineEdit()
        self.input_address.setPlaceholderText("例: 東京都千代田区...")

        self.input_memo = QTextEdit()
        self.input_memo.setPlaceholderText("案件詳細や特徴など")

        form_layout.addRow("会社名:", self.input_company)
        form_layout.addRow("氏名:", self.input_name)
        form_layout.addRow("郵便番号:", zip_layout)
        form_layout.addRow("住所:", self.input_address)
        form_layout.addRow("電話番号:", self.input_phone)
        form_layout.addRow("メール:", self.input_email)
        form_layout.addRow("メモ:", self.input_memo)

        layout.addLayout(form_layout)

        # ボタンエリア
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_save = QPushButton("保存 (Ctrl+S)")
        self.btn_save.setObjectName("saveButton")
        self.btn_save.clicked.connect(self.on_save)

        self.btn_delete = QPushButton("削除")
        self.btn_delete.setObjectName("deleteButton")
        self.btn_delete.clicked.connect(self.on_delete)

        self.btn_cancel = QPushButton("キャンセル")
        self.btn_cancel.clicked.connect(self.on_cancel)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_zip1_changed(self, text):
        """郵便番号の前半が3桁になったら自動で後半へフォーカス移動する。"""
        if len(text) == 3:
            self.input_zip2.setFocus()
            self.input_zip2.selectAll()

    def load_contact(self, contact):
        """指定された連絡先データをフォームにセットする。"""
        if contact:
            self.current_id = contact.get("id")
            self.header_label.setText("連絡先の編集")
            self.input_company.setText(contact.get("company_name", ""))
            self.input_name.setText(contact.get("name", ""))
            
            # 郵便番号の読み込み
            postal_code = contact.get("postal_code", "")
            if "-" in postal_code:
                parts = postal_code.split("-", 1)
                self.input_zip1.setText(parts[0])
                self.input_zip2.setText(parts[1])
            else:
                self.input_zip1.setText(postal_code[:3])
                self.input_zip2.setText(postal_code[3:7])

            self.input_phone.setText(contact.get("phone_number", ""))
            self.input_email.setText(contact.get("email_address", ""))
            self.input_address.setText(contact.get("company_address", ""))
            self.input_memo.setPlainText(contact.get("memo", ""))
            self.btn_delete.setEnabled(True)
        else:
            self.clear_form()

    def clear_form(self):
        """フォームをクリアして新規作成状態にする。"""
        self.current_id = None
        self.header_label.setText("新規連絡先")
        self.input_company.clear()
        self.input_name.clear()
        self.input_zip1.clear()
        self.input_zip2.clear()
        self.input_phone.clear()
        self.input_email.clear()
        self.input_address.clear()
        self.input_memo.clear()
        self.btn_delete.setEnabled(False)

    def focus_first(self):
        """最初の入力項目（会社名）にフォーカスを当てる。"""
        self.input_company.setFocus()
        self.input_company.selectAll()

    def on_save(self):
        # 会社名か氏名のいずれかは必須とする
        company = self.input_company.text().strip()
        name = self.input_name.text().strip()
        if not company and not name:
            QMessageBox.warning(self, "エラー", "会社名または氏名の少なくとも一方を入力してください。")
            return

        zip1 = self.input_zip1.text().strip()
        zip2 = self.input_zip2.text().strip()
        postal_code = f"{zip1}-{zip2}" if (zip1 or zip2) else ""

        data = {
            "id": self.current_id,
            "company_name": company,
            "name": name,
            "postal_code": postal_code,
            "phone_number": self.input_phone.text().strip(),
            "email_address": self.input_email.text().strip(),
            "company_address": self.input_address.text().strip(),
            "memo": self.input_memo.toPlainText().strip()
        }
        self.save_requested.emit(data)

    def on_delete(self):
        if self.current_id:
            confirm = QMessageBox.question(
                self, "削除確認", "この連絡先を本当に削除しますか？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.delete_requested.emit(self.current_id)

    def on_cancel(self):
        self.cancel_requested.emit()
