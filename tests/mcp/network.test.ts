import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'path';
import { MCPClient } from '../../src/mcp/client.js';
import { StdioTransport } from '../../src/mcp/transport.js';

const runner = path.resolve('src/mcp/server-runner.js');
const modulePath = path.resolve('tests/mcp/network_server.ts');
const policy = { allow: ['example.com'], protocols: ['https'] };

test('enforces per-server network policies', async () => {
  const client = new MCPClient();
  const transport = new StdioTransport(
    'node',
    ['--loader', 'ts-node/esm', runner, modulePath],
    policy,
  );
  await client.register('net', transport, policy);

  const badHost = await client.invoke('net', 'fetch_url', { url: 'https://notexample.com' });
  assert.match(badHost.error, /not allowed/);

  const badProto = await client.invoke('net', 'fetch_url', { url: 'http://example.com' });
  assert.match(badProto.error, /Protocol/);

  client.close();
});
