#!/usr/bin/env node
/**
 * Responsive Layout Validator
 * 
 * Validates that LibreAssistant components follow responsive design best practices.
 * This script can be run with Node.js to check component CSS for responsive patterns.
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const COMPONENTS_DIR = join(__dirname, '../ui/components');

/**
 * Checks if a CSS string contains responsive design patterns
 */
function analyzeResponsiveCSS(cssContent) {
    const patterns = {
        flexbox: /display:\s*flex/gi,
        grid: /display:\s*grid/gi,
        percentageWidths: /width:\s*\d+%/gi,
        maxWidth: /max-width:\s*\d+/gi,
        minWidth: /min-width:\s*\d+/gi,
        mediaQueries: /@media[^{]+\{/gi,
        viewport: /width:\s*100%/gi,
        relativeUnits: /(rem|em|vh|vw|%)/g,
        overflowHandling: /overflow(-x)?:\s*(auto|scroll|hidden)/gi
    };

    const results = {};
    for (const [pattern, regex] of Object.entries(patterns)) {
        const matches = cssContent.match(regex) || [];
        results[pattern] = matches.length;
    }

    return results;
}

/**
 * Scores responsive design implementation
 */
function scoreResponsiveness(analysis) {
    let score = 0;
    let maxScore = 0;

    // Flexbox usage (0-3 points)
    maxScore += 3;
    if (analysis.flexbox > 0) score += Math.min(3, analysis.flexbox);

    // Percentage/relative widths (0-2 points)
    maxScore += 2;
    if (analysis.percentageWidths > 0 || analysis.viewport > 0) score += 2;

    // Max/min width constraints (0-2 points)
    maxScore += 2;
    if (analysis.maxWidth > 0 || analysis.minWidth > 0) score += 2;

    // Relative units usage (0-2 points)
    maxScore += 2;
    if (analysis.relativeUnits > 5) score += 2;
    else if (analysis.relativeUnits > 2) score += 1;

    // Overflow handling (0-1 point)
    maxScore += 1;
    if (analysis.overflowHandling > 0) score += 1;

    return { score, maxScore, percentage: (score / maxScore) * 100 };
}

/**
 * Validates a single component file
 */
function validateComponent(componentPath) {
    try {
        const content = readFileSync(componentPath, 'utf8');
        
        // Extract CSS from JavaScript template literals
        const cssMatches = content.match(/`([^`]*(<style>[^`]*<\/style>)[^`]*)`/gs) || [];
        const allCSS = cssMatches.join('\n');
        
        if (!allCSS) {
            return {
                file: componentPath,
                hasCSS: false,
                analysis: null,
                score: null
            };
        }

        const analysis = analyzeResponsiveCSS(allCSS);
        const score = scoreResponsiveness(analysis);

        return {
            file: componentPath,
            hasCSS: true,
            analysis,
            score
        };
    } catch (error) {
        return {
            file: componentPath,
            error: error.message
        };
    }
}

/**
 * Main validation function
 */
function validateAllComponents() {
    const coreComponents = [
        'onboarding-flow.js',
        'switchboard.js',
        'past-requests.js',
        'main-tabs.js'
    ];

    console.log('🔍 LibreAssistant Responsive Design Validator\n');
    console.log('Analyzing core components for responsive design patterns...\n');

    const results = [];

    for (const component of coreComponents) {
        const componentPath = join(COMPONENTS_DIR, component);
        const result = validateComponent(componentPath);
        results.push(result);

        if (result.error) {
            console.log(`❌ ${component}: Error - ${result.error}`);
            continue;
        }

        if (!result.hasCSS) {
            console.log(`⚠️  ${component}: No CSS found`);
            continue;
        }

        const scoreData = result.score;
        const icon = scoreData.percentage >= 80 ? '✅' : scoreData.percentage >= 60 ? '⚠️' : '❌';
        
        console.log(`${icon} ${component}: ${scoreData.score}/${scoreData.maxScore} (${scoreData.percentage.toFixed(1)}%)`);
        console.log(`   Flexbox: ${result.analysis.flexbox} | Relative units: ${result.analysis.relativeUnits}`);
        console.log(`   Max/Min width: ${result.analysis.maxWidth + result.analysis.minWidth} | Overflow handling: ${result.analysis.overflowHandling}`);
        console.log('');
    }

    // Summary
    const validResults = results.filter(r => r.score && !r.error);
    const averageScore = validResults.reduce((sum, r) => sum + r.score.percentage, 0) / validResults.length;
    
    console.log('📊 Summary:');
    console.log(`Average responsive score: ${averageScore.toFixed(1)}%`);
    console.log(`Components analyzed: ${validResults.length}/${coreComponents.length}`);
    
    if (averageScore >= 80) {
        console.log('🎉 Excellent responsive design implementation!');
    } else if (averageScore >= 60) {
        console.log('👍 Good responsive design, with room for improvement');
    } else {
        console.log('⚠️  Responsive design needs attention');
    }
}

// Run if called directly
if (process.argv[1] === __filename) {
    validateAllComponents();
}