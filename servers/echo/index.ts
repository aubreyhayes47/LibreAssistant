import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

let lastMessage = '';

const tools: ToolSchema[] = [
  {
    name: 'echo_message',
    description: 'Echoes a message back to the caller',
    parameters: {
      type: 'object',
      properties: {
        message: { type: 'string', default: '' }
      },
      required: []
    },
    returns: {
      type: 'object',
      properties: {
        echo: { type: 'string' }
      },
      required: ['echo']
    }
  }
];

const resources: ResourceSchema[] = [
  { uri: 'echo:last_message', description: 'Last echoed message' }
];

const prompts: PromptSchema[] = [
  { name: 'echo_template', template: 'Repeat: {{message}}' }
];

async function invoke(tool: string, params: any) {
  if (tool === 'echo_message') {
    lastMessage = params?.message ?? '';
    return { echo: lastMessage };
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

// When executed directly, start a JSON-RPC server over stdio
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  serveStdio(server);
}
