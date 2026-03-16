# Mermaid.js バージョンアップ（v9 -> v11）改訂範囲の検討

Mermaid.js を現在の v9.4.3 から最新の v11.x へアップグレードする場合の、影響範囲と必要な作業について整理します。

## 1. 直接的な修正箇所（必須）

### [preview_pane.py](file:///g:/CODE/Antigravity/Py_FILE/ChainFlowWriter_v4/app/widgets/preview_pane.py)
- **CDNリンクの更新**: `_load_shell` メソッド内の `<script>` タグのURLを v11 のものに書き換え。
- **初期化処理の確認**: `mermaid.initialize` のオプション（`theme`, `securityLevel` 等）が v11 の仕様に合致しているか確認。

## 2. 実装への影響（要確認）

### レンダリング・ロジック
- **初期化タイミング**: v10 以降では `mermaid.init` よりも `mermaid.run` (Async) への移行が推奨されています。
- **例外処理の挙動**: バージョン移行により、描画エラーが発生した際の例外の投げ方や、エラー表示のDOM構造が変わる可能性があります。

## 3. 検証・品質保証

### 既存ドキュメントの表示確認
- これまで作成した Mermaid 図（フローチャート、シーケンス図等）が、新しいエンジンで正しく表示されるかどうかの目視。

### PDF 出力への影響
- `export_pdf` メソッド内で行っている「ページクローン時のMermaid要素の扱い」に変化がないか（特にフォントやスケールの計算）。

---
> [!IMPORTANT]
> Mermaid v10/v11 は内部エンジンが ESM (JavaScript Modules) ベースに大きく刷新されているため、単純な `<script>` タグの差し替えだけでは読み込み順や非同期処理の競合が発生するリスクがあります。実装時は一時的な HTML ファイルでの動作検証を強く推奨します。
