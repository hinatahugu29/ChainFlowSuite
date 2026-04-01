# Change Log

All notable changes to this project will be documented in this file.

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
