# ChainFlow Tool (Editor/Viewer) 🛠️📖

**ChainFlow Tool** は、Suite全体の基盤となる共通機能を備え、特に Markdown と HTML の「閲覧」と「簡易編集」に特化したインテリジェンスな汎用 hub です。

### ✨ 主な機能 / Key Features
- **Dual-Role Engine**:
    - **Editor Mode**: Markdown2 ベースの高速な Markdown 編集とリアルタイムプレビュー。
    - **Viewer Mode**: `QWebEngineView` (Chromiumベース) による、HTML、PDF、および高度なWebコンテンツの忠実な再現。
- **Integrated Logic**: `Ctrl+P` (Slash Menu) を通じて Suite の他ツールと密接に連携。
- **Snippet & Help**: よく使う Markdown 構文やショートカットをサイドパネルに常備。ダブルクリックで即座にエディタへ挿入可能。
- **Professional PDF Export**: 印刷用 CSS を動的に適用し、Web ページや Markdown を美しい等幅 PDF として出力。
- **Geometry Memory**: Filer から呼び出された際のウィンドウ位置やサイズをスマートに管理。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6 + QtWebEngine (+ QtPrintSupport)
- **Rendering**: Chromium エンジンによる最高峰の Web 互換性。
- **Stability**: Windows AppUserModelID 搭載により、Filer と同じブランドアイコンをタスクバーに正しく表示。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + S`: 保存
- `Ctrl + P`: スラッシュメニュー（ツール連携 / スニペット）
- `Ctrl + E`: PDF エクスポート
- `F1`: ヘルプパネルの表示 / 非表示
