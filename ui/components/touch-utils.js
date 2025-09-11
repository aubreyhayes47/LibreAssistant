// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

/**
 * Touch interaction utilities for mobile device support
 * Provides consistent touch event handling and simulation across components
 */

class TouchUtils {
  /**
   * Creates standardized touch events for testing and simulation
   * @param {string} type - Touch event type ('touchstart', 'touchmove', 'touchend')
   * @param {Object} options - Touch event options
   * @returns {TouchEvent} Configured touch event
   */
  static createTouchEvent(type, options = {}) {
    const {
      clientX = 0,
      clientY = 0,
      pageX = clientX,
      pageY = clientY,
      screenX = clientX,
      screenY = clientY,
      target = null,
      touches = [],
      targetTouches = [],
      changedTouches = []
    } = options;

    // Create touch object
    const touch = {
      identifier: 0,
      target: target || document.body,
      clientX,
      clientY,
      pageX,
      pageY,
      screenX,
      screenY,
      radiusX: 10,
      radiusY: 10,
      rotationAngle: 0,
      force: 1
    };

    // Create touch lists
    const touchList = touches.length > 0 ? touches : [touch];
    const targetTouchList = targetTouches.length > 0 ? targetTouches : (type !== 'touchend' ? [touch] : []);
    const changedTouchList = changedTouches.length > 0 ? changedTouches : [touch];

    try {
      // Try to create a real TouchEvent if supported
      return new TouchEvent(type, {
        bubbles: true,
        cancelable: true,
        touches: touchList,
        targetTouches: targetTouchList,
        changedTouches: changedTouchList
      });
    } catch (e) {
      // Fallback for environments that don't support TouchEvent
      const event = new Event(type, { bubbles: true, cancelable: true });
      event.touches = touchList;
      event.targetTouches = targetTouchList;
      event.changedTouches = changedTouchList;
      return event;
    }
  }

  /**
   * Simulates a complete tap gesture (touchstart + touchend)
   * @param {Element} element - Target element
   * @param {Object} options - Touch position and timing options
   * @returns {Promise} Resolves when tap is complete
   */
  static async simulateTap(element, options = {}) {
    const { clientX = 50, clientY = 50, delay = 50 } = options;
    const rect = element.getBoundingClientRect();
    const x = rect.left + (clientX || rect.width / 2);
    const y = rect.top + (clientY || rect.height / 2);

    // Dispatch touchstart
    const touchStart = this.createTouchEvent('touchstart', {
      clientX: x,
      clientY: y,
      target: element
    });
    element.dispatchEvent(touchStart);

    // Wait for delay
    await new Promise(resolve => setTimeout(resolve, delay));

    // Dispatch touchend
    const touchEnd = this.createTouchEvent('touchend', {
      clientX: x,
      clientY: y,
      target: element,
      targetTouches: [] // No touches remaining
    });
    element.dispatchEvent(touchEnd);

    return { touchStart, touchEnd };
  }

  /**
   * Simulates a long press gesture
   * @param {Element} element - Target element
   * @param {Object} options - Touch position and timing options
   * @returns {Promise} Resolves when long press is complete
   */
  static async simulateLongPress(element, options = {}) {
    const { clientX = 50, clientY = 50, duration = 500 } = options;
    const rect = element.getBoundingClientRect();
    const x = rect.left + (clientX || rect.width / 2);
    const y = rect.top + (clientY || rect.height / 2);

    // Dispatch touchstart
    const touchStart = this.createTouchEvent('touchstart', {
      clientX: x,
      clientY: y,
      target: element
    });
    element.dispatchEvent(touchStart);

    // Wait for long press duration
    await new Promise(resolve => setTimeout(resolve, duration));

    // Dispatch touchend
    const touchEnd = this.createTouchEvent('touchend', {
      clientX: x,
      clientY: y,
      target: element,
      targetTouches: []
    });
    element.dispatchEvent(touchEnd);

    return { touchStart, touchEnd, duration };
  }

