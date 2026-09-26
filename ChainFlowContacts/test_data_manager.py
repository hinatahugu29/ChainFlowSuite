import os
import unittest
from data_manager import ContactManager

class TestContactManager(unittest.TestCase):
    def setUp(self):
        # テスト用のJSONファイルパス
        self.test_file = "test_contacts.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.manager = ContactManager(filepath=self.test_file)

        # テストデータの投入
        self.data1 = {
            "postal_code": "106-6108",
            "company_name": "Google Japan",
            "company_address": "東京都港区六本木6-10-1",
            "phone_number": "03-1111-2222",
            "email_address": "info@google.jp",
            "name": "山田 太郎",
            "memo": "検索エンジン。AI開発パートナー。"
        }
        self.data2 = {
            "postal_code": "530-0001",
            "company_name": "株式会社チェインフロー (ChainFlow Corp)",
            "company_address": "大阪府大阪市北区梅田1-1-1",
            "phone_number": "06-3333-4444",
            "email_address": "support@chainflow.io",
            "name": "鈴木 花子",
            "memo": "ファイラ、ToDoなどの事務効率化ツール開発"
        }

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_and_load(self):
        # 追加
        c1 = self.manager.add_contact(self.data1)
        c2 = self.manager.add_contact(self.data2)
        
        self.assertEqual(len(self.manager.contacts), 2)
        self.assertEqual(self.manager.contacts[0]["name"], "山田 太郎")
        
        # 新しいマネージャーで再読み込み
        new_manager = ContactManager(filepath=self.test_file)
        self.assertEqual(len(new_manager.contacts), 2)
        self.assertEqual(new_manager.contacts[1]["company_name"], "株式会社チェインフロー (ChainFlow Corp)")

    def test_update_and_delete(self):
        c1 = self.manager.add_contact(self.data1)
        contact_id = c1["id"]
        
        # 更新
        updated_data = self.data1.copy()
        updated_data["name"] = "山田 健太"
        self.manager.update_contact(contact_id, updated_data)
        
        self.assertEqual(self.manager.contacts[0]["name"], "山田 健太")
        
        # 削除
        self.manager.delete_contact(contact_id)
        self.assertEqual(len(self.manager.contacts), 0)

    def test_search_normalization_and_multiword(self):
        self.manager.add_contact(self.data1)
        self.manager.add_contact(self.data2)

        # 1. 大文字小文字の無視 (google -> Google Japan)
        res = self.manager.search("google")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "山田 太郎")

        # 2. 全角半角の無視 (ｃｈａｉｎｆｌｏｗ -> ChainFlow)
        res = self.manager.search("ｃｈａｉｎｆｌｏｗ")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "鈴木 花子")

        # 3. 複数ワードAND検索 (大阪 鈴木)
        res = self.manager.search("大阪 鈴木")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["company_name"], "株式会社チェインフロー (ChainFlow Corp)")

        # 4. 横断検索 (電話番号で検索)
        res = self.manager.search("06-3333")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "鈴木 花子")

        # 5. 郵便番号での横断検索
        res = self.manager.search("530-0001")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "鈴木 花子")

        # 6. マッチしない場合
        res = self.manager.search("Yahoo")
        self.assertEqual(len(res), 0)

    def test_csv_export_and_import(self):
        # 1. テストデータを登録
        self.manager.add_contact(self.data1)
        self.manager.add_contact(self.data2)

        csv_file = "test_export.csv"
        
        # 2. エクスポート実行
        self.assertTrue(self.manager.export_to_csv(csv_file))

        # 3. 別のマネージャーでインポート (UTF-8-SIG)
        import_manager = ContactManager(filepath="temp_contacts.json")
        res = import_manager.import_from_csv(csv_file)
        self.assertIsNotNone(res)
        success, dup = res
        self.assertEqual(success, 2)
        self.assertEqual(dup, 0)
        self.assertEqual(len(import_manager.contacts), 2)
        self.assertEqual(import_manager.contacts[0]["name"], "山田 太郎")

        # 4. 重複インポート (スキップの場合)
        res_skip = import_manager.import_from_csv(csv_file, overwrite_duplicates=False)
        self.assertEqual(res_skip, (0, 2))  # 新規追加0, 重複2（スキップ）

        # 5. 重複インポート (上書きの場合)
        import_manager.contacts[0]["memo"] = "一時的なメモの変更"
        res_overwrite = import_manager.import_from_csv(csv_file, overwrite_duplicates=True)
        self.assertEqual(res_overwrite, (0, 2))  # 新規追加0, 重複2（上書き）
        self.assertEqual(import_manager.contacts[0]["memo"], "検索エンジン。AI開発パートナー。")

        # 6. CP932 (Shift-JIS) での読み込み検証
        import csv
        cp932_file = "test_cp932.csv"
        headers = ["会社名", "氏名", "郵便番号", "住所", "電話番号", "メールアドレス", "メモ"]
        with open(cp932_file, "w", encoding="cp932", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow(["日本電気", "NEC 太郎", "108-0014", "東京都港区芝", "03-0000-0000", "nec@nec.com", "電機メーカー"])

        res_cp932 = import_manager.import_from_csv(cp932_file)
        self.assertIsNotNone(res_cp932)
        self.assertEqual(res_cp932[0], 1)
        self.assertEqual(import_manager.contacts[-1]["name"], "NEC 太郎")

        # 後片付け
        for f in [csv_file, cp932_file, "temp_contacts.json"]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    unittest.main()
