# ChainFlow Search v23 [Parallel Oracle] 🔍✨

**ChainFlow Search** は、爆速の初動と、マルチコアをフル活用した並列処理を融合させた、プロフェッショナル仕様の次世代検索エンジンです。
単なるファイル検索の枠を超え、膨大なファイルシステムの中から目的のデータへ「最短距離」で到達するための**「情報の預言者（Oracle）」**として再定義されました。

---

## 🚀 ネイティブ・パラレル・エンジン / Parallel Engine

### 🦀 Rust Parallel Scan (`chainflow_search_core`)
ディレクトリ走査とパターンマッチングを **Rust (PyO3)** によるネイティブエンジンへ移譲。マルチスレッドでの再帰走査により、HDD/SSD の物理限界に迫る超高速な検索スピードを実現しました。

### ⚡ GIL-Free Search Performance
検索処理を Python のグローバル・インタプリタ・ロック（GIL）から解放されたネイティブレイヤーで実行。大規模な検索を実行している間も、UI の応答性を一切損なわない快適な操作性を維持します。

### 🌊 Instant Stream Rendering
検索結果が見つかった瞬間から UI にリアルタイムでストリーミング表示。全スキャンの完了を待つことなく、ヒットした項目へ即座にアクセス可能です。

---

## 🛠️ インテリジェンスな検索機能 / Smart Features

- **Advanced Query Syntax**: 
  - `Space`: AND 検索
  - `|`: OR 検索
  - `-`: 除外（NOT）検索
- **Multi-Tab Interface**: 複数のプロジェクトフォルダや異なる検索条件を個別のタブで管理。並行してリサーチを進めることが可能です。
- **Smart History**: ディレクトリの訪問履歴を自動追跡。Filer 等の他ツールとも連動したパス履歴のシームレスな共有。
- **Deep Integration**: 検索結果をエクスプローラーや他の Suite アプリへ直接ドラッグ、あるいは `Ctrl+C` でパスを即座にコピー。

---

## ⌨️ 操作方法 / Shortcuts
- **`Ctrl + F` / `/`**: 入力エリアへのフォーカス / クリア。
- **`Enter`**: ファイルを開く。
- **`Ctrl + C`**: ファイルパスをコピー。
- **`Ctrl + T`**: 新しい検索タブを作成。
- **`Tab`**: タブの切り替え。

---

## 🛠️ 技術スタック / Tech Stack
- **Languages**: Python 3.12+ / Rust (PyO3)
- **GUI Framework**: PySide6 (Qt for Python 6)
- **Native Engine**: `chainflow_search_core`
- **Build**: Nuitka によるマシン語コンパイル

---

## 📄 ライセンス / License
© 2026 hinatahugu29. All rights reserved.
**Parallel Power, Instant Result.** — 「探す」を「見つける」に変える、究極の検索。
