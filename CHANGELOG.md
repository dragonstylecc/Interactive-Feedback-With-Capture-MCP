# Changelog

## v0.3.0

### New Features
- **Adaptive heartbeat** — Dynamic frequency: 10s (0-10min), 60s (10-60min), 5min (60min+)
- **SOFT_TIMEOUT** — Proactive return before hard timeout (~58min), Agent can re-invoke to continue
- **Quick Reply** — ⚡ button with preset replies and direct-submit mode
- **Settings page** — ⚙ gear button to configure default toggles and manage quick replies
- **Bottom toggles** — "使用中文" and "重新读取Rules" quick switches
- **Thumbnail preview** — Click screenshot thumbnails to open full-size preview
- **Drag & drop images** — Drag image files from file explorer directly into the window
- **File-lock window management** — Cross-process reliable window ID assignment
- **Server logging** — Timestamped logs to temp directory with 2MB rotation
- **Version display** — Version shown in window title bar, VERSION file added
- **Cursor Rules file** — Out-of-box `.cursor/rules/mcp-feedback.mdc`

### Improvements
- Stale lock file auto-cleanup on process crash
- Window ID capped at 20 to prevent runaway loops
- Empty feedback no longer appends Chinese/Rules hints
- Dark theme applied consistently to Settings and Preview dialogs

## v0.2.7
- Fix: Windows feedback window stuck/invisible issue
- Force foreground window activation with `SetForegroundWindow`

## v0.2.6
- Docs: Cross-platform support documentation (Linux/macOS/Windows)

## v0.2.5
- Docs: English README with language toggle

## v0.2.4
- Remove `.python-version`, use `pyproject.toml` requires-python>=3.11

## v0.2.3
- Timeout config optimization, multi-Agent window management, orphaned window auto-cleanup

## v0.2.0
- Copyable/scrollable message area with Copy button
- Heartbeat keep-alive mechanism

## v0.1.0
- Initial release: screenshot feedback (capture, clipboard, browse)
- Predefined options support
- Dark theme UI
