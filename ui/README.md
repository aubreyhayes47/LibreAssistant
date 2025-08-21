<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# UI Package

This directory contains standalone web components and the assets needed to style them.

```text
ui/
  components/          # individual custom element modules
  tokens.css           # shared design tokens and built-in theme variables
  theme-catalog.json   # metadata for built-in and community themes
  themes/              # sanitized CSS for each theme listed in the catalog
```

## Components

Each file in `components/` defines a web component and registers it with
`customElements.define()`. Components can be loaded on demand by importing their
module:

```js
import './components/primary-button.js';
```

After the import, the `<primary-button>` tag becomes available to the page. This
pattern keeps bundles small and allows the runtime to lazy‑load components when
needed.

## Design tokens

`tokens.css` exposes the shared design tokens used across all components. It
contains typography, spacing and radius scales as well as color variables for
the built‑in light, dark and high‑contrast themes. The stylesheet should be
loaded once at application start so every component can reference the tokens.

## Themes

`theme-catalog.json` enumerates the themes that the application can load. The
JSON entries include an identifier, display name, author and preview color. The
catalog mixes core themes with community contributions such as the "Solarized"
example.

Sanitized CSS for each catalog entry lives in `ui/themes/`. Community members
submit new themes under `community-themes/`, and running
`scripts/build_theme_catalog.py` updates both the catalog and the compiled CSS in
`ui/themes/`.

### Registering a custom theme

To add your own theme:

1. Create `community-themes/<your-theme>/metadata.json` and
   `community-themes/<your-theme>/theme.css` with your variables.
2. Run `scripts/build_theme_catalog.py` to sanitize the CSS, copy it into
   `ui/themes/`, and append an entry to `ui/theme-catalog.json`.
3. Load the new theme in the UI by setting `data-theme="<your-theme>"` on the
   root element or by injecting the generated CSS.

## Web component loading

The application dynamically loads web component modules as their tags appear in
the DOM. This ensures the browser only downloads the code required for the
current view while maintaining compatibility with standard Web Component APIs.
