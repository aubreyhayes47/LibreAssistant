// Copyright (c) 2024 LibreAssistant contributors.
// Licensed under the MIT License.

/**
 * Schema describing an executable tool exposed by an MCP server.
 * Parameters and return values follow JSON Schema definitions.
 */
export interface ToolSchema {
  /** Name of the tool as invoked by clients */
  name: string;
  /** Human readable description of the tool's behavior */
  description: string;
  /** JSON Schema describing the expected parameter object */
  parameters: Record<string, unknown>; // JSON Schema
  /** JSON Schema describing the response object */
  returns: Record<string, unknown>; // JSON Schema
}

/**
 * Schema describing a static resource that can be fetched from a server.
 */
export interface ResourceSchema {
  /** URI that uniquely identifies the resource */
  uri: string;
  /** Human readable description of the resource */
  description: string;
}

/**
 * Schema for a prompt template that can be expanded by the client.
 */
export interface PromptSchema {
  /** Identifier of the prompt */
  name: string;
  /** Template string with handlebars style placeholders */
  template: string;
}

/**
 * Interface implemented by all MCP servers.
 * Each method may perform I/O or network requests depending on the server implementation.
 */
export interface MCPServer {
  /**
   * List tool definitions available on the server.
   * @returns Array of {@link ToolSchema} objects
   */
  listTools(): ToolSchema[];
  /**
   * List available resources on the server.
   * @returns Array of {@link ResourceSchema} objects
   */
  listResources(): ResourceSchema[];
  /**
   * List available prompt templates.
   * @returns Array of {@link PromptSchema} objects
   */
  listPrompts(): PromptSchema[];
  /**
   * Invoke a tool with a parameter object.
   * This may trigger arbitrary side effects depending on the tool implementation.
   * @param tool   Name of the tool to execute
   * @param params Parameters to pass to the tool
   * @returns Result value produced by the tool
   */
  invoke(tool: string, params: any): Promise<any>;
}

/**
 * Entry describing a single tool invocation for auditing purposes.
 */
export interface AuditEntry {
  /** Name of the server hosting the tool */
  server: string;
  /** Invoked tool name */
  tool: string;
  /** Parameter object supplied by the user */
  params: any;
  /** Result returned by the server */
  result: any;
  /** Unix timestamp when the call completed */
  timestamp: number;
  /** Optional hash of a file before invoking the tool */
  beforeHash?: string;
  /** Optional hash of a file after invoking the tool */
  afterHash?: string;
  /** External data sources referenced by the result */
  dataSources?: string[];
}

/**
 * Network access policy restricting where servers may make requests.
 */
export interface NetworkPolicy {
  /** Whitelisted hostnames */
  allow?: string[];
  /** Blacklisted hostnames */
  deny?: string[];
  /** Allowed protocols such as `https` or `http` */
  protocols?: string[];
}
