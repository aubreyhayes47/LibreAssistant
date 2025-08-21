// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

/**
 * Switchboard adapter that exposes MCP servers as high level "plugins".
 *
 * On initialization it loads `config/mcp.registry.json` and registers the
 * listed servers with an {@link MCPClient}. Each tool provided by the servers
 * is exposed under a plugin identifier `server.tool`. Destructive file
 * operations will trigger a user consent modal before execution, and every
 * invocation is recorded in the user's history log via HTTP.
 */
import path from 'path';
import { MCPClient } from '../mcp/client.js';
import { loadRegistry } from '../mcp/registry.js';

type ToolEntry = { server: string; tool: string };

export class MCPAdapter {
  private toolMap: Record<string, ToolEntry> = {};

  private constructor(private client: MCPClient) {}

  /**
   * Load the MCP registry and build the tool mapping.
   * @param client MCP client instance used for registration
   * @returns Initialized {@link MCPAdapter} instance
   */
  static async create(client: MCPClient) {
    const adapter = new MCPAdapter(client);
    await adapter.initialize();
    return adapter;
  }

  /**
   * Register servers declared in the registry and cache their tools.
   * @sideeffect Spawns MCP server processes and populates `toolMap`
   */
  private async initialize() {
    const registryPath = path.resolve('config/mcp.registry.json');
    await loadRegistry(registryPath, this.client);
    for (const serverName of this.client.listServers()) {
      const server = this.client.getServer(serverName);
      for (const tool of server.listTools()) {
        const key = `${serverName}.${tool.name}`;
        this.toolMap[key] = { server: serverName, tool: tool.name };
      }
    }
  }

  /**
   * Returns the identifiers of all available plugins.
   *
   * @returns Array of plugin names exposed by the adapter.
   */
  listPlugins(): string[] {
    return Object.keys(this.toolMap);
  }

  /**
   * Executes the MCP tool mapped to a plugin identifier.
   *
   * Destructive file operations prompt the user for consent and each
   * invocation is persisted to the user's history log.
   *
   * @param plugin - Plugin identifier to execute (format: server.tool).
   * @param params - Parameters forwarded to the underlying tool.
   * @param userId - User performing the action.
   * @returns Result from the MCP client.
   * @sideeffect May display a consent modal and log invocation history via HTTP.
   */
  async invokePlugin(plugin: string, params: any, userId: string): Promise<any> {
    const entry = this.toolMap[plugin];
    if (!entry) throw new Error(`Unknown plugin ${plugin}`);
    const { server, tool } = entry;

    let granted = true;
    // Prompt for confirmation on destructive file operations
    if (
      server === 'files' &&
      (tool === 'fs_update' || tool === 'fs_delete') &&
      !params.confirm
    ) {
      const ask = (globalThis as any).showConsentModal
        ? (msg: string) => (globalThis as any).showConsentModal(msg)
        : async () => true;
      granted = await ask(`Allow ${tool} on ${params.path}?`);
      params.confirm = granted;
      if (!granted) {
        await this.recordHistory(userId, plugin, params, false);
        return { error: 'PermissionDenied' };
      }
    }

    const result = await this.client.invoke(server, tool, params);
    await this.recordHistory(userId, plugin, params, granted);
    return result;
  }

  /**
   * Persist an invocation to the user's history log via HTTP.
   * Failures are ignored so as not to block plugin execution.
   * @param user    User identifier
   * @param plugin  Invoked plugin name
   * @param payload Parameters passed to the plugin
   * @param granted Whether consent was granted for the action
   * @sideeffect Performs a network request to `/api/v1/history`
   */
  private async recordHistory(
    user: string,
    plugin: string,
    payload: any,
    granted: boolean,
  ) {
    try {
      await fetch(`/api/v1/history/${user}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plugin, payload, granted }),
      });
    } catch {
      /* ignore logging failures */
    }
  }
}
