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

from fastmcp import FastMCP, Context
from fastmcp.utilities.types import Image
from pydantic import Field

mcp = FastMCP("Interactive Feedback MCP")

HEARTBEAT_INTERVAL = 15

async def launch_feedback_ui(
    summary: str,
    predefined_options: list[str] | None = None,
    ctx: Context | None = None,
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
            "--predefined-options", "|||".join(predefined_options) if predefined_options else ""
        ]
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )

        elapsed = 0
        while process.returncode is None:
            try:
                await asyncio.wait_for(process.wait(), timeout=HEARTBEAT_INTERVAL)
            except asyncio.TimeoutError:
                elapsed += HEARTBEAT_INTERVAL
                if ctx:
                    await ctx.report_progress(
                        progress=elapsed,
                        total=elapsed + 600,
                    )
                    await ctx.info(f"Waiting for user feedback... ({elapsed}s)")

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
    predefined_options_list = predefined_options if isinstance(predefined_options, list) else None
    result = await launch_feedback_ui(message, predefined_options_list, ctx)

    text = result.get("interactive_feedback", "")
    images_b64 = result.get("images", [])

    if not images_b64:
        return {"interactive_feedback": text}

    # Decode all images once, reuse the bytes for both file saving and Image content
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

if __name__ == "__main__":
    mcp.run(transport="stdio", log_level="ERROR")
