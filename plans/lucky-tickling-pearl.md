# Plan: Corporate Image Generation MCP Server (Python)

## Context

We need a local MCP server for Claude Desktop that generates images via OpenAI and Recraft APIs. It's a thin wrapper — handles API calls, file saving, returns paths. No prompt engineering, no caching, no model selection logic. The spec (`taskdocs/image-gen-mcp-spec.md`) originally called for TypeScript, but we're building in Python using FastMCP.

## API Research Summary

### OpenAI (gpt-image-1.5)
- SDK: `openai` Python package, `client.images.generate()`
- Response: always base64 (no URL option for GPT image models)
- Sizes: 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait)
- Quality: low / medium / high (pass through directly)
- Background: `"transparent"` / `"opaque"` — transparent requires png or webp
- Output formats: png, jpeg, webp. No SVG.

### Recraft V4
- OpenAI-compatible API — use `openai` SDK with `base_url="https://external.api.recraft.ai/v1"`
- Models: `recraftv4` (raster), `recraftv4_vector` (SVG), `recraftv4_pro` (4MP raster), `recraftv4_pro_vector` (pro SVG)
- Sizes: same pixel values work (1024x1024, etc.), also supports aspect ratio strings
- Quality maps to model choice: low/medium -> recraftv4, high -> recraftv4_pro
- Styles NOT supported on V4 — style guidance goes into prompt text
- Request `response_format="b64_json"` to avoid ephemeral URLs
- Vector endpoints return SVG content

### Python MCP SDK (v1.26.0)
- Package: `mcp[cli]`
- FastMCP decorator API with type annotations (Literal for enums, defaults for optional)
- Async tools supported, exceptions auto-converted to error responses
- `mcp.run()` defaults to stdio

## Design Decisions

1. **Use `openai` SDK for both providers** — Recraft is OpenAI-compatible, so one dependency covers both. No need for httpx. Pydantic AI was considered and rejected (it's an agent orchestration framework, not an API client — no direct image generation, no Recraft support, pulls in 143 packages).
2. **No abstract base class** — two providers with different param sets don't benefit from a shared interface. Simple module-level async functions.
3. **Icon sheet = single raster image** — both providers generate one image with grid layout. Minimal prompt wrapping (grid instruction) is acceptable as mechanical transformation, not prompt engineering.
4. **Entry point**: `uv run corporate-imgen` via pyproject.toml `[project.scripts]`
5. **Output directory**: `./data/` by default (configurable via `IMAGE_OUTPUT_DIR` env var)
6. **API keys**: Both keys available in `.env` file. Config module loads from environment variables (keys passed via Claude Desktop config or loaded from `.env` at runtime).

## File Structure

```
corporate_imgen/
  __init__.py           # Empty
  server.py             # FastMCP server, 3 tool definitions, main() entry point
  config.py             # Env var loading (API keys, output dir — default output: ./data/)
  models.py             # Literal types, ImageResult dataclass
  storage.py            # Filename sanitisation, image/SVG saving
  providers/
    __init__.py          # Empty
    openai.py            # OpenAI gpt-image-1.5 calls
    recraft.py           # Recraft V4 calls (raster + vector)
modularity.md           # Module inventory
tests/
  test_storage_cli.py   # Storage unit tests (no API keys needed)
  test_server_cli.py    # Server integration tests (needs API keys)
```

## Tool Signatures

### generate_image
```python
@mcp.tool()
async def generate_image(
    prompt: str,
    provider: Literal["openai", "recraft"] = "openai",
    background: Literal["transparent", "opaque"] = "opaque",
    quality: Literal["low", "medium", "high"] = "medium",
    aspect_ratio: Literal["square", "landscape", "portrait"] = "square",
    output_format: Literal["png", "jpg", "webp", "svg"] = "png",
) -> str:
```
Returns: JSON string with file_path and dimensions.

### generate_icon_sheet
```python
@mcp.tool()
async def generate_icon_sheet(
    prompt: str,
    provider: Literal["openai", "recraft"] = "openai",
    count: int = 6,
    style: str | None = None,
) -> str:
```
Returns: JSON string with file_path. Sets transparent bg, landscape size, wraps prompt with grid instruction.

### generate_vector
```python
@mcp.tool()
async def generate_vector(
    prompt: str,
    style: str | None = None,
    quality: Literal["standard", "pro"] = "standard",
) -> str:
```
Returns: JSON string with file_path. Recraft-only (raises clear error if Recraft key missing).

## Parameter Mappings

### Aspect ratio -> size (both providers)
| Aspect    | Size       |
|-----------|------------|
| square    | 1024x1024  |
| landscape | 1536x1024  |
| portrait  | 1024x1536  |

### Quality -> Recraft model
| Quality | Raster model   | Vector model          |
|---------|----------------|-----------------------|
| low     | recraftv4      | recraftv4_vector      |
| medium  | recraftv4      | recraftv4_vector      |
| high    | recraftv4_pro  | recraftv4_pro_vector  |

### Vector quality -> Recraft model
| Quality  | Model                |
|----------|----------------------|
| standard | recraftv4_vector     |
| pro      | recraftv4_pro_vector |

## Validation Rules (raise explicitly only when error would be cryptic)

- Missing API key for requested provider -> raise ValueError with clear message
- SVG output requested with OpenAI -> raise ValueError explaining SVG requires Recraft
- Transparent background requested with Recraft -> ignore silently (Recraft doesn't support it, but prompt can handle it)
- jpg format with transparent background -> raise ValueError (JPEG doesn't support transparency)

## Dependencies (pyproject.toml)

```toml
dependencies = [
    "mcp[cli]>=1.26.0",
    "openai>=1.60.0",
]

[project.scripts]
corporate-imgen = "corporate_imgen.server:main"
```

## Implementation Phases

### Phase 1: Scaffolding
- Update pyproject.toml
- Create config.py, models.py, storage.py
- Create modularity.md
- Write + run test_storage_cli.py

### Phase 2: Providers
- Create providers/openai.py and providers/recraft.py
- Install package: `uv pip install -e .`
- Smoke test imports

### Phase 3: Server + Tools
- Create server.py with all 3 tools
- Test stdio startup: `uv run corporate-imgen`

### Phase 4: Integration Testing
- Test each tool with real API calls (keys in .env — both OpenAI and Recraft available)
- Test error cases (missing key, unsupported combos)
- Update CLAUDE.md to reflect Python build
- Add `data/` to .gitignore

## Verification

1. `uv run corporate-imgen` starts cleanly on stdio
2. All 3 tools appear when connected to Claude Desktop
3. `generate_image` with OpenAI -> valid PNG on disc
4. `generate_image` with Recraft -> valid PNG on disc
5. `generate_icon_sheet` -> transparent PNG with icon grid
6. `generate_vector` -> valid SVG file
7. Missing API key -> clear error message
8. Files have sanitised-prompt-timestamp filenames

## Risks

- **Recraft via openai SDK**: `response_format="b64_json"` or vector endpoints might not map cleanly. If so, fall back to URL mode + httpx download, or direct HTTP for vector only.
- **Python 3.14 compat**: mcp and openai packages may not yet support 3.14. May need to relax to >=3.12.
