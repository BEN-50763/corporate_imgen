"""Recraft image generation provider using OpenAI-compatible API."""

import base64
from pathlib import Path

from openai import AsyncOpenAI

from corporate_imgen.config import get_recraft_api_key, get_output_dir
from corporate_imgen.models import (
    AspectRatio,
    Background,
    ImageResult,
    OutputFormat,
    Quality,
    VectorQuality,
    ASPECT_RATIO_TO_SIZE,
)
from corporate_imgen.models import ImageMetadata
from corporate_imgen.storage import save_base64_image, save_metadata_sidecar, save_svg


RASTER_QUALITY_TO_MODEL: dict[Quality, str] = {
    "low": "recraftv4",
    "medium": "recraftv4",
    "high": "recraftv4_pro",
}

VECTOR_QUALITY_TO_MODEL: dict[VectorQuality, str] = {
    "standard": "recraftv4_vector",
    "pro": "recraftv4_pro_vector",
}


def _make_client() -> AsyncOpenAI:
    """Create an OpenAI client pointed at the Recraft API."""
    api_key = get_recraft_api_key()
    if not api_key:
        raise ValueError("RECRAFT_API_KEY is not set")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://external.api.recraft.ai/v1",
    )


def _parse_size(size: str) -> tuple[int, int]:
    """Parse a size string like '1024x1024' into (width, height)."""
    w, h = size.split("x")
    return int(w), int(h)


def _save_sidecar(
    file_path: Path,
    prompt: str,
    provider: str,
    tool_used: str,
    fmt: str,
    width: int,
    height: int,
    category: str,
) -> None:
    """Save metadata sidecar next to the image."""
    from datetime import datetime, timezone

    save_metadata_sidecar(
        file_path,
        ImageMetadata(
            prompt=prompt,
            provider=provider,
            tool_used=tool_used,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            format=fmt,
            width=width,
            height=height,
            category=category,
            file_path=str(file_path),
        ),
    )


async def generate_image(
    prompt: str,
    background: Background = "opaque",
    quality: Quality = "medium",
    aspect_ratio: AspectRatio = "square",
    output_format: OutputFormat = "png",
    category: str = "general",
) -> ImageResult:
    """Generate a raster image via Recraft. Background param is silently ignored."""
    client = _make_client()
    model = RASTER_QUALITY_TO_MODEL[quality]
    size = ASPECT_RATIO_TO_SIZE[aspect_ratio]
    width, height = _parse_size(size)

    response = await client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        response_format="b64_json",
    )

    b64_data = response.data[0].b64_json
    output_dir = get_output_dir()
    file_path = save_base64_image(
        b64_data, output_dir, prompt, output_format, category=category
    )

    _save_sidecar(
        file_path,
        prompt,
        "recraft",
        "generate_image",
        output_format,
        width,
        height,
        category,
    )

    return ImageResult(
        file_path=str(file_path),
        width=width,
        height=height,
        format=output_format,
        b64_data=b64_data,
        category=category,
    )


async def generate_icon_sheet(
    prompt: str,
    count: int = 6,
    style: str | None = None,
    category: str = "general",
) -> ImageResult:
    """Generate a grid of related icons as a single raster image."""
    client = _make_client()
    size = ASPECT_RATIO_TO_SIZE["landscape"]
    width, height = _parse_size(size)

    full_prompt = f"A grid of {count} distinct icons: {prompt}"
    if style:
        full_prompt = f"{full_prompt}. Style: {style}"

    response = await client.images.generate(
        model="recraftv4",
        prompt=full_prompt,
        size=size,
        response_format="b64_json",
    )

    b64_data = response.data[0].b64_json
    output_dir = get_output_dir()
    file_path = save_base64_image(
        b64_data, output_dir, prompt, "png", category=category
    )

    _save_sidecar(
        file_path,
        prompt,
        "recraft",
        "generate_icon_sheet",
        "png",
        width,
        height,
        category,
    )

    return ImageResult(
        file_path=str(file_path),
        width=width,
        height=height,
        format="png",
        b64_data=b64_data,
        category=category,
    )


async def generate_vector(
    prompt: str,
    style: str | None = None,
    quality: VectorQuality = "standard",
    category: str = "general",
) -> ImageResult:
    """Generate an SVG vector graphic via Recraft."""
    client = _make_client()
    model = VECTOR_QUALITY_TO_MODEL[quality]

    full_prompt = prompt
    if style:
        full_prompt = f"{prompt}. Style: {style}"

    response = await client.images.generate(
        model=model,
        prompt=full_prompt,
        size="1024x1024",
        response_format="b64_json",
    )

    b64_data = response.data[0].b64_json
    svg_content = base64.b64decode(b64_data).decode("utf-8")
    output_dir = get_output_dir()
    file_path = save_svg(svg_content, output_dir, prompt, category=category)

    _save_sidecar(
        file_path, prompt, "recraft", "generate_vector", "svg", 1024, 1024, category
    )

    return ImageResult(
        file_path=str(file_path),
        width=1024,
        height=1024,
        format="svg",
        b64_data=b64_data,
        category=category,
    )
