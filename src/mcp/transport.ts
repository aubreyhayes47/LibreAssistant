import { spawn, ChildProcess } from 'child_process';
import { MCPServer, NetworkPolicy } from './types.js';

/**
 * Basic JSON-RPC request message as exchanged over transports.
 */
interface JSONRPCRequest {
  /** Version string, always `"2.0"` */
  jsonrpc: '2.0';
  /** Sequential identifier for matching responses */
  id: number;
  /** Method name being invoked */
  method: string;
  /** Optional parameters for the method */
  params?: any;
}

/**
 * Basic JSON-RPC response message as exchanged over transports.
 */
interface JSONRPCResponse {
  /** Version string, always `"2.0"` */
  jsonrpc: '2.0';
  /** Identifier of the original request */
  id: number;
  /** Result value when the call succeeds */
  result?: any;
  /** Error information when the call fails */
  error?: { code: number; message: string; data?: any };
}

/**
 * Transport interface used by the MCP client to send JSON-RPC messages.
 */
export interface Transport {
  /**
   * Send a JSON-RPC request and wait for the response.
   * @param method Name of the remote method
   * @param params Optional parameters object
   * @returns JSON result returned by the server
   */
  request(method: string, params?: any): Promise<any>;
  /**
   * Close any underlying resources such as sockets or processes.
   * Implementations should resolve the returned promise once all handles
   * have been fully released so tests can reliably await shutdown.
   */
  close(): Promise<void>;
}

/**
 * JSON-RPC transport implemented over a child process's stdio streams.
 * Spawns a process and proxies JSON-RPC messages to it.
 */
export class StdioTransport implements Transport {
  private proc: ChildProcess;
  private nextId = 1;
  private pending = new Map<
    number,
    { resolve: (v: any) => void; reject: (err: any) => void }
  >();
  private buffer = '';

  /**
   * Create a transport communicating with a child process.
   * @param command Command to spawn
   * @param args Arguments to pass to the command
   * @param policy Network policy passed to the child as environment variables
   * @sideeffect Spawns a new child process
   */
  constructor(command: string, args: string[] = [], policy?: NetworkPolicy) {
    this.proc = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'inherit'],
      env: {
        ...process.env,
        MCP_ALLOW_HOSTS: policy?.allow?.join(',') || '',
        MCP_DENY_HOSTS: policy?.deny?.join(',') || '',
        MCP_ALLOW_PROTOCOLS: policy?.protocols?.join(',') || '',
      },
    });
    this.proc.stdout!.setEncoding('utf8');
    this.proc.stdout!.on('data', chunk => {
      this.buffer += chunk;
      const parts = this.buffer.split('\n');
      this.buffer = parts.pop()!;
      for (const part of parts) {
        if (!part.trim()) continue;
        let msg: JSONRPCResponse;
        try {
          msg = JSON.parse(part);
        } catch {
          continue;
        }
        const pending = this.pending.get(msg.id);
        if (!pending) continue;
        this.pending.delete(msg.id);
        if (msg.error) pending.reject(new Error(msg.error.message));
        else pending.resolve(msg.result);
      }
    });
  }

  /**
   * Send a JSON-RPC request to the child process.
   * @param method Remote method name
   * @param params Optional parameters object
   * @returns JSON result from the child process
   */
  request(method: string, params?: any): Promise<any> {
    const id = this.nextId++;
    const req: JSONRPCRequest = { jsonrpc: '2.0', id, method, params };
    this.proc.stdin!.write(JSON.stringify(req) + '\n');
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  /**
   * Terminate the underlying child process.
   * @sideeffect Kills the spawned process
   */
  async close() {
    return new Promise<void>(resolve => {
      this.proc.once('exit', () => resolve());
      this.proc.kill();
    });
  }
}

/**
 * JSON-RPC transport that communicates with an HTTP endpoint and optional SSE stream.
 */
export class HTTPTransport implements Transport {
  private abort?: AbortController;
  /**
   * Create an HTTP transport.
   * @param endpoint URL accepting JSON-RPC POST requests
   * @param sseEndpoint Optional Server-Sent Events endpoint for notifications
   * @sideeffect Initiates a long-lived fetch when `sseEndpoint` is provided
   */
  constructor(private endpoint: string, private sseEndpoint?: string) {
    if (sseEndpoint) {
      this.abort = new AbortController();
      fetch(sseEndpoint, {
        headers: { Accept: 'text/event-stream' },
        signal: this.abort.signal,
      }).then(async res => {
        // Naive SSE parser for notifications
        const reader = res.body?.getReader();
        if (!reader) return;
        const decoder = new TextDecoder();
        let buf = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split('\n\n');
          buf = parts.pop()!;
          for (const part of parts) {
            const line = part.split('\n').find(l => l.startsWith('data:'));
            if (!line) continue;
            try {
              const msg = JSON.parse(line.slice(5));
              // notifications are ignored for now
            } catch {
              /* ignore */
            }
          }
        }
      });
    }
  }

  /**
   * Send a JSON-RPC request via HTTP POST.
   * @param method Remote method name
   * @param params Optional parameters object
   * @returns Parsed JSON result from the server
   */
  async request(method: string, params?: any): Promise<any> {
    const res = await fetch(this.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
    });
    const json = await res.json();
    if (json.error) throw new Error(json.error.message);
    return json.result;
  }

  /**
   * Abort any outstanding SSE connection.
   * @sideeffect Cancels network requests
   */
  async close() {
    this.abort?.abort();
    return Promise.resolve();
  }
}

/**
 * Utility helper to expose an {@link MCPServer} over the current process's stdio.
 * @param server MCP server implementation to expose
 * @sideeffect Reads from stdin and writes JSON-RPC responses to stdout
 */
export function serveStdio(server: MCPServer) {
  process.stdin.setEncoding('utf8');
  let buffer = '';
  process.stdin.on('data', chunk => {
    buffer += chunk;
    const parts = buffer.split('\n');
    buffer = parts.pop()!;
    for (const part of parts) {
      if (!part.trim()) continue;
      let req: JSONRPCRequest;
      try {
        req = JSON.parse(part);
      } catch {
        continue;
      }
      handle(req);
    }
  });

  async function handle(req: JSONRPCRequest) {
    try {
      let result;
      switch (req.method) {
        case 'listTools':
          result = server.listTools();
          break;
        case 'listResources':
          result = server.listResources();
          break;
        case 'listPrompts':
          result = server.listPrompts();
          break;
        case 'invoke':
          result = await server.invoke(req.params.tool, req.params.params ?? req.params);
          break;
        default:
          throw new Error(`Unknown method ${req.method}`);
      }
      const res: JSONRPCResponse = { jsonrpc: '2.0', id: req.id, result };
      process.stdout.write(JSON.stringify(res) + '\n');
    } catch (err: any) {
      const res: JSONRPCResponse = {
        jsonrpc: '2.0',
        id: req.id,
        error: { code: -32000, message: err.message },
      };
      process.stdout.write(JSON.stringify(res) + '\n');
    }
  }
}

