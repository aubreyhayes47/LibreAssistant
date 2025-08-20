import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPClient } from '../../src/mcp/client.js';

test('blocks disallowed network hosts', async () => {
  const client = new MCPClient();
  client.setAllowedHosts(['example.com']);
  await assert.rejects(() => fetch('https://notexample.com'), /not allowed/);
  client.setAllowedHosts([]); // reset allowlist
  client.close();
});
