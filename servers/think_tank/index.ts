import { MCPServer, ToolSchema, ResourceSchema, PromptSchema } from '../../src/mcp/types.js';
import { serveStdio } from '../../src/mcp/transport.js';
import { fileURLToPath } from 'url';

// -----------------------------------------------------------------------------
// Helper that interacts with a language model.  During unit tests the
// environment variable ``THINK_TANK_MODEL_RESPONSE`` provides a canned JSON
// response allowing the logic to run without external network calls.  When the
// variable is unset we attempt to use the OpenAI client.  The call is lazily
// imported so the dependency is optional.

async function callModel(prompt: string): Promise<any> {
  const mock = process.env.THINK_TANK_MODEL_RESPONSE;
  if (mock) {
    return JSON.parse(mock);
  }

  const mod: any = await (eval('import'))('openai');
  const client = new mod.OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const completion = await client.chat.completions.create({
    model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
    messages: [{ role: 'user', content: prompt }],
  });
  const text = completion.choices[0].message?.content || '{}';
  return JSON.parse(text);
}

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
            executive: {
              type: 'object',
              properties: {
                tasks: { type: 'array', items: { type: 'string' } }
              },
              required: ['tasks']
            },
            research: {
              type: 'object',
              properties: {
                summary: { type: 'string' },
                sources: { type: 'array', items: { type: 'string' } }
              },
              required: ['summary', 'sources']
            },
            devils_advocate: {
              type: 'object',
              properties: {
                concerns: { type: 'array', items: { type: 'string' } }
              },
              required: ['concerns']
            },
            argument: {
              type: 'object',
              properties: {
                points: { type: 'array', items: { type: 'string' } }
              },
              required: ['points']
            },
            communications: {
              type: 'object',
              properties: {
                message: { type: 'string' },
                audience: { type: 'string' }
              },
              required: ['message', 'audience']
            },
            visualizer: {
              type: 'object',
              properties: {
                description: { type: 'string' },
                data: {
                  type: 'object',
                  properties: {
                    type: { type: 'string' },
                    labels: { type: 'array', items: { type: 'string' } },
                    values: { type: 'array', items: { type: 'number' } }
                  },
                  required: ['type', 'labels', 'values']
                }
              },
              required: ['description', 'data']
            }
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
  const prompt = `You are a multidisciplinary think tank. Provide a JSON object with the following structure:
{
  "summary": string,
  "analysis": {
    "goal": string,
    "executive": {"tasks": string[]},
    "research": {"summary": string, "sources": string[]},
    "devils_advocate": {"concerns": string[]},
    "argument": {"points": string[]},
    "communications": {"message": string, "audience": string},
    "visualizer": {"description": string, "data": {"type": string, "labels": string[], "values": number[]}}
  }
}
Analyze the goal: ${goal}`;
  const result = await callModel(prompt);
  lastDossier = result;
  return result;
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
