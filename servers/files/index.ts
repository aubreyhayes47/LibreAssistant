import { promises as fs } from 'fs';
import path from 'path';
import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

const baseDir = path.resolve(process.env.MCP_FS_BASE_DIR || './mcp_fs');
await fs.mkdir(baseDir, { recursive: true });
const auditLog = path.resolve('logs/file_io_audit.ndjson');
await fs.mkdir(path.dirname(auditLog), { recursive: true });

const tools: ToolSchema[] = [
  {
    name: 'fs_read',
    description: 'Read a file',
    parameters: {
      type: 'object',
      properties: { path: { type: 'string' } },
      required: ['path']
    },
    returns: { type: 'object', properties: { content: { type: 'string' } }, required: ['content'] }
  },
  {
    name: 'fs_create',
    description: 'Create a new file',
    parameters: {
      type: 'object',
      properties: { path: { type: 'string' }, content: { type: 'string' } },
      required: ['path', 'content']
    },
    returns: { type: 'object', properties: { status: { enum: ['created'] } }, required: ['status'] }
  },
  {
    name: 'fs_update',
    description: 'Update an existing file',
    parameters: {
      type: 'object',
      properties: { path: { type: 'string' }, content: { type: 'string' }, confirm: { type: 'boolean' } },
      required: ['path', 'content', 'confirm']
    },
    returns: { type: 'object', properties: { status: { enum: ['updated'] } }, required: ['status'] }
  },
  {
    name: 'fs_delete',
    description: 'Delete a file',
    parameters: {
      type: 'object',
      properties: { path: { type: 'string' }, confirm: { type: 'boolean' } },
      required: ['path', 'confirm']
    },
    returns: { type: 'object', properties: { status: { enum: ['deleted'] } }, required: ['status'] }
  },
  {
    name: 'fs_list',
    description: 'List directory entries',
    parameters: {
      type: 'object',
      properties: { path: { type: 'string' } },
      required: ['path']
    },
    returns: { type: 'array', items: { type: 'string' } }
  }
];

const resources: ResourceSchema[] = [];

const prompts: PromptSchema[] = [
  { name: 'file_edit_template', template: 'Update file {{path}} with new content.' }
];

function resolve(p: string) {
  const full = path.resolve(baseDir, p);
  if (!full.startsWith(baseDir)) throw new Error('path outside allowed directory');
  return full;
}

async function audit(user: string | undefined, action: string, resolved: string) {
  const entry = { user_id: user, action, path: resolved, timestamp: Date.now() };
  await fs.appendFile(auditLog, JSON.stringify(entry) + '\n');
}

async function invoke(tool: string, params: any) {
  const user = params.user_id as string | undefined;
  switch (tool) {
    case 'fs_read': {
      const full = resolve(params.path);
      await audit(user, 'read', full);
      const content = await fs.readFile(full, 'utf-8');
      return { content };
    }
    case 'fs_create': {
      const full = resolve(params.path);
      await audit(user, 'create', full);
      await fs.writeFile(full, params.content, { flag: 'wx' });
      return { status: 'created' };
    }
    case 'fs_update': {
      if (!params.confirm) throw new Error('confirm required');
      const full = resolve(params.path);
      await audit(user, 'update', full);
      await fs.writeFile(full, params.content, { flag: 'w' });
      return { status: 'updated' };
    }
    case 'fs_delete': {
      if (!params.confirm) throw new Error('confirm required');
      const full = resolve(params.path);
      await audit(user, 'delete', full);
      await fs.unlink(full);
      return { status: 'deleted' };
    }
    case 'fs_list': {
      const full = resolve(params.path);
      await audit(user, 'list', full);
      const entries = await fs.readdir(full);
      return entries;
    }
  }
  throw new Error(`Unknown tool ${tool}`);
}

const server: MCPServer = {
  listTools: () => tools,
  listResources: () => resources,
  listPrompts: () => prompts,
  invoke
};

export default server;

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  serveStdio(server);
}
