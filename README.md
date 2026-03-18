**中文** | [English](README_EN.md)

# 🗣️ Interactive Feedback With Capture MCP

基于 [Interactive Feedback MCP](https://github.com/poliva/interactive-feedback-mcp) 的增强版本，新增**截图反馈**功能。

一个简单的 [MCP Server](https://modelcontextprotocol.io/)，用于在 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot)、[Windsurf](https://windsurf.com) 等 AI 辅助开发工具中实现人机协作工作流。不仅支持文字反馈，还支持**截图反馈**，让 AI 能够直接"看到"你的屏幕内容。

> **注意：** 本服务器设计为本地运行，需要直接访问用户操作系统来显示通知窗口和截图。

## ✨ 新增功能：截图反馈

在原版纯文字反馈的基础上，新增了以下截图能力：

- **📷 全屏截图** — 点击按钮自动最小化反馈窗口，截取全屏后恢复窗口
- **📋 剪贴板粘贴** — 支持按钮粘贴或在文本框中 `Ctrl+V` 直接粘贴截图（Windows: `Win+Shift+S`，Linux: 系统截图工具，macOS: `Cmd+Shift+4`）
- **📁 浏览图片** — 支持从本地文件选择图片（PNG、JPG、BMP、GIF、WebP）
- **🖼️ 缩略图预览** — 已添加的截图显示缩略图预览，支持单独删除
- **📐 自动压缩** — 超过 1600px 的大图自动等比例缩放

截图通过 MCP Image 内容类型返回给 AI，让 AI 可以直接查看截图内容。

## ✨ 提示内容增强

- **📝 Markdown 渲染** — AI 消息区域支持 Markdown 格式渲染（标题、粗体、代码块、列表等），大幅提升可读性
- **📋 一键复制** — 提示消息区域顶部提供 Copy 按钮，一键复制完整内容到剪贴板
- **🖱️ 文字可选** — 提示内容支持鼠标选择和 `Ctrl+C` 复制
- **📜 滚动显示** — 长文本自动出现垂直滚动条，不再因内容过多而显示不全
- **🔍 缩略图放大** — 点击截图缩略图弹出全尺寸预览窗口

## ⚡ 快捷回复

反馈窗口底部提供「⚡ Quick Reply」按钮，支持：
- **一键填入** — 从预设列表中选择常用回复，自动填入文本框
- **直接提交** — 选择「⚡ 前缀」选项后自动提交，无需再点 Send
- **预设列表** — 内置 "没问题，继续"、"还需要调整"、"确认，提交推送" 等常用回复
- **自定义扩展** — 通过 QSettings 持久化存储，支持自定义快捷回复列表

## ⏱️ 超时与连接管理

### 超时配置

反馈窗口需要等待用户输入，可能持续较长时间。MCP 配置中的 `timeout` 是**硬性上限**，超过该时间工具调用将直接超时失败。

**建议将 `timeout` 设置为足够大的值**（如 3600 秒 = 1 小时），以避免长时间等待时连接断开：

```json
"timeout": 3600
```

### 自适应心跳与 SOFT_TIMEOUT

服务器在等待用户输入期间，通过 `report_progress` 发送自适应频率的心跳：

| 等待时长 | 心跳间隔 | 说明 |
|---------|---------|------|
| 0 ~ 10 分钟 | 10 秒 | 初期高频监控 |
| 10 ~ 60 分钟 | 60 秒 | 中期降频减少噪音 |
| 60 分钟以上 | 5 分钟 | 长时间低频保活 |

心跳机制用于：
- **连接检测** — 连续 **3 次**心跳失败后，判定客户端已断开，**自动关闭孤立的反馈窗口**
- **SOFT_TIMEOUT** — 等待超过约 58 分钟后主动返回提示消息，Agent 可重新调用继续对话（避免硬超时 -32001 错误）
- **自动重试** — 孤立窗口关闭后，自动尝试重新弹出反馈窗口一次
- **备用方案** — 重试仍失败时返回错误信息，Agent 自动切换到内置 `AskQuestion` 工具

### 多 Agent 并行支持

当同一项目中有多个 Agent 并行运行时，每个 Agent 的反馈弹窗独立管理：
- 窗口标题显示动态编号（`#1`、`#2`...），方便区分不同 Agent 的请求
- 基于**文件锁**的跨进程窗口 ID 管理，编号自动分配最小可用值
- 各窗口互不干扰，用户可同时处理多个反馈

## 🔘 底部快捷开关

反馈窗口底部提供两个快捷开关：
- **使用中文** — 默认勾选，自动在反馈末尾追加 `(请使用中文回复和思考)`，确保 AI 全程中文
- **重新读取Rules** — 默认不勾选，勾选后追加 `(请重新读取 Cursor Rules)`

开关状态通过 QSettings 持久化保存，下次打开窗口自动恢复。

## ⚙️ 设置页面

点击反馈窗口底部的 **⚙ 齿轮按钮** 打开设置：
- **默认开关** — 配置"使用中文"和"重新读取Rules"的默认勾选状态
- **快捷回复管理** — 添加/编辑/删除自定义快捷回复列表
- **一键重置** — 恢复默认快捷回复列表
- **版本检查与更新** — 检查 PyPI/GitHub 最新版本，一键更新（源码用户 `git pull`，pip 用户 `pip install --upgrade`）

### 🔄 自动更新

- **启动时检查** — 窗口打开时自动后台检查最新版本，标题栏显示 `⬆ vX.Y.Z available`
- **设置页手动检查** — 点击「Check for updates」按钮手动检查
- **一键更新** — 点击「Update now」按钮自动执行更新，更新后提示重启 MCP 服务
- **uvx 用户** — 使用 `uvx interactive-feedback-with-capture@latest` 总是运行最新版

## 📋 日志与排查

服务器运行日志自动写入临时目录：
- **日志路径** — `%TEMP%/mcp_feedback_server.log`（Windows）或 `/tmp/mcp_feedback_server.log`（Linux/macOS）
- 记录工具调用、心跳事件、超时、错误等关键信息
- 方便排查连接问题和 UI 启动失败

## 🖥️ 平台支持

| 平台 | 支持状态 | 备注 |
|------|---------|------|
| Windows | ✅ 完整支持 | 推荐平台 |
| macOS | ✅ 完整支持 | — |
| Linux (X11) | ✅ 完整支持 | 需要桌面环境 |
| Linux (Wayland) | ⚠️ 部分支持 | 全屏截图可能受安全策略限制 |

**Linux 注意事项：**
- 需要安装**图形桌面环境**（GNOME、KDE 等），无头服务器无法显示反馈窗口
- Wayland 环境下 `grabWindow` 全屏截图可能受限，建议使用剪贴板粘贴方式替代
- 截图快捷键因桌面环境而异（如 GNOME 使用 `PrtSc`，KDE 使用 `Spectacle`），截取后通过剪贴板粘贴到反馈窗口

## 🖼️ 示例

![Interactive Feedback With Capture](https://raw.githubusercontent.com/dragonstylecc/Interactive-Feedback-With-Capture-MCP/refs/heads/main/.github/example.png)

## 💡 为什么使用它？

在 Cursor 等环境中，发送给 LLM 的每条提示都被视为一个独立请求，计入月度限额（如 500 次高级请求）。当你在模糊的指令上反复迭代或纠正被误解的输出时，每次后续澄清都会触发一个完整的新请求，效率很低。

本 MCP 服务器提供了一种解决方案：它允许模型在完成响应之前暂停并请求澄清。模型触发工具调用（`interactive_feedback`）打开交互式反馈窗口，你可以提供更多细节或要求更改 — 而模型在同一个请求中继续会话。

由于工具调用不计为单独的高级交互，你可以在不消耗额外请求的情况下循环多次反馈。

- **💰 减少 API 调用：** 避免在猜测的基础上浪费昂贵的 API 调用
- **✅ 减少错误：** 在行动之前澄清意味着更少的错误代码
- **⏱️ 更快的迭代：** 快速确认胜过调试错误的猜测
- **🎮 更好的协作：** 将单向指令变为对话，让你保持控制
- **📸 可视化沟通：** 截图让 AI 直接看到问题，比文字描述更直观

## 🛠️ 工具

本服务器通过 MCP 协议暴露以下工具：

- `interactive_feedback`：向用户提问并返回回答。支持预定义选项和**截图附件**。

## 📦 安装与配置

### 方式一：一键安装（推荐）

安装 [uv](https://github.com/astral-sh/uv) 后运行：

```bash
uvx interactive-feedback-with-capture install
```

自动完成：
- 更新 `~/.cursor/mcp.json`（Cursor 全局 MCP 配置）
- 安装 `~/.cursor/rules/mcp-feedback.mdc`（Cursor Rules 文件）
- 重启 Cursor 即可使用

也可以手动配置 `mcp.json`（Cursor）或 `claude_desktop_config.json`（Claude Desktop）：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uvx",
      "args": ["interactive-feedback-with-capture"],
      "timeout": 3600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

### 方式二：从源码运行

```bash
git clone https://github.com/dragonstylecc/Interactive-Feedback-With-Capture-MCP.git
```

**将 `/path/to/interactive-feedback-mcp` 替换为实际路径：**

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

> **前置要求：** Python 3.11+，[uv](https://github.com/astral-sh/uv)（Windows: `pip install uv`，Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`，macOS: `brew install uv`）

### Cursor Rules（一键安装已自动配置）

如果使用方式一（`install` 命令）安装，Rules 已自动写入 `~/.cursor/rules/mcp-feedback.mdc`。

手动配置方式：在 Cursor Settings > Rules > User Rules 中添加：

> 如果要求或指令不明确，在继续操作之前使用interactive_feedback工具向用户询问澄清问题，不要做出假设。
> 尽可能通过interactive_feedback MCP工具向用户提供预定义的选项，以促进快速决策。
> 每当即将完成用户请求时，调用interactive_feedback工具在结束流程前请求用户反馈。如果反馈为空，则可以结束请求，并且不要循环调用该工具，如果该工具调用失败时，使用内置 `AskQuestion` 工具。

## 📸 截图与图片附件

| 方式 | 说明 |
|------|------|
| 📷 Capture Screen | 自动最小化窗口，截取整个屏幕后恢复 |
| 📋 Paste Clipboard | 粘贴已复制的截图（Windows: `Win+Shift+S`，macOS: `Cmd+Shift+4`，Linux: 系统截图工具） |
| 📁 Browse... | 从本地选择图片文件（PNG、JPG、BMP、GIF、WebP） |
| 🖱️ 拖拽文件 | 从文件管理器直接拖拽图片到窗口 |
| ⌨️ Ctrl+V | 在文本框中直接粘贴剪贴板图片 |

截图以缩略图形式预览，**点击缩略图可放大查看原图**，点击 ✕ 可删除。

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 提交反馈 |
| `Ctrl+V` | 粘贴剪贴板图片 |

## 🙏 致谢

本项目基于以下优秀项目：

- 原始项目由 Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira)) 开发
- 由 Pau Oliva ([@pof](https://x.com/pof)) 增强，灵感来自 Tommy Tong 的 [interactive-mcp](https://github.com/ttommyth/interactive-mcp)
- 截图反馈功能由 [dragonstylecc](https://github.com/dragonstylecc) 添加
- v0.3.0 部分功能设计参考了 [rooney2020/qt-interactive-feedback-mcp](https://github.com/rooney2020/qt-interactive-feedback-mcp)（自适应心跳、SOFT_TIMEOUT、快捷回复、设置页面等）
