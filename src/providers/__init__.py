"""Provider facade — routes to the correct image generation provider."""

from __future__ import annotations

from corporate_imgen.models import (
    AspectRatio,
    Background,
    ImageResult,
    OutputFormat,
    Quality,
    VectorQuality,
)


async def generate_image(
    prompt: str,
    provider: str = "openai",
    background: Background = "opaque",
    quality: Quality = "medium",
    aspect_ratio: AspectRatio = "square",
    output_format: OutputFormat = "png",
    category: str = "general",
) -> ImageResult:
    """Route image generation to the requested provider."""
    if provider == "openai":
        from corporate_imgen.providers.openai import generate_image as _openai

        return await _openai(
            prompt, background, quality, aspect_ratio, output_format, category=category
        )

    from corporate_imgen.providers.recraft import generate_image as _recraft

    return await _recraft(
        prompt, background, quality, aspect_ratio, output_format, category=category
    )


async def generate_icon_sheet(
    prompt: str,
    provider: str = "openai",
    count: int = 6,
    style: str | None = None,
    category: str = "general",
) -> ImageResult:
    """Route icon sheet generation to the requested provider."""
    if provider == "openai":
        from corporate_imgen.providers.openai import generate_icon_sheet as _openai

        return await _openai(prompt, count, style, category=category)

    from corporate_imgen.providers.recraft import generate_icon_sheet as _recraft

    return await _recraft(prompt, count, style, category=category)


async def generate_vector(
    prompt: str,
    style: str | None = None,
    quality: VectorQuality = "standard",
    category: str = "general",
) -> ImageResult:
    """Generate SVG vector via Recraft (only supported provider)."""
    from corporate_imgen.providers.recraft import generate_vector as _recraft

    return await _recraft(prompt, style, quality, category=category)
