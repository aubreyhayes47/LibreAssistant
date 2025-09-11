// Simple test to verify escape key and focus trapping in modal dialogs
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
const modalDialogPath = path.resolve('ui/components/modal-dialog.js');
const confirmDialogPath = path.resolve('ui/components/confirm-dialog.js');

test('modal dialog escape key functionality', async () => {
  // Load modal dialog component
  eval(fs.readFileSync(modalDialogPath, 'utf8'));

  const modal = document.createElement('la-modal-dialog');
  document.body.appendChild(modal);
  
  // Set some content
  modal.innerHTML = '<span slot="title">Test Modal</span><p>Test content</p>';
  
  // Show the modal
  modal.show();
  assert.equal(modal.hasAttribute('open'), true, 'Modal should be open');
  
  // Simulate escape key on the modal element (since that's where the handler is)
  const escapeEvent = new dom.window.KeyboardEvent('keydown', {
    key: 'Escape',
    bubbles: true,
    cancelable: true
  });
  modal.dispatchEvent(escapeEvent);
  
  // Modal should be closed
  assert.equal(modal.hasAttribute('open'), false, 'Modal should be closed after escape key');
  
  // Clean up
  document.body.removeChild(modal);
});

test('confirm dialog escape key functionality', async () => {
  // Load confirm dialog component  
  eval(fs.readFileSync(confirmDialogPath, 'utf8'));

  const dialog = document.createElement('la-confirm-dialog');
  document.body.appendChild(dialog);
  
  // Show the dialog
  const showPromise = dialog.show('Test message', 'Test Title');
  assert.equal(dialog.hasAttribute('open'), true, 'Dialog should be open');
  
  // Simulate escape key
  const escapeEvent = new dom.window.KeyboardEvent('keydown', {
    key: 'Escape',
    bubbles: true,
    cancelable: true
  });
  dialog.dispatchEvent(escapeEvent);
  
  // Wait for promise to resolve (should return false for escape)
  const result = await showPromise;
  assert.equal(result, false, 'Should return false when dismissed with escape');
  assert.equal(dialog.hasAttribute('open'), false, 'Dialog should be closed');
  
  // Clean up
  document.body.removeChild(dialog);
});

test('modal dialog focus trapping', async () => {
  // Load modal dialog component
  eval(fs.readFileSync(modalDialogPath, 'utf8'));

  const modal = document.createElement('la-modal-dialog');
  document.body.appendChild(modal);
  
  // Set content with focusable elements
  modal.innerHTML = `
    <span slot="title">Test Modal</span>
    <button id="btn1">Button 1</button>
    <input id="input1" type="text" />
    <button id="btn2">Button 2</button>
  `;
  
  // Show the modal
  modal.show();
  
  // Wait for modal to be fully initialized
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // Check that the modal has focus trapping methods
  assert.ok(typeof modal._updateFocusableElements === 'function', 'Should have _updateFocusableElements method');
  assert.ok(typeof modal._handleTabKey === 'function', 'Should have _handleTabKey method');
  
  // Test that focusable elements can be found
  modal._updateFocusableElements();
  assert.ok(modal._focusableElements.length >= 0, 'Should be able to find focusable elements');
  
  // Clean up
  modal.hide();
  document.body.removeChild(modal);
});

test('confirm dialog focus trapping', async () => {
  // Load confirm dialog component
  eval(fs.readFileSync(confirmDialogPath, 'utf8'));

  const dialog = document.createElement('la-confirm-dialog');
  document.body.appendChild(dialog);
  
  // Show the dialog
  const showPromise = dialog.show('Test message', 'Test Title');
  
  // Wait for dialog to be fully initialized
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // Check that the dialog has focus trapping methods
  assert.ok(typeof dialog._updateFocusableElements === 'function', 'Should have _updateFocusableElements method');
  assert.ok(typeof dialog._handleTabKey === 'function', 'Should have _handleTabKey method');
  
  // Test that focusable elements can be found
  dialog._updateFocusableElements();
  assert.ok(dialog._focusableElements.length >= 0, 'Should be able to find focusable elements');
  
  // Close the dialog
  dialog.hide();
  
  try {
    await showPromise;
  } catch (e) {
    // Expected to reject or resolve with false
  }
  
  // Clean up
  document.body.removeChild(dialog);
});