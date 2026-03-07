"""OpenAI image generation provider using gpt-image-1.5."""

from openai import AsyncOpenAI

from corporate_imgen.config import get_openai_api_key, get_output_dir
from corporate_imgen.models import (
    ASPECT_RATIO_TO_SIZE,
    AspectRatio,
    Background,
    ImageResult,
    OutputFormat,
    Quality,
)
from corporate_imgen.models import ImageMetadata
from corporate_imgen.storage import save_base64_image, save_metadata_sidecar


def _make_client() -> AsyncOpenAI:
    """Create an OpenAI client, raising if the API key is missing."""
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set — cannot use OpenAI provider"
        )
    return AsyncOpenAI(api_key=api_key)


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse a 'WIDTHxHEIGHT' string into (width, height)."""
    w, h = size_str.split("x")
    return int(w), int(h)


async def generate_image(
    prompt: str,
    background: Background = "opaque",
    quality: Quality = "medium",
    aspect_ratio: AspectRatio = "square",
    output_format: OutputFormat = "png",
    category: str = "general",
) -> ImageResult:
    """Generate a single image via OpenAI's gpt-image-1.5 model."""
    if output_format == "svg":
        raise ValueError(
            "OpenAI does not support SVG output — use the Recraft provider"
        )
    if output_format == "jpg" and background == "transparent":
        raise ValueError("JPEG does not support transparency — use png or webp")

    client = _make_client()
    size = ASPECT_RATIO_TO_SIZE[aspect_ratio]
    width, height = _parse_size(size)

    response = await client.images.generate(
        model="gpt-image-1.5",
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
    )

    b64_data = response.data[0].b64_json
    extension = output_format if output_format != "jpg" else "jpg"
    output_dir = get_output_dir()
    file_path = save_base64_image(
        b64_data, output_dir, prompt, extension, category=category
    )

    from datetime import datetime, timezone

    save_metadata_sidecar(
        file_path,
        ImageMetadata(
            prompt=prompt,
            provider="openai",
            tool_used="generate_image",
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            format=output_format,
            width=width,
            height=height,
            category=category,
            file_path=str(file_path),
        ),
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
    """Generate a grid of related icons with transparent background."""
    style_clause = f" in {style} style" if style else ""
    grid_prompt = (
        f"A clean grid of {count} distinct icons{style_clause} on a transparent background, "
        f"evenly spaced: {prompt}"
    )

    return await generate_image(
        prompt=grid_prompt,
        background="transparent",
        quality="high",
        aspect_ratio="landscape",
        output_format="png",
        category=category,
    )
