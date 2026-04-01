# ChainFlow Search 🔍

**ChainFlow Search** は、爆速の初動と、思考を止めないインテリジェンスな絞り込みを両立させた、プロフェッショナル向けファイル検索エンジンです。

### ✨ 主な機能 / Key Features
- **Hybrid Engine**: `os.scandir` を活用した超高速な「非同期スキャン」と、確定した結果に対する瞬時な「メモリ内ストリームフィルタリング」を統合。
- **Advanced Query Syntax**: Space (AND), `|` (OR), `-` (NOT), `*` (Wildcard) を組み合わせた、正規表現に迫る高度なクエリ発行が可能。
- **Multi-Tab Interface**: 異なるディレクトリや条件を複数のタブで並行して検索。タブの複製やパスの引き継ぎもサポート。
- **Smart History**: ディレクトリの訪問履歴を自動追跡。Filerのお気に入りとも連動し、よく使う場所へ即座に移動。
- **External Drag & Drop**: 検索結果をエクスプローラーや他のアプリケーションへ直接ドラッグ、あるいはコピー(`Ctrl+C`)して連携。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6
- **Architecture**: 双方向通信シグナルを用いた完全非同期ワーカースレッド。
- **Optimization**: バッチ通信によるUIへの段階的反映で、数万件のヒット時も操作性を維持。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + T`: 新しい検索タブ
- `Enter`: ファイルを開く / `Ctrl + C`: ファイルをコピー
- `Ctrl + F`: 入力エリアへフォーカス
- `Tab`: タブ間の移動
- `/`: クエリのクリア
