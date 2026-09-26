import os
import json
import uuid
import unicodedata

class ContactManager:
    """アドレス帳のデータを管理・保存し、検索を行うクラス。"""

    def __init__(self, filepath="contacts.json"):
        self.filepath = filepath
        self.contacts = []
        self.load_contacts()

    def load_contacts(self):
        """JSONファイルから連絡先データを読み込む。存在しない場合は空リストにする。"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.contacts = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.contacts = []
        else:
            self.contacts = []

    def save_contacts(self):
        """連絡先データをJSONファイルに書き込む。"""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def add_contact(self, data):
        """新しい連絡先を追加する。"""
        new_contact = {
            "id": str(uuid.uuid4()),
            "postal_code": data.get("postal_code", "").strip(),
            "company_name": data.get("company_name", "").strip(),
            "company_address": data.get("company_address", "").strip(),
            "phone_number": data.get("phone_number", "").strip(),
            "email_address": data.get("email_address", "").strip(),
            "name": data.get("name", "").strip(),
            "memo": data.get("memo", "").strip()
        }
        self.contacts.append(new_contact)
        self.save_contacts()
        return new_contact

    def update_contact(self, contact_id, data):
        """指定されたIDの連絡先情報を更新する。"""
        for contact in self.contacts:
            if contact["id"] == contact_id:
                contact["postal_code"] = data.get("postal_code", "").strip()
                contact["company_name"] = data.get("company_name", "").strip()
                contact["company_address"] = data.get("company_address", "").strip()
                contact["phone_number"] = data.get("phone_number", "").strip()
                contact["email_address"] = data.get("email_address", "").strip()
                contact["name"] = data.get("name", "").strip()
                contact["memo"] = data.get("memo", "").strip()
                self.save_contacts()
                return contact
        return None

    def delete_contact(self, contact_id):
        """指定されたIDの連絡先を削除する。"""
        initial_len = len(self.contacts)
        self.contacts = [c for c in self.contacts if c["id"] != contact_id]
        if len(self.contacts) < initial_len:
            self.save_contacts()
            return True
        return False

    def _normalize(self, text):
        """英数字の大文字・小文字、全角・半角を平滑化する。"""
        if not text:
            return ""
        # NFKCで全角英数を半角にし、ひらがな/カタカナなども正規化、lower()で小文字化
        return unicodedata.normalize("NFKC", text).lower()

    def search(self, query):
        """インクリメンタル・複数ワードAND・横断検索を実行する。"""
        normalized_query = self._normalize(query).strip()
        if not normalized_query:
            return self.contacts

        # スペース区切りでキーワードリストを作成 (全角スペースも_normalizeで半角スペースに変換される)
        keywords = normalized_query.split()

        results = []
        for contact in self.contacts:
            # 連絡先の全フィールドを結合して検索対象文字列を作る
            searchable_fields = [
                contact.get("postal_code", ""),
                contact.get("company_name", ""),
                contact.get("company_address", ""),
                contact.get("phone_number", ""),
                contact.get("email_address", ""),
                contact.get("name", ""),
                contact.get("memo", "")
            ]
            combined_text = self._normalize(" ".join(searchable_fields))

            # 全てのキーワードが combined_text に含まれているか判定 (AND検索)
            is_match = True
            for kw in keywords:
                if kw not in combined_text:
                    is_match = False
                    break
            
            if is_match:
                results.append(contact)

        return results

    def export_to_csv(self, filepath):
        """連絡先データをCSVファイル（BOM付きUTF-8）にエクスポートする。"""
        import csv
        headers = ["会社名", "氏名", "郵便番号", "住所", "電話番号", "メールアドレス", "メモ"]
        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for c in self.contacts:
                    writer.writerow([
                        c.get("company_name", ""),
                        c.get("name", ""),
                        c.get("postal_code", ""),
                        c.get("company_address", ""),
                        c.get("phone_number", ""),
                        c.get("email_address", ""),
                        c.get("memo", "")
                    ])
            return True
        except IOError:
            return False

    def import_from_csv(self, filepath, overwrite_duplicates=False):
        """CSVファイルから連絡先データをインポートする。複数エンコーディングの自動判別を行う。
        戻り値: (成功件数, 重複スキップ/上書き件数) のタプル、または失敗時 None
        """
        import csv
        encodings = ["utf-8-sig", "utf-8", "cp932"]
        content = None
        
        for enc in encodings:
            try:
                with open(filepath, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, IOError):
                continue
                
        if content is None:
            return None

        # 文字列として読み込んだ内容をStringIO経由でcsv.readerにかける
        import io
        f_in = io.StringIO(content.strip())
        reader = csv.reader(f_in)
        
        try:
            headers = next(reader)
        except StopIteration:
            return None

        # ヘッダー項目からインデックスをマップ
        header_map = {}
        for idx, h in enumerate(headers):
            header_map[h.strip()] = idx

        # 最低限、会社名か氏名があればインポートを継続する
        if "会社名" not in header_map and "氏名" not in header_map:
            return None

        success_count = 0
        duplicate_count = 0

        for row in reader:
            if not row:
                continue
            
            # 各項目の値を取得
            comp = row[header_map["会社名"]].strip() if "会社名" in header_map and header_map["会社名"] < len(row) else ""
            name = row[header_map["氏名"]].strip() if "氏名" in header_map and header_map["氏名"] < len(row) else ""
            
            if not comp and not name:
                continue

            post = row[header_map["郵便番号"]].strip() if "郵便番号" in header_map and header_map["郵便番号"] < len(row) else ""
            addr = row[header_map["住所"]].strip() if "住所" in header_map and header_map["住所"] < len(row) else ""
            phone = row[header_map["電話番号"]].strip() if "電話番号" in header_map and header_map["電話番号"] < len(row) else ""
            email = row[header_map["メールアドレス"]].strip() if "メールアドレス" in header_map and header_map["メールアドレス"] < len(row) else ""
            memo = row[header_map["メモ"]] if "メモ" in header_map and header_map["メモ"] < len(row) else ""

            # 重複チェック (会社名 ＋ 氏名の一致)
            existing_contact = None
            for c in self.contacts:
                if c.get("company_name", "") == comp and c.get("name", "") == name:
                    existing_contact = c
                    break

            data = {
                "company_name": comp,
                "name": name,
                "postal_code": post,
                "company_address": addr,
                "phone_number": phone,
                "email_address": email,
                "memo": memo
            }

            if existing_contact:
                if overwrite_duplicates:
                    self.update_contact(existing_contact["id"], data)
                    duplicate_count += 1
                else:
                    duplicate_count += 1
                    continue
            else:
                self.add_contact(data)
                success_count += 1

        return success_count, duplicate_count