  /**
   * Simulates a swipe gesture
   * @param {Element} element - Target element
   * @param {Object} options - Swipe direction and distance options
   * @returns {Promise} Resolves when swipe is complete
   */
  static async simulateSwipe(element, options = {}) {
    const { 
      startX = 50, 
      startY = 50, 
      endX = 150, 
      endY = 50, 
      duration = 200,
      steps = 5 
    } = options;
    
    const rect = element.getBoundingClientRect();
    const x1 = rect.left + startX;
    const y1 = rect.top + startY;
    const x2 = rect.left + endX;
    const y2 = rect.top + endY;

    // Start touch
    const touchStart = this.createTouchEvent('touchstart', {
      clientX: x1,
      clientY: y1,
      target: element
    });
    element.dispatchEvent(touchStart);

    // Interpolate movement
    const stepDelay = duration / steps;
    const deltaX = (x2 - x1) / steps;
    const deltaY = (y2 - y1) / steps;

    for (let i = 1; i <= steps; i++) {
      await new Promise(resolve => setTimeout(resolve, stepDelay));
      
      const currentX = x1 + (deltaX * i);
      const currentY = y1 + (deltaY * i);
      
      const touchMove = this.createTouchEvent('touchmove', {
        clientX: currentX,
        clientY: currentY,
        target: element
      });
      element.dispatchEvent(touchMove);
    }

    // End touch
    const touchEnd = this.createTouchEvent('touchend', {
      clientX: x2,
      clientY: y2,
      target: element,
      targetTouches: []
    });
    element.dispatchEvent(touchEnd);

    return { startX: x1, startY: y1, endX: x2, endY: y2 };
  }

  /**
   * Adds standard touch event handling to an element
   * @param {Element} element - Target element
   * @param {Object} handlers - Event handler functions
   */
  static addTouchHandlers(element, handlers = {}) {
    const {
      onTouchStart,
      onTouchMove, 
      onTouchEnd,
      onTap,
      onLongPress,
      preventGhostClick = true
    } = handlers;

    let touchStartTime = 0;
    let touchStartPos = { x: 0, y: 0 };
    let longPressTimer = null;
    const LONG_PRESS_DURATION = 500;
    const TAP_THRESHOLD = 10; // px movement threshold for tap vs drag

    // Touch start handler
    element.addEventListener('touchstart', (e) => {
      touchStartTime = Date.now();
      const touch = e.touches[0];
      touchStartPos = { x: touch.clientX, y: touch.clientY };
      
      // Clear any existing long press timer
      if (longPressTimer) {
        clearTimeout(longPressTimer);
      }
      
      // Set long press timer
      if (onLongPress) {
        longPressTimer = setTimeout(() => {
          onLongPress(e);
          longPressTimer = null;
        }, LONG_PRESS_DURATION);
      }
      
      if (onTouchStart) {
        onTouchStart(e);
      }
    }, { passive: false });

    // Touch move handler
    element.addEventListener('touchmove', (e) => {
      // Cancel long press if finger moves too much
      if (longPressTimer) {
        const touch = e.touches[0];
        const deltaX = Math.abs(touch.clientX - touchStartPos.x);
        const deltaY = Math.abs(touch.clientY - touchStartPos.y);
        
        if (deltaX > TAP_THRESHOLD || deltaY > TAP_THRESHOLD) {
          clearTimeout(longPressTimer);
          longPressTimer = null;
        }
      }
      
      if (onTouchMove) {
        onTouchMove(e);
      }
    }, { passive: false });

    // Touch end handler
    element.addEventListener('touchend', (e) => {
      const touchEndTime = Date.now();
      const touchDuration = touchEndTime - touchStartTime;
      
      // Clear long press timer
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
        
        // This was a tap (released before long press threshold)
        if (onTap && touchDuration < LONG_PRESS_DURATION) {
          onTap(e);
        }
      }
      
      if (onTouchEnd) {
        onTouchEnd(e);
      }
      
      // Prevent ghost click after touch
      if (preventGhostClick) {
        e.preventDefault();
      }
    }, { passive: false });

    // Return cleanup function
    return () => {
      if (longPressTimer) {
        clearTimeout(longPressTimer);
      }
    };
  }

  /**
   * Checks if touch target meets accessibility size requirements
   * @param {Element} element - Element to check
   * @returns {Object} Size validation results
   */
  static validateTouchTarget(element) {
    const rect = element.getBoundingClientRect();
    const MIN_SIZE = 44; // WCAG recommended minimum touch target size
    
    return {
      width: rect.width,
      height: rect.height,
      meetsMinWidth: rect.width >= MIN_SIZE,
      meetsMinHeight: rect.height >= MIN_SIZE,
      meetsRequirements: rect.width >= MIN_SIZE && rect.height >= MIN_SIZE,
      recommendations: {
        width: Math.max(MIN_SIZE - rect.width, 0),
        height: Math.max(MIN_SIZE - rect.height, 0)
      }
    };
  }

  /**
   * Detects if device supports touch
   * @returns {boolean} True if touch is supported
   */
  static isTouchDevice() {
    return 'ontouchstart' in window || 
           navigator.maxTouchPoints > 0 || 
           navigator.msMaxTouchPoints > 0;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TouchUtils;
} else if (typeof window !== 'undefined') {
  window.TouchUtils = TouchUtils;
}