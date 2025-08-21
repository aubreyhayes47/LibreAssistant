import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPAdapter } from '../../src/switchboard/mcpAdapter.js';

class MockClient {
  public invokes: any[] = [];
  async invoke(plugin: string, tool: string, params: any): Promise<any> {
    this.invokes.push({ plugin, tool, params });
    return { plugin, tool, params };
  }
}

test('listPlugins exposes available plugin identifiers', () => {
  const adapter = new MCPAdapter(new MockClient() as any);
  assert.deepEqual(adapter.listPlugins().sort(), ['echo', 'files', 'law_by_keystone', 'think_tank']);
});

test('invokePlugin maps plugin names and logs history', async () => {
  const client = new MockClient();
  const adapter = new MCPAdapter(client as any);
  const calls: any[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any, init: any) => {
    calls.push({ url, init });
    return { ok: true } as any;
  };
  try {
    await adapter.invokePlugin('echo', { message: 'hi' }, 'u1');
    assert.deepEqual(client.invokes, [
      { plugin: 'echo', tool: 'echo_message', params: { message: 'hi' } },
    ]);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, '/api/v1/history/u1');
    const body = JSON.parse(calls[0].init.body);
    assert.equal(body.plugin, 'echo');
    assert.deepEqual(body.payload, { message: 'hi' });
    assert.equal(body.granted, true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('destructive file operations require consent and log outcome', async () => {
  const client = new MockClient();
  const adapter = new MCPAdapter(client as any);
  const history: any[] = [];
  const originalFetch = globalThis.fetch;
  const originalConsent = (globalThis as any).showConsentModal;
  let consentCalls = 0;
  globalThis.fetch = async (url: any, init: any) => {
    history.push({ url, init });
    return { ok: true } as any;
  };
  (globalThis as any).showConsentModal = async () => {
    consentCalls++;
    return true;
  };
  try {
    // consent granted
    await adapter.invokePlugin('files', { operation: 'update', path: '/tmp/a' }, 'u2');
    assert.deepEqual(client.invokes, [
      { plugin: 'files', tool: 'fs_update', params: { operation: 'update', path: '/tmp/a', confirm: true } },
    ]);
    assert.equal(consentCalls, 1);
    let body = JSON.parse(history[0].init.body);
    assert.equal(body.granted, true);

    // consent denied
    (globalThis as any).showConsentModal = async () => {
      consentCalls++;
      return false;
    };
    const result = await adapter.invokePlugin('files', { operation: 'delete', path: '/tmp/b' }, 'u2');
    assert.deepEqual(result, { error: 'PermissionDenied' });
    assert.equal(client.invokes.length, 1); // no new invoke
    assert.equal(consentCalls, 2);
    body = JSON.parse(history[1].init.body);
    assert.equal(body.plugin, 'files');
    assert.equal(body.payload.path, '/tmp/b');
    assert.equal(body.granted, false);
  } finally {
    globalThis.fetch = originalFetch;
    (globalThis as any).showConsentModal = originalConsent;
  }
});
