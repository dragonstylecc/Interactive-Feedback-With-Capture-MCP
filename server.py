# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import base64
import tempfile
import asyncio
import uuid

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

from fastmcp import FastMCP, Context
from fastmcp.utilities.types import Image
from pydantic import Field

mcp = FastMCP("Interactive Feedback MCP")

POLL_INTERVAL = 0.5
MAX_HEARTBEAT_FAILURES = 3
SOFT_TIMEOUT = 3500
_LOCK_DIR = os.path.join(tempfile.gettempdir(), "mcp_feedback_windows")
_LOG_PATH = os.path.join(tempfile.gettempdir(), "mcp_feedback_server.log")


_LOG_MAX_SIZE = 2 * 1024 * 1024  # 2 MB


def _slog(msg: str):
    """Append a timestamped line to the server log file, rotating at 2MB."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    try:
        if os.path.exists(_LOG_PATH) and os.path.getsize(_LOG_PATH) > _LOG_MAX_SIZE:
            bak = _LOG_PATH + ".bak"
            if os.path.exists(bak):
                os.unlink(bak)
            os.rename(_LOG_PATH, bak)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _adaptive_heartbeat_interval(elapsed: float) -> float:
    """Reduce heartbeat frequency for long waits to avoid message noise."""
    if elapsed < 600:
        return 10
    elif elapsed < 3600:
        return 60
    return 300


_MAX_WINDOWS = 20


def _cleanup_stale_locks():
    """Remove lock files left by crashed processes."""
    if not os.path.isdir(_LOCK_DIR):
        return
    for name in os.listdir(_LOCK_DIR):
        if not name.startswith("window_") or not name.endswith(".lock"):
            continue
        path = os.path.join(_LOCK_DIR, name)
        try:
            with open(path, "r") as f:
                pid_str = f.read().strip()
            if pid_str and pid_str.isdigit():
                pid = int(pid_str)
                try:
                    os.kill(pid, 0)
                    continue
                except OSError:
                    pass
            os.unlink(path)
            _slog(f"Cleaned stale lock: {name}")
        except Exception:
            pass


def _acquire_window_id() -> tuple[int, object]:
    """Acquire a globally unique window ID using file locks (cross-process safe)."""
    os.makedirs(_LOCK_DIR, exist_ok=True)
    _cleanup_stale_locks()
    window_id = 1
    while window_id <= _MAX_WINDOWS:
        lock_path = os.path.join(_LOCK_DIR, f"window_{window_id}.lock")
        fd = open(lock_path, "w")
        try:
            if sys.platform == "win32":
                msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fd.write(str(os.getpid()))
            fd.flush()
            return window_id, fd
        except (IOError, OSError):
            fd.close()
            window_id += 1
    raise RuntimeError(f"No available window ID (max {_MAX_WINDOWS})")


def _release_window_id(fd):
    """Release a window ID lock."""
    try:
        lock_path = fd.name
        if sys.platform == "win32":
            try:
                fd.seek(0)
                msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
            except (IOError, OSError):
                pass
        fd.close()
        os.unlink(lock_path)
    except (OSError, AttributeError):
        pass


async def launch_feedback_ui(
    summary: str,
    predefined_options: list[str] | None = None,
    ctx: Context | None = None,
    window_id: int = 1,
) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--predefined-options", "|||".join(predefined_options) if predefined_options else "",
            "--window-id", str(window_id),
        ]
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )

        try:
            wait_task = asyncio.ensure_future(process.wait())
            elapsed = 0.0
            last_heartbeat = 0.0
            heartbeat_failures = 0
            while not wait_task.done():
                await asyncio.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL

                if elapsed >= SOFT_TIMEOUT and process.returncode is None:
                    _slog(f"SOFT_TIMEOUT reached at {elapsed:.0f}s, terminating UI")
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        process.kill()
                    return {"interactive_feedback": "[心跳] 等待超时，请重新调用 interactive_feedback 继续对话。", "images": []}

                hb_interval = _adaptive_heartbeat_interval(elapsed)
                if not wait_task.done() and ctx and (elapsed - last_heartbeat) >= hb_interval:
                    last_heartbeat = elapsed
                    try:
                        await ctx.report_progress(
                            progress=elapsed,
                            total=elapsed + 600,
                        )
                        await ctx.info(f"Waiting for user feedback... ({elapsed:.0f}s)")
                        heartbeat_failures = 0
                    except Exception:
                        heartbeat_failures += 1
                        _slog(f"Heartbeat failed ({heartbeat_failures}/{MAX_HEARTBEAT_FAILURES})")
                        if heartbeat_failures >= MAX_HEARTBEAT_FAILURES:
                            if process.returncode is None:
                                process.terminate()
                                try:
                                    await asyncio.wait_for(process.wait(), timeout=5)
                                except asyncio.TimeoutError:
                                    process.kill()
                            break
            await wait_task
        except (asyncio.CancelledError, Exception):
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
            raise

        if process.returncode != 0:
            stderr_bytes = await process.stderr.read()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise Exception(
                f"Feedback UI exited with code {process.returncode}"
                + (f": {stderr_text}" if stderr_text else "")
            )

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        os.unlink(output_file)
        return data
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e


@mcp.tool()
async def interactive_feedback(
    message: str = Field(description="The specific question for the user"),
    predefined_options: list = Field(default=None, description="Predefined options for the user to choose from (optional)"),
    ctx: Context = None,
):
    """Request interactive feedback from the user. Supports text and screenshot responses."""
    window_id, lock_fd = _acquire_window_id()
    _slog(f"interactive_feedback called, window_id={window_id}")

    predefined_options_list = predefined_options if isinstance(predefined_options, list) else None
    max_attempts = 2
    last_error = None
    for attempt in range(max_attempts):
        try:
            _slog(f"Attempt {attempt+1}/{max_attempts} to launch UI")
            result = await launch_feedback_ui(message, predefined_options_list, ctx, window_id=window_id)
            _slog(f"UI returned successfully")
            break
        except Exception as e:
            last_error = e
            _slog(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_attempts - 1:
                continue
            _release_window_id(lock_fd)
            return {
                "interactive_feedback": (
                    f"[Feedback UI failed after {max_attempts} attempts: {last_error}. "
                    "Please use AskQuestion tool as fallback.]"
                )
            }

    _release_window_id(lock_fd)

    text = result.get("interactive_feedback", "")
    images_b64 = result.get("images", [])

    if not images_b64:
        return {"interactive_feedback": text}

    decoded_images: list[bytes] = [base64.b64decode(img) for img in images_b64]

    run_id = uuid.uuid4().hex[:8]
    image_paths = []
    for i, img_bytes in enumerate(decoded_images):
        temp_path = os.path.join(tempfile.gettempdir(), f"mcp_feedback_{run_id}_{i}.png")
        with open(temp_path, 'wb') as f:
            f.write(img_bytes)
        image_paths.append(temp_path)

    feedback_with_paths = text
    if image_paths:
        paths_str = "\n".join(image_paths)
        feedback_with_paths += f"\n\n[Screenshots saved to:\n{paths_str}]"

    contents: list = [feedback_with_paths]
    for img_bytes in decoded_images:
        contents.append(Image(data=img_bytes, format="png"))

    return contents

_MCP_CONFIG = {
    "interactive-feedback": {
        "command": "uvx",
        "args": ["interactive-feedback-with-capture@latest"],
        "timeout": 3600,
        "autoApprove": ["interactive_feedback"],
    }
}

_RULES_CONTENT = """\
---
description: Rules for interactive_feedback MCP tool usage - when to call, how to handle failures, and timeout management.
globs:
alwaysApply: true
---

