# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Corporate image generation MCP server for Claude Desktop. Generates visual assets (icons, stock imagery, illustrations, vector graphics) for presentations, documents, and one-pagers via external APIs.

- **Transport**: Stdio (local Claude Desktop use)
- **Language**: Python
- **MCP SDK**: `mcp[cli]` with FastMCP
- **Spec**: `taskdocs/image-gen-mcp-spec.md` is the source of truth for requirements

## Architecture

### Provider Pattern

Two image generation providers behind a common interface, designed for easy addition of new providers:

| Provider | Model | Auth Env Var | Key Capability |
|----------|-------|-------------|----------------|
| OpenAI | `gpt-image-1.5` | `OPENAI_API_KEY` | Transparent backgrounds (`background: "transparent"`) |
| Recraft | V4 raster + vector | `RECRAFT_API_KEY` | Native SVG vector output |

Both providers use the `openai` Python package (Recraft via OpenAI-compatible API).

### Tools Exposed

| Tool | Purpose | Provider Support |
|------|---------|-----------------|
| `generate_image` | General-purpose image from text prompt | Both |
| `generate_icon_sheet` | Grid of related icons with transparent bg | Both (OpenAI preferred) |
| `generate_vector` | Editable SVG vector graphic | Recraft only |

### Image Storage

- Output directory configurable via `IMAGE_OUTPUT_DIR` env var (default: `./data/`)
- Filenames: sanitised prompt + timestamp (e.g. `minimal-icons-security-2026-03-07-143022.png`)
- Tools return absolute file paths

## Commands

```bash
# Install
uv venv && . .venv/Scripts/activate && uv pip install -e .

# Run the server (stdio)
uv run corporate-imgen
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "image-gen": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/corporate_imgen", "corporate-imgen"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "RECRAFT_API_KEY": "...",
        "IMAGE_OUTPUT_DIR": "/path/to/output"
      }
    }
  }
}
```

## Key Design Decisions

- **No prompt engineering** in this server — that lives in a separate Claude skill
- **No model selection logic** — the calling skill decides which provider to use
- **No caching** — not needed at current usage volumes
- **Thin wrapper** — handles API calls, file saving, returns paths. Nothing more.
- Either API key can be omitted; tools return clear errors when a missing provider is requested
