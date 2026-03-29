**Version:** 21.0 (Alpha)  
**Last Updated:** 2026-02-10

## 1. プロジェクト概要
**Chain Flow Filer** は、パワーユーザー向けの作業効率化ファイルマネージャーです。
v21.0では、ユーザーフィードバックに基づきマウスホイールによるリサイズ操作の「カクカク感」を解消するスムーズリサイズ機能が実装されました。

*   **v21.0 (Alpha)**:
    *   **Smooth Resizing**: `Ctrl/Shift + Wheel` によるペインサイズ変更の計算式を刷新。固定ステップ（40px）からマウス回転量に応じた比例可変式に変更し、滑らかで直感的なリサイズ操作を実現しました。
    *   **Clipboard Image Paste**: クリップボードに画像データがある状態で `Ctrl+V` (Paste) を行うと、その画像をPNGファイルとして現在のフォルダに保存する機能を追加しました。タイムスタンプ付きファイル名で自動保存されます。
*   **v20.1 (Alpha)**:
    *   **Chain Flow Search**:
        *   **Standalone Application**: ファイル検索に特化した軽量な独立アプリ。
        *   **Tabbed Interface**: 複数の検索結果をタブで保持可能。
        *   **Local Socket Integration**: 既に起動している場合、新しい検索リクエストを既存インスタンスの新規タブとして処理（Single Instance）。
    *   **UI Polish**:
        *   **PDF Merger**: Windows DWM APIによるダークタイトルバー適用。
        *   **Fix Highlight Persistence**: Alt+Tab切り替え時のハイライト残留バグを修正。
        *   **Fix Cursor State**: PDF変換後のカーソル復帰漏れを修正。
*   **v17.0 (Alpha)**:
    *   **HTML & PDF Integration**: Chromeベースの高忠実度Webレンダリングエンジン (`QWebEngineView`) を搭載。HTMLファイルのプレビューと、見た目そのままのPDFエクスポートに対応。
    *   **Unified Scrollbar Design**: HTMLプレビュー内のスクロールバーにもアプリ共通のダークテーマを適用（CSS注入による制御）。
    *   **Robust Initialization**: 巨大なブラウザプロセスの起動に伴うUIのチラつきを「ウォームアップ処理」で完全に解消。
    *   **Dependency Update**: 総サイズは約640MBとなりましたが、スタンドアロンで最新のWeb技術を利用可能です。
*   **v16.2 (Alpha)**:
    *   **Integrated Markdown Editor**: ファイラから直接起動できるMarkdownエディタ。リアルタイムプレビュー、PDF出力（書類向けライトテーマ）機能付き。
    *   **Dark Theme Unification**: タイトルバー、メッセージボックス、動的生成ペインを含む全UIをダークテーマに統一。
    *   **Editor Lifecycle**: Filer終了時にEditor子プロセスを自動終了。
    *   **PDF Print Style**: PDF出力時は白背景・プロフェッショナルなドキュメントスタイルを自動適用。
*   **v16.0 (Alpha)**:
    *   **Generation Update**: 新しいメジャーバージョンの開発開始。
    *   **Satellite Editor Architecture**: 別プロセスとしてエディタを起動するアーキテクチャ。
    *   **Slash Menu System**: Ctrl+Pで呼び出せるコマンドパレット。
    *   **Full Row Highlight**: Altハイライトがカラム全体（行全体）に適用されるようになり、視認性が向上しました。
    *   **Multi-View Support**: 同じフォルダを複数の場所で開いていた場合、その全てが正しくハイライトされます。
    *   **Empty Folder Support**: 中身が空のフォルダでも、ペイン自体を認識して正しくコンテキストが表示されます。
