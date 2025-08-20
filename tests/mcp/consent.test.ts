import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPClient } from '../../src/mcp/client.js';
import { loadRegistry } from '../../src/mcp/registry.js';
import path from 'path';
import fs from 'fs';

test('registry enforces server consent', async () => {
  const client = new MCPClient();
  const consentPath = path.resolve('config/tmp.consent.json');
  fs.writeFileSync(consentPath, JSON.stringify({ echo: true }));
  try {
    await loadRegistry(path.resolve('config/mcp.registry.json'), client, consentPath);
    assert.deepEqual(client.listServers(), ['echo']);
  } finally {
    client.close();
    fs.unlinkSync(consentPath);
  }
});
