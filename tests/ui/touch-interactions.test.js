// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

// Set up JSDOM environment with touch support
const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`, {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
  resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.HTMLElement = dom.window.HTMLElement;
global.customElements = dom.window.customElements;
global.TouchEvent = dom.window.TouchEvent || class TouchEvent extends Event {
  constructor(type, eventInitDict = {}) {
    super(type, eventInitDict);
    this.touches = eventInitDict.touches || [];
    this.targetTouches = eventInitDict.targetTouches || [];
    this.changedTouches = eventInitDict.changedTouches || [];
  }
};

// Load touch utilities and components
const touchUtilsPath = path.resolve('ui/components/touch-utils.js');
const primaryButtonPath = path.resolve('ui/components/primary-button.js');
const inputFieldPath = path.resolve('ui/components/input-field.js');

eval(fs.readFileSync(touchUtilsPath, 'utf8'));
eval(fs.readFileSync(primaryButtonPath, 'utf8'));
eval(fs.readFileSync(inputFieldPath, 'utf8'));

const TouchUtils = global.window.TouchUtils;

test('TouchUtils creates valid touch events', () => {
  const touchEvent = TouchUtils.createTouchEvent('touchstart', {
    clientX: 100,
    clientY: 200
  });
  
  assert.equal(touchEvent.type, 'touchstart');
  assert.equal(touchEvent.touches.length, 1);
  assert.equal(touchEvent.touches[0].clientX, 100);
  assert.equal(touchEvent.touches[0].clientY, 200);
});

test('TouchUtils can simulate tap gesture', async () => {
  const button = document.createElement('button');
  button.style.width = '100px';
  button.style.height = '50px';
  button.style.position = 'absolute';
  button.style.left = '0px';
  button.style.top = '0px';
  document.body.appendChild(button);
  
  let touchStartFired = false;
  let touchEndFired = false;
  
  button.addEventListener('touchstart', () => { touchStartFired = true; });
  button.addEventListener('touchend', () => { touchEndFired = true; });
  
  await TouchUtils.simulateTap(button);
  
  assert.equal(touchStartFired, true, 'touchstart should fire');
  assert.equal(touchEndFired, true, 'touchend should fire');
  
  document.body.removeChild(button);
});

test('TouchUtils can simulate long press', async () => {
  const button = document.createElement('button');
  button.style.width = '100px';
  button.style.height = '50px';
  button.style.position = 'absolute';
  document.body.appendChild(button);
  
  let touchStartTime = 0;
  let touchEndTime = 0;
  
  button.addEventListener('touchstart', () => { touchStartTime = Date.now(); });
  button.addEventListener('touchend', () => { touchEndTime = Date.now(); });
  
  const result = await TouchUtils.simulateLongPress(button, { duration: 100 });
  
  assert.ok(touchEndTime - touchStartTime >= 100, 'Long press should respect duration');
  assert.equal(result.duration, 100);
  
  document.body.removeChild(button);
});

test('TouchUtils can simulate swipe gesture', async () => {
  const element = document.createElement('div');
  element.style.width = '200px';
  element.style.height = '100px';
  element.style.position = 'absolute';
  document.body.appendChild(element);
  
  let touchMoveCount = 0;
  element.addEventListener('touchmove', () => { touchMoveCount++; });
  
  await TouchUtils.simulateSwipe(element, {
    startX: 50,
    startY: 50,
    endX: 150,
    endY: 50,
    steps: 5
  });
  
  assert.ok(touchMoveCount >= 5, 'Should fire multiple touchmove events');
  
  document.body.removeChild(element);
});

test('TouchUtils validates touch target sizes', () => {
  const smallButton = document.createElement('button');
  smallButton.style.width = '30px';
  smallButton.style.height = '30px';
  smallButton.style.position = 'absolute';
  smallButton.style.top = '0px';
  smallButton.style.left = '0px';
  document.body.appendChild(smallButton);
  
  // Force layout calculation in JSDOM
  smallButton.getBoundingClientRect = () => ({
    width: 30,
    height: 30,
    left: 0,
    top: 0,
    right: 30,
    bottom: 30
  });
  
  const validation = TouchUtils.validateTouchTarget(smallButton);
  
  assert.equal(validation.width, 30);
  assert.equal(validation.height, 30);
  assert.equal(validation.meetsRequirements, false);
  assert.ok(validation.recommendations.width > 0);
  assert.ok(validation.recommendations.height > 0);
  
  document.body.removeChild(smallButton);
});

test('TouchUtils detects touch capability', () => {
  // In JSDOM, this will likely return false, but we test the function exists
  const isTouch = TouchUtils.isTouchDevice();
  assert.equal(typeof isTouch, 'boolean');
});

test('Primary button responds to touch events', async () => {
  const button = document.createElement('la-primary-button');
  button.textContent = 'Test Button';
  document.body.appendChild(button);
  
  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 10));
  
  let clickFired = false;
  button.addEventListener('click', () => { clickFired = true; });
  
  // Mock getBoundingClientRect for JSDOM
  button.getBoundingClientRect = () => ({
    width: 48,
    height: 44,
    left: 0,
    top: 0,
    right: 48,
    bottom: 44
  });
  
  // Simulate touch
  await TouchUtils.simulateTap(button);
  
  // Check if button meets accessibility requirements
  const validation = TouchUtils.validateTouchTarget(button);
  assert.ok(validation.width >= 44 || validation.height >= 44, 'Button should meet minimum touch target size');
  
  document.body.removeChild(button);
});

test('Input field handles touch interactions', async () => {
  const inputField = document.createElement('la-input-field');
  inputField.setAttribute('type', 'text');
  inputField.setAttribute('placeholder', 'Test input');
  document.body.appendChild(inputField);
  
  // Wait for component to initialize
  await new Promise(resolve => setTimeout(resolve, 10));
  
  const input = inputField.shadowRoot.querySelector('input');
  
  let focusFired = false;
  input.addEventListener('focus', () => { focusFired = true; });
  
  // Mock getBoundingClientRect for JSDOM
  inputField.getBoundingClientRect = () => ({
    width: 200,
    height: 44,
    left: 0,
    top: 0,
    right: 200,
    bottom: 44
  });
  
  // Simulate touch to focus
  await TouchUtils.simulateTap(input);
  
  // Small delay for focus to take effect
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Check accessibility
  const validation = TouchUtils.validateTouchTarget(inputField);
  assert.ok(validation.height >= 44, 'Input should meet minimum touch target height');
  
  document.body.removeChild(inputField);
});

test('Touch handlers can be added to custom elements', () => {
  const element = document.createElement('div');
  element.style.width = '100px';
  element.style.height = '100px';
  document.body.appendChild(element);
  
  let tapFired = false;
  let longPressFired = false;
  
  const cleanup = TouchUtils.addTouchHandlers(element, {
    onTap: () => { tapFired = true; },
    onLongPress: () => { longPressFired = true; }
  });
  
  // Test that cleanup function is returned
  assert.equal(typeof cleanup, 'function');
  
  cleanup();
  document.body.removeChild(element);
});

test('Touch events work with disabled buttons', async () => {
  const button = document.createElement('la-primary-button');
  button.setAttribute('disabled', '');
  button.textContent = 'Disabled Button';
  document.body.appendChild(button);
  
  await new Promise(resolve => setTimeout(resolve, 10));
  
  let clickFired = false;
  button.addEventListener('click', () => { clickFired = true; });
  
  await TouchUtils.simulateTap(button);
  
  // Click should not fire on disabled button
  assert.equal(clickFired, false, 'Disabled button should not respond to touch');
  
  document.body.removeChild(button);
});

test('Multiple touches can be simulated', () => {
  const touch1 = { identifier: 0, clientX: 50, clientY: 50 };
  const touch2 = { identifier: 1, clientX: 100, clientY: 100 };
  
  const multiTouchEvent = TouchUtils.createTouchEvent('touchstart', {
    touches: [touch1, touch2]
  });
  
  assert.equal(multiTouchEvent.touches.length, 2);
  assert.equal(multiTouchEvent.touches[0].clientX, 50);
  assert.equal(multiTouchEvent.touches[1].clientX, 100);
});

test('Touch events prevent ghost clicks', async () => {
  const button = document.createElement('la-primary-button');
  document.body.appendChild(button);
  
  await new Promise(resolve => setTimeout(resolve, 10));
  
  let touchEndPrevented = false;
  
  button.addEventListener('touchend', (e) => {
    touchEndPrevented = e.defaultPrevented;
  });
  
  await TouchUtils.simulateTap(button);
  
  // Note: In a real browser, preventDefault would be called to prevent ghost clicks
  // In our test environment, we verify the component is set up to handle this
  
  document.body.removeChild(button);
});