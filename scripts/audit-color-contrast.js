#!/usr/bin/env node

/**
 * Color Contrast Accessibility Audit Tool
 * Analyzes all themes for WCAG 2.1 AA compliance
 */

import fs from 'fs';
import path from 'path';

// WCAG 2.1 contrast ratio thresholds
const WCAG_AA_NORMAL = 4.5;
const WCAG_AA_LARGE = 3.0;
const WCAG_AAA_NORMAL = 7.0;
const WCAG_AAA_LARGE = 4.5;

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
 * Check if contrast ratio meets WCAG standards
 */
function checkWCAGCompliance(ratio) {
  return {
    AA_normal: ratio >= WCAG_AA_NORMAL,
    AA_large: ratio >= WCAG_AA_LARGE,
    AAA_normal: ratio >= WCAG_AAA_NORMAL,
    AAA_large: ratio >= WCAG_AAA_LARGE,
    ratio: Math.round(ratio * 100) / 100
  };
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
 * Audit a single theme file
 */
function auditTheme(themePath) {
  const themeName = path.basename(themePath, '.css');
  const cssContent = fs.readFileSync(themePath, 'utf8');
  const colors = parseThemeColors(cssContent);
  
  console.log(`\n=== ${themeName.toUpperCase()} THEME AUDIT ===`);
  console.log('Colors found:', Object.keys(colors).length);
  
  const results = [];
  
  // Define critical color combinations to test
  const combinations = [
    { name: 'Text on Background', fg: 'text', bg: 'background' },
    { name: 'Text on Surface', fg: 'text', bg: 'surface' },
    { name: 'Secondary on Background', fg: 'secondary', bg: 'background' },
    { name: 'Border on Background', fg: 'border', bg: 'background' },
    { name: 'Primary (self-contrast)', fg: 'primary', bg: 'background' }
  ];
  
  combinations.forEach(combo => {
    const fgColor = colors[combo.fg];
    const bgColor = colors[combo.bg];
    
    if (fgColor && bgColor) {
      const ratio = contrastRatio(fgColor, bgColor);
      const compliance = checkWCAGCompliance(ratio);
      
      const result = {
        combination: combo.name,
        foreground: fgColor,
        background: bgColor,
        ratio: compliance.ratio,
        compliance
      };
      
      results.push(result);
      
      const passAA = compliance.AA_normal ? '✓' : '✗';
      const passAAA = compliance.AAA_normal ? '✓' : '✗';
      
      console.log(`${combo.name}:`);
      console.log(`  ${fgColor} on ${bgColor}`);
      console.log(`  Ratio: ${compliance.ratio}:1`);
      console.log(`  WCAG AA: ${passAA} | WCAG AAA: ${passAAA}`);
      
      if (!compliance.AA_normal) {
        console.log(`  ⚠️  FAILS WCAG AA requirement (needs ${WCAG_AA_NORMAL}:1)`);
      }
    } else {
      console.log(`${combo.name}: Missing colors (fg: ${combo.fg}, bg: ${combo.bg})`);
    }
  });
  
  return {
    theme: themeName,
    colors,
    results,
    issues: results.filter(r => !r.compliance.AA_normal)
  };
}

/**
 * Generate summary report
 */
function generateSummaryReport(audits) {
  console.log('\n' + '='.repeat(50));
  console.log('ACCESSIBILITY AUDIT SUMMARY');
  console.log('='.repeat(50));
  
  const totalIssues = audits.reduce((sum, audit) => sum + audit.issues.length, 0);
  
  console.log(`\nThemes audited: ${audits.length}`);
  console.log(`Total accessibility issues: ${totalIssues}`);
  
  if (totalIssues > 0) {
    console.log('\nISSUES BY THEME:');
    audits.forEach(audit => {
      if (audit.issues.length > 0) {
        console.log(`\n${audit.theme}:`);
        audit.issues.forEach(issue => {
          console.log(`  - ${issue.combination}: ${issue.ratio}:1 (needs ${WCAG_AA_NORMAL}:1)`);
        });
      }
    });
    
    console.log('\nRECOMMENDATIONS:');
    audits.forEach(audit => {
      if (audit.issues.length > 0) {
        console.log(`\n${audit.theme}:`);
        audit.issues.forEach(issue => {
          const improvement = WCAG_AA_NORMAL / issue.ratio;
          console.log(`  - ${issue.combination} needs ${Math.round(improvement * 100)}% more contrast`);
        });
      }
    });
  } else {
    console.log('\n✅ All themes pass WCAG AA contrast requirements!');
  }
  
  return totalIssues;
}

/**
 * Save detailed JSON report
 */
function saveJSONReport(audits, outputPath) {
  const report = {
    timestamp: new Date().toISOString(),
    wcag_standard: 'AA',
    thresholds: {
      normal_text: WCAG_AA_NORMAL,
      large_text: WCAG_AA_LARGE
    },
    audits
  };
  
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
  console.log(`\nDetailed report saved to: ${outputPath}`);
}

/**
 * Main audit function
 */
function main() {
  const themeDir = path.join(process.cwd(), 'ui', 'themes');
  const outputFile = path.join(process.cwd(), 'color-contrast-audit-report.json');
  
  console.log('LibreAssistant Color Contrast Accessibility Audit');
  console.log('WCAG 2.1 Level AA Standards');
  console.log(`Source: ${themeDir}`);
  
  // Find all theme files
  const themeFiles = fs.readdirSync(themeDir)
    .filter(file => file.endsWith('.css'))
    .map(file => path.join(themeDir, file));
  
  console.log(`\nFound ${themeFiles.length} theme files`);
  
  // Audit each theme
  const audits = themeFiles.map(auditTheme);
  
  // Generate summary and save report
  const totalIssues = generateSummaryReport(audits);
  saveJSONReport(audits, outputFile);
  
  // Exit with error code if issues found
  process.exit(totalIssues > 0 ? 1 : 0);
}

// Run the audit
main();