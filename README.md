# ChainFlow Suite 📂✨

**ChainFlow Suite** は、Windows環境でのワークフローを極限まで効率化するために設計された、プロフェッショナル向けツール群のコレクションです。
個別のツールが独立して動作しつつも、共通の設計思想（キーボード主体、ダークテーマ、高速レスポンス）と、統一されたブランドアイデンティティ（AppUserModelIDによるタスクバー統合）により、シームレスな体験を提供します。

---

## 🚀 収録アプリケーション / Included Applications

### 📁 ChainFlow Filer (v21)
**超高速・キーボード主体の次世代ファイラー**
- **Slash Menu (`Ctrl+P`)**: 全てのSuiteツールやカスタムプラグインを瞬時に呼び出し。
- **Asynchronous Engine**: 数十万ファイルもフリーズさせない完全非同期スキャン。
- **Smart Logic**: フォルダとファイルを混在させてソートする独自のインテリジェンス。

### ✍️ ChainFlow Writer (v6)
**DTPレベルのレイアウト精度を持つ究極のMarkdownエディタ**
- **Beyond Typora**: リアルタイム改ページレンダリングにより、編集画面がそのままPDFの完成図に。
- **Stamp Syntax**: `<stamp>` 構文による絶対座標指定で、自由自在なレイアウト。
- **High Fidelity**: 1:1の再現性を誇るPDF出力エンジンを搭載。

### 🎨 ChainFlow Designer
**直感的な操作とインテリジェンスが融合したDTPエディタ**
- **Smart Snap**: オブジェクト間の端点、中心点、中心線を検知して吸着。
- **Pro Table**: セル単位のドラッグリサイズや構造変更（Excel風操作）に対応。
- **Advanced Export**: DPI指定可能な画像出力や、グリッド込のPDF出力。

### 🔍 ChainFlow Search
**「探す」を「見つける」に変えるハイブリッド検索エンジン**
- **Scan & Stream**: 高速スキャンとリアルタイムなメモリ内フィルタリングの二段構え。
- **Advanced Query**: AND/OR/NOT/- 記法をフルサポートした高度な絞り込み。
- **History & Tabs**: 検索履歴からの即時復旧と、複数タブによる並行検索。

### 📝 ChainFlow ToDo
**思考を妨げないミニマルなタスク管理**
- **MD Integration**: 全てのタスクをMarkdown形式で瞬時にバックアップ・共有。
- **Progress Tracking**: カテゴリごとの進捗率をリアルタイムに可視化。

### 📄 ChainFlow PDF Studio & Compare
**PDFを「読む」から「解析・検証する」へ**
- **Sync View (Studio)**: サムネイル、全ページ、プロパティを同期表示する3ペイン構成。
- **Multi-View Diff (Compare)**: 最大4画面の同期スクロール比較とZENモード。

---

## 🛠️ 技術スタック / Technical Stack
- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
- **PDF Engine**: PyMuPDF, QtWebEngine
- **Graphics**: PIL (Pillow), QtGraphicsScene
- **Distribution**: PyInstaller (Windows AppUserModelID supported)

## 📦 インストール / Installation
1. `git clone https://github.com/hinatahugu29/ChainFlowSuite.git`
2. 各ディレクトリ内の `main.py` を実行するか、ビルド済みのEXEを使用してください。
3. `py -m pip install -r requirements.txt` で必要な依存関係を解消してください。

## 📄 ライセンス / License
© 2026 hinatahugu29. All rights reserved. 個人利用および開発コミュニティへの貢献を歓迎します。
