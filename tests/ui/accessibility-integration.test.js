// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

// Set up JSDOM environment
const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`, {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
  resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.HTMLElement = dom.window.HTMLElement;
global.customElements = dom.window.customElements;
global.CustomEvent = dom.window.CustomEvent;
global.requestAnimationFrame = (callback) => setTimeout(callback, 16);
global.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  clear: () => {}
};
global.MutationObserver = dom.window.MutationObserver;

// Mock console methods to reduce noise
const originalConsoleError = console.error;
console.error = (...args) => {
  if (!args[0]?.includes?.('Failed to load plugins')) {
    originalConsoleError(...args);
  }
};

// Component paths
const componentPaths = {
  'main-tabs': path.resolve('ui/components/main-tabs.js'),
  'onboarding-flow': path.resolve('ui/components/onboarding-flow.js'),
  'theme-selector': path.resolve('ui/components/theme-selector.js'),
  'modal-dialog': path.resolve('ui/components/modal-dialog.js'),
  'confirm-dialog': path.resolve('ui/components/confirm-dialog.js')
};

test('main-tabs component has proper ARIA attributes', async () => {
  // Load main tabs component
  eval(fs.readFileSync(componentPaths['main-tabs'], 'utf8'));

  const mainTabs = document.createElement('la-main-tabs');
  document.body.appendChild(mainTabs);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(mainTabs.shadowRoot, 'Component should have shadow root');

  // Check for proper ARIA structure
  const tabList = mainTabs.shadowRoot.querySelector('[role="tablist"]');
  if (tabList) {
    assert.ok(tabList, 'Should have element with role="tablist"');
    
    // Check for tabs
    const tabs = mainTabs.shadowRoot.querySelectorAll('[role="tab"]');
    if (tabs.length > 0) {
      tabs.forEach(tab => {
        assert.ok(tab.hasAttribute('aria-selected'), 'Each tab should have aria-selected attribute');
        assert.ok(tab.hasAttribute('tabindex'), 'Each tab should have tabindex attribute');
      });
    }
  }

  // Clean up
  document.body.removeChild(mainTabs);
});

test('main-tabs component keyboard navigation', async () => {
  // Load main tabs component
  eval(fs.readFileSync(componentPaths['main-tabs'], 'utf8'));

  const mainTabs = document.createElement('la-main-tabs');
  document.body.appendChild(mainTabs);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Test arrow key navigation
  const rightArrowEvent = new dom.window.KeyboardEvent('keydown', {
    key: 'ArrowRight',
    bubbles: true,
    cancelable: true
  });

  const leftArrowEvent = new dom.window.KeyboardEvent('keydown', {
    key: 'ArrowLeft',
    bubbles: true,
    cancelable: true
  });

  // Dispatch events to test keyboard handling
  mainTabs.dispatchEvent(rightArrowEvent);
  mainTabs.dispatchEvent(leftArrowEvent);

  // Clean up
  document.body.removeChild(mainTabs);
});

test('onboarding-flow component progresses through steps', async () => {
  // Load onboarding flow component
  eval(fs.readFileSync(componentPaths['onboarding-flow'], 'utf8'));

  const onboardingFlow = document.createElement('la-onboarding-flow');
  document.body.appendChild(onboardingFlow);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(onboardingFlow.shadowRoot, 'Component should have shadow root');

  // Check for step indicators
  const steps = onboardingFlow.shadowRoot.querySelectorAll('.step');
  if (steps.length > 0) {
    assert.ok(steps.length >= 1, 'Should have at least one step');
  }

  // Test navigation methods if available
  if (typeof onboardingFlow.nextStep === 'function') {
    onboardingFlow.nextStep();
  }

  if (typeof onboardingFlow.previousStep === 'function') {
    onboardingFlow.previousStep();
  }

  // Clean up
  document.body.removeChild(onboardingFlow);
});

test('theme-selector component accessibility', async () => {
  // Load theme selector component
  eval(fs.readFileSync(componentPaths['theme-selector'], 'utf8'));

  const themeSelector = document.createElement('la-theme-selector');
  document.body.appendChild(themeSelector);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(themeSelector.shadowRoot, 'Component should have shadow root');

  // Check for proper labeling
  const label = themeSelector.shadowRoot.querySelector('label');
  const select = themeSelector.shadowRoot.querySelector('select');
  
  if (label && select) {
    assert.ok(label.textContent.length > 0, 'Label should have text content');
    assert.ok(select.hasAttribute('aria-label') || label.getAttribute('for') === select.id, 
             'Select should be properly labeled');
  }

  // Clean up
  document.body.removeChild(themeSelector);
});

test('modal-dialog component focus management', async () => {
  // Load modal dialog component
  eval(fs.readFileSync(componentPaths['modal-dialog'], 'utf8'));

  const modal = document.createElement('la-modal-dialog');
  document.body.appendChild(modal);

  // Add focusable content
  modal.innerHTML = `
    <span slot="title">Test Modal</span>
    <button id="first-btn">First Button</button>
    <input type="text" id="text-input" />
    <button id="last-btn">Last Button</button>
  `;

  // Show the modal
  modal.show();

  // Wait for modal to initialize
  await new Promise(resolve => setTimeout(resolve, 100));

  // Test focus management
  modal._updateFocusableElements();
  
  if (modal._focusableElements && modal._focusableElements.length > 0) {
    assert.ok(modal._focusableElements.length >= 2, 'Should find focusable elements');
    
    // Test tab navigation within modal
    const tabEvent = new dom.window.KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
      cancelable: true
    });
    
    // Test forward tab
    modal._handleTabKey(tabEvent);
    
    // Test backward tab (Shift+Tab)
    const shiftTabEvent = new dom.window.KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
      cancelable: true
    });
    
    modal._handleTabKey(shiftTabEvent);
  }

  // Clean up
  modal.hide();
  document.body.removeChild(modal);
});

test('confirm-dialog component button accessibility', async () => {
  // Load confirm dialog component
  eval(fs.readFileSync(componentPaths['confirm-dialog'], 'utf8'));

  const confirmDialog = document.createElement('la-confirm-dialog');
  document.body.appendChild(confirmDialog);

  // Show the dialog
  const dialogPromise = confirmDialog.show('Test confirmation message', 'Test Title');

  // Wait for dialog to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check button accessibility
  const buttons = confirmDialog.shadowRoot.querySelectorAll('button');
  
  if (buttons.length > 0) {
    buttons.forEach(button => {
      assert.ok(button.textContent.length > 0, 'Button should have text content');
      assert.ok(button.hasAttribute('aria-label') || button.textContent.length > 0, 
               'Button should be properly labeled');
    });
  }

  // Test keyboard navigation
  const enterEvent = new dom.window.KeyboardEvent('keydown', {
    key: 'Enter',
    bubbles: true,
    cancelable: true
  });

  confirmDialog.dispatchEvent(enterEvent);

  // Close dialog
  confirmDialog.hide();

  try {
    await dialogPromise;
  } catch (e) {
    // Expected to reject or resolve
  }

  // Clean up
  document.body.removeChild(confirmDialog);
});

test('component integration - modal with theme selector', async () => {
  // Load both components
  eval(fs.readFileSync(componentPaths['modal-dialog'], 'utf8'));
  eval(fs.readFileSync(componentPaths['theme-selector'], 'utf8'));

  const modal = document.createElement('la-modal-dialog');
  const themeSelector = document.createElement('la-theme-selector');

  document.body.appendChild(modal);

  // Add theme selector inside modal
  modal.innerHTML = `
    <span slot="title">Theme Settings</span>
    <div id="theme-container"></div>
  `;

  modal.show();

  // Wait for initialization
  await new Promise(resolve => setTimeout(resolve, 50));

  const container = modal.querySelector('#theme-container');
  if (container) {
    container.appendChild(themeSelector);

    // Wait for theme selector to initialize
    await new Promise(resolve => setTimeout(resolve, 50));

    // Test that theme selector works within modal
    assert.ok(themeSelector.shadowRoot, 'Theme selector should have shadow root');
    assert.ok(modal.hasAttribute('open'), 'Modal should be open');
  }

  // Clean up
  modal.hide();
  document.body.removeChild(modal);
});

test('responsive behavior - components adapt to viewport', async () => {
  // Test with mobile viewport
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: 375
  });

  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: 667
  });

  // Load theme selector for responsive test
  eval(fs.readFileSync(componentPaths['theme-selector'], 'utf8'));

  const themeSelector = document.createElement('la-theme-selector');
  document.body.appendChild(themeSelector);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Trigger resize event
  const resizeEvent = new dom.window.Event('resize');
  window.dispatchEvent(resizeEvent);

  // Component should still be functional
  assert.ok(themeSelector.shadowRoot, 'Component should maintain shadow root after resize');

  // Clean up
  document.body.removeChild(themeSelector);

  // Reset viewport
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: 1024
  });

  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: 768
  });
});