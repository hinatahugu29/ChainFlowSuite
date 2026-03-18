# ChainFlow Writer (v6) ✍️

**ChainFlow Writer** は、執筆体験をデザインの領域へと昇華させた「DTP志向」のMarkdownエディタです。従来のMarkdownエディタが到達できなかった、高度なレイアウト制御とPDF再現性を実現し、事務報告書や技術マニュアルの作成を極限まで効率化します。

---

## ✨ コア・コンセプト / Core Concepts

### 1. Real-time Page Engine
編集画面に「印刷境界線」をリアルタイム表示。物理的なA4/B5サイズを正確にシームレスに再現し、執筆しながら最終的なPDFの出来栄えを確認可能です。

### 2. 1:1 PDF Fidelity
Native Qt Print Engine と独自の同期システムにより、プレビューと寸分違わぬ1:1のPDF出力を実現。改ページ位置のズレやフォントの不一致に悩まされることはありません。

### 3. "Magic" Tag: `<m-d>` (Markdown in HTML)
HTMLの柔軟なレイアウト能力とMarkdownの執筆性を融合させる独自タグです。
- **HTMLネスト対応**: `<div>` やテーブルセルなどのHTML要素内でMarkdownを直接記述可能。
- **自動デデント (Auto-Dedent)**: HTMLのインデントに合わせてMarkdownが深くなっても、レンダリング時に左端の余白を自動で除去。パースエラーを防ぎ、読みやすいコード構造を維持できます。
- **使用例**:
  ```html
  <div class="custom-card">
    <m-d>
      #### インテリジェント・レイアウト
      - HTMLの枠組みの中で
      - **Markdown** の表現力を
      - 自由に発揮できます
    </m-d>
  </div>
  ```

### 4. Stamp Syntax (Logical Absolute Positioning)
`::: stamp` 構文により、印影や「社外秘」などの画像を自由な座標に配置可能。乗算（multiply）ブレンドにより、紙に押したようなリアルな質感を再現します。

---

## 🚀 最新のレンダリングエンジン / Modern Engines

- **Mermaid v11.4 (ESM)**: 最新のダイアグラムエンジンを搭載。XY Chart、ガントチャート、フローチャート等をテキストから生成。
- **KaTeX v0.16**: 論文品質の高速・高精細な数式描画をサポート。
- **highlight.js v11.11**: 広範なプログラミング言語のシンタックスハイライト。
- **QWebEngineView**: Chromeクラスの高品質なレンダリング基盤。

---

## 🛠️ 生産性向上ツール / Productivity Tools

- **Front Matter 変数置換**: YAMLで定義した変数を本文中の `{{key}}` で呼び出し。
- **スニペットギャラリー**: サムネイル付きで視覚的に管理されたHTML/Markdownスニペットを `Ctrl + H` で即座に挿入。
- **動的カスタマイズ**: フロントマターからコードブロックの背景色 (`code_bg`) や余白を一括調整。
- **印刷非表示 (`::: no-print`)**: 画面上には表示されるが、PDFには出力されない執筆者用メモ機能。

---

## ⌨️ クイックスタート / Getting Started

### 環境構築
Python 3.12以上が必要です。

```powershell
# 依存関係のインストール
py -m pip install PySide6 markdown2 pygments python-frontmatter
```

### 起動方法
```powershell
py main.py
```

### 主要ショートカット
| ショートカット | アクション |
| :--- | :--- |
| `Ctrl + S` | 保存 |
| `Ctrl + E` | PDFエクスポート |
| `Ctrl + B` | エディタサイドバーの切り替え |
| `Ctrl + R` | 設定ペイン（右部）の切り替え |
| `Ctrl + H` | チートシート（スニペットギャラリー）の表示 |
| `Ctrl + P` | スラッシュメニュー（ツール連携） |

---

## 📁 ディレクトリ構成
- `app/`: アプリケーションのコアロジック（UI, Widget, Utils）
- `snippets_data/`: 登録したスニペットとサムネイルの保存先
- `main.py`: エントリーポイント
- `Sample_Features.md`: 全機能を確認できるショーケースファイル

---

*ChainFlow Writer - 執筆を、もっと美しく、もっと自由に。*
