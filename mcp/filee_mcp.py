#!/usr/bin/env python3
"""MCP server that exposes the `filee` command line to MCP clients (stdio, no dependencies).

Set FILEE_CLI to the full path of the filee executable if it is not on PATH.
"""

import json
import os
import shutil
import subprocess
import sys

PROTOCOL_VERSION = "2024-11-05"
TIMEOUT_SECONDS = int(os.environ.get("FILEE_TIMEOUT", "600"))

TOOLS = [
    {
        "name": "filee_convert",
        "description": "Convert files or folders to another format with Filee. Output is saved next to the original unless output_dir is given.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "inputs": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "Files or folders to convert (absolute paths)."},
                "to": {"type": "string", "description": "Target format, e.g. pdf, png, jpg, docx. Use this or preset."},
                "preset": {"type": "string", "description": "Named preset instead of a target format (see filee_presets)."},
                "output_dir": {"type": "string", "description": "Folder for the results."},
                "quality": {"type": "integer", "minimum": 1, "maximum": 100},
                "recursive": {"type": "boolean", "description": "Descend into folders."},
                "overwrite": {"type": "boolean", "description": "Overwrite existing results."},
                "skip_existing": {"type": "boolean", "description": "Skip files whose result already exists."},
                "zip": {"type": "boolean", "description": "Collect the results into one ZIP."},
            },
            "required": ["inputs"],
        },
    },
    {
        "name": "filee_formats",
        "description": "List the formats Filee can convert.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "filee_presets",
        "description": "List the conversion presets saved in Filee.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def cli_path():
    return os.environ.get("FILEE_CLI") or shutil.which("filee") or shutil.which("filee-cli")


def run_cli(args):
    exe = cli_path()
    if not exe:
        return "Filee command not found. Install Filee or set FILEE_CLI to its path.", True
    try:
        done = subprocess.run([exe, *args], capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return f"Filee did not finish within {TIMEOUT_SECONDS} seconds.", True
    text = (done.stdout + done.stderr).strip() or "(no output)"
    return text, done.returncode != 0


def convert_args(a):
    args = ["convert", *a["inputs"]]
    if a.get("to"):
        args += ["--to", a["to"]]
    if a.get("preset"):
        args += ["--preset", a["preset"]]
    if a.get("output_dir"):
        args += ["--output", a["output_dir"]]
    if a.get("quality"):
        args += ["--quality", str(a["quality"])]
    for key, flag in (("recursive", "--recursive"), ("overwrite", "--overwrite"), ("skip_existing", "--skip"), ("zip", "--zip")):
        if a.get(key):
            args.append(flag)
    return args + ["--json"]


def call_tool(name, arguments):
    if name == "filee_convert":
        if not arguments.get("inputs"):
            return "inputs is required.", True
        if bool(arguments.get("to")) == bool(arguments.get("preset")):
            return "Give either to or preset.", True
        return run_cli(convert_args(arguments))
    if name == "filee_formats":
        return run_cli(["formats"])
    if name == "filee_presets":
        return run_cli(["presets"])
    return f"Unknown tool {name}.", True


def handle(msg):
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "filee", "version": "0.1.0"},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        text, is_error = call_tool(params.get("name"), params.get("arguments") or {})
        return {"content": [{"type": "text", "text": text}], "isError": is_error}
    if method == "ping":
        return {}
    raise LookupError(method)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" not in msg:  # notification
            continue
        try:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)}
        except LookupError:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "Method not found"}}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
