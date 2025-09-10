#!/usr/bin/env python3
"""
Test that validates theme marketplace can load all bundled themes correctly.
"""

import json
from pathlib import Path

def test_theme_marketplace_integration():
    """Test that theme marketplace can handle all bundled themes."""
    
    repo_root = Path(__file__).resolve().parents[1]
    catalog_path = repo_root / "ui" / "theme-catalog.json"
    themes_dir = repo_root / "ui" / "themes"
    marketplace_js = repo_root / "ui" / "components" / "theme-marketplace.js"
    
    # Load theme catalog
    catalog = json.loads(catalog_path.read_text())
    
    # Extract builtin themes from marketplace.js
    marketplace_content = marketplace_js.read_text()
    
    print("Theme Marketplace Integration Test")
    print("=" * 35)
    
    # Check that all themes in catalog have corresponding behavior
    builtin_themes = ['light', 'dark', 'high-contrast']
    
    issues = []
    
    for theme in catalog:
        theme_id = theme['id']
        print(f"\n✓ Testing theme: {theme_id}")
        
        if theme_id in builtin_themes:
            # Built-in themes should be handled via data-theme attribute
            if f"'{theme_id}'" not in marketplace_content:
                issues.append(f"Built-in theme '{theme_id}' not found in builtins array")
                print(f"  ❌ Not found in builtins array")
            else:
                print(f"  ✅ Found in builtins array")
        else:
            # Community themes should have CSS files
            css_file = themes_dir / f"{theme_id}.css"
            if not css_file.exists():
                issues.append(f"Community theme '{theme_id}' missing CSS file: {css_file}")
                print(f"  ❌ Missing CSS file: {css_file}")
            else:
                print(f"  ✅ CSS file exists: {css_file}")
    
    # Check that builtins array matches expected themes
    if "this.builtins = ['light', 'dark', 'high-contrast']" not in marketplace_content:
        issues.append("builtins array in theme-marketplace.js doesn't match expected built-in themes")
        print(f"\n❌ builtins array mismatch")
    else:
        print(f"\n✅ builtins array matches expected themes")
    
    # Summary
    print(f"\nSummary:")
    print(f"-------")
    
    if issues:
        print(f"❌ {len(issues)} issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"✅ All themes properly integrated with marketplace")
        print(f"   - {len([t for t in catalog if t['id'] in builtin_themes])} built-in themes")
        print(f"   - {len([t for t in catalog if t['id'] not in builtin_themes])} community themes") 
        print(f"   - {len(catalog)} total themes in catalog")
        return True

if __name__ == "__main__":
    success = test_theme_marketplace_integration()
    exit(0 if success else 1)