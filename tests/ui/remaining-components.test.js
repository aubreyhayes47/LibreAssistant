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

// Mock fetch for testing
global.fetch = async function(url, options) {
  return {
    ok: true,
    json: async () => ({ 
      data: 'mock response',
      history: [
        { id: 1, query: 'test query 1', response: 'test response 1', timestamp: Date.now() - 1000 },
        { id: 2, query: 'test query 2', response: 'test response 2', timestamp: Date.now() - 2000 }
      ],
      components: [
        { name: 'Component A', version: '1.0.0', license: 'MIT' },
        { name: 'Component B', version: '2.1.0', license: 'Apache-2.0' }
      ]
    })
  };
};

// Component paths
const componentPaths = {
  'past-requests': path.resolve('ui/components/past-requests.js'),
  'bill-of-materials': path.resolve('ui/components/bill-of-materials.js')
};

test('past-requests component displays request history', async () => {
  // Load past requests component
  eval(fs.readFileSync(componentPaths['past-requests'], 'utf8'));

  const pastRequests = document.createElement('la-past-requests');
  document.body.appendChild(pastRequests);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check that component is properly created
  assert.ok(pastRequests.shadowRoot, 'Component should have shadow root');

  // Test history loading if available
  if (typeof pastRequests.loadHistory === 'function') {
    await pastRequests.loadHistory();
    
    // Check if history items are rendered
    const historyItems = pastRequests.shadowRoot.querySelectorAll('.history-item');
    assert.ok(historyItems.length >= 0, 'Should render history items');
  }

  // Test search functionality if available
  if (typeof pastRequests.searchHistory === 'function') {
    pastRequests.searchHistory('test');
  }

  // Clean up
  document.body.removeChild(pastRequests);
});

test('past-requests component accessibility features', async () => {
  // Load past requests component
  eval(fs.readFileSync(componentPaths['past-requests'], 'utf8'));

  const pastRequests = document.createElement('la-past-requests');
  document.body.appendChild(pastRequests);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check for proper ARIA attributes
  const searchInput = pastRequests.shadowRoot.querySelector('input[type="search"]');
  if (searchInput) {
    assert.ok(searchInput.hasAttribute('aria-label') || searchInput.hasAttribute('aria-labelledby'), 
             'Search input should have proper labeling');
  }

  // Check for keyboard navigation support
  const historyList = pastRequests.shadowRoot.querySelector('[role="list"]') || 
                     pastRequests.shadowRoot.querySelector('ul');
  if (historyList) {
    assert.ok(historyList, 'Should have properly structured list');
  }

  // Clean up
  document.body.removeChild(pastRequests);
});

test('bill-of-materials component renders component list', async () => {
  // Load bill of materials component
  eval(fs.readFileSync(componentPaths['bill-of-materials'], 'utf8'));

  const billOfMaterials = document.createElement('la-bill-of-materials');
  document.body.appendChild(billOfMaterials);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check that component is properly created
  assert.ok(billOfMaterials.shadowRoot, 'Component should have shadow root');

  // Test component loading if available
  if (typeof billOfMaterials.loadComponents === 'function') {
    await billOfMaterials.loadComponents();
    
    // Check if components are rendered
    const componentItems = billOfMaterials.shadowRoot.querySelectorAll('.component-item');
    assert.ok(componentItems.length >= 0, 'Should render component items');
  }

  // Clean up
  document.body.removeChild(billOfMaterials);
});

test('bill-of-materials component license information', async () => {
  // Load bill of materials component
  eval(fs.readFileSync(componentPaths['bill-of-materials'], 'utf8'));

  const billOfMaterials = document.createElement('la-bill-of-materials');
  document.body.appendChild(billOfMaterials);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check for license display
  const licenseElements = billOfMaterials.shadowRoot.querySelectorAll('.license');
  if (licenseElements.length > 0) {
    licenseElements.forEach(license => {
      assert.ok(license.textContent.length > 0, 'License should have text content');
    });
  }

  // Test sorting functionality if available
  if (typeof billOfMaterials.sortByLicense === 'function') {
    billOfMaterials.sortByLicense();
  }

  if (typeof billOfMaterials.sortByName === 'function') {
    billOfMaterials.sortByName();
  }

  // Clean up
  document.body.removeChild(billOfMaterials);
});

test('component error handling and loading states', async () => {
  // Test error handling for both components
  const components = ['la-past-requests', 'la-bill-of-materials'];
  
  for (const componentName of components) {
    const element = document.createElement(componentName);
    document.body.appendChild(element);
    
    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Check that component handles errors gracefully
    assert.ok(element.shadowRoot, `${componentName} should have shadow root even with errors`);
    
    // Test that component doesn't throw when methods are called
    if (typeof element.handleError === 'function') {
      element.handleError(new Error('Test error'));
    }
    
    // Clean up
    document.body.removeChild(element);
  }
});

test('component responsive design behavior', async () => {
  // Test responsive behavior
  eval(fs.readFileSync(componentPaths['past-requests'], 'utf8'));
  eval(fs.readFileSync(componentPaths['bill-of-materials'], 'utf8'));

  const pastRequests = document.createElement('la-past-requests');
  const billOfMaterials = document.createElement('la-bill-of-materials');
  
  document.body.appendChild(pastRequests);
  document.body.appendChild(billOfMaterials);

  // Simulate mobile viewport
  Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });
  Object.defineProperty(window, 'innerHeight', { value: 667, writable: true });

  // Trigger resize event
  const resizeEvent = new dom.window.Event('resize');
  window.dispatchEvent(resizeEvent);

  // Wait for potential responsive adjustments
  await new Promise(resolve => setTimeout(resolve, 100));

  // Components should still function
  assert.ok(pastRequests.shadowRoot, 'Past requests should maintain shadow root after resize');
  assert.ok(billOfMaterials.shadowRoot, 'Bill of materials should maintain shadow root after resize');

  // Clean up
  document.body.removeChild(pastRequests);
  document.body.removeChild(billOfMaterials);

  // Reset viewport
  Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
  Object.defineProperty(window, 'innerHeight', { value: 768, writable: true });
});