# Screen Reader Testing Guide for LibreAssistant

This guide provides comprehensive instructions for testing LibreAssistant's user interface with screen readers, specifically NVDA, VoiceOver, and JAWS.

## Table of Contents
1. [Setup Instructions](#setup-instructions)
2. [Testing Workflows](#testing-workflows)
3. [Component-Specific Tests](#component-specific-tests)
4. [Common Issues and Solutions](#common-issues-and-solutions)
5. [Accessibility Best Practices](#accessibility-best-practices)

## Setup Instructions

### NVDA (Windows)
1. Download and install NVDA from https://www.nvaccess.org/
2. Ensure NVDA is running before starting tests
3. Key shortcuts for testing:
   - `NVDA + Space`: Toggle between browse and focus mode
   - `NVDA + T`: Read page title
   - `NVDA + D`: Read entire document
   - `NVDA + F7`: List all elements
   - `H`: Navigate by headings
   - `F`: Navigate by form controls
   - `B`: Navigate by buttons

### VoiceOver (macOS)
1. Enable VoiceOver: System Preferences > Accessibility > VoiceOver
2. Or use keyboard shortcut: `Cmd + F5`
3. Key shortcuts for testing:
   - `VO + Space`: Interact with controls
   - `VO + Right/Left Arrow`: Navigate elements
   - `VO + A`: Read all content
   - `VO + F5`: List form controls
   - `VO + U`: Open rotor menu
   - `VO + H`: Navigate by headings

### JAWS (Windows)
1. Ensure JAWS is running
2. Key shortcuts for testing:
   - `Tab/Shift + Tab`: Navigate form controls
   - `H/Shift + H`: Navigate headings
   - `F/Shift + F`: Navigate form fields
   - `B/Shift + B`: Navigate buttons
   - `Insert + F7`: List all links
   - `Insert + F5`: List all form fields

## Testing Workflows

### Flow 1: Application Onboarding
**Goal**: Verify new users can complete onboarding using only screen reader navigation.

**Test File**: `tests/screen-reader-user-flows.html#flow1`

**Steps**:
1. Navigate to the onboarding section
2. Activate "Start Onboarding Flow" button
3. Complete each step using only keyboard and screen reader
4. Verify each step is announced clearly
5. Check progress indicators are read correctly
6. Ensure form validation is announced

**Expected Behaviors**:
- Component loading is announced
- Step titles are read clearly
- Progress information is provided (e.g., "Step 1 of 4")
- Navigation buttons are properly labeled
- Disabled states are announced
- Form fields have proper labels and instructions
- Validation errors are announced immediately
- Completion is clearly announced

### Flow 2: Main Navigation
**Goal**: Navigate between application sections using tabs.

**Test File**: `tests/screen-reader-user-flows.html#flow2`

**Steps**:
1. Navigate to the tabs section
2. Use arrow keys to move between tabs
3. Use Enter/Space to activate tabs
4. Verify tab content is properly announced
5. Test Home/End key functionality

**Expected Behaviors**:
- Tab list is announced as "tablist"
- Each tab announces role and selection state
- Tab badges/counts are announced
- Arrow key navigation works and is announced
- Tab panels are announced when activated
- Content structure is properly communicated

### Flow 3: Modal Dialog Interactions
**Goal**: Interact with modal dialogs and confirm proper focus management.

**Test File**: `tests/screen-reader-user-flows.html#flow3`

**Steps**:
1. Open modal dialogs using trigger buttons
2. Navigate within modal using Tab key
3. Test Escape key to close
4. Verify focus returns to trigger element
5. Test form submission within modals

**Expected Behaviors**:
- Modal opening is announced
- Modal title is read
- Focus moves to modal content
- Tab cycling stays within modal
- Escape key closes modal with announcement
- Focus returns to trigger element
- Form errors are announced

### Flow 4: Form Input and Validation
**Goal**: Complete forms with proper validation feedback.

**Test File**: `tests/screen-reader-user-flows.html#flow4`

**Steps**:
1. Navigate through form fields
2. Enter invalid data to trigger validation
3. Correct errors and submit form
4. Test required field indicators
5. Verify help text is accessible

**Expected Behaviors**:
- Fieldsets and legends are announced
- Required fields are marked as required
- Help text is associated and announced
- Validation errors are announced immediately
- Error messages are descriptive
- Form submission results are announced

## Component-Specific Tests

### Modal Dialog Component
**File**: `ui/components/modal-dialog.js`

**Accessibility Features**:
- `role="dialog"` and `aria-modal="true"`
- `aria-labelledby` pointing to title
- `aria-describedby` pointing to content
- Focus trapping within modal
- Screen reader announcements for open/close
- Proper focus restoration

**Test Commands**:
```javascript
// Programmatic testing
const modal = document.getElementById('test-modal');
modal.show(); // Should announce opening
modal.hide(); // Should announce closing
```

### Main Tabs Component
**File**: `ui/components/main-tabs.js`

**Accessibility Features**:
- `role="tablist"` on container
- `role="tab"` on tab buttons
- `role="tabpanel"` on content areas
- `aria-selected` and `aria-controls` attributes
- Arrow key navigation
- Screen reader announcements for tab changes

**Test Commands**:
```javascript
// Test tab navigation
const tabs = document.getElementById('test-tabs');
tabs.activeIndex = 1; // Should announce tab change
```

### Input Field Component
**File**: `ui/components/input-field.js`

**Accessibility Features**:
- Proper label association
- `aria-required` for required fields
- `aria-invalid` and `aria-describedby` for errors
- Screen reader announcements for validation
- Help text association

**Test Commands**:
```javascript
// Test validation
const field = document.querySelector('la-input-field');
field.setCustomValidity('Custom error message'); // Should announce error
```

## Common Issues and Solutions

### Issue: Screen Reader Not Announcing Modal Opening
**Symptoms**: Modal opens but screen reader doesn't announce it
**Solutions**:
- Ensure `aria-modal="true"` is set
- Add live region announcements
- Verify focus moves to modal content

### Issue: Tab Navigation Not Working
**Symptoms**: Arrow keys don't navigate between tabs
**Solutions**:
- Check `role="tablist"` on container
- Ensure proper `tabindex` management
- Verify keyboard event handlers are attached

### Issue: Form Errors Not Announced
**Symptoms**: Validation errors appear visually but aren't read
**Solutions**:
- Use `aria-invalid="true"` on invalid fields
- Associate error messages with `aria-describedby`
- Implement live region announcements for errors

### Issue: Missing Context Information
**Symptoms**: Screen reader provides insufficient context
**Solutions**:
- Add proper heading structure
- Use landmarks and regions
- Provide descriptive labels and instructions

## Accessibility Best Practices

### 1. Semantic HTML
- Use proper heading hierarchy (h1, h2, h3...)
- Implement landmark roles (main, nav, aside, footer)
- Use semantic elements (button, nav, article, section)

### 2. ARIA Attributes
- `aria-label` for elements without visible text
- `aria-labelledby` to reference other elements
- `aria-describedby` for additional descriptions
- `aria-live` for dynamic content updates
- `aria-expanded` for collapsible content

### 3. Focus Management
- Ensure all interactive elements are keyboard accessible
- Implement logical tab order
- Manage focus for dynamic content
- Provide visible focus indicators

### 4. Screen Reader Announcements
- Use live regions for important updates
- Choose appropriate politeness levels (polite vs assertive)
- Provide clear, concise announcements
- Avoid overwhelming users with too many announcements

### 5. Testing Checklist
- [ ] All interactive elements are keyboard accessible
- [ ] Focus order is logical and predictable
- [ ] All form inputs have proper labels
- [ ] Error messages are associated with form fields
- [ ] Dynamic content changes are announced
- [ ] Modal dialogs trap focus properly
- [ ] Page structure is clear with headings and landmarks
- [ ] Instructions and help text are available

## Automated Testing Tools

While manual testing with actual screen readers is essential, these tools can help catch common issues:

- **axe DevTools**: Browser extension for accessibility testing
- **WAVE**: Web accessibility evaluation tool
- **Pa11y**: Command-line accessibility testing tool
- **Lighthouse**: Built-in Chrome accessibility audit

## Testing Frequency

### During Development
- Test each new component with screen readers
- Verify accessibility attributes are correctly implemented
- Check focus management for interactive elements

### Before Release
- Complete full user flow testing with all supported screen readers
- Verify no regressions in existing functionality
- Test on different browsers and operating systems

### Ongoing Maintenance
- Regular accessibility audits
- User feedback incorporation
- Updates for new screen reader versions

## Reporting Issues

When reporting accessibility issues, include:
1. Screen reader and version used
2. Browser and version
3. Operating system
4. Specific steps to reproduce
5. Expected vs. actual behavior
6. Severity level (blocker, high, medium, low)

## Resources

- [WebAIM Screen Reader Testing Guide](https://webaim.org/articles/screenreader_testing/)
- [NVDA User Guide](https://www.nvaccess.org/files/nvda/documentation/userGuide.html)
- [VoiceOver Getting Started Guide](https://support.apple.com/guide/voiceover/welcome/mac)
- [JAWS Documentation](https://support.freedomscientific.com/teachers/index.cfm)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)