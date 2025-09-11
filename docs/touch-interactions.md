# Touch Interaction Patterns

This document describes the touch interaction patterns implemented in LibreAssistant for mobile device support.

## Overview

LibreAssistant includes comprehensive touch interaction support to ensure all controls are usable on mobile devices. The implementation follows WCAG accessibility guidelines and provides consistent touch behavior across all components.

## Core Components

### TouchUtils (`ui/components/touch-utils.js`)

The `TouchUtils` class provides the foundation for all touch interactions:

```javascript
// Create touch events
const touchEvent = TouchUtils.createTouchEvent('touchstart', {
  clientX: 100,
  clientY: 200,
  target: element
});

// Simulate gestures
await TouchUtils.simulateTap(element);
await TouchUtils.simulateLongPress(element, { duration: 500 });
await TouchUtils.simulateSwipe(element, { startX: 50, endX: 150 });

// Validate accessibility
const validation = TouchUtils.validateTouchTarget(element);
console.log(validation.meetsRequirements); // true/false
```

### Key Methods

| Method | Purpose | Parameters |
|--------|---------|------------|
| `createTouchEvent()` | Create standardized touch events | type, options |
| `simulateTap()` | Simulate tap gesture | element, options |
| `simulateLongPress()` | Simulate long press | element, options |
| `simulateSwipe()` | Simulate swipe gesture | element, options |
| `addTouchHandlers()` | Add touch event handlers | element, handlers |
| `validateTouchTarget()` | Check WCAG compliance | element |
| `isTouchDevice()` | Detect touch capability | none |

## Component Implementations

### Buttons (`la-primary-button`)

Buttons include comprehensive touch support:

**Features:**
- **Touch feedback**: Visual scale animation on touch
- **Ghost click prevention**: Proper event handling to prevent double-firing
- **Accessibility sizing**: 44px minimum touch targets on touch devices
- **Responsive design**: Larger padding and sizing on mobile

**CSS Media Query:**
```css
@media (hover: none) and (pointer: coarse) {
  button {
    min-height: 44px;
    padding: var(--spacing-md) var(--spacing-lg);
  }
}
```

**Touch States:**
- `touchstart`: Add `touch-active` class for visual feedback
- `touchend`: Remove `touch-active` class and trigger click
- `touchcancel`: Remove `touch-active` class

### Input Fields (`la-input-field`)

Input fields are optimized for touch interaction:

**Features:**
- **Touch-friendly sizing**: 44px minimum height on touch devices
- **Enhanced focus**: Improved focus behavior for mobile
- **Larger text**: Increased font size on touch devices
- **Better spacing**: More generous padding for easier interaction

**Mobile Optimizations:**
```css
@media (hover: none) and (pointer: coarse) {
  input, textarea {
    min-height: 44px;
    padding: var(--spacing-md);
    font-size: var(--font-size-lg);
  }
}
```

### Confirm Dialog (`la-confirm-dialog`)

Dialogs include touch-optimized interactions:

**Features:**
- **Touch-friendly buttons**: All dialog buttons meet 44px minimum
- **Improved spacing**: Better button spacing for mobile
- **Touch feedback**: Visual feedback on all interactive elements
- **Accessible close button**: Large enough close button for touch

## Design Tokens

Touch-specific design tokens are available in `ui/tokens.css`:

```css
:root {
  --touch-target-min: 44px;           /* WCAG minimum */
  --touch-target-comfortable: 48px;   /* Comfortable size */
  --touch-spacing: 8px;               /* Minimum spacing */
}
```

## Testing

### Automated Tests

The touch interaction system includes comprehensive tests in `tests/ui/touch-interactions.test.js`:

```bash
npm run test:ui  # Runs all UI tests including touch tests
```

**Test Coverage:**
- Touch event creation and simulation
- Gesture recognition (tap, long press, swipe)
- Touch target size validation
- Component touch behavior
- Accessibility compliance

### Manual Testing

Use the demo page `touch-demo.html` for manual testing:

1. Start a local server: `python3 -m http.server 8000`
2. Open `http://localhost:8000/touch-demo.html`
3. Test various touch interactions and gestures

