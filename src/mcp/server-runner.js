/**
 * Helper script that boots a module exporting an MCP server and exposes it
 * over stdio using the {@link serveStdio} transport. Network policy restrictions
 * are enforced based on environment variables before the server is started.
 */
import { serveStdio } from './transport.ts';
import { fileURLToPath, pathToFileURL } from 'url';
import path from 'path';

const modArg = process.argv[2];
if (!modArg) {
  console.error('No module provided');
  process.exit(1);
}
const modulePath = path.resolve(modArg);

/**
 * Patch the global {@link fetch} to enforce network policies specified via
 * environment variables. This mirrors the client's network policy logic when
 * executing within the server process.
 */
function applyPolicy() {
  const allow = (process.env.MCP_ALLOW_HOSTS || '').split(',').filter(Boolean);
  const deny = (process.env.MCP_DENY_HOSTS || '').split(',').filter(Boolean);
  const protocols = (process.env.MCP_ALLOW_PROTOCOLS || '').split(',').filter(Boolean);
  if (!allow.length && !deny.length && !protocols.length) return;
  const original = globalThis.fetch.bind(globalThis);
  globalThis.fetch = async function (input, init) {
    const href =
      typeof input === 'string'
        ? input
        : input instanceof URL
        ? input.href
        : input.url;
    const url = new URL(href);
    if (url.protocol === 'file:' || url.protocol === 'node:' || url.protocol === 'data:') {
      return original(input, init);
    }
    if (allow.length && !allow.includes(url.hostname)) {
      return Promise.reject(new Error(`Host ${url.hostname} not allowed`));
    }
    if (deny.includes(url.hostname)) {
      return Promise.reject(new Error(`Host ${url.hostname} denied`));
    }
    if (protocols.length && !protocols.includes(url.protocol.replace(':', ''))) {
      return Promise.reject(new Error(`Protocol ${url.protocol} not allowed`));
    }
    return original(input, init);
  };
}

applyPolicy();

const mod = await import(pathToFileURL(modulePath).href);
const server = mod.default;
serveStdio(server);
