import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPAdapter } from '../../src/switchboard/mcpAdapter.js';
import { MCPClient } from '../../src/mcp/client.js';

class RecordingClient extends MCPClient {
  public invokes: any[] = [];
  async invoke(server: string, tool: string, params: any): Promise<any> {
    this.invokes.push({ server, tool, params });
    return super.invoke(server, tool, params);
  }
}

test('listPlugins exposes available plugin identifiers', async () => {
  const client = new RecordingClient();
  const adapter = await MCPAdapter.create(client);
  try {
    assert.deepEqual(
      adapter.listPlugins().sort(),
      [
        'echo.echo_message',
        'files.fs_create',
        'files.fs_delete',
        'files.fs_list',
        'files.fs_read',
        'files.fs_update',
        'law_by_keystone.generate_legal_summary',
        'think_tank.analyze_goal',
      ],
    );
  } finally {
    await client.close();
  }
});

test('invokePlugin maps plugin names and logs history', async () => {
  const client = new RecordingClient();
  const adapter = await MCPAdapter.create(client);
  const calls: any[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any, init: any) => {
    calls.push({ url, init });
    return { ok: true } as any;
  };
  try {
    await adapter.invokePlugin('echo.echo_message', { message: 'hi' }, 'u1');
    assert.deepEqual(client.invokes, [
      { server: 'echo', tool: 'echo_message', params: { message: 'hi' } },
    ]);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, '/api/v1/history/u1');
    const body = JSON.parse(calls[0].init.body);
    assert.equal(body.plugin, 'echo.echo_message');
    assert.deepEqual(body.payload, { message: 'hi' });
    assert.equal(body.granted, true);
  } finally {
    globalThis.fetch = originalFetch;
    await client.close();
  }
});

test('destructive file operations require consent and log outcome', async () => {
  const client = new RecordingClient();
  const adapter = await MCPAdapter.create(client);
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
    await adapter.invokePlugin('files.fs_update', { path: 'a.txt', content: '' }, 'u2');
    assert.deepEqual(client.invokes, [
      {
        server: 'files',
        tool: 'fs_update',
        params: { path: 'a.txt', content: '', confirm: true },
      },
    ]);
    assert.equal(consentCalls, 1);
    let body = JSON.parse(history[0].init.body);
    assert.equal(body.granted, true);

    // consent denied
    (globalThis as any).showConsentModal = async () => {
      consentCalls++;
      return false;
    };
    const result = await adapter.invokePlugin('files.fs_delete', { path: 'b.txt' }, 'u2');
    assert.deepEqual(result, { error: 'PermissionDenied' });
    assert.equal(client.invokes.length, 1); // no new invoke
    assert.equal(consentCalls, 2);
    body = JSON.parse(history[1].init.body);
    assert.equal(body.plugin, 'files.fs_delete');
    assert.equal(body.payload.path, 'b.txt');
    assert.equal(body.granted, false);
  } finally {
    globalThis.fetch = originalFetch;
    (globalThis as any).showConsentModal = originalConsent;
    await client.close();
  }
});
