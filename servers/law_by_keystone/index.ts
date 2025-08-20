import { promises as fs } from 'fs';
import path from 'path';
import {
  MCPServer,
  ToolSchema,
  ResourceSchema,
  PromptSchema,
} from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

const baseDir = path.resolve(process.env.MCP_FS_BASE_DIR || './mcp_fs');
await fs.mkdir(baseDir, { recursive: true });

const SOURCES = [
  'govinfo',
  'ecfr',
  'courtlistener',
  'openstates',
  'govtrack',
] as const;

type Source = (typeof SOURCES)[number];

const tools: ToolSchema[] = [
  {
    name: 'generate_legal_summary',
    description:
      'Fetch legal information from government APIs and export it',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        source: { enum: SOURCES, default: 'govinfo' },
        output_format: {
          enum: ['md', 'json', 'html', 'txt', 'xml'],
          default: 'md',
        },
        output_path: { type: 'string' },
      },
      required: ['query', 'output_path'],
    },
    returns: {
      type: 'object',
      properties: {
        status: { enum: ['exported'] },
        path: { type: 'string' },
        sources: { type: 'array', items: { type: 'string' } },
        metadata: { type: 'object' },
      },
      required: ['status', 'path', 'sources', 'metadata'],
    },
  },
];

const resources: ResourceSchema[] = [
  { uri: 'law:last_summary', description: 'Last legal summary generated' },
];

const prompts: PromptSchema[] = [
  {
    name: 'legal_research_template',
    template: 'Research the following query: {{query}}',
  },
];

function ensureDir(p: string) {
  const full = path.resolve(baseDir, p);
  if (!full.startsWith(baseDir)) throw new Error('path outside allowed directory');
  return full;
}

function escapeXml(str: string) {
  return str.replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]!));
}

function escapeHtml(str: string) {
  return str.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]!));
}

async function fetchApi(source: Source, query: string) {
  const govinfoKey = process.env.GOVINFO_API_KEY || 'DEMO_KEY';
  const openStatesKey = process.env.OPENSTATES_API_KEY || 'DEMO_KEY';
  const encoded = encodeURIComponent(query);
  try {
    switch (source) {
      case 'govinfo':
        return await fetch(
          `https://api.govinfo.gov/search?q=${encoded}&pageSize=5&api_key=${govinfoKey}`,
        ).then((r) => r.json());
      case 'ecfr':
        return await fetch(
          `https://api.ecfr.gov/v1/search?query=${encoded}`,
        ).then((r) => r.json());
      case 'courtlistener':
        return await fetch(
          `https://www.courtlistener.com/api/rest/v3/search/?q=${encoded}`,
        ).then((r) => r.json());
      case 'openstates':
        return await fetch(
          `https://v3.openstates.org/bills?search=${encoded}`,
          { headers: { 'X-API-KEY': openStatesKey } },
        ).then((r) => r.json());
      case 'govtrack':
        return await fetch(
          `https://www.govtrack.us/api/v2/bill?query=${encoded}`,
        ).then((r) => r.json());
    }
  } catch (err: any) {
    return { error: err.message };
  }
}

function formatContent(
  data: any,
  format: string,
  meta: { query: string; source: string },
) {
  const json = { query: meta.query, source: meta.source, data };
  switch (format) {
    case 'json':
      return { content: JSON.stringify(json, null, 2), ext: 'json' };
    case 'html':
      return {
        content: `<html><body><pre>${escapeHtml(
          JSON.stringify(json, null, 2),
        )}</pre></body></html>`,
        ext: 'html',
      };
    case 'txt':
      return {
        content: `Source: ${meta.source}\nQuery: ${meta.query}\n${JSON.stringify(
          data,
          null,
          2,
        )}`,
        ext: 'txt',
      };
    case 'xml':
      return {
        content: `<results><source>${meta.source}</source><query>${escapeXml(
          meta.query,
        )}</query><data>${escapeXml(JSON.stringify(data))}</data></results>`,
        ext: 'xml',
      };
    default:
      return {
        content:
          `# ${meta.source} results\n\n` +
          `Query: ${meta.query}\n\n` +
          '```json\n' +
          JSON.stringify(data, null, 2) +
          '\n```\n',
        ext: 'md',
      };
  }
}

async function invoke(tool: string, params: any) {
  if (tool !== 'generate_legal_summary')
    throw new Error(`Unknown tool ${tool}`);
  const { query, source = 'govinfo', output_format = 'md', output_path } =
    params;
  const data = await fetchApi(source as Source, query);
  const metadata = {
    query,
    source,
    format: output_format,
    resultCount:
      Array.isArray((data as any)?.results)
        ? (data as any).results.length
        : (data as any)?.count,
  };
  const { content, ext } = formatContent(data, output_format, {
    query,
    source,
  });
  const dir = ensureDir(output_path);
  await fs.mkdir(dir, { recursive: true });
  const filePath = path.join(dir, `summary.${ext}`);
  await fs.writeFile(filePath, content);
  return { status: 'exported', path: filePath, sources: [source], metadata };
}

const server: MCPServer = {
  listTools: () => tools,
  listResources: () => resources,
  listPrompts: () => prompts,
  invoke,
};

export default server;

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  serveStdio(server);
}

