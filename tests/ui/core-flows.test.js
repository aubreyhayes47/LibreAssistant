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
global.HTMLTemplateElement = dom.window.HTMLTemplateElement;
global.Event = dom.window.Event;
global.CustomEvent = dom.window.CustomEvent;
global.MutationObserver = dom.window.MutationObserver;

// Mock CSS tokens for theming
dom.window.document.documentElement.style.setProperty = function(prop, value) {
  // Mock implementation for CSS custom properties
};

// Mock localStorage
global.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {}
};

// Load component paths and create mock dependencies
const switchboardPath = path.resolve('ui/components/switchboard.js');
const onboardingPath = path.resolve('ui/components/onboarding-flow.js');
const pluginCataloguePath = path.resolve('ui/components/plugin-catalogue.js');
const themeSelectorPath = path.resolve('ui/components/theme-selector.js');
const confirmDialogPath = path.resolve('ui/components/confirm-dialog.js');

// Mock component dependencies that are not critical for testing core flows
class MockLAProviderSelector extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = '<select><option value="test">Test Provider</option></select>';
  }
  
  getCurrentProvider() {
    return 'test-provider';
  }
  
  addEventListener(event, handler) {
    super.addEventListener(event, handler);
  }
}

class MockLAInputField extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = '<label><slot name="label"></slot><input /></label>';
  }
}

// Register mock components before loading real components
customElements.define('la-provider-selector', MockLAProviderSelector);
customElements.define('la-input-field', MockLAInputField);

// Mock fetch for testing
const mockFetchResponses = new Map();
global.fetch = async function(url, options) {
  const key = `${options?.method || 'GET'} ${url}`;
  const response = mockFetchResponses.get(key);
  if (response) {
    return response;
  }
  // Return a default error response for unmocked requests
  return {
    ok: false,
    status: 404,
    statusText: 'Not Found',
    json: async () => ({ error: 'Mock not found' })
  };
};

function mockFetch(method, url, response, ok = true) {
  mockFetchResponses.set(`${method} ${url}`, {
    ok: ok,
    status: ok ? 200 : 400,
    statusText: ok ? 'OK' : 'Bad Request',
    json: async () => response,
    text: async () => typeof response === 'string' ? response : JSON.stringify(response)
  });
}

function clearMocks() {
  mockFetchResponses.clear();
}

// Mock notifications system
global.window.notifications = {
  info: () => 'info-id',
  success: () => 'success-id',
  error: () => 'error-id',
  loading: () => 'loading-id',
  dismiss: () => {}
};

// Utility to wait for component initialization
async function waitForComponent(component, timeout = 1000) {
  let elapsed = 0;
  while (!component.shadowRoot && elapsed < timeout) {
    await new Promise(resolve => setTimeout(resolve, 50));
    elapsed += 50;
  }
  if (!component.shadowRoot) {
    throw new Error('Component did not initialize within timeout');
  }
}

// ===== SWITCHBOARD TESTS =====

test('switchboard core functionality', async () => {
  clearMocks();
  
  // Only load switchboard if not already loaded
  if (!customElements.get('la-switchboard')) {
    eval(fs.readFileSync(confirmDialogPath, 'utf8'));
    eval(fs.readFileSync(switchboardPath, 'utf8'));
  }

  mockFetch('GET', '/api/v1/mcp/servers', { servers: [] });

  const switchboard = document.createElement('la-switchboard');
  document.body.appendChild(switchboard);
  
  await waitForComponent(switchboard);
  
  // Test 1: Basic initialization
  const input = switchboard.shadowRoot.getElementById('input');
  const send = switchboard.shadowRoot.getElementById('send');
  const plugin = switchboard.shadowRoot.getElementById('plugin');
  const log = switchboard.shadowRoot.getElementById('log');
  
  assert.ok(input, 'Input field should exist');
  assert.ok(send, 'Send button should exist');
  assert.ok(plugin, 'Plugin selector should exist');
  assert.ok(log, 'Activity log should exist');
  
  // Test 2: Dangerous operation detection
  assert.equal(typeof switchboard.isDangerousOperation, 'function', 'Should have isDangerousOperation method');
  
  const isDeleteDangerous = await switchboard.isDangerousOperation('files', 'delete file.txt');
  assert.equal(isDeleteDangerous, true, 'Should detect delete as dangerous');
  
  const isReadDangerous = await switchboard.isDangerousOperation('files', 'read file.txt');
  assert.equal(isReadDangerous, false, 'Should not detect read as dangerous');
  
  // Test 3: Plugin loading 
  clearMocks();
  const mockPlugins = [
    { name: 'echo', consent: false },
    { name: 'files', consent: true }
  ];
  mockFetch('GET', '/api/v1/mcp/servers', { servers: mockPlugins });
  
  await switchboard.loadPlugins();
  await new Promise(resolve => setTimeout(resolve, 100));
  
  const options = plugin.querySelectorAll('option');
  assert.equal(options.length >= 1, true, 'Should have at least the default option');
  
  document.body.removeChild(switchboard);
});

