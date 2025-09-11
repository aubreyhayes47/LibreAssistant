#!/usr/bin/env node

/**
 * Color Contrast Fix Utility
 * Generates accessible color fixes for failed contrast combinations
 */

import fs from 'fs';

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
 * Convert RGB to hex
 */
function rgbToHex(r, g, b) {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
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
 * Darken a color by a percentage
 */
function darkenColor(hex, percent) {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  
  const factor = 1 - (percent / 100);
  return rgbToHex(
    Math.round(rgb.r * factor),
    Math.round(rgb.g * factor),
    Math.round(rgb.b * factor)
  );
}

/**
 * Lighten a color by a percentage
 */
function lightenColor(hex, percent) {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  
  const factor = percent / 100;
  return rgbToHex(
    Math.round(rgb.r + (255 - rgb.r) * factor),
    Math.round(rgb.g + (255 - rgb.g) * factor),
    Math.round(rgb.b + (255 - rgb.b) * factor)
  );
}

/**
 * Find a color that meets WCAG AA contrast requirements
 */
function findAccessibleColor(originalColor, backgroundColor, preferDirection = 'auto') {
  const bgRgb = hexToRgb(backgroundColor);
  const bgLuminance = relativeLuminance(bgRgb.r, bgRgb.g, bgRgb.b);
  
  // Determine if we should go darker or lighter
  let shouldDarken = preferDirection === 'darker' || 
                    (preferDirection === 'auto' && bgLuminance > 0.5);
  
  let currentColor = originalColor;
  let step = 5; // Start with 5% adjustments
  let maxSteps = 20; // Prevent infinite loops
  let steps = 0;
  
  while (steps < maxSteps) {
    const ratio = contrastRatio(currentColor, backgroundColor);
    
    if (ratio >= WCAG_AA_NORMAL) {
      return {
        color: currentColor,
        ratio: Math.round(ratio * 100) / 100,
        adjustment: steps * step,
        direction: shouldDarken ? 'darker' : 'lighter'
      };
    }
    
    // Try adjusting the color
    currentColor = shouldDarken ? 
      darkenColor(originalColor, (steps + 1) * step) :
      lightenColor(originalColor, (steps + 1) * step);
    
    steps++;
    
    // If we've gone far and not found a solution, try the other direction
    if (steps > 10 && preferDirection === 'auto') {
      shouldDarken = !shouldDarken;
      currentColor = originalColor;
      steps = 0;
      preferDirection = shouldDarken ? 'darker' : 'lighter';
    }
  }
  
  // If we couldn't find a good color, return a safe fallback
  const fallbackColor = bgLuminance > 0.5 ? '#000000' : '#ffffff';
  return {
    color: fallbackColor,
    ratio: contrastRatio(fallbackColor, backgroundColor),
    adjustment: 'fallback',
    direction: 'fallback'
  };
}

/**
 * Generate fixes for all issues
 */
function generateFixes() {
  const reportPath = 'color-contrast-audit-report.json';
  
  if (!fs.existsSync(reportPath)) {
    console.error('No audit report found. Run the audit first.');
    process.exit(1);
  }
  
  const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  const fixes = [];
  
  console.log('Generating accessibility fixes...\n');
  
  report.audits.forEach(audit => {
    if (audit.issues.length > 0) {
      console.log(`=== ${audit.theme.toUpperCase()} THEME FIXES ===`);
      
      audit.issues.forEach(issue => {
        console.log(`\nFixing: ${issue.combination}`);
        console.log(`Current: ${issue.foreground} on ${issue.background} (${issue.ratio}:1)`);
        
        const fix = findAccessibleColor(issue.foreground, issue.background);
        
        console.log(`Fixed: ${fix.color} on ${issue.background} (${fix.ratio}:1)`);
        console.log(`Adjustment: ${fix.adjustment}% ${fix.direction}`);
        
        fixes.push({
          theme: audit.theme,
          issue: issue.combination,
          original: issue.foreground,
          background: issue.background,
          fixed: fix.color,
          originalRatio: issue.ratio,
          fixedRatio: fix.ratio,
          adjustment: fix.adjustment,
          direction: fix.direction
        });
      });
    }
  });
  
  return fixes;
}

/**
 * Apply fixes to theme files
 */
function applyFixes(fixes) {
  console.log('\n' + '='.repeat(50));
  console.log('APPLYING FIXES TO THEME FILES');
  console.log('='.repeat(50));
  
  const colorVariableMap = {
    'Border on Background': 'border',
    'Secondary on Background': 'secondary', 
    'Primary (self-contrast)': 'primary'
  };
  
  fixes.forEach(fix => {
    const themeFile = `ui/themes/${fix.theme}.css`;
    const variableName = colorVariableMap[fix.issue];
    
    if (!variableName) {
      console.log(`⚠️  Skipping ${fix.issue} - no variable mapping`);
      return;
    }
    
    if (!fs.existsSync(themeFile)) {
      console.log(`⚠️  Theme file not found: ${themeFile}`);
      return;
    }
    
    // Read the file content
    let content = fs.readFileSync(themeFile, 'utf8');
    
    // Create the regex pattern to match the variable
    const pattern = new RegExp(`(--color-${variableName}:\\s*)([#\\w]+)(;)`, 'g');
    
    // Replace the color value
    const newContent = content.replace(pattern, `$1${fix.fixed}$3`);
    
    if (content !== newContent) {
      // Write the updated content back
      fs.writeFileSync(themeFile, newContent, 'utf8');
      console.log(`✅ Fixed ${fix.theme} theme: --color-${variableName}: ${fix.original} → ${fix.fixed}`);
      console.log(`   Contrast improved: ${fix.originalRatio}:1 → ${fix.fixedRatio}:1`);
    } else {
      console.log(`⚠️  Could not apply fix to ${themeFile} (pattern not found)`);
    }
  });
}

/**
 * Main function
 */
function main() {
  console.log('LibreAssistant Color Contrast Fix Utility');
  console.log('Generating WCAG AA compliant color fixes');
  
  const fixes = generateFixes();
  
  if (fixes.length === 0) {
    console.log('\n✅ No fixes needed - all themes are accessible!');
    return;
  }
  
  console.log(`\nGenerated ${fixes.length} fixes`);
  
  // Save fixes report
  const fixesReport = {
    timestamp: new Date().toISOString(),
    fixes: fixes
  };
  
  fs.writeFileSync('color-contrast-fixes.json', JSON.stringify(fixesReport, null, 2));
  console.log('Fixes report saved to: color-contrast-fixes.json');
  
  // Apply the fixes
  applyFixes(fixes);
  
  console.log('\n✅ All accessibility fixes applied!');
  console.log('Run the audit again to verify the fixes.');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}