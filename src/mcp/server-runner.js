// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

/**
 * Bootstraps an MCP server module and exposes it over stdio. This script is
 * used by the registry to spawn servers in isolated processes while enforcing
 * network policies.
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
 * Apply network policy restrictions from environment variables to the global
 * `fetch` implementation. Hosts and protocols not explicitly allowed will
 * cause requests to be rejected.
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
