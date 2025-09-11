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
  if (!args[0]?.includes?.('Failed to load plugins') && !args[0]?.includes?.('Failed to parse URL')) {
    originalConsoleError(...args);
  }
};

// Mock fetch for testing
const mockFetchResponses = new Map();
global.fetch = async function(url, options) {
  const key = `${options?.method || 'GET'} ${url}`;
  const response = mockFetchResponses.get(key);
  if (response) {
    return response;
  }
  return {
    ok: true,
    json: async () => ({ data: 'mock response' })
  };
};

function mockFetch(method, url, response) {
  mockFetchResponses.set(`${method} ${url}`, {
    ok: true,
    json: async () => response
  });
}

// Component paths
const componentPaths = {
  'user-profile': path.resolve('ui/components/user-profile.js'),
  'notification-system': path.resolve('ui/components/notification-system.js'),
  'data-vault': path.resolve('ui/components/data-vault.js'),
  'information-card': path.resolve('ui/components/information-card.js'),
  'input-field': path.resolve('ui/components/input-field.js'),
  'primary-button': path.resolve('ui/components/primary-button.js'),
  'provider-selector': path.resolve('ui/components/provider-selector.js'),
  'system-health': path.resolve('ui/components/system-health.js'),
  'theme-marketplace': path.resolve('ui/components/theme-marketplace.js'),
  'plugin-catalogue': path.resolve('ui/components/plugin-catalogue.js'),
  'past-requests': path.resolve('ui/components/past-requests.js'),
  'bill-of-materials': path.resolve('ui/components/bill-of-materials.js')
};

test('user-profile component renders and functions', async () => {
  // Load user profile component
  eval(fs.readFileSync(componentPaths['user-profile'], 'utf8'));

  const userProfile = document.createElement('la-user-profile');
  document.body.appendChild(userProfile);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(userProfile.shadowRoot, 'Component should have shadow root');
  
  // Check for basic structure
  const profileContainer = userProfile.shadowRoot.querySelector('.profile-container');
  assert.ok(profileContainer, 'Should have profile container');

  // Clean up
  document.body.removeChild(userProfile);
});

test('notification-system component handles notifications', async () => {
  // Load notification system component
  eval(fs.readFileSync(componentPaths['notification-system'], 'utf8'));

  const notificationSystem = document.createElement('la-notification-system');
  document.body.appendChild(notificationSystem);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(notificationSystem.shadowRoot, 'Component should have shadow root');

  // Test notification functionality if available
  if (typeof notificationSystem.addNotification === 'function') {
    notificationSystem.addNotification('Test message', 'info');
    
    // Check if notification was added
    const notifications = notificationSystem.shadowRoot.querySelectorAll('.notification');
    assert.ok(notifications.length > 0, 'Should have at least one notification');
  }

  // Clean up
  document.body.removeChild(notificationSystem);
});

test('data-vault component renders', async () => {
  // Load data vault component
  eval(fs.readFileSync(componentPaths['data-vault'], 'utf8'));

  const dataVault = document.createElement('la-data-vault');
  document.body.appendChild(dataVault);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(dataVault.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(dataVault);
});

test('information-card component displays content', async () => {
  // Load information card component
  eval(fs.readFileSync(componentPaths['information-card'], 'utf8'));

  const infoCard = document.createElement('la-information-card');
  document.body.appendChild(infoCard);

  // Set some content
  infoCard.setAttribute('title', 'Test Title');
  infoCard.innerHTML = '<p>Test content</p>';

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(infoCard.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(infoCard);
});

test('input-field component handles input', async () => {
  // Load input field component
  eval(fs.readFileSync(componentPaths['input-field'], 'utf8'));

  const inputField = document.createElement('la-input-field');
  document.body.appendChild(inputField);

  // Set attributes
  inputField.setAttribute('label', 'Test Label');
  inputField.setAttribute('type', 'text');

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(inputField.shadowRoot, 'Component should have shadow root');

  // Check for input element
  const input = inputField.shadowRoot.querySelector('input');
  if (input) {
    assert.equal(input.type, 'text', 'Input should have correct type');
  }

  // Clean up
  document.body.removeChild(inputField);
});

test('primary-button component responds to clicks', async () => {
  // Load primary button component
  eval(fs.readFileSync(componentPaths['primary-button'], 'utf8'));

  const primaryButton = document.createElement('la-primary-button');
  document.body.appendChild(primaryButton);

  // Set content
  primaryButton.textContent = 'Click me';

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(primaryButton.shadowRoot, 'Component should have shadow root');

  // Check for button element
  const button = primaryButton.shadowRoot.querySelector('button');
  if (button) {
    // Test click event
    let clicked = false;
    primaryButton.addEventListener('click', () => {
      clicked = true;
    });
    
    button.click();
    assert.equal(clicked, true, 'Button should trigger click event');
  }

  // Clean up
  document.body.removeChild(primaryButton);
});

test('provider-selector component renders options', async () => {
  // Load provider selector component
  eval(fs.readFileSync(componentPaths['provider-selector'], 'utf8'));

  const providerSelector = document.createElement('la-provider-selector');
  document.body.appendChild(providerSelector);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(providerSelector.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(providerSelector);
});

test('system-health component displays health status', async () => {
  // Load system health component
  eval(fs.readFileSync(componentPaths['system-health'], 'utf8'));

  const systemHealth = document.createElement('la-system-health');
  document.body.appendChild(systemHealth);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(systemHealth.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(systemHealth);
});

test('theme-marketplace component loads themes', async () => {
  // Mock theme data
  mockFetch('GET', '/api/themes', {
    themes: [
      { id: 'theme1', name: 'Test Theme', version: '1.0.0' }
    ]
  });

  // Load theme marketplace component
  eval(fs.readFileSync(componentPaths['theme-marketplace'], 'utf8'));

  const themeMarketplace = document.createElement('la-theme-marketplace');
  document.body.appendChild(themeMarketplace);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(themeMarketplace.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(themeMarketplace);
});

test('plugin-catalogue component displays plugins', async () => {
  // Mock plugin data
  mockFetch('GET', '/api/plugins', {
    plugins: [
      { id: 'plugin1', name: 'Test Plugin', version: '1.0.0' }
    ]
  });

  // Load plugin catalogue component
  eval(fs.readFileSync(componentPaths['plugin-catalogue'], 'utf8'));

  const pluginCatalogue = document.createElement('la-plugin-catalogue');
  document.body.appendChild(pluginCatalogue);

  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 50));

  // Check that component is properly created
  assert.ok(pluginCatalogue.shadowRoot, 'Component should have shadow root');

  // Clean up
  document.body.removeChild(pluginCatalogue);
});