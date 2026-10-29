# Filee MCP server

Lets Claude (or any MCP client) convert files through the `filee` command. Runs locally, no dependencies beyond Python 3.

## Setup

1. Install Filee (the installer adds the `filee` command).
2. Add this to `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "filee": {
      "command": "python",
      "args": ["C:\\path\\to\\Filee\\mcp\\filee_mcp.py"],
      "env": { "FILEE_CLI": "C:\\path\\to\\filee.exe" }
    }
  }
}
```

`FILEE_CLI` is only needed when `filee` is not on PATH. On macOS/Linux use `python3`.

3. Restart Claude Desktop.

## Tools

- `filee_convert`: convert files or folders (`inputs`, `to` or `preset`, `output_dir`, `quality`, `recursive`, `overwrite`, `skip_existing`, `zip`).
- `filee_formats`: list supported formats.
- `filee_presets`: list saved presets.
