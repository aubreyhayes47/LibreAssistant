/**
 * Color Contrast Accessibility Tests
 * Ensures all themes meet WCAG 2.1 AA standards
 */

import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import path from 'path';

// WCAG 2.1 contrast ratio thresholds
const WCAG_AA_NORMAL = 4.5;

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * Calculate relative luminance
 */
function relativeLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 */
function contrastRatio(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return 0;
  
  const l1 = relativeLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = relativeLuminance(rgb2.r, rgb2.g, rgb2.b);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Parse CSS variables from theme file
 */
function parseThemeColors(cssContent) {
  const colors = {};
  const variableRegex = /--color-(\w+):\s*([#\w\s(),.-]+);/g;
  let match;
  
  while ((match = variableRegex.exec(cssContent)) !== null) {
    const colorName = match[1];
    let colorValue = match[2].trim();
    
    // Handle only hex colors for now, skip rgba values
    if (colorValue.startsWith('#')) {
      colors[colorName] = colorValue;
    }
  }
  
  return colors;
}

/**
 * Test color contrast for a theme
 */
function testThemeContrast(themePath, expectedMinimumContrast = WCAG_AA_NORMAL) {
  const themeName = path.basename(themePath, '.css');
  const cssContent = fs.readFileSync(themePath, 'utf8');
  const colors = parseThemeColors(cssContent);
  
  // Critical color combinations that must meet WCAG AA
  const criticalCombinations = [
    { name: 'Text on Background', fg: 'text', bg: 'background' },
    { name: 'Text on Surface', fg: 'text', bg: 'surface' },
    { name: 'Secondary on Background', fg: 'secondary', bg: 'background' }
  ];
  
  const failures = [];
  
  criticalCombinations.forEach(combo => {
    const fgColor = colors[combo.fg];
    const bgColor = colors[combo.bg];
    
    if (fgColor && bgColor) {
      const ratio = contrastRatio(fgColor, bgColor);
      
      if (ratio < expectedMinimumContrast) {
        failures.push({
          combination: combo.name,
          foreground: fgColor,
          background: bgColor,
          ratio: Math.round(ratio * 100) / 100,
          required: expectedMinimumContrast
        });
      }
    }
  });
  
  return {
    theme: themeName,
    colors,
    failures
  };
}

test('light theme meets WCAG AA contrast requirements', () => {
  const result = testThemeContrast('ui/themes/light.css');
  
  assert.strictEqual(result.failures.length, 0, 
    `Light theme has contrast failures: ${JSON.stringify(result.failures, null, 2)}`);
  
  // Verify specific color values that were fixed
  assert.strictEqual(result.colors.border, '#6f7173', 
    'Light theme border color should be accessible');
});

test('dark theme meets WCAG AA contrast requirements', () => {
  const result = testThemeContrast('ui/themes/dark.css');
  
  assert.strictEqual(result.failures.length, 0, 
    `Dark theme has contrast failures: ${JSON.stringify(result.failures, null, 2)}`);
  
  // Verify specific color values that were fixed  
  assert.strictEqual(result.colors.border, '#7b7f83',
    'Dark theme border color should be accessible');
});

test('high-contrast theme meets WCAG AA contrast requirements', () => {
  const result = testThemeContrast('ui/themes/high-contrast.css');
  
  assert.strictEqual(result.failures.length, 0, 
    `High-contrast theme has contrast failures: ${JSON.stringify(result.failures, null, 2)}`);
  
  // High contrast theme should exceed minimum requirements
  const textOnBg = contrastRatio(result.colors.text, result.colors.background);
  assert(textOnBg >= 7.0, 'High-contrast theme should exceed AAA standards');
});

test('solarized theme meets WCAG AA contrast requirements', () => {
  const result = testThemeContrast('ui/themes/solarized.css');
  
  assert.strictEqual(result.failures.length, 0, 
    `Solarized theme has contrast failures: ${JSON.stringify(result.failures, null, 2)}`);
  
  // Verify specific color values that were fixed
  assert.strictEqual(result.colors.primary, '#2076b3',
    'Solarized theme primary color should be accessible');
  assert.strictEqual(result.colors.secondary, '#207972',
    'Solarized theme secondary color should be accessible');
  assert.strictEqual(result.colors.border, '#677171',
    'Solarized theme border color should be accessible');
});

test('all theme border colors are sufficiently visible', () => {
  const themeDir = 'ui/themes';
  const themeFiles = fs.readdirSync(themeDir)
    .filter(file => file.endsWith('.css'))
    .map(file => path.join(themeDir, file));
  
  themeFiles.forEach(themePath => {
    const themeName = path.basename(themePath, '.css');
    const cssContent = fs.readFileSync(themePath, 'utf8');
    const colors = parseThemeColors(cssContent);
    
    if (colors.border && colors.background) {
      const ratio = contrastRatio(colors.border, colors.background);
      
      // Border visibility requires at least 3:1 contrast for large elements
      assert(ratio >= 3.0, 
        `${themeName} theme border visibility insufficient: ${ratio}:1 (needs 3:1)`);
    }
  });
});

test('audit report contains no accessibility issues', () => {
  const reportPath = 'color-contrast-audit-report.json';
  
  // Run the audit if the report doesn't exist
  if (!fs.existsSync(reportPath)) {
    const { execSync } = require('child_process');
    execSync('node scripts/audit-color-contrast.js', { stdio: 'inherit' });
  }
  
  const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  const totalIssues = report.audits.reduce((sum, audit) => sum + audit.issues.length, 0);
  
  assert.strictEqual(totalIssues, 0, 
    'Audit report should contain no accessibility issues');
});