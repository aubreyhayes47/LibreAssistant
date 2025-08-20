import { MCPServer, ToolSchema } from '../../src/mcp/types.js';

const tools: ToolSchema[] = [
  {
    name: 'fetch_url',
    description: 'Fetches a URL and returns status',
    parameters: {
      type: 'object',
      properties: {
        url: { type: 'string' }
      },
      required: ['url']
    },
    returns: {
      type: 'object',
      properties: {
        status: { type: 'number' },
        error: { type: 'string' }
      },
      required: []
    }
  }
];

async function invoke(tool: string, params: any) {
  if (tool === 'fetch_url') {
    try {
      const res = await fetch(params.url);
      return { status: res.status };
    } catch (err: any) {
      return { error: err.message };
    }
  }
  throw new Error(`Unknown tool ${tool}`);
}

const server: MCPServer = {
  listTools: () => tools,
  listResources: () => [],
  listPrompts: () => [],
  invoke
};

export default server;
