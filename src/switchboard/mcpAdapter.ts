import { MCPClient } from '../mcp/client.js';

/**
 * Adapter that exposes MCP servers as high level "plugins" to the UI.
 * Each plugin maps to a primary tool via the internal `toolMap`, keeping the
 * underlying tools, resources, and prompts hidden from the switchboard.
 *
 * Destructive file operations trigger an optional consent modal via a global
 * `showConsentModal` function. If the user declines, the operation is aborted
 * and a permission error is returned.
 *
 * Every plugin invocation is recorded to `/api/v1/history` with the payload
 * and whether permission was granted.
 */
export class MCPAdapter {
  private toolMap: Record<string, string | ((params: any) => string)> = {
    echo: 'echo_message',
    files: (params: any) => {
      const op = params?.operation;
      const mapping: Record<string, string> = {
        read: 'fs_read',
        create: 'fs_create',
        update: 'fs_update',
        delete: 'fs_delete',
        list: 'fs_list',
      };
      return mapping[op];
    },
    law_by_keystone: 'generate_legal_summary',
    think_tank: 'analyze_goal',
  }; 

  constructor(private client: MCPClient) {}

  /**
   * List available plugin names.
   * @returns Array of plugin identifiers
   */
  listPlugins(): string[] {
    return Object.keys(this.toolMap);
  }

  /**
   * Invoke a plugin by mapping it to the underlying MCP tool.
   * Prompts for confirmation on destructive file operations and records history.
   * @param plugin Plugin identifier to execute
   * @param params Parameters to forward to the underlying tool
   * @param userId User performing the action
   * @returns Result from the MCP client or a permission error
   * @sideeffect May display a consent modal and logs invocation history via HTTP
   */
  async invokePlugin(plugin: string, params: any, userId: string): Promise<any> {
    const mapping = this.toolMap[plugin];
    if (!mapping) throw new Error(`Unknown plugin ${plugin}`);
    const tool = typeof mapping === 'function' ? mapping(params) : mapping;
    if (!tool) throw new Error(`Unknown operation for plugin ${plugin}`);

    let granted = true;
    // Prompt for confirmation on destructive file operations
    if (
      plugin === 'files' &&
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

    const result = await this.client.invoke(plugin, tool, params);
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
