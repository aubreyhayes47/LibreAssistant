# Accessibility Guide for LibreAssistant

LibreAssistant is designed to be fully accessible to users with disabilities. This guide explains how to use LibreAssistant with assistive technologies, including screen readers, keyboard navigation, and other accessibility tools.

## Table of Contents

1. [Overview](#overview)
2. [Supported Assistive Technologies](#supported-assistive-technologies)
3. [Getting Started](#getting-started)
4. [Keyboard Navigation](#keyboard-navigation)
5. [Screen Reader Usage](#screen-reader-usage)
6. [Component-Specific Accessibility Features](#component-specific-accessibility-features)
7. [Accessibility Settings](#accessibility-settings)
8. [Troubleshooting](#troubleshooting)
9. [Accessibility Standards Compliance](#accessibility-standards-compliance)
10. [Providing Feedback](#providing-feedback)

## Overview

LibreAssistant follows the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA standards and includes:

- **Full keyboard navigation** - Navigate the entire interface without a mouse
- **Screen reader compatibility** - Works with NVDA, JAWS, VoiceOver, and other screen readers
- **High contrast themes** - Multiple theme options including high-contrast mode
- **Focus management** - Clear focus indicators and logical tab order
- **ARIA labels and descriptions** - Comprehensive markup for assistive technologies
- **Live regions** - Important updates are announced to screen readers
- **Color contrast compliance** - All text meets WCAG AA contrast requirements

## Supported Assistive Technologies

### Screen Readers
- **NVDA** (Windows) - Fully supported with optimized announcements
- **JAWS** (Windows) - Compatible with all major features
- **VoiceOver** (macOS) - Native support for Apple's screen reader
- **ORCA** (Linux) - Basic support for Linux users
- **TalkBack** (Android) - Mobile browser compatibility
- **VoiceOver** (iOS) - Mobile browser compatibility

### Other Assistive Technologies
- **Voice control software** (Dragon NaturallySpeaking, Voice Control)
- **Switch navigation** devices
- **Eye tracking** software
- **Magnification** software (ZoomText, Windows Magnifier)

## Getting Started

### Initial Setup

1. **Enable your assistive technology** before launching LibreAssistant
2. **Navigate to LibreAssistant** at [http://localhost:8000](http://localhost:8000)
3. **Set up accessibility preferences** in the Settings tab
4. **Choose an appropriate theme** - High-contrast theme is recommended for users with visual impairments

### First-Time User Experience

When you first access LibreAssistant, you'll encounter:

1. **Page title announcement** - "LibreAssistant - AI Assistant Interface"
2. **Main navigation** - Tab-based interface with clear labels
3. **Onboarding flow** (optional) - Guided setup with accessibility instructions
4. **Primary content area** - The main switchboard for interacting with AI models

## Keyboard Navigation

### Essential Keyboard Shortcuts

| Key(s) | Action |
|--------|--------|
| `Tab` | Move to next interactive element |
| `Shift + Tab` | Move to previous interactive element |
| `Enter` | Activate buttons and links |
| `Space` | Activate buttons, toggle checkboxes |
| `Arrow Keys` | Navigate within tabs, lists, and menus |
| `Escape` | Close modals and dialogs |
| `Home` | Go to first item in a list or first tab |
| `End` | Go to last item in a list or last tab |

### Navigation Patterns

#### Tab Navigation
- Use `Left/Right Arrow` keys to move between tabs
- Use `Enter` or `Space` to activate a tab
- Tab content loads automatically when a tab is selected

#### Form Navigation
- Use `Tab` to move between form fields
- Use `Arrow keys` for radio buttons and dropdown menus
- Required fields are announced as "required"
- Error messages are announced immediately when validation fails

#### Modal Dialogs
- Focus automatically moves to the modal when opened
- `Tab` cycles through interactive elements within the modal
- `Escape` closes the modal and returns focus to the trigger element

## Screen Reader Usage

### Getting Optimal Announcements

LibreAssistant provides rich announcements for screen reader users:

#### Application State Changes
- Tab switches: "Switchboard tab selected, tab 1 of 4"
- Loading states: "Loading content, please wait"
- Form submissions: "Message sent successfully"
- Errors: "Error: Invalid API key format"

#### Dynamic Content Updates
- New messages in chat appear in a live region
- Plugin outputs are announced when received
- Status changes are communicated immediately

### Screen Reader Specific Instructions

#### NVDA (Windows)
1. **Browse vs Focus Mode**: LibreAssistant automatically switches to Focus mode for interactive elements
2. **Element Navigation**: Use `H` for headings, `F` for form fields, `B` for buttons
3. **Live Regions**: Updates are announced automatically without interrupting your current task

#### VoiceOver (macOS)
1. **Web Rotor**: Use `VO + U` to navigate by element type
2. **Interaction**: Use `VO + Space` to interact with complex controls
3. **Quick Navigation**: Use `H`, `F`, and `B` for quick element navigation

#### JAWS (Windows)
1. **Virtual Cursor**: Navigate normally with arrow keys
2. **Forms Mode**: Automatically activated for interactive elements
3. **Quick Keys**: Use `H`, `F`, `B` for quick navigation

### Optimizing Your Screen Reader

For the best experience with LibreAssistant:

1. **Update your screen reader** to the latest version
2. **Enable web browsing announcements** for dynamic content
3. **Configure speech rate** to a comfortable level for technical content
4. **Enable punctuation reading** for code and technical details

## Component-Specific Accessibility Features

### Switchboard (Main Chat Interface)

**Accessibility Features:**
- Message input field with clear labeling: "Enter your message"
- Send button with descriptive label: "Send message to AI model"
- Provider selection dropdown with current selection announced
- Message history in a scrollable log with proper heading structure

**Usage Tips:**
- Messages are automatically announced when received
- Use `Shift + Enter` for line breaks in your message
- Provider switching is announced: "OpenAI provider selected"

### Navigation Tabs

**Accessibility Features:**
- Tab list with proper ARIA roles (`tablist`, `tab`, `tabpanel`)
- Current tab announced: "Switchboard tab, selected"
- Badge counts included in announcements: "History tab, 5 items"

**Usage Tips:**
- Use arrow keys for quick tab switching
- Tab panels load instantly when selected
- Focus remains on tab list until you Tab into the content

### Modal Dialogs

**Accessibility Features:**
- Dialog opening announced: "Settings dialog opened"
- Focus trapped within dialog
- Title and description associated via ARIA
- Close button clearly labeled

**Usage Tips:**
- `Escape` key always closes dialogs
- Focus returns to the element that opened the dialog
- Required form fields are clearly marked

### Form Fields

**Accessibility Features:**
- Labels properly associated with form controls
- Required fields marked with `aria-required="true"`
- Error messages linked via `aria-describedby`
- Help text provided for complex fields

**Usage Tips:**
- Validation happens as you type or on form submission
- Error messages are announced immediately
- Use `F6` or equivalent to navigate between form sections

### Theme Selector

**Accessibility Features:**
- Current theme announced: "Dark theme selected"
- Theme preview described: "Theme preview shows dark background"
- Selection confirmed: "Light theme applied"

**Usage Tips:**
- Theme changes take effect immediately
- High-contrast theme recommended for visual impairments
- All themes meet WCAG AA color contrast requirements

## Accessibility Settings

### Built-in Accessibility Options

LibreAssistant provides several accessibility settings:

#### Theme Options
- **Light Theme** - High contrast black text on white background
- **Dark Theme** - Light text on dark background, easier on eyes
- **High-Contrast Theme** - Maximum contrast for users with visual impairments
- **Solarized Theme** - Reduced blue light with optimal color contrast

#### Interaction Settings
- **Reduced Motion** - Minimizes animations and transitions
- **Focus Indicators** - Enhanced focus outlines for keyboard navigation
- **Screen Reader Optimizations** - Additional announcements and descriptions

### Browser Accessibility Settings

Enhance your experience by configuring browser settings:

#### Chrome/Edge
1. Settings > Advanced > Accessibility
2. Enable "Use a screen reader"
3. Adjust text size and zoom levels

#### Firefox
1. Preferences > General > Accessibility
2. Enable "Prevent accessibility services from accessing your browser"
3. Configure text size and contrast

#### Safari
1. Preferences > Advanced > Accessibility
2. Enable VoiceOver integration
3. Configure text size and zoom

## Troubleshooting

### Common Issues and Solutions

#### Screen Reader Not Announcing Changes
**Problem**: Dynamic content updates aren't being announced
**Solutions:**
- Ensure your screen reader is in Browse/Virtual mode
- Check that live regions are enabled in your screen reader settings
- Refresh the page to reset ARIA live regions

#### Keyboard Navigation Not Working
**Problem**: Tab key doesn't move focus as expected
**Solutions:**
- Check that focus mode is enabled in your screen reader
- Look for visible focus indicators to track your location
- Try using arrow keys within complex components like tabs

#### Missing Context or Labels
**Problem**: Screen reader provides insufficient information
**Solutions:**
- Navigate to headings using `H` to understand page structure
- Use element navigation (`F` for forms, `B` for buttons) to find interactive elements
- Check if you're in the correct mode (Browse vs. Focus) for your screen reader

#### Form Submission Issues
**Problem**: Forms don't submit or provide feedback
**Solutions:**
- Ensure all required fields are completed
- Listen for validation error announcements
- Try using `Enter` on the submit button instead of clicking

### Getting Help

If you encounter accessibility issues:

1. **Check the logs** - Browser developer tools may show accessibility errors
2. **Try different browsers** - Some screen readers work better with specific browsers
3. **Update your assistive technology** - Ensure you have the latest version
4. **Report the issue** - Use our accessibility feedback process (see below)

## Accessibility Standards Compliance

LibreAssistant meets or exceeds the following accessibility standards:

### WCAG 2.1 Level AA Compliance

- ✅ **Perceivable**: All content is available to assistive technologies
- ✅ **Operable**: Full keyboard navigation and assistive technology compatibility
- ✅ **Understandable**: Clear language, consistent navigation, and helpful error messages
- ✅ **Robust**: Works with current and future assistive technologies

### Specific Compliance Details

#### Color and Contrast
- Minimum 4.5:1 contrast ratio for normal text
- Minimum 3:1 contrast ratio for large text and UI elements
- All themes audited and verified for compliance

#### Keyboard Navigation
- All interactive elements reachable via keyboard
- Logical tab order throughout the interface
- No keyboard traps that prevent navigation

#### Screen Reader Support
- Proper heading structure (H1, H2, H3, etc.)
- ARIA landmarks for page regions (main, nav, aside)
- Descriptive link text and button labels
- Live regions for dynamic content

### Testing and Validation

Our accessibility compliance is verified through:

- **Automated testing** with axe-core and Pa11y
- **Manual testing** with multiple screen readers
- **User testing** with actual assistive technology users
- **Regular audits** by accessibility experts

## Providing Feedback

Your accessibility feedback helps us improve LibreAssistant for all users.

### How to Report Accessibility Issues

1. **Email**: accessibility@libreassistant.org
2. **GitHub Issues**: Tag with "accessibility" label
3. **User Testing**: Join our accessibility user testing program

### Information to Include

When reporting accessibility issues, please provide:

- **Assistive technology** used (name and version)
- **Browser** and version
- **Operating system**
- **Specific steps** to reproduce the issue
- **Expected behavior** vs. actual behavior
- **Severity level** (how much it impacts your usage)

### Response Timeline

- **Critical issues** (blocking basic functionality): 24-48 hours
- **High priority issues** (significant impact): 3-5 business days
- **Medium priority issues** (moderate impact): 1-2 weeks
- **Low priority issues** (minor improvements): Next release cycle

## Resources and Further Reading

### LibreAssistant Accessibility Documentation
- [Screen Reader Testing Guide](SCREEN_READER_TESTING.md) - Technical testing procedures
- [Accessibility Audit Report](accessibility-audit-report.md) - Color contrast compliance details
- [Touch Interactions Guide](touch-interactions.md) - Mobile and touch accessibility

### External Resources
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)
- [NVDA User Guide](https://www.nvaccess.org/files/nvda/documentation/userGuide.html)
- [VoiceOver Getting Started](https://support.apple.com/guide/voiceover/welcome/mac)
- [JAWS Documentation](https://support.freedomscientific.com/teachers/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Accessibility Communities
- [WebAIM Community](https://webaim.org/discussion/)
- [NVDA Community](https://github.com/nvaccess/nvda/discussions)
- [Accessibility Guidelines Working Group](https://www.w3.org/WAI/GL/)

---

*This guide is continuously updated to reflect the latest accessibility improvements and user feedback. Last updated: December 2024*