#!/usr/bin/env python3
"""
Theme validation script for LibreAssistant.

This script validates that all bundled themes in ui/themes/ are complete
and cover all major color modes (light, dark, high-contrast).
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# Required CSS variables that all themes should define
REQUIRED_VARIABLES = {
    '--color-primary',
    '--color-primary-hover', 
    '--color-secondary',
    '--color-background',
    '--color-surface',
    '--color-text',
    '--color-border',
    '--color-backdrop',
    '--shadow-card',
    '--font-family-mono',
}

# Expected major color modes
EXPECTED_THEMES = {
    'light': 'Light theme for normal environments',
    'dark': 'Dark theme for low-light environments', 
    'high-contrast': 'High contrast theme for accessibility'
}

def extract_css_variables(css_content: str) -> Set[str]:
    """Extract CSS variable names from CSS content."""
    pattern = r'--[\w-]+(?=\s*:)'
    matches = re.findall(pattern, css_content)
    return set(matches)

def validate_theme_file(theme_path: Path) -> Dict[str, any]:
    """Validate a single theme CSS file."""
    result = {
        'path': str(theme_path),
        'name': theme_path.stem,
        'exists': theme_path.exists(),
        'variables_found': set(),
        'missing_variables': set(),
        'is_complete': False,
        'errors': []
    }
    
    if not theme_path.exists():
        result['errors'].append(f"Theme file {theme_path} does not exist")
        return result
    
    try:
        css_content = theme_path.read_text()
        result['variables_found'] = extract_css_variables(css_content)
        result['missing_variables'] = REQUIRED_VARIABLES - result['variables_found']
        result['is_complete'] = len(result['missing_variables']) == 0
        
        if not result['is_complete']:
            result['errors'].append(f"Missing variables: {', '.join(result['missing_variables'])}")
            
    except Exception as e:
        result['errors'].append(f"Error reading theme file: {e}")
    
    return result

def validate_theme_catalog(catalog_path: Path) -> Dict[str, any]:
    """Validate the theme catalog JSON file."""
    result = {
        'path': str(catalog_path),
        'exists': catalog_path.exists(),
        'themes': [],
        'missing_major_themes': set(),
        'errors': []
    }
    
    if not catalog_path.exists():
        result['errors'].append(f"Theme catalog {catalog_path} does not exist")
        return result
    
    try:
        catalog_content = json.loads(catalog_path.read_text())
        result['themes'] = [theme['id'] for theme in catalog_content]
        
        # Check for major color modes
        found_themes = set(result['themes'])
        result['missing_major_themes'] = set(EXPECTED_THEMES.keys()) - found_themes
        
        if result['missing_major_themes']:
            result['errors'].append(f"Missing major themes: {', '.join(result['missing_major_themes'])}")
            
    except Exception as e:
        result['errors'].append(f"Error reading theme catalog: {e}")
    
    return result

def main():
    """Main validation function."""
    print("LibreAssistant Theme Validation Report")
    print("=" * 40)
    
    # Setup paths
    repo_root = Path(__file__).resolve().parents[1]
    themes_dir = repo_root / "ui" / "themes"
    catalog_path = repo_root / "ui" / "theme-catalog.json"
    
    # Validate themes directory
    if not themes_dir.exists():
        print(f"❌ CRITICAL: Themes directory {themes_dir} does not exist!")
        return False
    
    # Validate theme catalog
    print("\n1. Theme Catalog Validation")
    print("-" * 25)
    catalog_result = validate_theme_catalog(catalog_path)
    
    if catalog_result['errors']:
        print(f"❌ Catalog validation failed:")
        for error in catalog_result['errors']:
            print(f"   - {error}")
    else:
        print(f"✅ Catalog validation passed")
        print(f"   - Found themes: {', '.join(catalog_result['themes'])}")
    
    # Validate individual theme files
    print(f"\n2. Individual Theme Validation")
    print("-" * 30)
    
    theme_files = list(themes_dir.glob("*.css"))
    if not theme_files:
        print(f"❌ CRITICAL: No theme CSS files found in {themes_dir}!")
        return False
    
    all_valid = True
    for theme_file in sorted(theme_files):
        result = validate_theme_file(theme_file)
        
        if result['is_complete'] and not result['errors']:
            print(f"✅ {result['name']}: Complete theme")
        else:
            print(f"❌ {result['name']}: Issues found")
            for error in result['errors']:
                print(f"   - {error}")
            all_valid = False
    
    # Check for major color mode coverage
    print(f"\n3. Major Color Mode Coverage")
    print("-" * 30)
    
    found_theme_files = {f.stem for f in theme_files}
    missing_major_themes = set(EXPECTED_THEMES.keys()) - found_theme_files
    
    if missing_major_themes:
        print(f"❌ Missing major theme files: {', '.join(missing_major_themes)}")
        all_valid = False
    else:
        print(f"✅ All major color modes have theme files")
    
    for theme_id, description in EXPECTED_THEMES.items():
        if theme_id in found_theme_files:
            print(f"   ✅ {theme_id}: {description}")
        else:
            print(f"   ❌ {theme_id}: {description} - MISSING")
    
    # Summary
    print(f"\n4. Summary")
    print("-" * 10)
    
    if all_valid and not catalog_result['errors']:
        print("✅ All theme validations passed!")
        print("   - All major color modes are covered")
        print("   - All theme files are complete") 
        print("   - Theme catalog is valid")
        return True
    else:
        print("❌ Theme validation failed!")
        print("   Please fix the issues above to ensure proper theme functionality.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)