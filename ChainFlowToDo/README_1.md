# ChainFlow Filer v23.2 [Modular Refined] 📁✨

**ChainFlow Filer** は、Python の柔軟な知性と Rust の圧倒的な剛性を融合させた、プロフェッショナル向け次世代ファイルマネージャーです。
単なるファイル閲覧ソフトの枠を超え、大量の素材を複数のツール群へ高速かつ正確に流し込む（Flow）ための**「ワークフローのハブ（作業用コックピット）」**として再定義されました。

---

## 🚀 次世代のコア・テクノロジー / Core Technologies

### 🦀 Rust Native Engine (`chainflow_core`)
ディレクトリ走査、ソート、フィルタリングといった I/O 集約型処理を **Rust (PyO3)** で実装されたネイティブコアへ移譲。数万ファイル規模のフォルダも「0.01秒」でハンドリングする、マシンレベルのパフォーマンスを実現しました。

### 🧩 Modular Refined Architecture
UI レイヤーからビジネスロジック（ファイル操作、セッション管理）を完全に分離。
- **`core/actions.py`**: ファイル移動、コピー、外部ツール起動などのアクションを統括。
- **`core/session.py`**: タブ構成やソート順、レーンレイアウトの永続化を担当。

### 🛡️ Stability Guard (`shiboken6`)
`shiboken6` を利用した C++ オブジェクトの生存確認を実装。高速なタブ切り替えやフォルダ遷移の瞬間に発生しがちな `RuntimeError` を構造的に排除し、極限の操作速度においても「絶対的安定」を保証します。

---

## 🎨 独創的なユーザー体験 / User Experience

### Massive Parallel Tiling (超多ペイン並置)
単一ウィンドウ内に無数のディレクトリをタイル状に敷き詰め、関連するプロジェクトフォルダを一元的に監視・操作可能。幅の狭いレーンを多数並べ、それらを**「縦スタック（Vertical Stack）」**させることで、情報の密度を極限まで高めます。

### Keyboard-Driven Workflow
マウス操作による「思考の断絶」を排除。ホームポジションから離れることなく、エディタのような感覚でファイル操作を完結できます。

### 📋 主要ショートカット / Interaction
- **`H` / `J` / `K` / `L`**: Vim スタイルによるペイン移動・ファイル選択。
- **`Ctrl + P`**: スラッシュメニュー（コマンドパレット）。Suite アプリやカスタムツールを瞬時に呼び出し。
- **`V`**: 垂直分割（新規ペインの作成）。
- **`S`**: 高速検索 / フィルタリング。
- **`X`**: 実行 / アクション選択。
- **`Q`**: ペインを閉じる / アプリケーション終了。

---

## 🛠️ 技術スタック / Tech Stack
- **Languages**: Python 3.12+ / Rust (PyO3)
- **GUI Framework**: PySide6 (Qt for Python 6)
- **Native Engine**: `chainflow_core` (Maturin-built)
- **Compilation**: Nuitka (C-Translator) によるマシン語化
- **Stability**: `shiboken6` (Stability Guard)

---

## 📄 ライセンス / License
© 2026 hinatahugu29. All rights reserved.
**Zero-Proxy, Native Core Architecture.** — 思考の速度を、ファイルシステムの速度へ。
