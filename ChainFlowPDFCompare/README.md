# ChainFlow PDF Compare 📄⚖️

**ChainFlow PDF Compare** は、二つ以上のドキュメント間の微細な差異を逃さない、厳密な校正と検証のための比較ツールです。

### ✨ 主な機能 / Key Features
- **Multi-View Engine**: 1画面から最大4画面まで、用途に合わせたレイアウト構成を瞬時に切り替え（1, 2H, 2V, 4 Views）。
- **Global Sync Scrolling**: 全てのビュー（あるいは特定のグループ）を完全に同期してスクロール。異なるバージョンの資料を同一箇所で精密に比較。
- **ZEN Mode (F11)**: UIツールバーやサイドバーを全て隠し、広大な画面全体を比較作業のみに捧げる全画面集中モード。
- **Pop-out Workspace**: 特定のドキュメントを別ウィンドウとして独立させ、マルチディスプレイ環境での比較を強化。
- **Diff Detection**: テキストレベルだけでなく、レンダリングされた結果の微細なピクセル差異も視覚的に補足。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6
- **UI Manager**: `MultiViewContainer` による動的なレイアウト管理と、プロセス間同期に近いビュー間同期ロジック。
- **Compatibility**: Windows 11 のウィンドウ整理機能と調和するモダンなアーキテクチャ。

### ⌨️ 操作方法 / Shortcuts
- `F11`: ZEN モード（全画面）
- `1 / 2 / 4`: ビュー分割数の切り替え
- `S`: 同期スクロールの ON / OFF
- `Delete`: アクティブなビューのPDFをクリア
