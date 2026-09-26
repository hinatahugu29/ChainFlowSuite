# Change Log

All notable changes to this project will be documented in this file.

## [v23.10] - 2026-09-26

### Fixed
- **作り直したファイルが日付ソートで動かなかった**: ZIP の作り直しや同名への上書きコピーのように、行が増減せず中身だけが変わる操作のあと、更新日時で並べ替えても順位が古いままでした。プロキシがメタデータをパス単位でキャッシュしており、行の挿入・削除でしか捨てていなかったためです(`dataChanged` を見ていなかった)。一覧に出ている更新日時とサイズの表示自体は元から追随していたので、「表示は新しいのに一番下に沈んだまま」という形で出ていました。更新された行のキャッシュを捨てて並べ替え直すようにしています。連続する通知は120msでまとめるため、フォルダ読み込みは遅くなりません(5,000件で実測 1,225ms → 1,202ms)。

### Fixed (tests)
- **テストを全部まとめて実行するとプロセスごと落ちていた**: `test_file_worker` が非GUIの `QCoreApplication` を作っており、ウィジェットを使うテストが同じプロセスでそれを掴むためでした。生成を `tests/__init__.py` に一本化しています。

### Added
- **単体テスト**: 44件。上記の並べ替えの回帰を止めるテストを追加しました。

---

## [v23.9] - 2026-09-12

### Added
- **Undo (Ctrl+Z)**: 移動・リネーム・コピーを取り消せるようになりました。移動とリネームは元の場所へ正確に戻し、コピーは作られた複製をゴミ箱へ送ります(元は触りません)。戻し先に別の項目ができている場合は、黙って上書きせず中止して理由を表示します。インライン編集中の Ctrl+Z はテキストの取り消しのままです。
- **BUCKET セクション**: Alt+Click で集めた項目をサイドバーに常設表示します。件数、名前、元フォルダが一覧でき、ダブルクリックでその場所へ移動、ボタンで現在のフォルダへ一括コピー/移動ができます。タブごとに独立し、セッションに保存されるため再起動後も残ります。
- **上書き確認ダイアログ**: ペースト時に同名の項目があると、既存と貼付側のサイズ・更新日時を並べて確認します。上書き / 新しければ上書き / スキップ / 別名で保存 / 操作を中止 から選べ、複数衝突時は一括適用できます。
- **単体テスト**: `py -m unittest discover -s tests -v` で43件。ファイル操作・削除・Undo の回帰を止めます。

### Fixed
- **削除がゴミ箱を経由していなかった**: `QFileSystemModel.remove()` による完全削除だったため、Delete キー + Yes で復元不能でした。`SHFileOperationW` (FOF_ALLOWUNDO) 経由に変更。ゴミ箱に入らず完全削除になる場合は OS の警告を出します。
- **コピー/移動の失敗が「成功」と報告されていた**: 個々の例外を stderr に print するだけで常に `finished(True)` を emit していたため、移動に失敗しても完了表示になっていました。失敗を集計して内訳とともに報告します。
- **フォルダコピーの進捗が動かず、キャンセルも効かなかった**: `shutil.copytree()` の一発呼び出しだったためです。ファイル単位に分解し、進捗の分母も総ファイル数に変更しました。
- **同名衝突が黙って連番になっていた**: 上書き確認が無く、貼り直しでの差し替えができませんでした(上記 Added を参照)。
- **Filer の終了で Suite ツールが道連れに落ちていた**: `closeEvent` が起動した全ツールを `terminate()` していたため、Writer や ToDo の未保存作業が失われました。参照を手放すだけに変更しています。
- **ファイル操作中でも無言で終了できていた**: 実行中は確認し、中断を選んだ場合のみキャンセルして終了します。
- **自分自身・自分の内側・同一フォルダへの移動**を事前に拒否するようにしました。

---

## [v23.5] - 2026-07-05

### Improved
- **Native Bulk Sort**: Added `compute_rank_order()` to the Rust native core (`chainflow_core`). When a folder is opened, all item metadata is sent to the native engine in a single call, which returns a fully sorted rank order. `lessThan()` now does an O(1) dictionary lookup per comparison instead of a per-pair Rust call + metadata construction.
    - Benchmarked on a 5,000-file folder: sort time reduced by roughly 30-65% depending on the sort column (e.g. Date sort: ~1048ms → ~355ms).
- **Filter Fast-Path**: `filterAcceptsRow()` skips the expensive path-normalization step for rows that are clearly not ancestors of the current folder (based on a cheap path-length check), reducing per-row overhead when navigating.

## [v23.4] - 2026-04-20

### Added
- **Folder Shortcut Integration**: Shortcuts (.lnk) pointing to folders now behave like actual folders.
    - Single click: Shows the target folder's content in the right pane.
    - Double click: Navigates into the target folder.
