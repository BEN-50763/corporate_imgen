"""FastMCP server exposing image generation tools."""

import json
from typing import Literal

from mcp import types
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult

from corporate_imgen.models import (
    AspectRatio,
    Background,
    ImageResult,
    OutputFormat,
    Quality,
    VectorQuality,
)
from corporate_imgen.config import get_output_dir
from corporate_imgen.providers import (
    generate_icon_sheet,
    generate_image,
    generate_vector,
)
from corporate_imgen.storage import (
    compress_for_preview,
    list_category_tree,
    list_images_in_category,
)

mcp = FastMCP("corporate-imgen")


def _build_response(result: ImageResult) -> CallToolResult:
    """Build a CallToolResult with compressed inline preview + metadata text."""
    preview_b64 = compress_for_preview(result.b64_data, result.format)
    preview_mime = "image/jpeg" if result.format != "svg" else "image/svg+xml"

    metadata = json.dumps(
        {
            "file_path": result.file_path,
            "width": result.width,
            "height": result.height,
            "format": result.format,
            "category": result.category,
        }
    )

    return CallToolResult(
        content=[
            types.ImageContent(type="image", data=preview_b64, mimeType=preview_mime),
            types.TextContent(type="text", text=metadata),
        ]
    )


@mcp.tool()
async def tool_generate_image(
    prompt: str,
    provider: Literal["openai", "recraft"] = "openai",
    background: Background = "opaque",
    quality: Quality = "low",
    aspect_ratio: AspectRatio = "square",
    output_format: OutputFormat = "png",
    category: str = "general",
) -> CallToolResult:
    """Generate an image from a text prompt.

    Returns the image inline plus JSON metadata with file_path, width, height, and format.
    """
    result = await generate_image(
        prompt=prompt,
        provider=provider,
        background=background,
        quality=quality,
        aspect_ratio=aspect_ratio,
        output_format=output_format,
        category=category,
    )
    return _build_response(result)


@mcp.tool()
async def tool_generate_icon_sheet(
    prompt: str,
    provider: Literal["openai", "recraft"] = "openai",
    count: int = 6,
    style: str | None = None,
    category: str = "general",
) -> CallToolResult:
    """Generate a sheet of related icons with transparent backgrounds.

    Returns the image inline plus JSON metadata with file_path, width, height, and format.
    """
    result = await generate_icon_sheet(
        prompt=prompt,
        provider=provider,
        count=count,
        style=style,
        category=category,
    )
    return _build_response(result)


@mcp.tool()
async def tool_generate_vector(
    prompt: str,
    style: str | None = None,
    quality: VectorQuality = "standard",
    category: str = "general",
) -> CallToolResult:
    """Generate an editable SVG vector graphic via Recraft.

    Returns the image inline plus JSON metadata with file_path, width, height, and format.
    """
    result = await generate_vector(
        prompt=prompt,
        style=style,
        quality=quality,
        category=category,
    )
    return _build_response(result)


@mcp.tool()
async def tool_list_categories() -> str:
    """List all image categories and their image counts.

    Returns JSON tree of categories with counts. Call this at the start of a session
    to see what images already exist before generating new ones.
    """
    tree = list_category_tree(get_output_dir())
    return json.dumps(tree, indent=2)


@mcp.tool()
async def tool_list_images(category: str) -> str:
    """List existing images in a category.

    Returns JSON array of image metadata (prompt, provider, tool, timestamp, etc).
    Use a parent category like "icons" to list all subcategories, or a specific
    path like "icons/people" for just that folder.
    """
    images = list_images_in_category(get_output_dir(), category)
    return json.dumps(images, indent=2)


def main() -> None:
    mcp.run()
