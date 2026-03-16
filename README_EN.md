[中文](README.md) | **English**

# 🗣️ Interactive Feedback With Capture MCP

An enhanced version of [Interactive Feedback MCP](https://github.com/poliva/interactive-feedback-mcp) with **screenshot feedback** support.

A simple [MCP Server](https://modelcontextprotocol.io/) for human-in-the-loop workflows in AI-assisted development tools like [Cursor](https://www.cursor.com), [Cline](https://cline.bot), and [Windsurf](https://windsurf.com). Supports both text feedback and **screenshot feedback**, allowing AI to directly "see" your screen content.

> **Note:** This server is designed to run locally, requiring direct access to the user's operating system for displaying notification windows and capturing screenshots.

## ✨ Screenshot Feedback

Built on top of the original text-only feedback, the following screenshot capabilities are added:

- **📷 Full Screen Capture** — Click to auto-minimize the feedback window, capture the full screen, then restore
- **📋 Clipboard Paste** — Paste via button or `Ctrl+V` in the text box (Windows: `Win+Shift+S`, Linux: system screenshot tool, macOS: `Cmd+Shift+4`)
- **📁 Browse Images** — Select image files locally (PNG, JPG, BMP, GIF, WebP)
- **🖼️ Thumbnail Preview** — Attached screenshots show thumbnail previews, individually removable
- **📐 Auto Compression** — Images larger than 1600px are automatically scaled down proportionally

Screenshots are returned to AI via MCP Image content type, allowing AI to directly view the screenshot content.

## ✨ Enhanced Message Display

- **📋 One-Click Copy** — Copy button at the top of the message area to copy full content to clipboard
- **🖱️ Text Selectable** — Message content supports mouse selection and `Ctrl+C` copy
- **📜 Scrollable** — Long text automatically shows a vertical scrollbar
- **🔍 Thumbnail Zoom** — Click screenshot thumbnails to open a full-size preview dialog

## ⚡ Quick Reply

The feedback window provides a "⚡ Quick Reply" button at the bottom:
- **One-click fill** — Choose from preset replies to auto-fill the text box
- **Direct submit** — Select "⚡ prefixed" options to auto-submit without clicking Send
- **Preset list** — Built-in common replies like "No problem, continue", "Need adjustments", etc.
- **Customizable** — Persisted via QSettings, supports custom quick reply lists

## ⏱️ Timeout & Connection Management

### Timeout Configuration

The feedback window waits for user input and may last a long time. The `timeout` in MCP configuration is a **hard limit** — exceeding it will cause the tool call to fail.

**Recommend setting `timeout` to a sufficiently large value** (e.g., 3600 seconds = 1 hour):

```json
"timeout": 3600
```

### Adaptive Heartbeat & SOFT_TIMEOUT

The server sends adaptive-frequency heartbeats via `report_progress` while waiting:

| Wait Duration | Heartbeat Interval | Notes |
|--------------|-------------------|-------|
| 0 ~ 10 min | 10 seconds | High-frequency initial monitoring |
| 10 ~ 60 min | 60 seconds | Reduced frequency to minimize noise |
| 60 min+ | 5 minutes | Low-frequency keep-alive |

Heartbeat features:
- **Connection Detection** — After **3 consecutive** failures, the client is assumed disconnected and the **orphaned feedback window is automatically closed**
- **SOFT_TIMEOUT** — After ~58 minutes, proactively returns a prompt message so the Agent can re-invoke to continue (avoids hard timeout -32001 errors)
- **Auto Retry** — After closing an orphaned window, automatically retries once
- **Fallback** — If retry fails, prompts the Agent to switch to the built-in `AskQuestion` tool

### Multi-Agent Parallel Support

When multiple Agents run in parallel within the same project, each Agent's feedback window is independently managed:
- Window titles display dynamic numbering (`#1`, `#2`...) to distinguish different Agent requests
- **File-lock based** cross-process window ID management with automatic lowest-available assignment
- Windows do not interfere with each other; users can handle multiple feedback requests simultaneously

## 🔘 Bottom Quick Toggles

Two quick toggles at the bottom of the feedback window:
- **Use Chinese** — Checked by default, auto-appends `(请使用中文回复和思考)` to ensure AI responds in Chinese
- **Reload Rules** — Unchecked by default, appends `(请重新读取 Cursor Rules)` when checked

Toggle states are persisted via QSettings and automatically restored on next launch.

## ⚙️ Settings Page

Click the **⚙ gear button** at the bottom of the feedback window:
- **Default Toggles** — Configure default states for "Use Chinese" and "Reload Rules"
- **Quick Reply Management** — Add/edit/delete custom quick reply presets
- **Reset to Defaults** — Restore the default quick reply list

## 📋 Logging & Troubleshooting

Server logs are written to the temp directory:
- **Log path** — `%TEMP%/mcp_feedback_server.log` (Windows) or `/tmp/mcp_feedback_server.log` (Linux/macOS)
- Records tool calls, heartbeat events, timeouts, errors, and other key information
- Useful for debugging connection issues and UI launch failures

## 🖥️ Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows | ✅ Fully supported | Recommended |
| macOS | ✅ Fully supported | — |
| Linux (X11) | ✅ Fully supported | Requires desktop environment |
| Linux (Wayland) | ⚠️ Partial support | Full screen capture may be restricted by security policies |

**Linux Notes:**
- A **graphical desktop environment** (GNOME, KDE, etc.) is required — headless servers cannot display the feedback window
- Under Wayland, `grabWindow` full-screen capture may be limited; use clipboard paste as an alternative
- Screenshot shortcuts vary by desktop environment (e.g., GNOME uses `PrtSc`, KDE uses `Spectacle`); capture a region and paste it into the feedback window via clipboard

## 🖼️ Example

![Interactive Feedback With Capture](https://raw.githubusercontent.com/dragonstylecc/Interactive-Feedback-With-Capture-MCP/refs/heads/main/.github/example.png)

## 💡 Why Use It?

In environments like Cursor, every prompt sent to the LLM counts as a separate request toward your monthly quota (e.g., 500 premium requests). When iterating on vague instructions or correcting misunderstood outputs, each follow-up clarification triggers a full new request — very inefficient.

This MCP server provides a solution: it allows the model to pause and request clarification before completing its response. The model triggers a tool call (`interactive_feedback`) to open an interactive feedback window where you can provide more details or request changes — while the model continues the same request session.

Since tool calls don't count as separate premium interactions, you can loop through multiple feedback cycles without consuming additional requests.

- **💰 Reduce API Calls:** Avoid wasting expensive API calls on guesswork
- **✅ Fewer Errors:** Clarifying before acting means less broken code
- **⏱️ Faster Iteration:** Quick confirmation beats debugging wrong guesses
- **🎮 Better Collaboration:** Turn one-way instructions into a dialogue, keeping you in control
- **📸 Visual Communication:** Screenshots let AI see the problem directly, more intuitive than text descriptions

## 🛠️ Tools

This server exposes the following tool via the MCP protocol:

- `interactive_feedback`: Ask the user a question and return the answer. Supports predefined options and **screenshot attachments**.

## 📦 Installation

1.  **Prerequisites:**
    *   Python 3.11 or newer
    *   [uv](https://github.com/astral-sh/uv) (Python package manager):
        *   Windows: `pip install uv`
        *   Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
        *   macOS: `brew install uv`
2.  **Get the code:**
    ```bash
    git clone https://github.com/dragonstylecc/Interactive-Feedback-With-Capture-MCP.git
    ```

## ⚙️ Configuration

1. Add the following configuration to `claude_desktop_config.json` (Claude Desktop) or `mcp.json` (Cursor):

**Replace `/path/to/interactive-feedback-mcp` with the actual path where you cloned the repository.**

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/interactive-feedback-mcp",
        "run",
        "server.py"
      ],
      "timeout": 3600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

2. **Cursor Rules file (recommended):**

   The project includes an out-of-box Rules file `.cursor/rules/mcp-feedback.mdc`. Copy it to your project:

   ```bash
   cp -r /path/to/interactive-feedback-mcp/.cursor/rules/ /your/project/.cursor/rules/
   ```

   Or manually add to Cursor Settings > Rules > User Rules:

   > If a request or instruction is unclear, use the interactive_feedback tool to ask the user clarifying questions before proceeding. Do not make assumptions.
   > Provide predefined options to the user via the interactive_feedback MCP tool whenever possible to facilitate quick decision-making.
   > Each time you are about to complete a user request, call the interactive_feedback tool to ask for user feedback before finalizing the process. If the feedback is empty, you may end the request and must not call the tool in a loop. If the tool call fails, use the built-in AskQuestion tool.

## 📸 Screenshots & Image Attachments

| Method | Description |
|--------|-------------|
| 📷 Capture Screen | Auto-minimizes window, captures entire screen, then restores |
| 📋 Paste Clipboard | Paste copied screenshots (Windows: `Win+Shift+S`, macOS: `Cmd+Shift+4`, Linux: system tool) |
| 📁 Browse... | Select image files from local filesystem (PNG, JPG, BMP, GIF, WebP) |
| 🖱️ Drag & Drop | Drag image files from file explorer directly into the window |
| ⌨️ Ctrl+V | Paste clipboard images in the text box |

Thumbnails are shown inline. **Click a thumbnail to preview full-size.** Click ✕ to remove.

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Submit feedback |
| `Ctrl+V` | Paste clipboard image |

## 🙏 Acknowledgements

This project is based on the following excellent projects:

- Original project developed by Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira))
- Enhanced by Pau Oliva ([@pof](https://x.com/pof)), inspired by Tommy Tong's [interactive-mcp](https://github.com/ttommyth/interactive-mcp)
- Screenshot feedback added by [dragonstylecc](https://github.com/dragonstylecc)
- v0.3.0 features partially inspired by [rooney2020/qt-interactive-feedback-mcp](https://github.com/rooney2020/qt-interactive-feedback-mcp) (adaptive heartbeat, SOFT_TIMEOUT, quick reply, settings page, etc.)
