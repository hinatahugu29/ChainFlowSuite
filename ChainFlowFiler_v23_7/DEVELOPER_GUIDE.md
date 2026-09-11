# ChainFlowFiler 技術仕様書 & 開発者ガイド (v23.4)

このドキュメントは、**ChainFlowFiler** のコードベース構造、主要コンポーネントの役割、およびデータフローを解説する技術資料です。
AIアシスタントや新規開発者がプロジェクトの全体像を把握し、保守・拡張を行うための「地図」として機能します。

---

## 1. プロジェクト構造 (Directory map)

v23.4では、パフォーマンスの大幅な向上のため、ファイル走査処理をRust(PyO3)へオフロードし、本体はNuitkaでコンパイルする設計となっています。

```
ChainFlowFiler_v23_4/
├── main.py                  # Filerアプリケーションのエントリーポイント
├── build_nuitka.bat         # Nuitkaビルド用スクリプト
├── build_native.bat         # Rustネイティブ拡張のビルド(maturin)用スクリプト
├── DEVELOPER_GUIDE.md       # 本書（技術仕様書）
│
├── core/                    # [Core] Pythonユーティリティ・Rust拡張ラッパー
│   ├── global_model.py      # QFileSystemModelのプロキシ
│   └── logger.py            # ロギングラッパー
│
├── models/                  # [Model] データロジック
│   └── proxy_model.py       # Rustソート+フィルタ+アイコン制御
│
├── native/                  # [Rust] Rust(PyO3) コントロール
│   └── src/                 # Rustソースコード
│
└── widgets/                 # [View/Controller] UIコンポーネント
    ├── main_window.py       # Filer骨格
    ├── flow_area.py         # タブごとの作業エリア
    ├── file_pane/           # ファイル一覧ペインの実装
    └── quick_look.py        # スペースキーでのプレビューウィンドウ
```

---

## 2. コア技術: Native Core への分離 (Rust)

v23.1以降、`QSortFilterProxyModel` 等によるPython側のループソートボトルネックを解消するため、ファイルのメタデータ取得と自然順ソート・フィルタリングを Rust プラグイン `chainflow_core.pyd` へと移行しました。

*   **開発フロー**: `native/` ディレクトリ内でRustを記述し、`maturin build --release` でコンパイルします。
*   **高速化の要と注意**: OSネイティブのキャッシュを利用して数千ファイルのソートを一瞬で行います。Python側からは一切のメタデータ（サイズ、日付）の走査を行わず、すべてプロキシを通す構造を徹底してください。

---

## 3. 主要なデータフローとメカニズム

### Asynchronous File Engine (非同期ファイル監視)
*   **QFileSystemModel**: ルートパスを監視し、OSの変更通知を受け取ります。このインスタンスは `core/global_model.py` でシングルトンとして生成され、すべてのペインで共有してリソースを削減します。
*   **ResolveSymlinks回避**: フォルダショートカット(`.lnk`)の柔軟なハンドリングのため、`QFileSystemModel.setResolveSymlinks(False)` を適用し、解決と表示処理はプロキシに委譲しています。

---

## 4. ビルドとデプロイ (Building)

現在、配布パッケージの生成には **Nuitka** を使用しています。

```powershell
# 1. まずRustネイティブコアをビルドし、ルートにコピー
.\build_native.bat

# 2. Nuitkaで全体をコンパイル(onedirモード)
.\build_nuitka.bat
```

> [!NOTE]
> `tools.json` を通じて外部のChainFlowスイート(Tool/Image)等と連携するため、Filer自体は超軽量に保たれています。

---

## 5. 開発・メンテナンスの指針

*   **パフォーマンス第一**: ファイルの走査や描画（`data` や `paint` メソッド）内で `os.path.exists()` などのI/Oを発生させないでください。
*   **UI/UXの整合性**: ダークテーマへの統一、およびマウス・キーボード両方でのアクセシビリティを保つこと。