// ===== ONBOARDING FLOW TESTS =====

test('onboarding flow core functionality', async () => {
  clearMocks();
  
  if (!customElements.get('la-onboarding-flow')) {
    eval(fs.readFileSync(onboardingPath, 'utf8'));
  }

  mockFetch('GET', '/api/v1/mcp/servers', { servers: [] });

  const onboarding = document.createElement('la-onboarding-flow');
  document.body.appendChild(onboarding);
  
  await waitForComponent(onboarding);
  await new Promise(resolve => setTimeout(resolve, 200)); // Wait for loadPlugins
  
  // Test 1: Basic initialization
  assert.equal(onboarding.step, 0, 'Should start at step 0');
  
  const steps = onboarding.shadowRoot.querySelectorAll('.step');
  assert.equal(steps.length, 6, 'Should have 6 onboarding steps');
  
  // Check first step is visible
  const firstStep = steps[0];
  assert.equal(firstStep.hidden, false, 'First step should be visible');
  
  // Check other steps are hidden
  for (let i = 1; i < steps.length; i++) {
    assert.equal(steps[i].hidden, true, `Step ${i} should be hidden`);
  }
  
  // Test 2: Step validation
  assert.equal(onboarding.validateStep(), false, 'Should fail validation without engine selection');
  
  const engineSelect = onboarding.shadowRoot.getElementById('engine');
  engineSelect.value = 'cloud';
  assert.equal(onboarding.validateStep(), true, 'Should pass validation with engine selected');
  
  // Test 3: Plugin configuration
  clearMocks();
  const mockPlugins = [
    { name: 'echo', consent: false, description: 'Echo plugin' },
    { name: 'files', consent: true, description: 'File operations' }
  ];
  mockFetch('GET', '/api/v1/mcp/servers', { servers: mockPlugins });
  mockFetch('POST', '/api/v1/mcp/consent/echo', { status: 'ok' });

  await onboarding.loadPlugins();
  await new Promise(resolve => setTimeout(resolve, 100));
  
  assert.equal(onboarding.plugins.length, 2, 'Should load 2 plugins');
  assert.equal(onboarding.plugins[0].name, 'echo', 'Should load echo plugin');
  
  document.body.removeChild(onboarding);
});

// ===== PLUGIN CATALOGUE TESTS =====