**Demo Features:**
- Device capability detection
- Interactive button testing
- Touch gesture area
- Real-time accessibility validation

## Accessibility Guidelines

### WCAG Compliance

All touch targets follow WCAG 2.1 AA guidelines:

- **Minimum size**: 44×44 CSS pixels
- **Target spacing**: Minimum 8px between targets
- **Visual feedback**: Clear indication of touch states

### Validation

Use the built-in validation to check compliance:

```javascript
const validation = TouchUtils.validateTouchTarget(element);
if (!validation.meetsRequirements) {
  console.warn(`Element needs ${validation.recommendations.width}px more width, ${validation.recommendations.height}px more height`);
}
```

## Usage Examples

### Adding Touch Support to New Components

```javascript
class MyComponent extends HTMLElement {
  connectedCallback() {
    this._setupTouchHandlers();
  }
  
  _setupTouchHandlers() {
    TouchUtils.addTouchHandlers(this, {
      onTap: (e) => this.handleTap(e),
      onLongPress: (e) => this.handleLongPress(e),
      preventGhostClick: true
    });
  }
}
```

### Testing Touch Interactions

```javascript
// In your test file
import TouchUtils from '../ui/components/touch-utils.js';

test('component responds to touch', async () => {
  const component = document.createElement('my-component');
  document.body.appendChild(component);
  
  await TouchUtils.simulateTap(component);
  
  // Assert expected behavior
  assert.equal(component.activated, true);
});
```

### Validating Accessibility

```javascript
// Check all interactive elements
document.querySelectorAll('button, input, [role="button"]').forEach(el => {
  const validation = TouchUtils.validateTouchTarget(el);
  if (!validation.meetsRequirements) {
    console.warn(`${el.tagName} fails touch target requirements`, validation);
  }
});
```

## Device Detection

The system automatically detects touch capabilities:

```javascript
if (TouchUtils.isTouchDevice()) {
  // Apply touch-specific behavior
  element.classList.add('touch-enabled');
}
```

**Detection Methods:**
- `'ontouchstart' in window`
- `navigator.maxTouchPoints > 0`
- `navigator.msMaxTouchPoints > 0`

## CSS Media Queries

Use media queries to provide touch-specific styling:

```css
/* Touch devices only */
@media (hover: none) and (pointer: coarse) {
  .interactive-element {
    min-height: var(--touch-target-min);
    padding: var(--spacing-md);
  }
}

/* Non-touch devices */
@media (hover: hover) and (pointer: fine) {
  .interactive-element:hover {
    background-color: var(--color-hover);
  }
}
```

## Best Practices

### Do's

✅ **Use minimum 44px touch targets**
✅ **Provide visual feedback for touch states**
✅ **Test on actual mobile devices**
✅ **Use semantic HTML for accessibility**
✅ **Implement proper focus management**

### Don'ts

❌ **Don't rely only on hover states**
❌ **Don't make touch targets too small**
❌ **Don't forget about touch spacing**
❌ **Don't ignore ghost click prevention**
❌ **Don't skip accessibility validation**

## Troubleshooting

### Common Issues

**Touch events not firing:**
- Check if `preventDefault()` is being called inappropriately
- Ensure proper event listener options (`passive: false` when needed)

**Double-clicking on mobile:**
- Implement ghost click prevention
- Use proper touch event handling in components

**Small touch targets:**
- Run accessibility validation
- Apply mobile-specific CSS media queries
- Use design tokens for consistent sizing

**Poor performance:**
- Use passive event listeners when possible
- Debounce gesture recognition
- Optimize touch feedback animations

## Future Enhancements

Potential improvements for touch interaction support:

- **Multi-touch gestures**: Pinch, zoom, rotate
- **Swipe navigation**: For tab switching and navigation
- **Touch haptic feedback**: When supported by device
- **Advanced gesture recognition**: Custom gesture patterns
- **Performance monitoring**: Touch interaction analytics

## Contributing

When adding new touch interactions:

1. **Follow existing patterns** in `TouchUtils`
2. **Add comprehensive tests** for new functionality
3. **Update documentation** with examples
4. **Validate accessibility** compliance
5. **Test on multiple devices** when possible