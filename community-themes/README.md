<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Community Themes

Theme contributions live in this directory. Each theme is stored in its own
folder containing a `metadata.json` file and a `theme.css` stylesheet.

```text
community-themes/
  my-theme/
    metadata.json
    theme.css
```

Submit pull requests that add a new folder with your theme files. The
`scripts/build_theme_catalog.py` utility sanitizes the CSS and updates the
UI catalog consumed by the marketplace.