test('plugin catalogue core functionality', async () => {
  clearMocks();
  
  if (!customElements.get('la-plugin-catalogue')) {
    eval(fs.readFileSync(pluginCataloguePath, 'utf8'));
  }

  const mockPlugins = [
    { name: 'echo', consent: false },
    { name: 'files', consent: true },
    { name: 'weather', consent: false }
  ];
  
  mockFetch('GET', '/api/v1/mcp/servers', { servers: mockPlugins });

  const catalogue = document.createElement('la-plugin-catalogue');
  document.body.appendChild(catalogue);
  
  await waitForComponent(catalogue);
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // Test 1: Plugin loading and display
  const items = catalogue.shadowRoot.querySelectorAll('.plugin-item');
  assert.equal(items.length, 3, 'Should display 3 plugins');
  
  const firstItem = items[0];
  const status = firstItem.querySelector('.plugin-status');
  assert.ok(status, 'Should have status indicator');
  
  // Test 2: Search filtering
  catalogue.filter('echo');
  const filteredItems = catalogue.shadowRoot.querySelectorAll('.plugin-item');
  assert.equal(filteredItems.length, 1, 'Should filter to 1 plugin');
  
  // Reset filter
  catalogue.render();
  
  // Test 3: Plugin toggle
  clearMocks();
  mockFetch('POST', '/api/v1/mcp/consent/echo', { status: 'ok' });
  
  let toggleEventFired = false;
  catalogue.addEventListener('plugin-toggle', (event) => {
    toggleEventFired = true;
    assert.equal(event.detail.name, 'echo', 'Should toggle echo plugin');
  });
  
  const toggle = catalogue.shadowRoot.querySelector('input[type="checkbox"]');
  if (toggle) {
    toggle.click();
    await new Promise(resolve => setTimeout(resolve, 100));
    assert.equal(toggleEventFired, true, 'Should fire toggle event');
  }
  
  document.body.removeChild(catalogue);
});

// ===== THEME SELECTOR TESTS =====

test('theme selector core functionality', async () => {
  clearMocks();
  
  if (!customElements.get('la-theme-selector')) {
    eval(fs.readFileSync(themeSelectorPath, 'utf8'));
  }

  // Test 1: Fallback to built-in themes when API fails
  mockFetch('GET', '/api/v1/themes', { error: 'Not found' }, false);

  const themeSelector = document.createElement('la-theme-selector');
  document.body.appendChild(themeSelector);
  
  await waitForComponent(themeSelector);
  await new Promise(resolve => setTimeout(resolve, 200));
  
  assert.equal(themeSelector.themes.length, 3, 'Should have 3 built-in themes');
  assert.equal(themeSelector.themes[0].id, 'light', 'Should include light theme');
  assert.equal(themeSelector.themes[1].id, 'dark', 'Should include dark theme');
  assert.equal(themeSelector.themes[2].id, 'high-contrast', 'Should include high-contrast theme');
  
  // Test 2: Load custom themes
  clearMocks();
  const mockThemes = {
    themes: [
      { id: 'light', name: 'Light', preview: '#ffffff' },
      { id: 'dark', name: 'Dark', preview: '#000000' },
      { id: 'custom', name: 'Custom Theme', preview: '#123456' }
    ]
  };
  mockFetch('GET', '/api/v1/themes', mockThemes);

  await themeSelector.loadThemes();
  await new Promise(resolve => setTimeout(resolve, 100));
  
  assert.equal(themeSelector.themes.length, 3, 'Should load 3 themes');
  assert.equal(themeSelector.themes[2].name, 'Custom Theme', 'Should include custom theme');
  
  // Test 3: Theme application
  let themeChangeEventFired = false;
  const themeChangeHandler = (event) => {
    if (event.detail.themeId === 'dark') {
      themeChangeEventFired = true;
      assert.equal(event.detail.themeId, 'dark', 'Should change to dark theme');
    }
  };
  themeSelector.addEventListener('theme-change', themeChangeHandler);
  
  await themeSelector.applyTheme('dark');
  assert.equal(themeSelector.currentTheme, 'dark', 'Should update current theme');
  assert.equal(themeChangeEventFired, true, 'Should fire theme change event');
  
  // Remove handler before next test
  themeSelector.removeEventListener('theme-change', themeChangeHandler);
  
  // Test 4: Error handling for custom theme loading
  clearMocks();
  mockFetch('GET', '/api/v1/themes/custom.css', { error: 'Not found' }, false);
  
  let errorEventFired = false;
  const errorHandler = (event) => {
    if (!event.detail.success) {
      errorEventFired = true;
      assert.ok(event.detail.error, 'Should include error details');
    }
  };
  themeSelector.addEventListener('theme-change', errorHandler);
  
  await themeSelector.applyTheme('custom');
  assert.equal(errorEventFired, true, 'Should fire theme change event with error');
  
  document.body.removeChild(themeSelector);
});