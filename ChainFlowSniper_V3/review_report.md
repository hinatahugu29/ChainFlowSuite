# Sniper Research Shell ― 俯瞰レビューレポート

全ソースファイルを精読し、**バグ（潜在的な障害）**、**堅牢性・安全性**、**パフォーマンス**、**UX（使い勝手）**、**アーキテクチャ（設計）** の5つの観点から課題と改善案をまとめました。

---

## 🔴 優先度：高（潜在的なバグ・データ損失リスク）

### 1. 【バグ】クリップボード監視のスレッド安全性
- **箇所**: [main_window.py L240-248](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L240-L248)
- **問題**: [on_extraction_clicked](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#240-249) で `_block_clipboard_signal = True` → クリップボード操作 → `False` を「同期的に」行っていますが、Qt のシグナル/スロットはイベントループ経由のため、`dataChanged` シグナルが`False`に戻した**後**に到着する可能性があります。結果として、自分自身のコピーが「外部コピー」として二重登録される intermittent（断続的）バグが潜んでいます。
- **改善案**: `QTimer.singleShot(100, ...)` で遅延解除するか、直前のクリップボードテキストを変数に保持して比較する方式へ変更。

### 2. 【バグ】Detach時のデータ消失リスク
- **箇所**: [main_window.py L315-331](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L315-L331)
- **問題**: [detach_list()](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#315-332) で `self.extraction_list.clear()` を呼んでいますが、[ClipboardPopup](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#33-83) の [closeEvent](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#77-83) が正常に発火しなかった場合（例: アプリ強制終了、ウィンドウマネージャによる kill）、 [attach_list](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#333-341) が呼ばれず、**蓄積した全抽出データが失われます**。
- **改善案**: デタッチ時にテキストデータを `self._detached_backup` のようなリストに保持しておき、[attach_list](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#333-341) が呼ばれなかった場合にもメインウィンドウの [closeEvent](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#77-83) で復旧できるようにする。

### 3. 【バグ】sniper.js のクリックイベントにおけるモード判定漏れ
- **箇所**: [sniper.js L329-330](file:///e:/CODE/Antigravity/web-parts/resources/sniper.js#L329-L330)
- **問題**: [click](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#53-56) イベントのガード条件は `if (!isSniperMode && !isBatchMode) return;` になっていますが、**Aキーのダイレクトモードでも `isStructMode === false` のまま**テーブル/リストの `.closest('table, ul, ol')` を探しに行き、見つかるとMarkdown化して返してしまいます。Aキーは「単一要素」の意図なのに、テーブル内セルをクリックするとテーブル全体が返る。
- **改善案**: `isStructMode` が `false` の場合は `.closest()` による構造探索をスキップし、常に `targetElement.innerText` を返すべき。

### 4. 【バグ】履歴リストの無限肥大（メモリリーク相当）
- **箇所**: [main_window.py L179-194](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L179-L194)
- **問題**: 閲覧履歴は `QListWidget` に無限に追加されますが、上限がありません。長時間のリサーチセッション（数百ページ巡回）ではメモリ消費が増大し、GUIの描画負荷も増します。
- **改善案**: 最大保持件数（例: 200件）を設定し、超過分は先頭から自動削除する。

---

## 🟡 優先度：中（堅牢性・安全性・信頼性）

### 5. 【堅牢性】`os.path.dirname(__file__)` への依存（凍結/パッケージ化に非互換）
- **箇所**: [main_window.py L23, L155, L262](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L23), [storage.py L10](file:///e:/CODE/Antigravity/web-parts/core/storage.py#L10)
- **問題**: `__file__` ベースのパス解決が各ファイルに散在しています。PyInstaller 等でのパッケージ化やインストール先変更に脆弱です。
- **改善案**: プロジェクトルートを一箇所で定義（例: `config.py` に `PROJECT_ROOT`）し、全ファイルがそこを参照する形に統一。

### 6. 【堅牢性】[favorites.json](file:///e:/CODE/Antigravity/web-parts/favorites.json) の書き込み中クラッシュによるファイル破損
- **箇所**: [storage.py L24-31](file:///e:/CODE/Antigravity/web-parts/core/storage.py#L24-L31)
- **問題**: `json.dump` で直接ファイルに書き込んでおり、書き込み中のクラッシュや電源断でJSONが壊れる（0バイトや途中切れ）可能性があります。
- **改善案**: 一時ファイル（`.favorites.json.tmp`）に書き出してから、`os.replace()` でアトミックに差し替える方式にする。

### 7. 【安全性】[load_favorites](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#161-168) のJSONスキーマ非検証
- **箇所**: [main_window.py L161-167](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L161-L167)
- **問題**: [favorites.json](file:///e:/CODE/Antigravity/web-parts/favorites.json) のデータ構造が壊れていた場合（[title](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#179-195) や [url](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#175-178) キーが欠落）、`KeyError` でクラッシュします。[storage.py](file:///e:/CODE/Antigravity/web-parts/core/storage.py) 側では `try/except` があるものの、読み込んだデータをそのまま辞書アクセスしています。
- **改善案**: `fav.get("title", "")` / `fav.get("url", "")` のように安全にアクセスするか、バリデーション層を挟む。

### 8. 【安全性】sniper.js の XSS（クロスサイトスクリプティング）リスク
- **箇所**: [sniper.js L129, L144](file:///e:/CODE/Antigravity/web-parts/resources/sniper.js#L129-L144)
- **問題**: `indicator.innerHTML` にユーザーがホバーした要素の `tagName` やバッチ収集したテキストを直接 HTML として挿入しています。悪意あるサイトが `<img onerror=alert(1)>` のようなテキストを含む要素を持っていた場合、スナイパーのインジケータ経由でスクリプトが実行される恐れがあります。
- **改善案**: `textContent` で安全にテキスト挿入するか、挿入前にHTMLエスケープ処理を行う。

---

## 🟢 優先度：低〜中（パフォーマンス・UX・設計改善）

### 9. 【パフォーマンス】[updateHighlight()](file:///e:/CODE/Antigravity/web-parts/resources/sniper.js#217-238) の全要素走査
- **箇所**: [sniper.js L218-220](file:///e:/CODE/Antigravity/web-parts/resources/sniper.js#L218-L220)
- **問題**: ハイライト更新時に毎回 `document.querySelectorAll(...)` でページ全体を走査しています。複雑なページ（DOM要素が数千〜数万ノード）ではパフォーマンスに影響し得ます。
- **改善案**: 前回ハイライトした要素を変数に保持し、その要素のみクラスを削除する方式に変更。

### 10. 【UX】抽出リストの「クリア」機能がない
- **問題**: 右ペインの抽出リストを全消去する手段が UI 上にありません。長時間のリサーチで数十〜数百件溜まった後、新しいセッションを始めたい場合にリセットできません。
- **改善案**: `EXTRACTIONS` ヘッダー横に「🗑」ボタンを追加し、確認ダイアログ付きで全消去する機能を追加。

### 11. 【UX】お気に入り重複登録の防止がない
- **箇所**: [main_window.py L202-213](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L202-L213)
- **問題**: 同じページで「+」を何度も押すと、同一URLが何個でも重複登録されてしまいます。
- **改善案**: 追加前に既存リストのURLと照合して重複を弾く。

### 12. 【UX】URL バーでの検索エンジン連携がない
- **箇所**: [main_window.py L169-173](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#L169-L173)
- **問題**: URL バーに `http` で始まらないテキスト（例: `Python リスト操作`）を入力すると、`https://Python リスト操作` という無効なURLに遷移してしまいます。
- **改善案**: ドットを含まない入力の場合は Google 検索 (`https://www.google.com/search?q=...`) にリダイレクトする。

### 13. 【設計】[bridge.py](file:///e:/CODE/Antigravity/web-parts/core/bridge.py) の [update_history_title](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#179-195) が Dead Code の可能性
- **箇所**: [bridge.py L19-23](file:///e:/CODE/Antigravity/web-parts/core/bridge.py#L19-L23)
- **問題**: `SniperBridge.update_history_title` はJS側から呼ばれる想定ですが、[sniper.js](file:///e:/CODE/Antigravity/web-parts/resources/sniper.js) 内にこの関数を呼び出すコードが見当たりません。現状では死んだコードです。
- **改善案**: 不要であれば削除し、コードの見通しを良くする。必要であればJS側に呼び出しを追加する。

### 14. 【設計】[ClipboardPopup](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#33-83) にテーマ（QSS）が適用されない
- **箇所**: [widgets.py L36-51](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#L36-L51)
- **問題**: [ClipboardPopup](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#33-83) は `QDialog` で、[MainWindow](file:///e:/CODE/Antigravity/web-parts/core/main_window.py#14-341) の子として生成されますが、`QDialog` には親の `setStyleSheet` が完全には継承されない場合があります。ポップアップのリストだけデフォルトのOS白背景になる可能性があります。
- **改善案**: ポップアップの [__init__](file:///e:/CODE/Antigravity/web-parts/core/widgets.py#5-20) 内で明示的に `self.setStyleSheet(parent.styleSheet())` を呼ぶか、`QApplication` レベルでテーマを適用する。

### 15. 【設計】[walkthrough.md](file:///e:/CODE/Antigravity/web-parts/walkthrough.md) が最新の分割アーキテクチャを反映していない
- **箇所**: [walkthrough.md L7](file:///e:/CODE/Antigravity/web-parts/walkthrough.md#L7)
- **問題**: ファイルリンクが旧構成の [main.py](file:///e:/CODE/Antigravity/web-parts/main.py) を指しており、「Phase 8」の記述のまま古い情報が残っています。[README.md](file:///e:/CODE/Antigravity/web-parts/README.md) が正式マニュアルとして作成されたため、このファイルの役割が曖昧です。
- **改善案**: [walkthrough.md](file:///e:/CODE/Antigravity/web-parts/walkthrough.md) を削除するか、README.md に統合済みであることを明記してリダイレクトする。

---

## 📊 総合評価

| 観点 | 評価 | コメント |
| :--- | :---: | :--- |
| **機能完成度** | ⭐⭐⭐⭐ | A/Z/Cキーの操作体系は非常に洗練されており、リサーチツールとして実用レベル。 |
| **コード構造** | ⭐⭐⭐⭐ | Phase 9 の分割により可読性・拡張性が大幅に向上。各モジュールの責務が明確。 |
| **堅牢性** | ⭐⭐⭐ | データ永続化周りに「最悪のケース」への備えが不足。上記 #2, #6, #7 が主な改善対象。 |
| **セキュリティ** | ⭐⭐⭐ | innerHTML による XSS リスク (#8) は悪意あるサイトでの利用時に顕在化する可能性あり。 |
| **UX / DX** | ⭐⭐⭐⭐ | 抽出操作は直感的。クリアボタンや検索エンジン連携など「あると嬉しい」改善が残る。 |
