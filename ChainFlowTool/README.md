
# Chain Flow Filer v16.2 (Alpha)

**Unleash Your Workflow.**  
Chain Flow Filer is a keyboard-centric, high-performance file manager designed for power users who demand efficiency.

---

## 🚀 What is New in v16.2?

v16.2 introduces an **Integrated Markdown Editor** and complete **Dark Theme Unification**.

### 1. Integrated Markdown Editor
*   **Launch from Filer**: Double-click any `.md` file to open the built-in editor.
*   **Real-time Preview**: See your Markdown rendered as you type (dark theme).
*   **PDF Export**: Export to professional, print-ready PDF (white background, proper typography).
*   **Slash Menu (Ctrl+P)**: Quick access to commands and Markdown snippets.

### 2. Dark Theme Unification
*   **Title Bars**: Both Filer and Editor now feature dark title bars (Windows 10/11).
*   **Message Boxes**: All dialogs match the dark theme.
*   **New Panes**: Dynamically created panes no longer flash white.

### 3. Editor-Filer Coordination
*   **Automatic Cleanup**: Closing the Filer automatically closes any open Editor windows.
*   **Unified Icons**: Editor displays the same app icon in the taskbar.

---

## 🚀 Previous Major Features

### Context Highlight (Alt Hold)
Hold the `Alt` key to visualize the full file hierarchy:
*   **Ancestors**: Parent folders are highlighted and scrolled into view.
*   **Descendants**: Child panes showing folder contents glow gold.

### Freeze Prevention (v14.2)
*   Heavy file operations run in background threads.
*   Cancelable progress dialog for long operations.

### Quick Look (Space)
*   Instant file preview without opening external apps.
*   Copy button for text and image content.

---

## 🎮 Key Controls (Cheat Sheet)

| Key | Action |
| :--- | :--- |
| **Space** | **Quick Look** (Preview file content) |
| **Ctrl+P** | **Command Palette / Slash Menu** |
| **Alt + Click**| **Mark Item** (Add to "Collection Bucket") |
| **Alt + C** | **Clear Marks** (Empty the bucket) |
| **Alt (Hold)**| **Context Highlight** (Show ancestors/descendants) |
| **Q / Backspace**| Go Up (Parent Directory) |
| **V** | New Vertical Lane |
| **N** | New Horizontal Pane |
| **W / Shift+W** | Close Pane / Close View |
| **Ctrl+B** | Toggle Sidebar |
| **Ctrl+Shift+R** | Reset Layout |
| **F5** | Refresh All Panes |

---

## 🛠 Installation & Usage

This application is distributed as a **Portable App**.

1.  **Unzip**: Extract the provided archive.
2.  **Run**: Double-click `ChainFlowFiler.exe` inside the folder.
3.  **Portable**: All settings are saved within the same folder.

---

## 💡 Tips
*   **Mark & Drag**: Use `Alt+Click` to mark files across multiple folders, then drag them all at once.
*   **Quick Copy**: Press `Space` on an image, then click "Copy Content" to copy it to clipboard.
*   **Editor PDF**: The PDF export uses professional styling (white background) even though the preview is dark.

---

## 📜 Version History
*   **v16.2**: Integrated Markdown Editor, Dark Theme Unification, Editor Lifecycle Management.
*   **v16.0**: Satellite Editor Architecture, Slash Menu System.
*   **v15.0**: Full Row Highlight, New File Creation, QuickLook Edit.
*   **v14.2**: Freeze Prevention (Async File Ops), Fix Ancestral Highlight.
*   **v14.0**: Context Highlight (Alt), F5 Refresh, Layout Reset.
*   **v13.0**: Layout Reset (Ctrl+Shift+R).
*   **v12.0**: Sidebar Refactoring, Hover-to-Act.

---

## 📦 Build Information
```powershell
py -m PyInstaller ChainFlowFiler.spec --clean
```