*   **Header UI Fix**: カラムヘッダー右端の白い余白を修正。
*   **Freeze Prevention (v14.2)**: コピー、移動、ZIP圧縮・解凍などの時間がかかる操作をバックグラウンドスレッドで実行。進捗ダイアログが表示され、キャンセルも可能です。
*   **Context Highlight (v14.0)**: `Alt` キーを押し続けている間、選択中のファイルの文脈（上流・下流）がハイライト表示されます。
    *   **Upstream (Ancestors)**: 親フォルダ、その親……と、上流のペインにある祖先フォルダがハイライト＆スクロールされます。
    *   **Downstream (Descendants)**: 選択したアイテムがフォルダで、かつその中身を表示している子ペインがある場合、そのペイン（ヘッダーまたは枠）がゴールド色でハイライトされます。
    *   これにより、「どこから来て（親）、どこへ展開されているか（子）」というフロー全体を一目で把握できます。
*   **F5 Refresh (v14.0)**: `F5` キーで現在タブの全ペインを再読み込みします（選択状態維持）。
*   **Layout Reset (v13.0)**: `Ctrl+Shift+R` を押すことで、ペイン幅のばらつきやサイドバーの状態を一発で均等割り（計算上のデフォルト）にリセットできます。
    *   サイドバーが強制表示され、デフォルト幅に戻ります。
    *   全ての水平ペインが均等な幅に調整されます。
    *   全ての垂直レーンが均等な高さに調整されます。
    *   **各ペイン内の積まれたビューも均等な高さに調整されます。**
*   **Sectioned Sidebar**: ナビゲーションペインを `STANDARD`, `FAVORITES`, `DRIVES` の3セクションに分割し、折りたたみ可能にしました。
*   **Resizable Sidebar Sections**: サイドバー内の各セクション（Standard含む）はマウスドラッグまたは `Shift+Scroll` で高さを自由に調整可能。Spacerによる上詰め配置補正付き。
*   **Standard Folders**: デスクトップ、ダウンロードなどの標準フォルダへのクイックアクセスを実装。


*   **View Unstacking (v11.0)**: `Shift+W` で、ペイン全体ではなく「現在アクティブなビュー」だけを閉じることができます。
*   **Hover Auto-Focus (v11.1)**: ペイン内の個別のビュー（分割ブロック）に対しても、マウスオーバーだけでフォーカスが移動し、青いハイライトが追従します。
*   **Q-Key Fix (v11.1)**: `Q` (Go Up) キーが、アクティブなビューに対して正しく作用するように修正されました。
*   **New Icon (v11.1)**: 視認性を高めた新デザインのアイコンを採用。
*   **Unified Batch Drag (v10.1)**: 安全性を高めた一括ドラッグ機能。
*   **Quick Copy (v10.0)**: プレビューからのコンテンツコピー。
*   **Icon Update**: `app_icon.ico` を透過版画像で確実に上書きし、タスクバー等への反映を修正。


---

## 2. 実装済み機能 (Requirements Implemented)

### 2.1 ナビゲーション & ビュー
*   **Chain Flow Interface**: フォルダを開くたびに右側に新しいペインが追加される方式。
*   **Layout Reset (v13.0)**: `Ctrl+Shift+R` で全ペイン・レーンのサイズを均等化。
*   **Sectioned Sidebar (v12.0)**: `STANDARD`, `FAVORITES`, `DRIVES` の3セクション構成。全てのスプリッターが操作可能で、Spacerにより閉じた際の上詰めレイアウトを自動調整します。
*   **Standard Folders**: デスクトップ、ドキュメントなどへのクイックアクセス。
*   **Address Bar**: 現在地のパス表示と直接入力による高速ジャンプ。
*   **Hover Lock / Persistent Highlight**: マウス操作の焦点を維持し、誤操作を防ぐ。
*   **Hover Focus (v12.0 Fix)**: マウスオーバーだけで対象ペインを選択状態とし、クリックせずとも `Ctrl+C` 等のキー操作を受け付けます。
*   **Vertical Flow Lanes**: 複数のフローを縦に積み重ねて表示可能（`V` キー）。
*   **Tabbed Workspace**: 複数の作業スペースをタブとして管理（`Ctrl+T`）。
*   **Compact Mode (`C` Key)**: スタック表示時のスペース効率を最大化。
*   **Sidebar Toggle (`Ctrl+B`)**: ナビゲーションペインの表示切り替え。

