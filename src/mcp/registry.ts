import { MCPClient } from './client.js';
import { StdioTransport } from './transport.js';
import { NetworkPolicy } from './types.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Shape of the JSON configuration consumed by {@link loadRegistry}.
 */
interface RegistryConfig {
  /** Servers that may be registered */
  servers: { name: string; module: string; network?: NetworkPolicy }[];
  /** Optional default network policy applied when none specified per server */
  defaultNetwork?: NetworkPolicy;
}

/**
 * Load MCP servers from a registry file while enforcing per-server consent.
 * Only servers explicitly granted consent will be registered with the client.
 *
 * @param configPath Path to the registry configuration listing available servers
 * @param client     MCP client instance used for registration
 * @param consentPath Optional path to a JSON file mapping server names to
 *                    boolean consent flags. Defaults to `mcp.consent.json`
 *                    in the same directory as the config file.
 * @returns Promise that resolves when all allowed servers have been registered
 * @sideeffect Spawns server processes and updates client state
 */
export async function loadRegistry(
  configPath: string,
  client: MCPClient,
  consentPath?: string,
) {
  const config: RegistryConfig = JSON.parse(
    fs.readFileSync(configPath, 'utf-8'),
  );
  const consentFile =
    consentPath ||
    path.resolve(path.dirname(configPath), 'mcp.consent.json');
  let consent: Record<string, boolean> = {};
  if (fs.existsSync(consentFile)) {
    consent = JSON.parse(fs.readFileSync(consentFile, 'utf-8'));
  }
  const runner = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    'server-runner.js'
  );
  if (config.defaultNetwork) {
    client.setDefaultPolicy(config.defaultNetwork);
  }
  for (const entry of config.servers) {
    if (!consent[entry.name]) continue;
    const modulePath = path.resolve(entry.module);
    const policy = entry.network || config.defaultNetwork;
    const transport = new StdioTransport(
      'node',
      ['--loader', 'ts-node/esm', runner, modulePath],
      policy,
    );
    await client.register(entry.name, transport, policy);
  }
}
