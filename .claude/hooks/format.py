"""Auto-format Python files with ruff after Claude Code edits them."""
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    data = json.load(sys.stdin)
    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not file_path.endswith(".py"):
        return

    path = Path(file_path)
    if not path.exists():
        return

    subprocess.run(
        ["ruff", "check", "--fix", "--quiet", str(path)],
        capture_output=True,
    )
    subprocess.run(
        ["ruff", "format", "--quiet", str(path)],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