### 2.2 プレビュー機能 (Quick Look)
*   **Popup Preview (`Space` Key)**: 選択中のファイルを即座にポップアップ表示。
*   **Supported Formats**:
    *   **Images**: 各種画像形式（png, jpg, webp, svg等）。
    *   **Text/Code**: ソースコード、Markdown、**AutoHotkey (.ahk)** 等。
*   **Copy Content Button (v10.0)**:
    *   プレビューウィンドウ右上のボタンから、表示中のテキストまたは画像データをクリップボードへコピー可能。
*   **Stays On Top & No Focus**: プレビューを表示したままリストを操作可能。

### 2.3 ファイル操作 & 実行
*   **Unified Batch Drag (v10.0)**:
    *   **Selection + Marks**: **現在操作中のペインの選択アイテム**と、`Alt+Mark` されたアイテムを**合算**してドラッグ開始可能。
    *   ※ 他のペインで「選択」されているだけ（非マーク）のアイテムはドラッグ対象に含まれません（誤操作防止のため）。
    *   これにより、あちこちのフォルダから素材を`Alt+Click`で集めて、一回で別フォルダや外部アプリへ放り込むことが可能。
*   **Context Menu Extensions (v10.0)**:
    *   **Create Shortcut**: その場にショートカット(.lnk)を作成。
    *   **Properties**: Windows標準のプロパティ画面を表示。
    *   **Copy Path Special**: パス、ファイル名、Unix形式パスなどのコピー。
*   **Collection Bucket (Alt-Marking)**: 
    *   **Alt + Click**: 赤いマーク（ワインレッド）でアイテムを「カゴ」に入れる。移動しても維持される。
    *   **Batch Menu**: マークされたアイテムに対する一括操作メニュー。
*   **Standard Actions**: Copy/Cut/Paste, Delete, Rename (F2), Drag & Drop.

### 2.4 その他
*   **Session Persistence**: アプリ終了時の状態を保存 (Portable対応)。
*   **Smart Sorting**: 自然順ソート。
*   **Deep Blue Scrollbars**: v10で採用された、落ち着いた青色の角丸スクロールバー。

---

## 3. 操作マニュアル (Key Bindings)

| Key | Action | Description |
| :--- | :--- | :--- |
| **Space** | **Quick Look** | プレビュー表示 (Copyボタン付き) |
| **Alt (Hold)** | **Ancestral Highlight** | 祖先フォルダをハイライト表示 |
| **Alt + Click** | **Mark (Bucket)** | アイテムを赤くマーク (ドラッグ対象に追加) |
| **Alt + C** | **Clear Marked** | マーク全解除 |
| **Drag** | **Batch Drag** | 選択+マーク項目を一括ドラッグ |
| **Q / Backspace** | Go Up | 親ディレクトリへ戻る |
| **V** | Vertical Split | 新しいレーンを追加 |
| **C** | Compact Mode | 表示モード切替 |
| **Ctrl+C / V** | Copy / Paste | クリップボード操作 |
| **Ctrl+B** | Sidebar Toggle | サイドバー表示切替 |
| **Ctrl/Shift + Wheel** | Resize | ペイン幅/レーン高さ調整 |
| **Ctrl+Shift+R** | **Layout Reset** | レイアウトを均等割りにリセット |
| **F5** | **Refresh** | 現在タブの全ペインを再読み込み |

---

## 2. コア機能 (Core Features)
### A. ChainFlowFiler (Main App) - "The Cockpit"
*   **Lightweight Core**: Removed explicit dependencies on WebEngine, reducing size to ~120MB.
*   **Plugin Architecture**: Dynamic tool launching via `tools.json`.
*   **Process Management**: Automatically terminates launched tools when the main app closes.
*   **Column-Based Navigation**: Miller Columns (Cascading Lists) similar to macOS Finder.
*   **Zero-Latency Preview**: "Quick Look" for text, code, and images. Redirects complex files (PDF/HTML) to ChainFlowTool.
*   **Keyboard-Centric**: Vim-like navigation (H/J/K/L), Slash Menu (Ctrl+P).

