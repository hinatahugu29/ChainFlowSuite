# ChainFlow Suite 📂✨

**ChainFlow Suite** は、Windows環境でのワークフローを極限まで効率化するために設計された、プロフェッショナル向けツール群のコレクションです。
個別のツールが独立して動作しつつも、共通の設計思想（キーボード主体、ダークテーマ、高速レスポンス）と、統一されたブランドアイデンティティ（AppUserModelIDによるタスクバー統合）により、シームレスな体験を提供します。

---

## 🚀 収録アプリケーション / Included Applications

### 📁 ChainFlow Filer (v22)
**超高速・I/O負荷ゼロの次世代ファイラー**
- **Slash Menu (`Ctrl+P`)**: 全てのSuiteツールや最新の Sniper V3 / Writer v9 などを瞬時に呼び出し。
- **I/O-Zero Engine**: インメモリ・アイコン生成技術により、ディスク負荷を最小化した極限の高速表示。
- **Global Model**: スイート全域で共有される高速ファイルシステム・アーキテクチャ。

### ✍️ ChainFlow Writer (v9)
**IDE級の視認性とDTPの精度を兼ね備えたドキュメントエンジン**
- **IDE-Style Highlight**: 複雑なHTML/CSSノイズを背景に沈めつつ、意味的に色分けする高度なシンタックスハイライト。
- **Beyond Typora**: リアルタイム改ページレンダリングにより、編集画面がそのままPDFの完成図に。
- **Stamp Syntax**: `<stamp>` 構文による絶対座標指定で、公的な書類レイアウトを自由自在に。
- **High Fidelity**: 1:1の再現性を誇るPDF出力エンジンを搭載。

### 🔍 ChainFlow Sniper (V3)
**情報の「構造」と「見た目」を射抜くリサーチ・ステーション**
- **4-Quadrant Extraction**: A(Text), Z(Markdown), S(Style), D(DOM) の4つのモードで、あらゆるWeb情報を資産化。
- **Pure DOM Snipe (D-Mode)**: 装飾を排除し、AI連携やWriterテーマに最適化された純粋構造のみを抽出。
- **Rich Style Restorer**: CSS GridやFilterまでをもポータブルに再構築し、A4紙面にWebの表現力を持ち込む。
- **Deep Penetration**: iFrameやShadow DOMの内部さえも透過してスナイプ可能。

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
