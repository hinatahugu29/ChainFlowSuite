# ChainFlow Filer (v21) 📁

**ChainFlow Filer** は、キーボード駆動のワークフローと、大規模ファイルシステムにも耐えうる強力な非同期エンジンを融合させた、プロフェッショナル仕様のファイラーです。

### ✨ 主な機能 / Key Features
- **Slash Menu (`Ctrl+P`)**: 全てのSuiteアプリケーション、内部コマンド、カスタムスクリプトを瞬時に呼び出すコマンドランチャー。
- **Asynchronous File Engine**: ネットワークドライブや大規模ディレクトリでもUIをフリーズさせない、完全非同期のファイル列挙。
- **Smart Sorting**: ファイルとフォルダを区別せず混在させた独自のソートや、自然順序によるインテリジェンスな並び替え。
- **Mark & Process**: キーボードによる直感的なファイル「マーク」機能と、マーク済みファイルに対する一括操作。
- **Path History**: 最近使用したフォルダや頻繁に訪れる場所への、シームレスなアクセス。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6 (Qt for Python)
- **Model**: 高度に最適化された `QFileSystemModel` カスタムプロキシ。
- **IPC**: 他の ChainFlow ツールへの引数受け渡しとプロセス管理。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + P`: スラッシュメニュー（コマンド実行）
- `Enter`: 実行 / フォルダ移動
- `Backspace`: 上の階層へ
- `F5`: 強制リフレッシュ（キャッシュ破棄）
- `Esc`: 選択解除
