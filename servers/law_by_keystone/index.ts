import { promises as fs } from 'fs';
import path from 'path';
import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

const baseDir = path.resolve(process.env.MCP_FS_BASE_DIR || './mcp_fs');
await fs.mkdir(baseDir, { recursive: true });

const tools: ToolSchema[] = [
  {
    name: 'generate_legal_summary',
    description: 'Generate a stub legal research summary and export it',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        output_format: { enum: ['md', 'json', 'html'], default: 'md' },
        output_path: { type: 'string' }
      },
      required: ['query', 'output_path']
    },
    returns: {
      type: 'object',
      properties: { status: { enum: ['exported'] }, path: { type: 'string' } },
      required: ['status', 'path']
    }
  }
];

const resources: ResourceSchema[] = [
  { uri: 'law:last_summary', description: 'Last legal summary generated' }
];

const prompts: PromptSchema[] = [
  { name: 'legal_research_template', template: 'Research the following query: {{query}}' }
];

function ensureDir(p: string) {
  const full = path.resolve(baseDir, p);
  if (!full.startsWith(baseDir)) throw new Error('path outside allowed directory');
  return full;
}

async function invoke(tool: string, params: any) {
  if (tool !== 'generate_legal_summary') throw new Error(`Unknown tool ${tool}`);
  const { query, output_format = 'md', output_path } = params;
  const summary = {
    query,
    results: [{ title: 'Example Case', summary: 'No real data fetched' }]
  };
  let content: string;
  let ext: string;
  if (output_format === 'md') {
    content = `# Research Summary\n\nQuery: ${query}\n`;
    ext = 'md';
  } else if (output_format === 'json') {
    content = JSON.stringify(summary, null, 2);
    ext = 'json';
  } else {
    content = `<html><body><h1>Research Summary</h1><p>Query: ${query}</p></body></html>`;
    ext = 'html';
  }
  const dir = ensureDir(output_path);
  await fs.mkdir(dir, { recursive: true });
  const filePath = path.join(dir, `summary.${ext}`);
  await fs.writeFile(filePath, content);
  return { status: 'exported', path: filePath };
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
