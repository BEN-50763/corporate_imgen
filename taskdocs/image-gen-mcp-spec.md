# Image Generation MCP Server — Specification

## Purpose

A local MCP server for Claude Desktop that generates images via external APIs. Used primarily for creating visual assets for presentations, documents, and one-pagers — including icons with transparent backgrounds, stock-photo-style imagery, conceptual illustrations, and icon sprite sheets.

The server is a thin wrapper around image generation APIs. It handles API calls, file saving, and returns image paths. It does **not** contain prompt engineering logic — that lives in a separate Claude skill.

## Transport

- **Stdio** (for Claude Desktop local use)
- Standard MCP protocol over stdin/stdout
- Should be runnable via `npx` or `node` from the Claude Desktop config

## Providers

The server wraps two image generation API providers. The architecture should make it straightforward to add more providers in future.

### 1. OpenAI — GPT Image 1.5

- **API**: OpenAI Images API (`gpt-image-1.5`)
- **Auth**: `OPENAI_API_KEY` environment variable
- **Key capability**: Native transparent background support via `background: "transparent"` parameter
- **Docs**: https://platform.openai.com/docs/guides/image-generation

### 2. Recraft — V4

- **API**: Recraft API (V4 raster + V4 Vector)
- **Auth**: `RECRAFT_API_KEY` environment variable
- **Key capability**: Native SVG vector output — actual editable vector files, not traced rasters
- **Docs**: https://www.recraft.ai/docs/api-reference

## Tools

The server should expose three tools:

### `generate_image`

General-purpose image generation from a text prompt.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | yes | Text description of the image to generate |
| `provider` | enum | no | `openai` or `recraft`. Default: `openai` |
| `background` | enum | no | `transparent` or `opaque`. Default: `opaque`. Only supported by OpenAI. |
| `quality` | enum | no | `low`, `medium`, `high`. Default: `medium`. Mapping varies by provider. |
| `aspect_ratio` | enum | no | `square`, `landscape`, `portrait`. Default: `square`. Map to provider-specific size params. |
| `output_format` | enum | no | `png`, `jpg`, `webp`, `svg`. Default: `png`. SVG only available with Recraft. |

**Returns:** Local file path to the saved image, plus the image dimensions.

### `generate_icon_sheet`

Generates multiple related icons on a single image, each with a transparent background. Optimised for creating consistent icon sets for presentations.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | yes | Description of the icon set (e.g. "6 minimal line icons for: search, settings, user, notification, analytics, security") |
| `provider` | enum | no | `openai` or `recraft`. Default: `openai` |
| `count` | integer | no | Number of icons to generate on the sheet. Default: 6 |
| `style` | string | no | Style guidance (e.g. "minimal line art", "filled flat colour", "3D tactile") |

**Returns:** Local file path to the saved sprite sheet image.

**Implementation note:** For OpenAI, this generates a single image containing all icons arranged in a grid, with `background: "transparent"`. The prompt should be constructed to request a grid layout. For Recraft, consider using the vector endpoint to get individual SVG icons.

### `generate_vector`

Generates an editable SVG vector graphic. Recraft-only.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | yes | Text description of the vector graphic |
| `style` | string | no | Style guidance for the vector output |
| `quality` | enum | no | `standard` or `pro`. Default: `standard`. Pro gives higher resolution/detail. |

**Returns:** Local file path to the saved SVG file.

## Image Storage

- Save all generated images to a configurable output directory
- Default: `./generated-images/` relative to the server's working directory
- Configurable via `IMAGE_OUTPUT_DIR` environment variable
- Use descriptive filenames based on a sanitised version of the prompt + timestamp (e.g. `minimal-icons-security-2026-03-07-143022.png`)
- Return absolute file paths in tool responses so Claude can reference them

## Configuration

All configuration via environment variables in the Claude Desktop config:

```json
{
  "mcpServers": {
    "image-gen": {
      "command": "node",
      "args": ["/path/to/image-gen-mcp/dist/index.js"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "RECRAFT_API_KEY": "...",
        "IMAGE_OUTPUT_DIR": "/path/to/output"
      }
    }
  }
}
```

Either API key can be omitted if that provider isn't needed. If a tool call specifies a provider whose key is missing, return a clear error message.

## Error Handling

- API errors: Return the provider's error message clearly (e.g. content policy violations, rate limits, invalid parameters)
- Missing API key: Return a message stating which key is needed
- Unsupported parameter combinations: Return a message explaining what's not supported (e.g. SVG output requested with OpenAI provider)
- Network failures: Return a clear timeout/connection error

## Tech Stack Guidance

- **Language**: TypeScript (standard for MCP servers)
- **MCP SDK**: `@modelcontextprotocol/sdk`
- **HTTP clients**: Use each provider's official SDK or straightforward HTTP requests — whichever is simpler
  - OpenAI: `openai` npm package
  - Recraft: Direct HTTP (their API is simple REST)
- Keep dependencies minimal

## Out of Scope

These are explicitly **not** part of this MCP server:

- **Prompt engineering / enhancement** — handled by a separate Claude skill
- **Model selection logic** (when to use which provider) — handled by a separate Claude skill
- **Image editing / inpainting** — may be added later
- **Image-to-image generation** — may be added later
- **Hosting / HTTP transport** — this is local stdio only for now
- **Caching** — not needed at current usage volumes

## Future Extensibility

The provider architecture should make it easy to add:

- Additional providers (e.g. Vertex AI/Imagen if they add transparent background support)
- Additional tools (e.g. `edit_image`, `upscale_image`)
- Additional output formats per provider as they become available