### B. ChainFlowTool (Plugin) - "The Viewer"
*   **Rich Content Engine**: Powered by QtWebEngine (Chromium).
*   **PDF Viewer**: High-fidelity PDF rendering.
*   **HTML Preview**: Full web page rendering including CSS/JS.
*   **Markdown Editor**: Split-view editor with live preview and PDF export.

### C. ChainFlowImage (Plugin) - "The Utility"
*   **Image Processor**: Bulk format conversion (JPG, PNG, WEBP).
*   **Smart Resize**: Width-based or percentage-based resizing.
*   **Safety**: Auto-renaming to prevent accidental overwrites.l)

---

## 4. 技術スタックとアーキテクチャ
*   **Language**: Python 3.11+
*   **GUI Framework**: PySide6 (Qt6)
*   **Build Tool**: PyInstaller (onedir mode)
*   **Icons**: Standard .ico support
*   **Project Structure**:
    *   **core/**: 共通ユーティリティ (FileOps, Styles, Logger)
    *   **widgets/**: UIコンポーネント (MainWindow, FlowArea, FilePane)
    *   **models/**: データモデル (ProxyModel)

---

## 5. 作業履歴要約 (Development History)
*   **v20.0 (Generation Update)**:
    *   **Version Increment**: v19からのコピー・基盤の用意。
    *   **Build Environment**: `build_v20.bat` および v20用ビルド構成の整備。
    *   **Core UI**: ウィンドウタイトルを v20 へ更新。
    *   **PDF Merger**: サブツール `PDF Merger` を実装。`Ctrl+P` (Slash Menu) から呼び出し、ドラッグ＆ドロップでPDFを結合可能。
    *   **Auto-Close Option**: PDF結合成功時にウィンドウを自動で閉じるかどうかを選択できるチェックボックスを実装。
*   **v19.0 (Plugin Era)**:
    *   **Suite Separation**: Filer本体を軽量化し、リッチ機能を外部ツールへ分離。
    *   **Plugin System**: `tools.json` ベースの汎用プラグインランチャーおよびプロセス管理機能の実装。
    *   **ChainFlowTool**: PDF/HTML/Markdown統合ビューアとしてリビルド。
    *   **ChainFlowImage**: 画像変換・リサイズ専用ツールの新規追加。
    *   **Process Sync**: 本体終了時に全プラグインツールを自動終了させる同期機能を実装。
*   **v17.0 (Alpha)**:
    *   **HTML & PDF Integration**: Chromeベースの高忠実度Webレンダリングエンジン (`QWebEngineView`) を搭載。HTMLファイルのプレビューと、見た目そのままのPDFエクスポートに対応。
    *   **Unified Scrollbar Design**: HTMLプレビュー内のスクロールバーにもアプリ共通のダークテーマを適用（CSS注入による制御）。
    *   **Robust Initialization**: 巨大なブラウザプロセスの起動に伴うUIのチラつきを「ウォームアップ処理」で完全に解消。
    *   **Dependency Update**: 総サイズは約640MBとなりましたが、スタンドアロンで最新のWeb技術を利用可能です。
*   **v16.2 (Alpha)**:
    *   **Integrated Markdown Editor**: ファイラから直接起動できるMarkdownエディタ。リアルタイムプレビュー、PDF出力（書類向けライトテーマ）機能付き。
    *   **Dark Theme Unification**: タイトルバー、メッセージボックス、動的生成ペインを含む全UIをダークテーマに統一。
    *   **Editor Lifecycle**: Filer終了時にEditor子プロセスを自動終了。
    *   **PDF Print Style**: PDF出力時は白背景・プロフェッショナルなドキュメントスタイルを自動適用。
*   **v16.0 (Alpha)**:
    *   **Generation Update**: 新しいメジャーバージョンの開発開始。
    *   **Satellite Editor Architecture**: 別プロセスとしてエディタを起動するアーキテクチャ。
    *   **Slash Menu System**: Ctrl+Pで呼び出せるコマンドパレット。
    *   **Full Row Highlight**: Altハイライトがカラム全体（行全体）に適用されるようになり、視認性が向上しました。
    *   **Multi-View Support**: 同じフォルダを複数の場所で開いていた場合、その全てが正しくハイライトされます。
    *   **Empty Folder Support**: 中身が空のフォルダでも、ペイン自体を認識して正しくコンテキストが表示されます。
*   **v15.0 (Alpha)**:
    *   **New File Creation**: `New File...` コンテキストメニューを追加。名前指定での空ファイル作成に対応。
    *   **Quick Edit (QuickLook)**: QuickLookに `Edit` / `Save` ボタンを実装。新規ファイル作成から直感的にテキスト編集へ移行可能に。
    *   **Refined Context Highlight**: Altハイライトの全カラム対応、重複フォルダ対応、空フォルダ対応などのUX改善を実装。
    *   **Header UI Fix**: カラムヘッダー右端の白い余白を修正。
*   **v14.1 (Refactoring Phase)**:
    *   **Architecture Update**: 巨大化した `file_pane.py` を解体し、保守性を向上。
    *   **Modules**: `HighlightDelegate`, `BatchTreeView`, `ContextMenuBuilder` を独立モジュール化。
    *   **Core Utilities**: ファイル操作 (`file_operations.py`)、スタイル (`styles.py`)、ログ (`logger.py`) を共通ライブラリとして分離。
    *   **Performance Optimization**: リサイズイベントのデバウンス（遅延実行）処理により、描画の軽量化とスムーズさを向上。
    *   **Highlight Logic Optimization**: パス計算ロジックの最適化により、ハイライト機能のレスポンスを改善。
*   **v14.0 (Alpha)**:
    *   **Context Highlight**: `Alt` キー長押しで祖先(上流)と子孫(下流)ペインを同時ハイライト。フローの可視化。
    *   **F5 Refresh**: `F5` キーで現在タブの全ペインを再読み込み。
*   **v13.0 (Alpha)**:
    *   **Layout Reset**: `Ctrl+Shift+R` による一発整頓機能。
*   **v12.0 (Alpha)**:
    *   **Sidebar Refactoring**: `Standard`, `Favorites`, `Drives` の3セクション分割 + Spacer。
    *   **Focus UX Improvement**: ホバー時のフォーカス・操作対象認識ロジック改良。
    *   **Column UX**: 「名前」列を自動伸縮(Stretch)に設定し、ペインリサイズ操作だけで長いファイル名の確認を容易化。
    *   **Build**: PyInstallerによる単一ファイルビルドワークフローの確立。
*   **v11.0 - v11.1**:
    *   **New Icon**: 透過対応モダンアイコン (`112.png`) の採用。
    *   **Hover Auto-Focus**: マウスオーバーによる直感的なフォーカス切り替え機能。
    *   **View Unstacking**: Shift+Wでの個別ビュー破棄。
    *   **Q-Key Fix**: 上位階層移動の挙動改善。
*   **v10.0 (Alpha)**:
    *   **Unified Batch Drag**: `BatchTreeView` クラスの実装により、選択アイテムとマーク済みアイテムの合同ドラッグを実現。
    *   **Quick Look Ehancements**: `.ahk` 対応、コピーボタン実装（テキスト/画像）。
    *   **Context Menu**: ショートカット作成、プロパティ表示、パスコピー拡張。
    *   **UI Polish**: スクロールバーカラーを Deep Blue (#153b93) に変更。
*   **v9.2 (Stable)**: Sidebar Toggle, Scroll Event Fix.
*   **v9.0**: Mouse Wheel Resizing.
*   **v8.0**: Custom UI Styling (Accent Rounded).
*   **v7.0 - v7.2**: Collection Bucket, PDF Converter.

---

## 6. ビルド情報
```powershell
./build_v20.bat
```
