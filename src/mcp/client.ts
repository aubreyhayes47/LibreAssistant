import { createHash } from 'crypto';
import Ajv, { ValidateFunction } from 'ajv';
import { MCPServer, AuditEntry, NetworkPolicy } from './types.js';
import { Transport } from './transport.js';
import fs from 'fs/promises';
import path from 'path';

const MAX_LOG_SIZE = 5 * 1024 * 1024; // 5MB

// Wrapper around a remote MCP server accessed via a Transport.
class RemoteServer implements MCPServer {
  constructor(
    private transport: Transport,
    private cachedTools: any[],
    private cachedResources: any[],
    private cachedPrompts: any[],
    private validators: Map<string, ValidateFunction>
  ) {}

  listTools() {
    return this.cachedTools;
  }

  listResources() {
    return this.cachedResources;
  }

  listPrompts() {
    return this.cachedPrompts;
  }

  async invoke(tool: string, params: any) {
    const validator = this.validators.get(tool);
    const args = params ?? {};
    if (validator && !validator(args)) {
      return { error: 'ValidationError', details: validator.errors };
    }
    return this.transport.request('invoke', { tool, params: args });
  }
}

// Client that connects to MCP servers via JSON-RPC transports.
export class MCPClient {
  private servers: Map<string, RemoteServer> = new Map();
  private transports: Map<string, Transport> = new Map();
  private policies: Map<string, NetworkPolicy> = new Map();
  public auditLog: AuditEntry[] = [];
  private ajv = new Ajv({ useDefaults: true });
  private static defaultPolicy?: NetworkPolicy;
  private static activePolicy?: NetworkPolicy;
  private static fetchPatched = false;
  private logPath = path.resolve('logs/audit.ndjson');

  constructor() {
    MCPClient.patchFetch();
  }

  async register(name: string, transport: Transport, policy?: NetworkPolicy) {
    const tools = await transport.request('listTools');
    const resources = await transport.request('listResources');
    const prompts = await transport.request('listPrompts');
    const validators = new Map<string, ValidateFunction>();
    for (const t of tools) {
      if (t.parameters) {
        validators.set(t.name, this.ajv.compile(t.parameters));
      }
    }
    const server = new RemoteServer(transport, tools, resources, prompts, validators);
    this.servers.set(name, server);
    this.transports.set(name, transport);
    if (policy) this.policies.set(name, policy);
  }

  listServers() {
    return Array.from(this.servers.keys());
  }

  getServer(name: string): MCPServer {
    const server = this.servers.get(name);
    if (!server) throw new Error(`Unknown server ${name}`);
    return server;
  }

  async invoke(serverName: string, tool: string, params: any) {
    const server = this.getServer(serverName);
    let beforeHash: string | undefined;
    let afterHash: string | undefined;

    // For file operations we capture before/after hashes if path provided
    if (params && params.path && typeof params.path === 'string') {
      try {
        const before = await import('fs/promises').then(fs => fs.readFile(params.path));
        beforeHash = createHash('sha256').update(before).digest('hex');
      } catch {
        // ignore if file doesn't exist
      }
    }

    const prev = MCPClient.activePolicy;
    MCPClient.activePolicy = this.policies.get(serverName) || MCPClient.defaultPolicy;
    const result = await server.invoke(tool, params);
    MCPClient.activePolicy = prev;

    if (params && params.path && typeof params.path === 'string') {
      try {
        const after = await import('fs/promises').then(fs => fs.readFile(params.path));
        afterHash = createHash('sha256').update(after).digest('hex');
      } catch {
        // ignore
      }
    }

    const sources = Array.isArray(result?.sources)
      ? result.sources
      : Array.isArray(result?.metadata?.sources)
      ? result.metadata.sources
      : undefined;
    const entry: AuditEntry = {
      server: serverName,
      tool,
      params,
      result,
      timestamp: Date.now(),
      beforeHash,
      afterHash,
      dataSources: sources,
    };
    this.auditLog.push(entry);
    await this.appendAudit(entry);
    return result;
  }

  private async appendAudit(entry: AuditEntry) {
    try {
      await fs.mkdir(path.dirname(this.logPath), { recursive: true });
      try {
        const stats = await fs.stat(this.logPath);
        if (stats.size > MAX_LOG_SIZE) {
          await fs.rename(this.logPath, this.logPath + '.1');
        }
      } catch {
        // file doesn't exist yet
      }
      await fs.appendFile(this.logPath, JSON.stringify(entry) + '\n');
    } catch (err) {
      console.error('Failed to write audit log', err);
    }
  }

  close() {
    for (const transport of this.transports.values()) {
      transport.close();
    }
  }

  setDefaultPolicy(policy?: NetworkPolicy) {
    MCPClient.defaultPolicy = policy;
  }

  private static patchFetch() {
    if (MCPClient.fetchPatched) return;
    const original = globalThis.fetch.bind(globalThis);
    globalThis.fetch = async function (input: any, init?: any) {
      const href =
        typeof input === 'string'
          ? input
          : input instanceof URL
          ? input.href
          : input.url;
      const url = new URL(href);
      if (url.protocol === 'file:' || url.protocol === 'node:' || url.protocol === 'data:') {
        return original(input as any, init);
      }
      const policy = MCPClient.activePolicy || MCPClient.defaultPolicy;
      if (policy) {
        if (policy.allow && policy.allow.length && !policy.allow.includes(url.hostname)) {
          return Promise.reject(new Error(`Host ${url.hostname} not allowed`));
        }
        if (policy.deny && policy.deny.includes(url.hostname)) {
          return Promise.reject(new Error(`Host ${url.hostname} denied`));
        }
        if (policy.protocols && policy.protocols.length && !policy.protocols.includes(url.protocol.replace(':', ''))) {
          return Promise.reject(new Error(`Protocol ${url.protocol} not allowed`));
        }
      }
      return original(input as any, init);
    } as any;
    MCPClient.fetchPatched = true;
  }
}
