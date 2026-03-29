# AI Handover Document: Sniper Research Shell

This document is intended for future AI assistants to quickly understand the architecture, design philosophy, and specific technical "quirks" (hard-earned fixes) of the `Sniper Research Shell` project.

## 1. Project Overview & Architecture
The application is a PyQt6/PySide6 based custom web browser tailored for web scraping, data extraction ("sniping"), and research organization.

In Phase 9 (latest), the huge monolithic `main.py` was structurally refactored into a highly modular `core/` package to support upcoming complex output features (Export, AI context, Scrapbook).

**Directory Structure:**
- `main.py`: A tiny execution entry point.
- `core/main_window.py`: The orchestrator, sets up the 3-pane layout (`Favorites/History` -> `QWebEngineView` -> `Extraction List`).
- `core/browser.py`: Contains `SniperBrowser` (overrides createWindow to force single-window mode).
- `core/bridge.py`: Contains `SniperBridge` for two-way communication via `QWebChannel` between JS and Python.
- `core/widgets.py`: Custom UI (e.g., `ExtractionItemWidget` with accordion expansion, `ClipboardPopup` for always-on-top detach feature).
- `core/storage.py`: Manages reading/writing persistence like `favorites.json`.
- `resources/sniper.js`: The frontend DOM manipulation logic (A/Z/C key hold modes, outline highlighting, markdown parsing).
- `resources/theme.qss`: Premium dark theme CSS overrides.

## 2. Hard-Earned Knowledge & Quirks (CRITICAL)
If you modify this app, **DO NOT** revert the following fixes without careful consideration. They solve nasty, obscure bugs found through extensive trial and error.

### UI & Aesthetics
- **QListWidget Visual Glitch**: By default, PySide6 draws an ugly orange focus dotted outline on selected items, clashing with the dark theme. AND selected items (`#89b4fa` background) make grey text invisible. 
  - *Fix*: `outline: none;` added to `theme.qss` for `QListWidget`. And `QListWidget::item:selected` uses `rgba(137, 180, 250, 0.15)` with a left accent border.

### PySide6 / QtWebEngine Quirks
- **Slot 'X' not found Error**: When a Python method is connected to a native C++ signal (`titleChanged`, `itemClicked`), PySide6 6.6+ can throw fatal binding errors if the target method lacks explicitly typed slot decorators.
  - *Fix*: All bridge and main window endpoints are explicitly decorated with `@Slot(str)` or `@Slot(QListWidgetItem)`.
- **qwebchannel.js Double Injection Panic**: If you use `QWebEngineScript` injected at the `Profile` level (`setInjectionPoint(QWebEngineScript.DocumentReady)`), it runs flawlessly across all frames/iframes. 
  - *Trap*: If you ALSO try to inject `qwebchannel.js` via `runJavaScript` on the `loadFinished` event (legacy way), the channel object (`qt.webChannelTransport`) will be overwritten or unresolved (`Uncaught ReferenceError: qt is not defined`). The legacy `loadFinished` method was completely eradicated.
- **Session Persistence for Internal Systems**: `QWebEngineProfile.defaultProfile()` evaporates state on exit. Even if you use a named profile, normal configuration drops "Session Cookies" (cookies without an expiration date, which 99% of internal enterprise systems use).
  - *Fix*: The profile MUST be named (`QWebEngineProfile("SniperProfile", self)`) AND the `PersistentCookiesPolicy` MUST be explicitly set to `ForcePersistentCookies`. This mimics Chrome's "Continue where you left off" setting and magically solves internal system relogin prompts.
- **Google "Insecure Browser" Block**: Google login pages instantly block QtWebEngine out of the box. 
  - *Fix*: Spoofed the UA via `self.profile.setHttpUserAgent(firefox_ua)`. 

### JavaScript (sniper.js) Event Interference
- **The "Native Browsing" Problem**: Previously, capturing `click` and `click` with `preventDefault()` hijacked *normal* web interactions (like expanding a dropdown or clicking a standard link).
  - *Fix*: UX was completely redesigned into **"Hold-To-Activate"**. Variables `isDirectMode` (A-key) and `isStructMode` (Z-key) are only `true` *while the key is held down*. Click listeners immediately ignore the event if these flags are false, allowing the browser to act 100% natively without DOM event bleeding.
- **Extracting Data from `Disabled` or Form Elements**: Normally `pointer-events: none` on disabled buttons prevents capturing them. 
  - *Fix*: `sniper.js` injects CSS that forces `pointer-events: auto !important` and `cursor: crosshair` on `disabled`, `input`, and `textarea` elements.
- **Z-Index Wars**: If the bounding box outline `div` is appended to `document.body`, absolute positioning inside `relative` containers clips it or hides it behind other z-indexed layers.
  - *Fix*: The highlight box is strategically appended to `document.documentElement` to exist outside standard body stacking contexts as much as possible.

## 3. Next Steps
The next AI session should focus on the **Output Layer**.
The foundational "input" mechanisms are rock solid. Future implementations should naturally plug into `core/storage.py` and `core/main_window.py`:
- Save `extraction_list` to a merged Markdown or CSV (`Export` feature).
- Pass extracted lists to an LLM endpoint for structuring/summarization (`AI Context` feature).
- Manage screenshot serialization mapped to captured DOM nodes (`Scrapbook` feature).
