import { MCPClient } from './client.js';
import { StdioTransport } from './transport.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

interface RegistryConfig {
  servers: { name: string; module: string }[];
  allowedHosts?: string[];
}

export async function loadRegistry(configPath: string, client: MCPClient) {
  const config: RegistryConfig = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  const runner = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    'server-runner.js'
  );
  if (config.allowedHosts) {
    client.setAllowedHosts(config.allowedHosts);
  }
  for (const entry of config.servers) {
    const modulePath = path.resolve(entry.module);
    const transport = new StdioTransport('node', [
      '--loader',
      'ts-node/esm',
      runner,
      modulePath,
    ]);
    await client.register(entry.name, transport);
  }
}
