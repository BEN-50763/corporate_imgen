# corporate-imgen

MCP server for generating corporate visual assets — icons, illustrations, stock imagery, and SVG vectors — via OpenAI and Recraft APIs. Designed for use with Claude Desktop and Claude Code to produce images for presentations, one-pagers, and documents.

## Tools

| Tool | Description | Providers |
|------|-------------|-----------|
| `generate_image` | General-purpose image from a text prompt | OpenAI, Recraft |
| `generate_icon_sheet` | Grid of related icons with transparent backgrounds | OpenAI, Recraft |
| `generate_vector` | Editable SVG vector graphic | Recraft only |
| `list_categories` | Browse existing image categories and counts | — |
| `list_images` | List images in a category with metadata | — |

## Providers

| Provider | Model | Key Capability |
|----------|-------|----------------|
| **OpenAI** | gpt-image-1.5 | Transparent backgrounds |
| **Recraft** | V4 raster + vector | Native SVG vector output |

Both use the `openai` Python package (Recraft via OpenAI-compatible endpoint).

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv venv && . .venv/Scripts/activate && uv pip install -e .
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For OpenAI provider | OpenAI API key |
| `RECRAFT_API_KEY` | For Recraft provider | Recraft API key |
| `IMAGE_OUTPUT_DIR` | No | Output directory (default: `./data/`) |

Either API key can be omitted — tools return clear errors when a missing provider is requested.

## Adding to Claude Desktop

Add to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "corporate-imgen": {
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

Config file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Adding to Claude Code

Run this from your terminal:

```bash
claude mcp add corporate-imgen \
  -e OPENAI_API_KEY=sk-... \
  -e RECRAFT_API_KEY=... \
  -e IMAGE_OUTPUT_DIR=/path/to/output \
  -- uv run --directory /path/to/corporate_imgen corporate-imgen
```

Or add it manually to your `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "corporate-imgen": {
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

## Architecture

Thin wrapper — handles API calls, saves files, returns paths and inline previews. No prompt engineering, no model selection logic, no caching. Those concerns live in separate Claude skills.

```
src/
├── server.py          # FastMCP tool definitions
├── config.py          # Environment/configuration
├── models.py          # Data types and enums
├── storage.py         # File I/O, previews, listing
└── providers/
    ├── openai.py      # OpenAI image generation
    └── recraft.py     # Recraft raster + vector generation
```

## Output

Images are saved with descriptive filenames based on the prompt and timestamp, organised into categories:

```
data/
├── icons/
│   └── minimal-line-icons-2026-03-07-143022.png
├── illustrations/
│   └── cloud-architecture-2026-03-07-150311.png
└── general/
    └── team-photo-style-2026-03-08-091200.jpg
```

Tools return both an inline compressed preview and JSON metadata including the absolute file path, dimensions, and format.
