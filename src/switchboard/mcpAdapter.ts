import { MCPClient } from '../mcp/client.js';

// Adapter that exposes MCP servers as high level "plugins" to the UI.
// Each plugin maps to a primary tool; the underlying tools/resources/prompts
// remain hidden from the switchboard.
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

  listPlugins(): string[] {
    return Object.keys(this.toolMap);
  }

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
