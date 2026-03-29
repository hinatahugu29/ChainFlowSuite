# ChainFlow Filer 開発における教訓と注意点

このドキュメントは、ChainFlow Filerの開発過程で得られた教訓、遭遇したバグ、および今後の開発で注意すべきポイントをまとめたものです。

---

## 1. Qt/PySide6 イベント処理の罠

### 1.1 Enterキーの二重発火問題
**症状:** F2でリネームモードに入り、Enterで確定すると「ファイルが存在しない」エラー。

**原因:** `eventFilter` でEnterキーを検出し「ダブルクリック（ファイルを開く）」を発火させていたが、リネーム中でもこれが実行されてしまった。リネーム確定前の「古いファイル名」で開こうとするためエラー。

**解決策:**
```python
if view.state() == QAbstractItemView.EditingState:
    return False  # リネーム中はショートカット処理をスキップ
```

**教訓:** ショートカットキーを実装する際は、**編集状態（EditingState）を必ずチェック**すること。

---

### 1.2 ダークタイトルバーの適用タイミング
**症状:** `DwmSetWindowAttribute` でダークモードを設定しても、タイトルバーが白いままになることがある。

**原因:** `__init__` 内で呼んでも、ウィンドウがまだ表示されていない段階ではOSが無視する場合がある。

**解決策:**
```python
def showEvent(self, event):
    apply_dark_title_bar(self)  # 表示時に再適用
    super().showEvent(event)
```

**教訓:** OS依存のAPI呼び出しは、**ウィンドウが実際に表示されるタイミング**で行うのが確実。

---

### 1.3 フォーカス管理とポップアップ
**症状:** `Ctrl+P` でSlash Menuを開いても、キーボード入力が効かない。

**原因:** `Qt.WA_ShowWithoutActivating` 属性や、`setFocus()` のタイミングが早すぎた。

**解決策:**
```python
self.show()
self.activateWindow()  # 明示的にウィンドウをアクティブ化
self.raise_()
self.search_box.setFocus()
```

**教訓:** ポップアップウィンドウでキーボード入力を受け付けたい場合は、`activateWindow()` + `raise_()` を明示的に呼ぶ。

---

## 2. ファイルシステム操作の注意点

### 2.1 パス比較は正規化してから
**症状:** 同じフォルダなのに「異なる」と判定される。

**原因:** `C:\Folder` vs `C:/Folder` vs `c:\folder` など、表記揺れがある。

**解決策:**
```python
def same_path(p1, p2):
    return os.path.normcase(os.path.normpath(p1)) == os.path.normcase(os.path.normpath(p2))
```

**教訓:** ファイルパスの比較は**必ず正規化**してから行う。

---

### 2.2 上書き防止のファイル名生成
**症状:** 画像処理で出力ファイルが既存ファイルを上書きしてしまう。

**解決策:**
```python
def get_unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"
```

**教訓:** ファイル保存時は**既存ファイルの有無を確認**し、必要に応じてナンバリングする。

---

## 3. アーキテクチャ設計の教訓

### 3.1 重量級コンポーネントの分離
**問題:** QtWebEngineを含むとアプリサイズが100MB超に。

**解決策:** V19でスイート構成に分離。コアFilerは軽量に保ち、リッチ機能は外部ツールとして提供。

**教訓:**
- 起動頻度の高いコアアプリは**軽量に保つ**
- 重量級機能は**オプショナルな外部ツール**として分離
- プラグインシステム（`tools.json`）で柔軟に連携

---

### 3.2 ビルド時のリソース同梱漏れ
**症状:** 開発環境では動くが、ビルド後に `tools.json` が見つからない。

**原因:** PyInstallerの `datas` に `tools.json` を含めていなかった。

**解決策:**
```python
# .spec ファイル
datas=[('tools.json', '.'), ('app_icon.ico', '.')]
```

**教訓:** ビルド後は**実際のexeを実行してテスト**する。開発環境と本番環境の差異に注意。

---

### 3.3 子プロセスの終了管理
**症状:** メインアプリを閉じても、外部ツールが残り続ける。

**解決策:**
```python
def closeEvent(self, event):
    self.plugin_manager.terminate_all()  # 全子プロセスを終了
    super().closeEvent(event)
```

**教訓:** 外部プロセスを起動するアプリは、**終了時の後始末**を必ず実装する。

---

## 4. UI/UX の落とし穴

### 4.1 ダークテーマでのリネーム入力欄
**症状:** リネーム時、入力欄の背景と文字が同系色で見づらい。

**解決策:**
```css
QTreeView QLineEdit {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #007acc;
}
```

**教訓:** ダークテーマでは**編集状態の視認性**を特に意識する。

---

### 4.2 動的なタブ名更新のタイミング
**要件:** アドレスバーのようにリアルタイムでタブ名を更新したい。

**解決策:** `set_active_pane`（ホバー時に呼ばれる）内でタブ名を更新。

**教訓:** 「いつ更新されるべきか」を明確にし、**そのイベントフックに処理を入れる**。

---

## 5. デバッグのコツ

### 5.1 ログ出力の活用
```python
from core import logger
logger.log_debug(f"[Highlight] Request: {target_path}")
```

複雑なフロー（親子ペイン間の連携など）では、**各段階でログを出力**して動作を追跡する。

### 5.2 段階的な検証
大きな変更を一度に行わず、**小さな単位でテスト**する。特にイベント処理は予期せぬ副作用が起きやすい。

---

## 6. 今後の改善候補

- [ ] セッション復元時のパス存在確認（削除済みフォルダへの対応）
- [ ] Undo/Redo機能の実装
- [ ] 非同期ファイル操作によるUI応答性向上
- [ ] 設定ファイル（テーマ、ショートカットのカスタマイズ）

---

*最終更新: 2026-02-03*
