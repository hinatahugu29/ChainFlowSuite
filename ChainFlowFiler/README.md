# ChainFlow Filer (v23.10) 📁

**ChainFlow Filer** は、キーボード駆動のワークフローと、大規模ファイルシステムにも耐えうるRust製Native Coreを利用した強力な非同期エンジンを融合させた、プロフェッショナル仕様のファイラーです。

### ✨ 主な機能 / Key Features
- **Slash Menu (`Ctrl+P`)**: 全てのSuiteアプリケーション、内部コマンド、カスタムスクリプトを瞬時に呼び出すコマンドランチャー。
- **Transparent Folder Shortcuts**: フォルダのショートカット(.lnk)を実体フォルダと同等に扱い、ディレクトリ構造に縛られない柔軟なナビゲーションを実現。
- **Asynchronous File Engine**: ネットワークドライブや大規模ディレクトリでもUIをフリーズさせない、完全非同期のファイル列挙。
- **Smart Sorting**: 拡張子や自然順序に基づく高速なインテリジェント並び替え。v23.5でRustネイティブ一括ソートに刷新し、大規模フォルダでも体感速度を大幅に改善。
- **Mark & Process**: キーボードによる直感的なファイル「マーク」機能と、マーク済みファイルに対する一括操作・ドラッグ＆ドロップ。
- **Path History**: 最近使用したフォルダや頻繁に訪れる場所への、シームレスなアクセス。
- **Bucket**: `Alt+Click` でフォルダを横断して項目を集め、サイドバーの BUCKET で内容を確認しながら一括で処理。タブごとに独立し、セッションをまたいで残ります。
- **Undo**: `Ctrl+Z` で移動・リネーム・コピーを取り消し。削除はゴミ箱経由のため OS の「元に戻す」で復元できます。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6 (Qt for Python)
- **Model**: `QFileSystemModel` と連動し、アイコンキャッシュやカスタム描画を備えた最適化済みプロキシ。
- **Core Engine**: Rust (PyO3) によるネイティブ拡張 `chainflow_core.pyd` を搭載。OSレベルのファイル高速ソートを実現。
- **Build System**: Nuitka によるPythonコードのC言語コンパイルで、起動速度と動作パフォーマンスを最大化。
- **Tests**: `py -m unittest discover -s tests -v` で、ファイル操作・削除・Undo・並べ替えの単体テスト(44件)を実行できます。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + P`: スラッシュメニュー（コマンド実行）
- `Space`: クイックプレビュー (テキスト・画像)
- `Enter`: 実行 / フォルダ移動
- `Backspace`: 上の階層へ
- `F5`: 強制リフレッシュ（キャッシュ破棄）
- `Esc`: 選択解除
- `Ctrl + Z`: 直前のファイル操作を取り消し
- `Alt + Click`: Bucket に追加 / 解除
