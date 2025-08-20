import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'path';
import { MCPClient } from '../../src/mcp/client.js';
import { loadRegistry } from '../../src/mcp/registry.js';

async function setup() {
  const client = new MCPClient();
  await loadRegistry(path.resolve('config/mcp.registry.json'), client);
  return client;
}

test('rejects params that do not match schema', async () => {
  const client = await setup();
  try {
    const res = await client.invoke('echo', 'echo_message', { message: 123 });
    assert.equal(res.error, 'ValidationError');
    assert.ok(Array.isArray(res.details));
  } finally {
    client.close();
  }
});
