"""CLI tests for corporate_imgen.storage module."""

from __future__ import annotations

import base64
import os
import re
import tempfile
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])

from corporate_imgen.storage import (
    build_filename,
    sanitise_filename,
    save_base64_image,
    save_svg,
)

# ── sanitise_filename ────────────────────────────────────────────────

# Basic slug
result = sanitise_filename("Hello World")
assert result == "hello-world", f"basic slug: got {result!r}"
print("PASS: sanitise_filename basic slug")

# Special characters removed
result = sanitise_filename("icons: security & finance!!")
assert result == "icons-security-finance", f"special chars: got {result!r}"
print("PASS: sanitise_filename special chars removed")

# Length truncation
long_prompt = "a" * 100
result = sanitise_filename(long_prompt, max_length=20)
assert len(result) <= 20, f"truncation: length {len(result)} > 20"
print("PASS: sanitise_filename length truncation")

# Whitespace normalised
result = sanitise_filename("  lots   of   spaces  ")
assert result == "lots-of-spaces", f"whitespace: got {result!r}"
print("PASS: sanitise_filename whitespace normalised")

# ── build_filename ───────────────────────────────────────────────────

result = build_filename("test prompt", "png")
# Expected pattern: slug-YYYY-MM-DD-HHMMSS.ext
pattern = r"^test-prompt-\d{4}-\d{2}-\d{2}-\d{6}\.png$"
assert re.match(pattern, result), f"build_filename: got {result!r}"
print("PASS: build_filename correct format")

# ── save_base64_image ────────────────────────────────────────────────

raw_bytes = b"\x89PNG tiny"
b64_data = base64.b64encode(raw_bytes).decode()

with tempfile.TemporaryDirectory() as tmpdir:
    out_dir = Path(tmpdir)
    path = save_base64_image(b64_data, out_dir, "my image", "png")
    assert path.exists(), f"save_base64_image: file not created at {path}"
    assert path.read_bytes() == raw_bytes, "save_base64_image: content mismatch"
    assert path.suffix == ".png", f"save_base64_image: wrong suffix {path.suffix}"
    print("PASS: save_base64_image creates file with correct content")

# ── save_svg ─────────────────────────────────────────────────────────

svg_content = (
    '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
)

with tempfile.TemporaryDirectory() as tmpdir:
    out_dir = Path(tmpdir)
    path = save_svg(svg_content, out_dir, "vector graphic")
    assert path.exists(), f"save_svg: file not created at {path}"
    assert path.read_text(encoding="utf-8") == svg_content, "save_svg: content mismatch"
    assert path.suffix == ".svg", f"save_svg: wrong suffix {path.suffix}"
    print("PASS: save_svg creates file with correct SVG content")

print("\nALL TESTS PASSED")
