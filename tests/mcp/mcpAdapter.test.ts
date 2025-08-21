import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPAdapter } from '../../src/switchboard/mcpAdapter.js';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

class MockClient {
  private servers: Map<string, { tools: string[]; handler?: (tool: string, params: any) => any }> = new Map();
  public invokes: any[] = [];

  registerServer(name: string, tools: string[], handler?: (tool: string, params: any) => any) {
    this.servers.set(name, { tools, handler });
  }

  listServers() {
    return Array.from(this.servers.keys());
  }

  getServer(name: string) {
    const entry = this.servers.get(name);
    if (!entry) throw new Error(`Unknown server ${name}`);
    return {
      listTools: () => entry.tools.map(n => ({ name: n })),
      invoke: entry.handler || (async () => ({})),
    };
  }

  async invoke(server: string, tool: string, params: any) {
    this.invokes.push({ server, tool, params });
    return this.getServer(server).invoke(tool, params);
  }

  async close() {}
}

const repoRoot = process.cwd();
function setupTempConfig(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mcp-test-'));
  const cfg = path.join(dir, 'config');
  fs.mkdirSync(cfg, { recursive: true });
  fs.writeFileSync(path.join(cfg, 'mcp.registry.json'), JSON.stringify({ servers: [] }));
  fs.writeFileSync(path.join(cfg, 'mcp.consent.json'), '{}');
  return dir;
}

test('listPlugins enumerates server tools', async () => {
  const client = new MockClient();
  client.registerServer('echo', ['echo_message']);
  client.registerServer('files', ['fs_update', 'fs_delete']);

  const tmp = setupTempConfig();
  process.chdir(tmp);
  const adapter = await MCPAdapter.create(client as any);
  process.chdir(repoRoot);
  fs.rmSync(tmp, { recursive: true, force: true });

  assert.deepEqual(adapter.listPlugins().sort(), [
    'echo.echo_message',
    'files.fs_delete',
    'files.fs_update',
  ]);
});

test('invokePlugin prompts for consent on destructive file ops', async () => {
  const client = new MockClient();
  client.registerServer('files', ['fs_delete']);

  const tmp = setupTempConfig();
  process.chdir(tmp);
  const adapter = await MCPAdapter.create(client as any);
  process.chdir(repoRoot);
  fs.rmSync(tmp, { recursive: true, force: true });

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({ ok: true } as any);
  let prompts = 0;
  (globalThis as any).showConsentModal = async () => {
    prompts++;
    return false;
  };
  const res = await adapter.invokePlugin('files.fs_delete', { path: 'a.txt' }, 'user1');
  assert.equal(prompts, 1);
  assert.deepEqual(res, { error: 'PermissionDenied' });
  assert.equal(client.invokes.length, 0);
  delete (globalThis as any).showConsentModal;
  globalThis.fetch = originalFetch;
});

test('history logging via HTTP is attempted', async () => {
  const client = new MockClient();
  client.registerServer('echo', ['echo_message'], async (_tool, params) => ({ echoed: params.message }));

  const tmp = setupTempConfig();
  process.chdir(tmp);
  const adapter = await MCPAdapter.create(client as any);
  process.chdir(repoRoot);
  fs.rmSync(tmp, { recursive: true, force: true });

  const calls: any[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any, init: any) => {
    calls.push({ url, init });
    return { ok: true } as any;
  };
  await adapter.invokePlugin('echo.echo_message', { message: 'hi' }, 'user2');

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, '/api/v1/history/user2');
  const body = JSON.parse(calls[0].init.body);
  assert.equal(body.plugin, 'echo.echo_message');
  assert.deepEqual(body.payload, { message: 'hi' });
  assert.equal(body.granted, true);

  globalThis.fetch = originalFetch;
});
