# Modularity — corporate-imgen

## File Structure

```
src/
  __init__.py           # Package marker
  server.py             # FastMCP server, 5 tool definitions, main() entry point
  config.py             # Env var loading (API keys, output dir)
  models.py             # Literal types, ASPECT_RATIO_TO_SIZE, ImageResult, ImageMetadata
  storage.py            # Filename sanitisation, image/SVG saving, category browsing, metadata sidecars
  providers/
    __init__.py          # Facade — routes to correct provider
    openai.py            # OpenAI gpt-image-1.5 calls
    recraft.py           # Recraft V4 calls (raster + vector)
```

## What belongs where

| Concern | File |
|---------|------|
| MCP tool definitions | `server.py` |
| Environment variables, API keys | `config.py` |
| Type aliases, dataclasses, constants | `models.py` |
| File I/O (save images, sidecars, browse categories) | `storage.py` |
| Provider routing (facade) | `providers/__init__.py` |
| OpenAI API calls | `providers/openai.py` |
| Recraft API calls | `providers/recraft.py` |

## Design Patterns

- **Facade** (`providers/__init__.py`): single entry point for all image generation, delegates to provider modules
- **Strategy** (`providers/openai.py`, `providers/recraft.py`): each provider implements the same function signatures, swappable via the facade

## Function Inventory

### config.py
- `get_openai_api_key() -> str | None`
- `get_recraft_api_key() -> str | None`
- `get_output_dir() -> Path`

### models.py
- `Provider`, `Background`, `Quality`, `AspectRatio`, `OutputFormat`, `VectorQuality` (Literal types)
- `ASPECT_RATIO_TO_SIZE` (dict)
- `ImageResult` (dataclass) — file_path, width, height, format, b64_data, category
- `ImageMetadata` (dataclass) — prompt, provider, tool_used, timestamp, format, width, height, category, file_path

### storage.py
- `sanitise_filename(prompt, max_length) -> str`
- `build_filename(prompt, extension) -> str`
- `save_base64_image(data, output_dir, prompt, extension, category) -> Path`
- `save_svg(content, output_dir, prompt, category) -> Path`
- `save_metadata_sidecar(image_path, metadata) -> Path`
- `list_category_tree(output_dir) -> dict` — nested folder hierarchy with `_count` per category
- `list_images_in_category(output_dir, category, recurse) -> list[dict]` — reads JSON sidecars

### providers/__init__.py (facade)
- `generate_image(prompt, provider, background, quality, aspect_ratio, output_format, category) -> ImageResult`
- `generate_icon_sheet(prompt, provider, count, style, category) -> ImageResult`
- `generate_vector(prompt, style, quality, category) -> ImageResult`

### providers/openai.py
- `generate_image(prompt, background, quality, aspect_ratio, output_format, category) -> ImageResult`
- `generate_icon_sheet(prompt, count, style, category) -> ImageResult`

### providers/recraft.py
- `generate_image(prompt, background, quality, aspect_ratio, output_format, category) -> ImageResult`
- `generate_icon_sheet(prompt, count, style, category) -> ImageResult`
- `generate_vector(prompt, style, quality, category) -> ImageResult`

### server.py
- `tool_generate_image(...)` — MCP tool, returns inline image + metadata
- `tool_generate_icon_sheet(...)` — MCP tool, returns inline image + metadata
- `tool_generate_vector(...)` — MCP tool, returns inline image + metadata
- `tool_list_categories()` — MCP tool, returns category tree JSON
- `tool_list_images(category)` — MCP tool, returns image metadata from sidecars
- `main()` — entry point
