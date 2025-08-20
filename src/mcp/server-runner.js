import { serveStdio } from './transport.ts';
import { fileURLToPath, pathToFileURL } from 'url';
import path from 'path';

const modArg = process.argv[2];
if (!modArg) {
  console.error('No module provided');
  process.exit(1);
}
const modulePath = path.resolve(modArg);

const mod = await import(pathToFileURL(modulePath).href);
const server = mod.default;
serveStdio(server);
