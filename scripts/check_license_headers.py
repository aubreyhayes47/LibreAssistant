#!/usr/bin/env python3
# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.
"""Simple license header checker for repository files."""

from __future__ import annotations

import pathlib
import sys

MIT_PHRASE = "Licensed under the MIT License."


def file_has_header(path: pathlib.Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as fh:
            snippet = fh.read(1024)
            return MIT_PHRASE in snippet
    except UnicodeDecodeError:
        # Skip binary files
        return True


def main() -> None:
    repo = pathlib.Path(__file__).resolve().parent.parent
    failures: list[str] = []
    for path in repo.rglob("*"):
        if (
            path.is_file()
            and ".git" not in path.parts
            and ".pytest_cache" not in path.parts
            and "node_modules" not in path.parts
            and ".venv" not in path.parts
            and path.name != "LICENSE.txt"
        ):
            if path.suffix in {".md", ".py", ".yml", ".yaml", ".sh", ".txt"}:
                if not file_has_header(path):
                    failures.append(str(path.relative_to(repo)))
    if failures:
        print("Missing MIT license header in:")
        for name in failures:
            print(f" - {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
