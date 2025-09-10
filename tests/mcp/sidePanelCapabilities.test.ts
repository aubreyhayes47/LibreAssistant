import test from 'node:test';
import assert from 'node:assert/strict';

// Mock server class to simulate MCP server behavior
class MockServer {
  private name: string;
  private tools: string[];
  private prompts: { name: string; template: string }[];
  private consent: boolean;

  constructor(name: string, tools: string[] = [], prompts: { name: string; template: string }[] = [], consent: boolean = true) {
    this.name = name;
    this.tools = tools;
    this.prompts = prompts;
    this.consent = consent;
  }

  getName() { return this.name; }
  getTools() { return this.tools; }
  getPrompts() { return this.prompts; }
  hasConsent() { return this.consent; }
  setConsent(consent: boolean) { this.consent = consent; }
}

// Mock side panel server registry
class MockSidePanelRegistry {
  private servers: MockServer[] = [];

  addServer(server: MockServer) {
    this.servers.push(server);
  }

  discoverServers() {
    // Simulate the /api/v1/mcp/servers endpoint
    return {
      servers: this.servers.map(s => ({
        name: s.getName(),
        consent: s.hasConsent(),
        tools: s.getTools(),
        prompts: s.getPrompts()
      }))
    };
  }

  getConsentedServers() {
    return this.servers.filter(s => s.hasConsent());
  }

  expandTools() {
    // Simulate tool expansion from consented servers (like switchboard.js loadPlugins)
    const tools: string[] = [];
    this.getConsentedServers().forEach(server => {
      server.getTools().forEach(tool => {
        tools.push(`${server.getName()}.${tool}`);
      });
    });
    return tools;
  }

  expandPrompts() {
    // Simulate prompt template expansion
    const prompts: { name: string; template: string; server: string }[] = [];
    this.getConsentedServers().forEach(server => {
      server.getPrompts().forEach(prompt => {
        prompts.push({
          name: `${server.getName()}.${prompt.name}`,
          template: prompt.template,
          server: server.getName()
        });
      });
    });
    return prompts;
  }

  updateConsent(serverName: string, consent: boolean) {
    // Simulate the /api/v1/mcp/consent/{server} endpoint
    const server = this.servers.find(s => s.getName() === serverName);
    if (server) {
      server.setConsent(consent);
      return true;
    }
    return false;
  }
}

test('side panel server discovery enumerates tools from multiple servers', async () => {
  const registry = new MockSidePanelRegistry();
  
  // Add servers with various tool configurations
  registry.addServer(new MockServer('file-manager', ['read_file', 'write_file', 'list_directory'], [], true));
  registry.addServer(new MockServer('data-analyzer', ['analyze_csv', 'generate_chart', 'export_data'], [], true));
  registry.addServer(new MockServer('web-scraper', ['scrape_url', 'extract_links'], [], false)); // no consent

  // Test server discovery
  const discovery = registry.discoverServers();
  assert.equal(discovery.servers.length, 3);

  // Test tool expansion (only from consented servers)
  const expandedTools = registry.expandTools();
  assert.deepEqual(expandedTools.sort(), [
    'data-analyzer.analyze_csv',
    'data-analyzer.export_data',
    'data-analyzer.generate_chart',
    'file-manager.list_directory',
    'file-manager.read_file',
    'file-manager.write_file'
  ]);

  // Verify non-consented server tools are not included
  assert(!expandedTools.some(tool => tool.startsWith('web-scraper')));
});

test('side panel server discovery handles prompt templates', async () => {
  const registry = new MockSidePanelRegistry();
  
  // Add servers with prompt templates
  registry.addServer(new MockServer(
    'template-provider',
    ['analyze'],
    [
      { name: 'code_review', template: 'Review this code:\n{{code}}\n\nFocus on: {{focus_areas}}' },
      { name: 'data_analysis', template: 'Analyze the following data:\n{{data}}\n\nProvide insights on: {{analysis_type}}' }
    ],
    true
  ));
  
  registry.addServer(new MockServer(
    'report-generator',
    ['generate_report'],
    [
      { name: 'summary_template', template: 'Summary: {{content}}' },
      { name: 'detailed_template', template: 'Detailed analysis: {{details}}' }
    ],
    true
  ));

  // Test prompt template expansion
  const expandedPrompts = registry.expandPrompts();
  assert.equal(expandedPrompts.length, 4);
  
  // Check specific templates
  const codeReviewPrompt = expandedPrompts.find(p => p.name === 'template-provider.code_review');
  assert(codeReviewPrompt);
  assert.equal(codeReviewPrompt.template, 'Review this code:\n{{code}}\n\nFocus on: {{focus_areas}}');
  assert.equal(codeReviewPrompt.server, 'template-provider');

  const summaryPrompt = expandedPrompts.find(p => p.name === 'report-generator.summary_template');
  assert(summaryPrompt);
  assert.equal(summaryPrompt.template, 'Summary: {{content}}');
  assert.equal(summaryPrompt.server, 'report-generator');
});

