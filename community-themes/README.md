<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Community Themes

Theme contributions live in this directory. Each theme is stored in its own
folder containing a `metadata.json` file and a `theme.css` stylesheet
that overrides design tokens via CSS custom properties. Only a small whitelist
of standard properties is permitted; others will be removed during sanitization.

```text
community-themes/
  my-theme/
    metadata.json
    theme.css
```

Submit pull requests that add a new folder with your theme files. The
`scripts/build_theme_catalog.py` utility sanitizes the CSS, updates
`ui/theme-catalog.json`, and writes the cleaned stylesheet to `ui/themes/`. The
API exposes the sanitized CSS at `/api/v1/themes/{name}.css`, and the
marketplace loads it in a sandboxed iframe with a strict Content Security Policy.

## `metadata.json` Style Guide

Each theme must include a `metadata.json` file with these fields:

- `id`: Lowercase, dash-separated identifier matching the folder name.
- `name`: Human-readable display name in Title Case.
- `author`: Name or handle of the theme's creator.
- `preview`: Hex color (`#RRGGBB` or `#RGB`) used for previews.
- `rating`: Integer from `0`–`5` indicating relative contrast.

Example:

```json
{
  "id": "solarized",
  "name": "Solarized",
  "author": "Community",
  "preview": "#fdf6e3",
  "rating": 3
}
```

## Verifying your theme

Run the build script to sanitize your CSS and refresh the catalog:

```bash
python scripts/build_theme_catalog.py
```

This generates sanitized styles under `ui/themes/` and updates
`ui/theme-catalog.json`. Open the resulting `ui/themes/<id>.css` in a browser or
local build to confirm the theme renders as expected before submitting a pull
request.
