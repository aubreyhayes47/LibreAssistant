import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

let lastDossier: any = null;

const tools: ToolSchema[] = [
  {
    name: 'analyze_goal',
    description: 'Generate a structured analysis of a goal',
    parameters: {
      type: 'object',
      properties: { goal: { type: 'string' } },
      required: ['goal']
    },
    returns: {
      type: 'object',
      properties: {
        summary: { type: 'string' },
        analysis: {
          type: 'object',
          properties: {
            goal: { type: 'string' },
            executive: { type: 'string' },
            research: { type: 'string' },
            devils_advocate: { type: 'string' },
            argument: { type: 'string' },
            communications: { type: 'string' },
            visualizer: { type: 'string' }
          },
          required: [
            'goal',
            'executive',
            'research',
            'devils_advocate',
            'argument',
            'communications',
            'visualizer'
          ]
        }
      },
      required: ['summary', 'analysis']
    }
  }
];

const resources: ResourceSchema[] = [
  { uri: 'thinktank:last_dossier', description: 'Latest analysis generated' }
];

const prompts: PromptSchema[] = [
  { name: 'thinktank_question_template', template: 'Consider the goal: {{goal}}' }
];

async function invoke(tool: string, params: any) {
  if (tool !== 'analyze_goal') throw new Error(`Unknown tool ${tool}`);
  const goal = params.goal;
  const analysis = {
    goal,
    executive: `Breakdown of '${goal}' into manageable tasks.`,
    research: `Research findings for '${goal}' (stub).`,
    devils_advocate: `Potential issues with pursuing '${goal}'.`,
    argument: `Supporting arguments for '${goal}'.`,
    communications: `Clear and concise explanation of '${goal}'.`,
    visualizer: 'Visualization not implemented in stub.'
  };
  const summary = [
    analysis.communications,
    `Argument: ${analysis.argument}`,
    `Caveats: ${analysis.devils_advocate}`
  ].join('\n');
  lastDossier = { summary, analysis };
  return lastDossier;
}

const server: MCPServer = {
  listTools: () => tools,
  listResources: () => resources,
  listPrompts: () => prompts,
  invoke
};

export default server;

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  serveStdio(server);
}
