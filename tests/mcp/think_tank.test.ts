import test from 'node:test';
import assert from 'node:assert/strict';
import { MCPClient } from '../../src/mcp/client.js';
import { loadRegistry } from '../../src/mcp/registry.js';
import path from 'path';

async function setup() {
  const client = new MCPClient();
  await loadRegistry(path.resolve('config/mcp.registry.json'), client);
  return client;
}

test('think tank returns structured analysis', async () => {
  process.env.THINK_TANK_MODEL_RESPONSE = JSON.stringify({
    summary: 'test',
    analysis: {
      goal: 'world peace',
      executive: { tasks: [] },
      research: { summary: '', sources: [] },
      devils_advocate: { concerns: [] },
      argument: { points: [] },
      communications: { message: '', audience: '' },
      visualizer: { description: '', data: { type: '', labels: [], values: [] } }
    }
  });
  const client = await setup();
  try {
    const res = await client.invoke('think_tank', 'analyze_goal', { goal: 'world peace' });
    assert.equal(res.analysis.goal, 'world peace');
    assert.ok(res.summary);
  } finally {
    client.close();
  }
});
