"""Shared types and data classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Provider = Literal["openai", "recraft"]
Background = Literal["transparent", "opaque"]
Quality = Literal["low", "medium", "high"]
AspectRatio = Literal["square", "landscape", "portrait"]
OutputFormat = Literal["png", "jpg", "webp", "svg"]
VectorQuality = Literal["standard", "pro"]

ASPECT_RATIO_TO_SIZE: dict[AspectRatio, str] = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
}


@dataclass
class ImageResult:
    file_path: str
    width: int
    height: int
    format: str
    b64_data: str = ""
    category: str = "general"


@dataclass
class ImageMetadata:
    prompt: str
    provider: str
    tool_used: str
    timestamp: str
    format: str
    width: int
    height: int
    category: str
    file_path: str
