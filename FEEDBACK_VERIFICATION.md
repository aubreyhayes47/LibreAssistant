# LibreAssistant Feedback Mechanisms - Manual Verification Guide

This document outlines how to manually verify that all actions in LibreAssistant provide clear feedback.

## Setup

1. Start the LibreAssistant server:
   ```bash
   cd /path/to/LibreAssistant
   python -m uvicorn libreassistant.main:app --host 0.0.0.0 --port 8000
   ```

2. Open the feedback test page in a browser:
   ```
   http://localhost:8000/feedback-test.html
   ```

## Verification Checklist

### 1. Sending Requests (Switchboard Component)

**Progress Feedback:**
- [ ] Loading spinner appears on Send button when request is processing
- [ ] Send button becomes disabled during request
- [ ] Loading notification appears with "Sending request..." message

**Success Feedback:**
- [ ] Success notification appears when request completes successfully
- [ ] Response appears in chat log with success styling (green color)
- [ ] Send button returns to normal state

**Error Feedback:**
- [ ] Error notification appears when request fails
- [ ] Error message appears in chat log with error styling (red color)
- [ ] Error details include specific error information

**Test Cases:**
1. Send a valid request with no plugin selected (uses provider)
2. Send a request with a plugin selected (if plugins are available)
3. Test with invalid input or network error to trigger error states

### 2. Switching Providers (Provider Selector Component)

**Progress Feedback:**
- [ ] Status indicator shows loading animation when switching providers
- [ ] Provider dropdown becomes disabled during switch
- [ ] Loading notification appears with "Switching to [Provider]..." message

**Success Feedback:**
- [ ] Success notification confirms provider switch
- [ ] Status indicator turns green to show connected state
- [ ] Provider dropdown re-enables with new selection

**Error Feedback:**
- [ ] Error notification appears if provider switch fails
- [ ] Status indicator turns red to show error state
- [ ] Dropdown reverts to previous selection

**Test Cases:**
1. Switch between Cloud and Local providers
2. Test switching when provider is unavailable (should show error)

### 3. Installing Plugins (Plugin Catalogue Component)

**Progress Feedback:**
- [ ] Plugin status shows "Enabling..." or "Disabling..." during operation
- [ ] Checkbox becomes disabled during operation
- [ ] Loading notification appears with plugin operation message

**Success Feedback:**
- [ ] Success notification confirms plugin enabled/disabled
- [ ] Plugin status updates to "Enabled" or "Disabled"
- [ ] Checkbox state reflects successful change

**Error Feedback:**
- [ ] Error notification appears if plugin operation fails
- [ ] Plugin status shows "Error" state
- [ ] Checkbox reverts to previous state on failure

**Test Cases:**
1. Enable a plugin that's currently disabled
2. Disable a plugin that's currently enabled
3. Test with network error to trigger failure state

### 4. Changing Themes (Theme Components)

#### Theme Selector

**Progress Feedback:**
- [ ] Theme selector becomes disabled during theme application
- [ ] Loading notification appears with "Applying theme [Name]..." message

**Success Feedback:**
- [ ] Success notification confirms theme applied
- [ ] Theme preview updates to show new theme color
- [ ] Visual changes are immediately visible on the page

**Error Feedback:**
- [ ] Error notification appears if theme fails to load
- [ ] Theme selector reverts to previous selection
- [ ] Visual theme remains unchanged on error

#### Theme Marketplace

**Progress Feedback:**
- [ ] Install button shows loading spinner and "Installing..." text
- [ ] Install button becomes disabled during installation
- [ ] Loading notification appears with installation message

**Success Feedback:**
- [ ] Success notification confirms theme installation
- [ ] Theme is immediately applied to the page
- [ ] Install button returns to normal state

**Error Feedback:**
- [ ] Error notification appears if theme installation fails
- [ ] Install button returns to normal state
- [ ] Page theme remains unchanged on error

**Test Cases:**
1. Install a built-in theme (light, dark, high-contrast)
2. Install a community theme (if available)
3. Test with invalid theme ID to trigger error

## Additional Verification Points

### Notification System
- [ ] Notifications appear in top-right corner
- [ ] Multiple notifications stack properly
- [ ] Notifications can be manually dismissed with X button
- [ ] Loading notifications persist until updated or dismissed
- [ ] Success/error notifications auto-dismiss after 5-8 seconds
- [ ] Notification types have distinct visual styling (colors, icons)

### General Feedback Principles
- [ ] All async operations show loading states
- [ ] All operations provide success or error feedback
- [ ] Error messages include actionable information
- [ ] Loading states prevent user interaction during operations
- [ ] Visual feedback is consistent across all components
- [ ] Notifications are accessible and readable

### Accessibility
- [ ] Loading states are announced to screen readers
- [ ] Success/error states are clearly communicated
- [ ] Interactive elements have appropriate ARIA labels
- [ ] Color is not the only indicator of state (icons, text also used)

## Test Results

Record your verification results here:

**Date:** ___________
**Tester:** ___________

### Sending Requests
- Progress Feedback: ✓ / ✗
- Success Feedback: ✓ / ✗  
- Error Feedback: ✓ / ✗
- Notes: ___________

### Switching Providers
- Progress Feedback: ✓ / ✗
- Success Feedback: ✓ / ✗
- Error Feedback: ✓ / ✗
- Notes: ___________

### Installing Plugins
- Progress Feedback: ✓ / ✗
- Success Feedback: ✓ / ✗
- Error Feedback: ✓ / ✗
- Notes: ___________

### Changing Themes
- Progress Feedback: ✓ / ✗
- Success Feedback: ✓ / ✗
- Error Feedback: ✓ / ✗
- Notes: ___________

### Overall Assessment
- All required feedback mechanisms implemented: ✓ / ✗
- Feedback is clear and actionable: ✓ / ✗
- User experience is improved: ✓ / ✗
- Ready for production: ✓ / ✗