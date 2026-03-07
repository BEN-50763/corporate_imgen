"""File I/O for saving generated images."""

from __future__ import annotations

import base64
import dataclasses
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


from corporate_imgen.models import ImageMetadata

IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MAX_PREVIEW_BYTES: int = 750_000  # ~1MB base64 budget (base64 inflates ~33%)
MAX_PREVIEW_DIMENSION: int = 768


def compress_for_preview(b64_data: str, image_format: str) -> str:
    """Compress an image for inline display, guaranteed under 1MB base64.

    Returns base64-encoded JPEG. SVGs are returned as-is (already small).
    """
    if image_format == "svg":
        return b64_data

    raw = base64.b64decode(b64_data)
    if len(raw) <= MAX_PREVIEW_BYTES:
        return b64_data

    from io import BytesIO

    from PIL import Image

    img = Image.open(BytesIO(raw))

    # Resize if larger than max dimension
    longest = max(img.width, img.height)
    if longest > MAX_PREVIEW_DIMENSION:
        scale = MAX_PREVIEW_DIMENSION / longest
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    # Convert RGBA to RGB for JPEG
    if img.mode in ("RGBA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background

    # Compress as JPEG, lowering quality until under budget
    for quality in (75, 50, 30):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        if buf.tell() <= MAX_PREVIEW_BYTES:
            return base64.b64encode(buf.getvalue()).decode()

    # Last resort: already the smallest we can do
    return base64.b64encode(buf.getvalue()).decode()


def sanitise_filename(prompt: str, max_length: int = 50) -> str:
    """Convert a prompt into a filesystem-safe slug."""
    slug = prompt.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_length].rstrip("-")


def build_filename(prompt: str, extension: str) -> str:
    """Build a descriptive filename from prompt + timestamp."""
    slug = sanitise_filename(prompt)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    return f"{slug}-{timestamp}.{extension}"


def save_base64_image(
    data: str,
    output_dir: Path,
    prompt: str,
    extension: str,
    category: str = "general",
) -> Path:
    """Decode base64 image data and save to disc."""
    filename = build_filename(prompt, extension)
    category_dir = output_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    filepath = category_dir / filename
    filepath.write_bytes(base64.b64decode(data))
    return filepath


def save_svg(
    content: str,
    output_dir: Path,
    prompt: str,
    category: str = "general",
) -> Path:
    """Save SVG content to disc."""
    filename = build_filename(prompt, "svg")
    category_dir = output_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    filepath = category_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def save_metadata_sidecar(image_path: Path, metadata: ImageMetadata) -> Path:
    """Save a JSON sidecar file next to the image."""
    sidecar_path = image_path.with_suffix(".json")
    sidecar_path.write_text(
        json.dumps(dataclasses.asdict(metadata), indent=2),
        encoding="utf-8",
    )
    return sidecar_path


def list_category_tree(output_dir: Path) -> dict[str, Any]:
    """Walk output dir recursively, returning folder hierarchy with image counts."""
    tree: dict[str, Any] = {}

    if not output_dir.is_dir():
        return tree

    for path in output_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        rel = path.relative_to(output_dir)
        parts = rel.parts[:-1]  # directory parts only

        node = tree
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]
            node["_count"] = node.get("_count", 0) + 1

    return tree


def list_images_in_category(
    output_dir: Path,
    category: str,
    recurse: bool = True,
) -> list[dict[str, Any]]:
    """Read .json sidecar files from a category folder."""
    category_dir = output_dir / category

    if not category_dir.is_dir():
        return []

    pattern = "**/*.json" if recurse else "*.json"
    results: list[dict[str, Any]] = []

    for sidecar in category_dir.glob(pattern):
        if not sidecar.is_file():
            continue
        # Only include sidecars that have a matching image file
        image_exists = any(
            sidecar.with_suffix(ext).is_file() for ext in IMAGE_EXTENSIONS
        )
        if not image_exists:
            continue
        results.append(json.loads(sidecar.read_text(encoding="utf-8")))

    return results
