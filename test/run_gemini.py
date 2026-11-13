"""Run the project's existing CLI with the Gemini provider."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    command = [
        sys.executable,
        str(project_root / "main.py"),
        *sys.argv[1:],
        "--provider",
        "gemini",
    ]
    return subprocess.run(command, cwd=project_root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
