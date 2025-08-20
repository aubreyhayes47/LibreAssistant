// Basic types for Model Context Protocol objects
export interface ToolSchema {
  name: string;
  description: string;
  parameters: Record<string, unknown>; // JSON Schema
  returns: Record<string, unknown>; // JSON Schema
}

export interface ResourceSchema {
  uri: string;
  description: string;
}

export interface PromptSchema {
  name: string;
  template: string;
}

export interface MCPServer {
  listTools(): ToolSchema[];
  listResources(): ResourceSchema[];
  listPrompts(): PromptSchema[];
  invoke(tool: string, params: any): Promise<any>;
}

export interface AuditEntry {
  server: string;
  tool: string;
  params: any;
  result: any;
  timestamp: number;
  beforeHash?: string;
  afterHash?: string;
  dataSources?: string[];
}

export interface NetworkPolicy {
  allow?: string[];
  deny?: string[];
  protocols?: string[];
}
