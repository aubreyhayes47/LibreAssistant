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

test('law summary generation', async () => {
  const client = await setup();
  try {
    const res = await client.invoke('law_by_keystone', 'generate_legal_summary', {
      query: 'test',
      source: 'govinfo',
      output_format: 'txt',
      output_path: 'law',
    });
    assert.equal(res.status, 'exported');
    assert.ok(Array.isArray(res.sources));
    assert.ok(res.sources.includes('govinfo'));
    assert.equal(res.metadata.source, 'govinfo');
    assert.equal(res.metadata.format, 'txt');
    assert.ok(fs.existsSync(res.path));
  } finally {
    client.close();
  }
});
