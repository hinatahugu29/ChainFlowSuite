# ChainFlowFiler 技術仕様書 & 開発者ガイド (v17.0)

このドキュメントは、**ChainFlowFiler** のコードベース構造、主要コンポーネントの役割、およびデータフローを解説する技術資料です。
AIアシスタントや新規開発者がプロジェクトの全体像を把握し、保守・拡張を行うための「地図」として機能します。

---

## 1. プロジェクト構造 (Directory map)

v17.0では、Chromiumベースのレンダリングエンジン統合に伴い、依存関係が増加しています。

```
ChainFlowFiler_v17/
├── main.py                  # Filerアプリケーションのエントリーポイント
├── editor.py                # [NEW] Editorアプリケーションのエントリーポイント (Subprocess)
├── ChainFlowFiler.spec      # [NEW] PyInstallerビルド設定ファイル (Multi-EXE)
├── PROJECT_DOC.md           # ユーザー向け機能説明・履歴
├── DEVELOPER_GUIDE.md       # 本書（技術仕様書）
│
├── core/                    # [Core] 共通ユーティリティ・基盤など
│   ├── __init__.py
│   ├── file_operations.py   # OS依存のファイル操作
│   ├── file_worker.py       # 非同期ファイル操作ワーカー (QThread)
│   ├── styles.py            # カラーパレット、共通QSS、定数定義
│   └── logger.py            # ロギングラッパー
│
├── models/                  # [Model] データロジック
│   └── proxy_model.py       # QFileSystemModelに対するフィルタ・ソート・マーク機能
│
└── widgets/                 # [View/Controller] UIコンポーネント
    ├── main_window.py       # Filer骨格。Editorプロセスの管理も担当
    ├── flow_area.py         # タブごとの作業エリア
    ├── flow_lane.py         # 垂直レーン
    ├── navigation_pane.py   # サイドバー (Standard, Favorites, Drives)
    ├── quick_look.py        # スペースキーでのプレビューウィンドウ
    ├── slash_menu.py        # [NEW] コマンドパレット (Ctrl+P)
    ├── ui_utils.py          # [NEW] Windows DWM API連携 (Dark Title Bar)
    │
    └── file_pane/           # [Sub-package] ファイル一覧ペインの実装
        ├── context_menu.py      # コンテキストメニュー構築
        ├── highlight_delegate.py # Context Highlight描画
        ├── batch_tree_view.py    # カスタムTreeView
        └── file_pane.py          # FilePane本体
```

---

## 2. モジュール詳細解説

### Editor Integration (`editor.py`)
v16.0で導入された独立エディタ。ファイラとは別プロセスとして動作しますが、密接に連携します。
*   **Subprocess Launch**: `main_window.py` の `launch_editor` メソッドから `subprocess.Popen` で起動されます。
*   **Process Management**: メインウィンドウ終了時、起動した全エディタプロセスを追跡して終了させます (`self.editor_processes`)。
*   **AppUserModelID**: タスクバーアイコンをPythonアイコンではなくアプリ固有アイコンにするため、Windows API (`SetCurrentProcessExplicitAppUserModelID`) を使用。
*   **Print-Friendly Export**: PDF出力時は、一時的にライトテーマと印刷用CSSを適用し、出力後にダークテーマに戻すロジックを実装。

### Core (`core/`)
*   **ui_utils.py**: Windows 11/10 の DWM API (`dwmapi.dll`) を叩き、ウィンドウのタイトルバーをダークモードにする。FilerとEditor両方で使用。

### Widgets (`widgets/`)
*   **slash_menu.py**: `QDialog` ベースのコマンドパレット。リストフィルタリングと実行ロジックを持つ。
*   **navigation_pane.py**: v16.2でHELPセクションを一時無効化（将来の再実装待ち）。

---

## 3. 主要なデータフローとメカニズム

### Multi-Process Architecture
*   ChainFlowFiler本体とEditorは**疎結合**です。
*   Filer -> Editor: コマンドライン引数でファイルパスを渡して起動。
*   Editor -> Filer: 直接の通信なし（ファイルシステムを介した連携）。
*   この設計により、FilerがクラッシュしてもEditor（編集中データ）は巻き込まれにくい利点があります（ただし、現状は親プロセス終了時に子も道連れにする仕様）。

### Asynchronous File Operations (非同期ファイル操作)
1.  **Trigger**: コピー/移動、ZIP圧縮/解凍などの重い操作。
2.  **Worker**: `FileOperationWorker` が `QThread` で処理開始。
3.  **Signal**: `progress` シグナルでUI更新。

---

## 4. ビルドとデプロイ (Building)

v17.0より、WebEngineを含むため**ビルドサイズが約640MB**になります。必ずSPECファイルを使用してください。

```powershell
# 仮想環境 (venv) にて実行
py -m PyInstaller ChainFlowFiler.spec --clean
```

これにより `dist/ChainFlowFiler/` フォルダが生成され、内部に以下の2つの実行ファイルが含まれます。
*   `ChainFlowFiler.exe` (Main App)
*   `editor.exe` (Markdown Editor)
*   `_internal/` (QtWebEngineを含む依存ライブラリ群)

> [!NOTE]
> `_internal` フォルダ内の `Qt6WebEngineCore.dll` 等がサイズの大部分を占めますが、これは高品質なHTMLレンダリングのために必須です。

---

## 5. 開発・メンテナンスの指針

### 新機能追加時のフロー
1.  **Editor機能**: `editor.py` を修正。UIロジックは単一ファイルに集中しているため、ここを中心に編集。
2.  **Filer機能**: `widgets/` 内の該当コンポーネントを修正。

### 既知の課題とTodo
*   **Settings**: 設定画面の実装。
*   **Sidebar Help**: チートシートの正確な記述と復活。

