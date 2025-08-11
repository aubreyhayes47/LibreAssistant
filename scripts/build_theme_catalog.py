# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.
"""Utility to build the theme catalog from community submissions."""

from __future__ import annotations

import json
from pathlib import Path

from libreassistant.themes import sanitize_css

BUILTIN_THEMES = [
    {"id": "light", "name": "Light", "author": "LibreAssistant", "preview": "#f8f9fa", "rating": 5},
    {"id": "dark", "name": "Dark", "author": "LibreAssistant", "preview": "#1e1e1e", "rating": 4},
    {"id": "high-contrast", "name": "High Contrast", "author": "LibreAssistant", "preview": "#000000", "rating": 4},
]


def build_catalog(repo_dir: Path, dest_dir: Path, catalog_path: Path) -> None:
    """Generate sanitized CSS and theme catalog JSON."""
    themes = list(BUILTIN_THEMES)
    dest_dir.mkdir(parents=True, exist_ok=True)
    for theme_dir in sorted(p for p in repo_dir.iterdir() if p.is_dir()):
        meta_file = theme_dir / "metadata.json"
        css_file = theme_dir / "theme.css"
        if not meta_file.exists() or not css_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        css = css_file.read_text()
        sanitized = sanitize_css(css)
        (dest_dir / f"{meta['id']}.css").write_text(sanitized)
        themes.append(meta)
    catalog_path.write_text(json.dumps(themes, indent=2))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    repo_dir = root / "community-themes"
    dest_dir = root / "ui" / "themes"
    catalog_path = root / "ui" / "theme-catalog.json"
    build_catalog(repo_dir, dest_dir, catalog_path)


if __name__ == "__main__":
    main()
