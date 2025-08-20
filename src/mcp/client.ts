import { createHash } from 'crypto';
import Ajv, { ValidateFunction } from 'ajv';
import { MCPServer, AuditEntry, NetworkPolicy } from './types.js';
import { Transport } from './transport.js';
import fs from 'fs/promises';
import path from 'path';

const MAX_LOG_SIZE = 5 * 1024 * 1024; // 5MB

/**
 * Wrapper around a remote MCP server accessed via a {@link Transport}.
 * Caches capability lists and validates parameters before dispatching requests.
 */
class RemoteServer implements MCPServer {
  constructor(
    private transport: Transport,
    private cachedTools: any[],
    private cachedResources: any[],
    private cachedPrompts: any[],
    private validators: Map<string, ValidateFunction>
  ) {}

  /**
   * Return cached tool definitions from the server.
   * @returns Array of tool schemas
   */
  listTools() {
    return this.cachedTools;
  }

  /**
   * Return cached resource definitions from the server.
   * @returns Array of resource schemas
   */
  listResources() {
    return this.cachedResources;
  }

  /**
   * Return cached prompt templates from the server.
   * @returns Array of prompt schemas
   */
  listPrompts() {
    return this.cachedPrompts;
  }

  /**
   * Invoke a remote tool after validating parameters.
   * @param tool   Tool name to execute
   * @param params Parameter object to validate and forward
   * @returns Result from the remote server or validation error object
   */
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
 * Maintains per-server network policies and an audit log of invocations.
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
   * Register a remote server with the client and cache its capabilities.
   * @param name      Logical name of the server
   * @param transport Transport used for communication
   * @param policy    Optional network policy for requests through this server
   * @sideeffect Adds the server to internal maps and may start background processes
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

  /**
   * List the names of all registered servers.
   * @returns Array of server identifiers
   */
  listServers() {
    return Array.from(this.servers.keys());
  }

  /**
   * Retrieve a previously registered server by name.
   * @param name Server identifier
   * @returns {@link MCPServer} instance
   */
  getServer(name: string): MCPServer {
    const server = this.servers.get(name);
    if (!server) throw new Error(`Unknown server ${name}`);
    return server;
  }

  /**
   * Invoke a tool on a registered server while applying network policies
   * and recording an audit entry.
   * @param serverName Server identifier
   * @param tool       Tool to execute
   * @param params     Parameters supplied to the tool
   * @returns Result from the remote invocation
   * @sideeffect Writes to audit log and may modify files referenced by `params`
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

  /**
   * Append an entry to the persistent audit log.
   * @param entry Audit information to record
   * @sideeffect Writes to the file system under `logs/`
   */
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

  /**
   * Close all registered transports and release their resources.
   * @sideeffect Terminates network connections or child processes
   */
  async close() {
    await Promise.all(
      Array.from(this.transports.values(), t => t.close()),
    );
  }

  /**
   * Set the default network policy applied when invoking servers without a specific policy.
   * @param policy Network policy to enforce
   */
  setDefaultPolicy(policy?: NetworkPolicy) {
    MCPClient.defaultPolicy = policy;
  }

  /**
   * Patch the global `fetch` function to enforce active network policies.
   * The patch is applied only once per process.
   * @sideeffect Overrides the global `fetch`
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
