# Responsive Layout Testing

This directory contains comprehensive responsive layout tests for LibreAssistant's core components.

## Test Files

- `responsive-layout-test.html` - Main responsive layout test suite for core flows

## Usage

1. Start a local HTTP server from the repository root:
   ```bash
   cd /path/to/LibreAssistant
   python3 -m http.server 8080
   ```

2. Open the test in a browser:
   ```
   http://localhost:8080/tests/responsive-layout-test.html
   ```

## Test Coverage

The responsive layout test covers:

### Components Tested
- **Onboarding Flow** - Multi-step onboarding wizard
- **Switchboard** - Main AI interaction interface
- **History/Past Requests** - Request history display
- **Main Tabs Navigation** - Primary navigation tabs

### Viewport Sizes
- **Small (320px)** - Mobile devices
- **Medium (768px)** - Tablet devices  
- **Large (1200px)** - Desktop devices

### Test Criteria
- Component visibility and rendering
- Proper dimensions and container fitting
- Responsive element detection
- Font size readability across viewports
- Container overflow prevention

## Features

- **Interactive Viewport Switching** - Test components at different screen sizes
- **Automated Test Suite** - Run all tests across all viewports automatically
- **Real-time Validation** - Live testing with detailed pass/fail reporting
- **Visual Component Display** - See how components render at each viewport
- **Comprehensive Reporting** - Detailed test summaries and statistics

## Test Results Interpretation

- ✓ **Green checks** - Tests passing normally
- ⚠ **Yellow warnings** - Components may have limited responsive features (but still functional)
- ✗ **Red errors** - Actual layout issues requiring attention

The warning about components "may not be fully responsive" for Main Tabs and History components is expected, as these components use appropriate fallback strategies (horizontal scrolling for tabs, simple block layout for history).