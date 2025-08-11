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
