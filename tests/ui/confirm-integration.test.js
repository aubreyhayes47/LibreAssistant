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

// Load the components
const confirmDialogPath = path.resolve('ui/components/confirm-dialog.js');
const switchboardPath = path.resolve('ui/components/switchboard.js');

// Mock fetch for testing
const mockFetchResponses = new Map();
global.fetch = async function(url, options) {
  const key = `${options?.method || 'GET'} ${url}`;
  const response = mockFetchResponses.get(key);
  if (response) {
    return response;
  }
  throw new Error(`No mock response for ${key}`);
};

function mockFetch(method, url, response) {
  mockFetchResponses.set(`${method} ${url}`, {
    ok: true,
    json: async () => response
  });
}

test('switchboard checks server consent before invocation', async () => {
  // Load components
  eval(fs.readFileSync(confirmDialogPath, 'utf8'));
  eval(fs.readFileSync(switchboardPath, 'utf8'));

  // Set up mocks
  mockFetch('GET', '/api/v1/mcp/servers', {
    servers: [{ name: 'echo', consent: false }]
  });
  
  mockFetch('GET', '/api/v1/mcp/consent/echo', { consent: false });
  mockFetch('POST', '/api/v1/mcp/consent/echo', { status: 'ok' });
  mockFetch('POST', '/api/v1/invoke', { result: 'Hello!' });

  // Create switchboard element
  const switchboard = document.createElement('la-switchboard');
  document.body.appendChild(switchboard);
  
  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Mock showConsentModal to return true (user consents)
  global.window.showConsentModal = async () => true;
  
  // Test that consent is checked
  const hasConsent = await switchboard.checkServerConsent('echo');
  assert.equal(hasConsent, false, 'Should initially have no consent');
  
  // Test consent request
  const granted = await switchboard.requestServerConsent('echo');
  assert.equal(granted, true, 'Should grant consent when user accepts');
  
  // Clean up
  document.body.removeChild(switchboard);
  delete global.window.showConsentModal;
});

test('switchboard detects dangerous operations', async () => {
  // Load components
  eval(fs.readFileSync(switchboardPath, 'utf8'));

  const switchboard = document.createElement('la-switchboard');
  document.body.appendChild(switchboard);
  
  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Test dangerous operation detection
  try {
    assert.equal(
      await switchboard.isDangerousOperation('files', 'delete file.txt'),
      true,
      'Should detect delete operation as dangerous'
    );
    
    assert.equal(
      await switchboard.isDangerousOperation('files', 'update data.json'),
      true,
      'Should detect update operation as dangerous'
    );
    
    assert.equal(
      await switchboard.isDangerousOperation('files', 'read file.txt'),
      false,
      'Should not detect read operation as dangerous'
    );
    
    assert.equal(
      await switchboard.isDangerousOperation('echo', 'hello world'),
      false,
      'Should not detect echo operation as dangerous'
    );
  } catch (error) {
    console.error('Test error:', error.message);
    throw error;
  }
  
  // Clean up
  document.body.removeChild(switchboard);
});

test('confirm dialog shows and resolves correctly', async () => {
  // Load confirm dialog component
  eval(fs.readFileSync(confirmDialogPath, 'utf8'));

  const dialog = document.createElement('la-confirm-dialog');
  document.body.appendChild(dialog);
  
  // Test dialog show/hide
  const showPromise = dialog.show('Test message', 'Test Title');
  
  // Verify dialog is open
  assert.equal(dialog.hasAttribute('open'), true, 'Dialog should be open');
  
  // Simulate clicking confirm button
  const confirmBtn = dialog.shadowRoot.querySelector('#confirm-btn');
  confirmBtn.click();
  
  // Wait for promise to resolve
  const result = await showPromise;
  assert.equal(result, true, 'Should return true when confirmed');
  assert.equal(dialog.hasAttribute('open'), false, 'Dialog should be closed');
  
  // Clean up
  document.body.removeChild(dialog);
});

test('showConsentModal utility function works', async () => {
  // Load confirm dialog component
  eval(fs.readFileSync(confirmDialogPath, 'utf8'));
  
  // Test the utility function
  const modalPromise = global.window.showConsentModal('Test consent message', 'Test Consent');
  
  // Find the dialog that was created
  const dialog = document.querySelector('la-confirm-dialog');
  assert.ok(dialog, 'Dialog should be created');
  assert.equal(dialog.hasAttribute('open'), true, 'Dialog should be open');
  
  // Simulate user clicking confirm
  const confirmBtn = dialog.shadowRoot.querySelector('#confirm-btn');
  confirmBtn.click();
  
  const result = await modalPromise;
  assert.equal(result, true, 'Should return true when confirmed');
  
  // Dialog should be removed from DOM
  assert.equal(document.querySelector('la-confirm-dialog'), null, 'Dialog should be removed');
});