- **Plugin Context Awareness**: Fixed an issue where the current folder path was not being passed to Search, Designer, and other tools. Tools now correctly inherit the view's context.
- **Improved Taskbar AppID**: Standardized AppID to `ChainFlow.Filer.v23.4`.

### Fixed
- **Nuitka Build Stability**: Resolved "compiler overflow" errors with Pillow by streamlining included modules and adjusting heap settings.
- **Binary Path Resolution**: Robust implementation of dual-path strategy (EXE/Internal vs Dev) to ensure tools launch correctly across all environments.
- **Performance**: Enabled Link Time Optimization (LTO) for Nuitka-compiled binaries to improve runtime execution speed.

---

## [v20.1] - 2026-02-09

### Added
- **Chain Flow Search**: A new standalone, tabbed file search utility integrated with Filer.
- **PDF Merger Dark Theme**: Applied consistent dark title bar to the PDF Merger window.

### Fixed
- **Highlight Persistence**: Fixed a bug where context highlight remained active after Alt-Tab.
- **Cursor Reset**: Fixed an issue where the cursor remained in "Wait" state after PDF conversion.

---

## [v17.0] - 2026-02-02

### Added
- **HTML Quick Look**: High-fidelity HTML preview using Chromium-based `QWebEngineView`. Supports unlimited scrolling and complex CSS.
- **HTML PDF Export**: Export currently viewed HTML to PDF with one click.
- **Unified Scrollbar**: Custom CSS injection to style the WebEngine scrollbar matching the app's dark theme.
- **Chromium Warm-up**: Pre-load logical added to initialization to preventing GUI flashing on first use.

### Changed
- **Build Size**: Application size increased (~640MB) due to inclusion of QtWebEngine binaries.

### Fixed
- **Initial Scroll Issue**: Fixed a focus timing issue where scrolling wouldn't work immediately after opening a large HTML file.
- **GUI Flash**: Resolved an issue where the main window would briefly disappear when initializing the GPU process.

---

## [v16.2] - 2026-02-02

### Added
- **Integrated Markdown Editor**: Launch a powerful Markdown editor directly from the file manager. Features real-time preview, Slash Menu (Ctrl+P), and professional PDF export.
- **PDF Print-Friendly Export**: PDF output uses a white-background, professional document style while maintaining dark theme for preview.
- **Dark Theme Unification**: Complete dark theme including window title bars (Windows DWM API), message boxes, and dynamically created panes.
- **Editor Lifecycle Management**: Editor windows are automatically closed when the main Filer window closes.
- **AppUserModelID**: Editor now displays its own icon in the Windows taskbar instead of Python's.

### Fixed
- **Quick Look Overlay**: Removed `WindowStaysOnTopHint` to prevent Quick Look from floating over unrelated windows.
- **White Pane Background**: Fixed issue where new panes created with N-key had a white background.
- **Slash Key Conflict**: Removed `/` key binding; Slash Menu is now exclusively triggered by `Ctrl+P`.

### Changed
- Disabled sidebar HELP section (Cheat Sheet) as shortcuts need review.
- PDF export default directory now uses the current file's directory.

---

## [v16.0] - 2026-02-01

### Added
- **Satellite Editor Architecture**: Introduced a separate Markdown editor (`editor.py`) that launches as a subprocess.
- **Slash Menu System**: Command palette for quick actions in both Filer and Editor.
- **Enhanced Markdown Support**: Added quote, strikethrough, horizontal rule, and inline code snippets.

---

## [v15.0] - 2026-01-31

### Added
- **Full Row Highlight**: Alt-key highlighting now applies to the entire row for improved visibility.
- **Multi-View Support**: Highlights work correctly when the same folder is open in multiple panes.
- **Empty Folder Support**: Context highlights now work even for empty folders.
- **New File Creation**: Added "New File..." context menu option.
- **Quick Edit (QuickLook)**: Edit and Save buttons in QuickLook window.

### Fixed
- **Header UI**: Fixed white margin on the right edge of column headers.

---

## [v14.2] - 2026-02-01

### Added
- **Freeze Prevention**: Copy, Move, ZIP compression, and Unzipping operations are now processed in background threads to prevent UI freezing during large file operations.
- **Progress Dialog**: Added a progress dialog with cancel capability for long-running file operations.
- **Non-blocking PDF Conversion**: LibreOffice PDF conversion now runs asynchronously.

### Fixed
- **Ancestral Highlight**: Fixed an issue where ancestor path highlighting was not correctly displayed when traversing to the root directory.

---

## [v14.0] - 2026-01-30

### Added
- **Context Highlight**: Hold Alt key to highlight ancestor (upstream) and descendant (downstream) panes simultaneously.
- **F5 Refresh**: Reload all panes in the current tab with F5.
- **Layout Reset**: Ctrl+Shift+R to reset all pane/lane sizes to equal distribution.

---

## [v13.0 - v9.0] - Earlier Releases

See PROJECT_DOC.md for detailed history.
