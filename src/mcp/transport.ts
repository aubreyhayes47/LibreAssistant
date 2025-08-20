import { spawn, ChildProcess } from 'child_process';
import { MCPServer } from './types.js';

// Basic JSON-RPC message types
interface JSONRPCRequest {
  jsonrpc: '2.0';
  id: number;
  method: string;
  params?: any;
}

interface JSONRPCResponse {
  jsonrpc: '2.0';
  id: number;
  result?: any;
  error?: { code: number; message: string; data?: any };
}

// Transport interface used by the MCP client
export interface Transport {
  request(method: string, params?: any): Promise<any>;
  close(): void;
}

// JSON-RPC over child-process stdio
export class StdioTransport implements Transport {
  private proc: ChildProcess;
  private nextId = 1;
  private pending = new Map<
    number,
    { resolve: (v: any) => void; reject: (err: any) => void }
  >();
  private buffer = '';

  constructor(command: string, args: string[] = []) {
    this.proc = spawn(command, args, { stdio: ['pipe', 'pipe', 'inherit'] });
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

  request(method: string, params?: any): Promise<any> {
    const id = this.nextId++;
    const req: JSONRPCRequest = { jsonrpc: '2.0', id, method, params };
    this.proc.stdin!.write(JSON.stringify(req) + '\n');
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  close() {
    this.proc.kill();
  }
}

// JSON-RPC over simple HTTP POST + optional SSE stream
export class HTTPTransport implements Transport {
  private abort?: AbortController;
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

  close() {
    this.abort?.abort();
  }
}

// Utility to serve an MCPServer over stdio
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

