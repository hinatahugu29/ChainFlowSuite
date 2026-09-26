# ChainFlow Writer v9 [Document Engine] ✍️✨

**ChainFlow Writer** は、執筆体験をデザインの領域へと昇華させた、プロフェッショナル向け「DTP 志向」の Markdown エディタです。
従来の Markdown 環境では到達できなかった高度なレイアウト制御と、1:1 の PDF 再現性を実現し、事務報告書や技術マニュアルの作成を極限まで効率化します。

---

## 🚀 次世代の執筆基盤 / Core Technologies

### 📄 Real-time Page Rendering [Beyond Typora]
編集画面に「印刷境界線」をリアルタイム表示。物理的な A4/B5 サイズを正確かつシームレスに再現し、執筆しながら最終的な PDF の出来栄えをミリ単位で確認可能です。

### 💎 1:1 PDF Fidelity (Professional Grade)
Native Qt Print Engine と独自の同期システムにより、プレビューと寸分違わぬ **1:1 の PDF 出力** を実現。改ページ位置のズレや余白の不一致を完全に排除し、ビジネス資料としての完成度を保証します。

### 🎨 IDE-Style Syntax Highlighting (New v9)
複雑な HTML/CSS 要素を背景に馴染ませ、文書の構造に特化した高度な色分けを導入。Markdown エディタでありながら、IDE のような情報の視覚的高効率化を実現しました。

---

## 🛠️ 強力なレイアウト・拡張機能 / Advanced Features

- **"Magic" Tag: `<m-d>` (Markdown in HTML)**: HTML の柔軟なレイアウト能力と Markdown の執筆速度を融合。`<div>` やテーブルセルの内部で Markdown を記述し、自動デデント機能で美しいコード構造を維持します。
- **Stamp Syntax (Absolute Positioning)**: `::: stamp` 構文により、印影や画像を自由な座標に配置。乗算（Multiply）ブレンドにより、紙に押したようなリアルな質感を再現。
- **Smart Snippets**: `Ctrl + Q` により、頻繁に使用する定型文や HTML テンプレートを瞬時に呼び出し。

---

## 🚀 最新のレンダリング・エンジン / Modern Engines
- **Mermaid v11.4 (ESM)**: フローチャート、ガント、マインドマップ等の最新記法をサポート。
- **KaTeX v0.16**: 高精細な数式描画。
- **highlight.js v11.11**: プログラミング言語のシンタックスハイライト。
- **Chromium-based Engine**: 業界標準の高品質なレンダリング。

---

## ⌨️ 主要ショートカット / Interaction
- **`Ctrl + P`**: PDF エクスポート（1:1 同期出力）。
- **`Ctrl + S`**: 文書の保存。
- **`F11`**: **集中モード (Focus Mode)**。
- **`Ctrl + Q`**: スニペット・ギャラリーの呼び出し。
- **`Ctrl + Shift + Enter`**: **強制改ページ** の挿入。

---

## 🛠️ 技術スタック / Tech Stack
- **Framework**: PySide6 (Qt for Python 6)
- **Language**: Python 3.12+
- **PDF Engine**: Qt Native Print Engine
- **Web Engine**: QtWebEngine (Chromium)

---

## 📄 ライセンス / License
© 2026 hinatahugu29. All rights reserved.
**Writer, Not Processor.** — 執筆を、もっと美しく、もっと自由に。
