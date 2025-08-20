import { createHash } from 'crypto';
import Ajv, { ValidateFunction } from 'ajv';
import { MCPServer, AuditEntry, NetworkPolicy } from './types.js';
import { Transport } from './transport.js';
import fs from 'fs/promises';
import path from 'path';

const MAX_LOG_SIZE = 5 * 1024 * 1024; // 5MB

/**
 * Wrapper around a remote MCP server accessed via a {@link Transport}.
 * Caches introspection data and performs parameter validation before invoking
 * tools on the remote server.
 */
class RemoteServer implements MCPServer {
  constructor(
    private transport: Transport,
    private cachedTools: any[],
    private cachedResources: any[],
    private cachedPrompts: any[],
    private validators: Map<string, ValidateFunction>
  ) {}

  /** Return the list of tools exposed by the server. */
  listTools() {
    return this.cachedTools;
  }

  /** Return the list of resources exposed by the server. */
  listResources() {
    return this.cachedResources;
  }

  /** Return the list of prompts exposed by the server. */
  listPrompts() {
    return this.cachedPrompts;
  }

  /** Invoke a tool on the remote server after validating its parameters. */
  async invoke(tool: string, params: any) {
    const validator = this.validators.get(tool);
    const args = params ?? {};
    if (validator && !validator(args)) {
      return { error: 'ValidationError', details: validator.errors };
    }
    return this.transport.request('invoke', { tool, params: args });
  }
}

/**
 * Client that connects to MCP servers via JSON-RPC transports.
 *
 * The client manages multiple remote servers, enforces network policies and
 * records an audit log of all invocations.
 */
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

  /**
   * Register a new remote server with the client.
   *
   * @param name      Unique name of the server
   * @param transport Transport used to communicate with the server
   * @param policy    Optional network policy for the server
   */
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

  /** Return a list of registered server names. */
  listServers() {
    return Array.from(this.servers.keys());
  }

  /** Retrieve a registered server by name. */
  getServer(name: string): MCPServer {
    const server = this.servers.get(name);
    if (!server) throw new Error(`Unknown server ${name}`);
    return server;
  }

  /**
   * Invoke a tool on a registered server while recording an audit trail.
   *
   * @param serverName Name of the registered server
   * @param tool       Tool to invoke
   * @param params     Parameters for the tool
   */
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

  /** Append an invocation entry to the audit log on disk. */
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

  /** Close all active transports. */
  close() {
    for (const transport of this.transports.values()) {
      transport.close();
    }
  }

  /** Set a default network policy applied to all invocations. */
  setDefaultPolicy(policy?: NetworkPolicy) {
    MCPClient.defaultPolicy = policy;
  }

  /**
   * Patch the global {@link fetch} function to enforce active network policies.
   * The patch is applied only once for all client instances.
   */
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
