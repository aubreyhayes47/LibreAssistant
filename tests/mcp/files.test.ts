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

test('file CRUD operations', async () => {
  const client = await setup();
  try {
    const file = 'crud.txt';
    const dir = '.';
    await client.invoke('files', 'fs_create', { path: file, content: 'hello' });
    const read1 = await client.invoke('files', 'fs_read', { path: file });
    assert.equal(read1.content, 'hello');
    await client.invoke('files', 'fs_update', { path: file, content: 'world', confirm: true });
    const read2 = await client.invoke('files', 'fs_read', { path: file });
    assert.equal(read2.content, 'world');
    const list = await client.invoke('files', 'fs_list', { path: dir });
    assert.ok(Array.isArray(list));
    await client.invoke('files', 'fs_delete', { path: file, confirm: true });
  } finally {
    client.close();
  }
});

test('refuses destructive operations without confirm', async () => {
  const client = await setup();
  try {
    const file = 'consent.txt';
    await client.invoke('files', 'fs_create', { path: file, content: 'hi' });
    const update = await client.invoke('files', 'fs_update', {
      path: file,
      content: 'bye'
    });
    assert.equal(update.error, 'ValidationError');
    const del = await client.invoke('files', 'fs_delete', { path: file });
    assert.equal(del.error, 'ValidationError');
    await client.invoke('files', 'fs_delete', { path: file, confirm: true });
  } finally {
    client.close();
  }
});
