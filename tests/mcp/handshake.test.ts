import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPClient } from '../../src/mcp/client.js';
import { loadRegistry } from '../../src/mcp/registry.js';
import path from 'path';

async function setup() {
  const client = new MCPClient();
  await loadRegistry(path.resolve('config/mcp.registry.json'), client);
  return client;
}

test('servers expose tools', async () => {
  const client = await setup();
  try {
    const servers = client.listServers();
    assert.deepEqual(servers.sort(), ['echo','files','law_by_keystone','think_tank']);
    for (const name of servers) {
      const server = client.getServer(name);
      assert.ok(server.listTools().length > 0);
    }
  } finally {
    client.close();
  }
});
