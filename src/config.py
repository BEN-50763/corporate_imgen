"""Configuration loading from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY")


def get_recraft_api_key() -> str | None:
    return os.environ.get("RECRAFT_API_KEY")


def get_output_dir() -> Path:
    raw = os.environ.get("IMAGE_OUTPUT_DIR", "./data")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()
