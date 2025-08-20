import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPClient } from '../../src/mcp/client.js';
import { loadRegistry } from '../../src/mcp/registry.js';
import path from 'path';
import fs from 'fs';

async function setup() {
  const client = new MCPClient();
  await loadRegistry(path.resolve('config/mcp.registry.json'), client);
  return client;
}

test('audit log records invocations', async () => {
  const client = await setup();
  try {
    await client.invoke('echo', 'echo_message', { message: 'hi' });
    assert.equal(client.auditLog.length, 1);
    const logPath = path.resolve('logs/audit.ndjson');
    assert.ok(fs.existsSync(logPath));
    const lines = fs
      .readFileSync(logPath, 'utf8')
      .trim()
      .split('\n')
      .filter(Boolean)
      .map((l) => JSON.parse(l));
    assert.ok(lines.some((e) => e.tool === 'echo_message'));
  } finally {
    client.close();
  }
});

test('audit entry captures data sources', async () => {
  const client = await setup();
  try {
    await client.invoke('law_by_keystone', 'generate_legal_summary', {
      query: 'test',
      source: 'govtrack',
      output_path: 'law_audit',
    });
    const last = client.auditLog.at(-1);
    assert.ok(last?.dataSources?.includes('govtrack'));
  } finally {
    client.close();
  }
});
