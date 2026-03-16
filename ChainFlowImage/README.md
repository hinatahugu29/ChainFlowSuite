# ChainFlow Image Tool 🖼️⚡

**ChainFlow Image Tool** は、大量の画像に対する一括リサイズや形式変換を爆速で処理する、パフォーマンス重視のユーティリティです。

### ✨ 主な機能 / Key Features
- **Multi-threaded Processing**: `ThreadPoolExecutor` を活用し、CPUコア数を最大限に引き出した並列処理により、数千枚の画像も一瞬で完了。
- **Drag & Drop Workflow**: エクスプローラーや Filer から直接画像をドロップし、変換設定を選んで実行するだけの極めてシンプルなフロー。
- **Independant Resize Modes**: 指定ピクセルへの幅固定、またはパーセント指定による比率維持リサイズをサポート。
- **Smart Format Conversion**: JPG, PNG, WEBP への相互変換。JPEG変換時の透過背景の白埋め処理などを自動で実行。
- **Processed Logging**: 各ファイルの結果（成功・失敗・出力先）をリアルタイムにログ表示し、完了時に一括通知。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6
- **Processing Core**: PIL (Pillow) による高品質・高速な画像エンコード/デコード。
- **Efficiency**: 非同期 GUI アーキテクチャにより、数百枚の処理中もメインウィンドウが応答を維持。

### ⌨️ 操作方法 / Shortcuts
- `Delete`: リストから選択項目を削除
- `Esc`: 処理のキャンセル
- `Enter`: 処理の開始（ボタンにフォーカスがある場合）
