<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Scripts

Developer utilities for maintaining and building parts of the project.

## `build_theme_catalog.py`

Generates sanitized CSS files and the `theme-catalog.json` index from themes
in `community-themes`.

Run from the repository root:

```bash
python scripts/build_theme_catalog.py
```

The script writes sanitized CSS files into `ui/themes/` and creates
`ui/theme-catalog.json` with metadata for both built‑in and community themes.

## `check_license_headers.py`

Scans the repository for files missing the standard MIT license header and
returns a non‑zero exit code if any are found.

Invoke with:

```bash
python scripts/check_license_headers.py
# or, since it is executable
./scripts/check_license_headers.py
```

## Environment

Both scripts require **Python 3.10+**.

`build_theme_catalog.py` depends on the `libreassistant` package, which in turn
uses `cssutils` for CSS sanitization. Install project dependencies before
running the script:

```bash
pip install -e .
```

`check_license_headers.py` uses only the Python standard library and has no
additional dependencies.