# Interactive Feedback MCP Rules

## Core Rules

1. If a request or instruction is unclear, use the `interactive_feedback` tool to ask the user clarifying questions before proceeding. Do not make assumptions.
2. Provide predefined options via the `interactive_feedback` MCP tool whenever possible to facilitate quick decision-making.
3. Each time you are about to complete a user request, call the `interactive_feedback` tool to ask for user feedback before finalizing. If the feedback is empty, you may end the request and must not call the tool in a loop.

## Fallback

If the `interactive_feedback` tool call fails (timeout, connection error, or UI launch failure), use the built-in `AskQuestion` tool as a fallback.

## Timeout Handling

- The feedback window may remain open for extended periods while the user reviews or provides detailed feedback.
- If the tool returns a message containing `[心跳]`, it means the soft timeout was reached. Re-invoke `interactive_feedback` to continue the conversation.
- Do not assume a timeout means the user is unresponsive — they may simply need more time.
"""


def _install():
    """Auto-configure Cursor MCP settings and Rules files."""
    home = os.path.expanduser("~")
    cursor_dir = os.path.join(home, ".cursor")

    # --- MCP config ---
    mcp_path = os.path.join(cursor_dir, "mcp.json")
    if os.path.exists(mcp_path):
        with open(mcp_path, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        os.makedirs(cursor_dir, exist_ok=True)
        config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}
    config["mcpServers"].update(_MCP_CONFIG)

    with open(mcp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ MCP config updated: {mcp_path}")

    # --- Rules file ---
    rules_dir = os.path.join(cursor_dir, "rules")
    os.makedirs(rules_dir, exist_ok=True)
    rules_path = os.path.join(rules_dir, "mcp-feedback.mdc")
    with open(rules_path, "w", encoding="utf-8") as f:
        f.write(_RULES_CONTENT)
    print(f"✅ Rules file installed: {rules_path}")

    print("\n🎉 Installation complete! Restart Cursor to activate.")
    print("   MCP tool: interactive_feedback")
    print("   Rules: always-apply mcp-feedback.mdc")


def main():
    """Entry point for uvx / python -m invocation."""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        _install()
        return
    mcp.run(transport="stdio", log_level="ERROR")


if __name__ == "__main__":
    main()
