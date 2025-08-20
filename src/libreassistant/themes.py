# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Utilities for loading and sanitizing theme CSS."""

from __future__ import annotations

from pathlib import Path

import cssutils

SAFE_PROPERTIES = {
    "color",
    "background",
    "background-color",
    "border",
    "border-radius",
    "font-family",
    "font-size",
    "font-weight",
    "box-shadow",
}

THEME_DIR = Path(__file__).resolve().parents[2] / "ui" / "themes"


def sanitize_css(css_text: str) -> str:
    """Return a sanitized CSS string allowing only whitelisted properties."""
    parser = cssutils.CSSParser()
    sheet = parser.parseString(css_text)
    for rule in list(sheet.cssRules):
        if rule.type != rule.STYLE_RULE:
            sheet.deleteRule(rule)
            continue
        for prop in list(rule.style):
            if (
                prop.name not in SAFE_PROPERTIES
                and not prop.name.startswith("--")
            ):
                rule.style.removeProperty(prop.name)
    cssutils.ser.prefs.useMinified()
    return sheet.cssText.decode("utf-8")


def get_theme_css(theme_id: str) -> str:
    """Load and sanitize CSS for the given theme id."""
    allowed = {p.stem for p in THEME_DIR.glob("*.css")}
    if theme_id not in allowed:
        raise FileNotFoundError(f"Theme '{theme_id}' not found")
    path = THEME_DIR / f"{theme_id}.css"
    css = path.read_text()
    return sanitize_css(css)
