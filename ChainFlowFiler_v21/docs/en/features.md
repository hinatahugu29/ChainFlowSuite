# Feature Details

Detailed explanation of Chain Flow Filer's unique features.

## 1. Integrated Markdown Editor (v16.2)

A lightweight editor for editing Markdown files directly from the file manager.

### How to Launch
*   Double-click any `.md` file in the file list
*   Select `Launch Editor` from Slash Menu (Ctrl+P)

### Features
*   **Real-time Preview**: Edit text on the left, see rendered output on the right instantly
*   **Dark Theme**: Editor matches the app's unified dark theme
*   **PDF Export**: Export PDF button generates professional document style (white background, black text)
*   **Slash Menu**: Access commands and Markdown snippets via Ctrl+P

### Supported Markdown Syntax
*   Headings (`#`, `##`, `###`)
*   Bold/Italic (`**bold**`, `*italic*`)
*   Code blocks (` ``` `)
*   Tables
*   Blockquotes (`>`)
*   Strikethrough (`~~text~~`)
*   Horizontal rules (`---`)
*   Inline code (`` `code` ``)

---

## 2. Navigation Sidebar (v12.0)

The sidebar is divided into three sections:

*   **STANDARD**: System standard folders like Desktop, Documents, Downloads.
*   **FAVORITES**: User-registered favorite folders.
*   **DRIVES**: List of connected drives.

### Resizing and Layout
You can drag the boundaries (splitters) of each section to adjust them.
*   **Shift + Wheel**: Change section height.

---

## 3. Quick Look

The preview feature, invoked with the `Space` key.

*   **Code Preview**: Syntax highlighting for Python, JS, Markdown, AHK.
*   **Image Preview**: Supports common image formats.
*   **Copy Content**: Copy text or image data to clipboard.

---

## 4. Context Highlight (v14.0)

Hold the `Alt` key to visualize the context of the selected file.

*   **Upstream (Ancestors)**: Parent folders highlighted and scrolled into view
*   **Downstream (Descendants)**: Child panes showing folder contents glow gold

---

## 5. PDF Conversion

In environments with MS Office or LibreOffice, right-click document files to **Convert to PDF**.
Combined with the marking feature, batch convert multiple documents at once.

---

## 6. Extended Context Menu

The right-click menu includes convenient features:

*   **Create Shortcut**: Create a shortcut in the current folder.
*   **Copy Path Special**:
    *   `Copy Unix Path`: Copy with slashes instead of backslashes.
    *   `Copy as "Path"`: Copy enclosed in double quotes.

---

## 7. Dark Theme Unification (v16.2)

The entire app is unified with a complete dark theme.

*   **Title Bars**: Darkened using Windows DWM API
*   **Message Boxes**: Confirmation dialogs also use dark theme
*   **Dynamic Panes**: Newly created panes start with dark background
