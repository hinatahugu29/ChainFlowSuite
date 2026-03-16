# ChainFlow Writer (v6) ✍️

**ChainFlow Writer** は、執筆体験をデザインの領域へと昇華させた「DTP志向」のMarkdownエディタです。従来のMarkdownエディタが到達できなかった、高度なレイアウト制御とPDF再現性を実現します。

### ✨ 主な機能 / Key Features
- **Real-time Page Engine**: 編集画面に「印刷境界線」をリアルタイム表示。執筆しながら最終的なPDFの出来栄えを確認可能。
- **Stamp Syntax**: `<stamp>` 構文による絶対座標指定。ヘッダー、フッター、あるいは用紙の任意の場所に透かしや注釈を配置可能。
- **1:1 PDF Fidelity**: Native Qt Print Engine による、プレビューと寸分違わぬ1:1のPDF出力。
- **Advanced Snippets**: 数式やMermaid図表を管理。バックグラウンドでサムネイルを自動生成し、視覚的なスニペット管理を実現。
- **DTP-like HTML**: HTMLタグによる精密な配置と、Markdownの構文をシームレスに混在させる「ハイブリッド・レイアウト」。

### 🛠️ 技術情報 / Technical Info
- **Rendering**: markdown2 + KaTeX (Math) + Mermaid v11 (Diagrams)
- **Engine**: QWebEngineView による、Chromeクラスの高品質レンダリング。
- **Stability**: Windows タスクバーでの正しいグルーピング och アイコン表示をサポート。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + S`: 保存
- `Ctrl + E`: PDFエクスポート
- `Ctrl + B`: 太字 / サイドバー切り替え
- `Ctrl + P`: スラッシュメニュー（ツール連携）