test('side panel server discovery respects consent changes', async () => {
  const registry = new MockSidePanelRegistry();
  
  registry.addServer(new MockServer('server1', ['tool1'], [], false)); // initially no consent
  registry.addServer(new MockServer('server2', ['tool2'], [], true));  // initially consented

  // Initially only server2 tools should be available
  let expandedTools = registry.expandTools();
  assert.deepEqual(expandedTools, ['server2.tool2']);

  // Grant consent to server1
  registry.updateConsent('server1', true);
  expandedTools = registry.expandTools();
  assert.deepEqual(expandedTools.sort(), ['server1.tool1', 'server2.tool2']);

  // Revoke consent from server2
  registry.updateConsent('server2', false);
  expandedTools = registry.expandTools();
  assert.deepEqual(expandedTools, ['server1.tool1']);

  // Verify discovery still shows all servers but with correct consent status
  const discovery = registry.discoverServers();
  assert.equal(discovery.servers.length, 2);
  assert.equal(discovery.servers.find(s => s.name === 'server1')?.consent, true);
  assert.equal(discovery.servers.find(s => s.name === 'server2')?.consent, false);
});

test('side panel handles servers with mixed capabilities', async () => {
  const registry = new MockSidePanelRegistry();
  
  // Server with tools only
  registry.addServer(new MockServer('tools-only', ['file_read', 'file_write'], [], true));
  
  // Server with prompts only  
  registry.addServer(new MockServer('prompts-only', [], [
    { name: 'analysis', template: 'Analyze: {{input}}' }
  ], true));
  
  // Server with both tools and prompts
  registry.addServer(new MockServer('mixed-server', ['process'], [
    { name: 'report', template: 'Report: {{data}}' }
  ], true));
  
  // Server with neither (edge case)
  registry.addServer(new MockServer('empty-server', [], [], true));

  // Test discovery includes all servers
  const discovery = registry.discoverServers();
  assert.equal(discovery.servers.length, 4);

  // Test tool expansion
  const tools = registry.expandTools();
  assert.deepEqual(tools.sort(), ['mixed-server.process', 'tools-only.file_read', 'tools-only.file_write']);

  // Test prompt expansion
  const prompts = registry.expandPrompts();
  assert.equal(prompts.length, 2);
  assert(prompts.some(p => p.name === 'prompts-only.analysis'));
  assert(prompts.some(p => p.name === 'mixed-server.report'));
});

test('side panel server discovery handles error scenarios gracefully', async () => {
  const registry = new MockSidePanelRegistry();
  
  // Test with no servers (empty registry)
  let discovery = registry.discoverServers();
  assert.equal(discovery.servers.length, 0);
  assert.equal(registry.expandTools().length, 0);
  assert.equal(registry.expandPrompts().length, 0);

  // Test consent update for non-existent server
  const result = registry.updateConsent('non-existent', true);
  assert.equal(result, false);

  // Add servers and test normal operation
  registry.addServer(new MockServer('test-server', ['test_tool'], [
    { name: 'test_prompt', template: 'Test: {{input}}' }
  ], true));

  discovery = registry.discoverServers();
  assert.equal(discovery.servers.length, 1);
  assert.equal(registry.expandTools().length, 1);
  assert.equal(registry.expandPrompts().length, 1);
});

test('side panel tool invocation flow after discovery', async () => {
  const registry = new MockSidePanelRegistry();
  
  // Add servers similar to switchboard.js usage pattern
  registry.addServer(new MockServer('file-ops', ['read', 'write', 'delete'], [], true));
  registry.addServer(new MockServer('api-client', ['get', 'post'], [], true));
  
  // Simulate the switchboard dropdown population
  const tools = registry.expandTools();
  const toolOptions = [''].concat(tools); // Include "No plugin" option like switchboard.js
  
  assert.equal(toolOptions.length, 6); // '' + 5 tools
  assert.equal(toolOptions[0], ''); // No plugin option
  assert(toolOptions.includes('file-ops.read'));
  assert(toolOptions.includes('file-ops.write'));
  assert(toolOptions.includes('api-client.get'));
  
  // Simulate tool selection and invocation preparation
  const selectedTool = 'file-ops.read';
  const [serverName, toolName] = selectedTool.split('.');
  
  assert.equal(serverName, 'file-ops');
  assert.equal(toolName, 'read');
  
  // Verify the selected tool comes from a consented server
  const consentedServers = registry.getConsentedServers();
  const targetServer = consentedServers.find(s => s.getName() === serverName);
  assert(targetServer);
  assert(targetServer.getTools().includes(toolName));
});