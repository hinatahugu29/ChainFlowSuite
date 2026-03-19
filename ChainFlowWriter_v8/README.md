# ChainFlow Writer (v7) ✍️

**ChainFlow Writer** は、執筆体験をデザインの領域へと昇華させた「DTP志向」の Markdown エディタです。従来の Markdown 環境では到達できなかった高度なレイアウト制御と、1:1 の PDF 重現性を実現し、事務報告書や技術マニュアルの作成を極限まで効率化します。

---

## ✨ コア・コンセプト / Core Concepts

### 1. Real-time Page Engine
編集画面に「印刷境界線」をリアルタイム表示。物理的な A4/B5 サイズを正確かつシームレスに再現し、執筆しながら最終的な PDF の出来栄えを確認可能です。

### 2. 1:1 PDF Fidelity (Professional Grade)
Native Qt Print Engine と独自の同期システムにより、プレビューと寸分違わぬ **1:1 の PDF 出力** を実現。改ページ位置のズレや余白の不一致に悩まされることはありません。v7 ではマージン相殺防止ロジックにより、さらに堅牢なレイアウトを保ちます。

### 3. "Magic" Tag: `<m-d>` (Markdown in HTML)
HTML の柔軟なレイアウト能力と Markdown の執筆速度を融合させる独自タグです。
- **HTMLネスト対応**: `<div>` やテーブルセルなどの内部で Markdown を直接記述可能。
- **自動デデント (Auto-Dedent)**: HTML のインデントに合わせて Markdown が深くなっても、レンダリング時に左端の余白を自動で除去。パースエラーを防ぎ、美しいコード構造を維持できます。

### 4. Stamp Syntax (Absolute Positioning)
`::: stamp` 構文により、印影や「社外秘」などの画像を自由な座標に配置。標準の **乗算 (Multiply)** ブレンドにより、紙に押したようなリアルな質感を再現します。

---

## 🚀 最新のレンダリングエンジン / Modern Engines

- **Mermaid v11.4 (ESM)**: 最新のダイアグラムエンジン。フロー、ガント、マインドマップ等に対応。
- **KaTeX v0.16**: 論文品質の高速・高精細な数式描画。
- **highlight.js v11.11**: 多彩な言語に対応したシンタックスハイライト。
- **Chromium-based Engine**: 業界標準の高品質なレンダリング基盤。

---

## ⌨️ クイックスタート / Getting Started

### 環境準備
Python 3.12 以上が必要です。

```powershell
# 依存関係のインストール
py -m pip install PySide6 markdown2 pygments python-frontmatter PyYAML
```

### 起動方法
```powershell
py main.py
```

### 主要ショートカット
| ショートカット | アクション |
| :--- | :--- |
| `Ctrl + S` | 保存 |
| `Ctrl + P` | PDF 出力 |
| `F11` | **集中モード (Focus Mode)** |
| `Ctrl + Q` | スニペットギャラリー |
| `Ctrl + Shift + Enter` | **強制改ページ** |

---

## 📁 ディレクトリ構成
- `app/`: アプリケーションのコアロジック（UI, Widget, Utils）
- `snippets_data/`: 登録済みスニペットと設定データの保存場所
- `main.py`: エントリーポイント
- `DOCUMENTATION.md`: 詳細な機能マニュアル（機能の使い方はこちらを参照）

---

*ChainFlow Writer - 執筆を、もっと美しく、もっと自由に。*
