import { promises as fs } from 'fs';
import path from 'path';
import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

const baseDir = path.resolve(process.env.MCP_FS_BASE_DIR || './mcp_fs');
await fs.mkdir(baseDir, { recursive: true });

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

async function invoke(tool: string, params: any) {
  switch (tool) {
    case 'fs_read': {
      const content = await fs.readFile(resolve(params.path), 'utf-8');
      return { content };
    }
    case 'fs_create': {
      await fs.writeFile(resolve(params.path), params.content, { flag: 'wx' });
      return { status: 'created' };
    }
    case 'fs_update': {
      if (!params.confirm) throw new Error('confirm required');
      await fs.writeFile(resolve(params.path), params.content, { flag: 'w' });
      return { status: 'updated' };
    }
    case 'fs_delete': {
      if (!params.confirm) throw new Error('confirm required');
      await fs.unlink(resolve(params.path));
      return { status: 'deleted' };
    }
    case 'fs_list': {
      const entries = await fs.readdir(resolve(params.path));
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
