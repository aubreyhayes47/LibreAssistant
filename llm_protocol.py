"""
llm_protocol.py: JSON schema-based LLM communication protocol for LibreAssistant
- Enforces structured responses from LLM for deterministic parsing
- Handles routing between plugin invocations and user-facing messages
- Generates system instructions that expose available plugins to the LLM
"""

import json
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from jsonschema import validate, ValidationError

# Path to the LLM response schema
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "llm-response.schema.json")

class LLMProtocolError(Exception):
    """Exception raised for LLM protocol-related errors"""
    def __init__(self, message: str, error_type: str = "general", invalid_output: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.error_type = error_type  # e.g., "json_parse", "schema_validation", "missing_field"
        self.invalid_output = invalid_output  # The original invalid output for debugging
        self.details = details or {}  # Additional context
        super().__init__(message)

class LLMProtocol:
    """Handles structured LLM communication with JSON schema validation"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path or SCHEMA_PATH
        self._schema = None
        self.logger = logging.getLogger(__name__)
    
    def _load_schema(self) -> Dict:
        """Load and cache the JSON schema"""
        if self._schema is None:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema
    
    def validate_response(self, response: Dict) -> bool:
        """Validate an LLM response against the schema"""
        try:
            schema = self._load_schema()
            validate(instance=response, schema=schema)
            return True
        except ValidationError as e:
            # Extract more specific validation error information
            error_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            validation_details = {
                "path": error_path,
                "failed_value": e.instance,
                "schema_path": ".".join(str(p) for p in e.schema_path) if e.schema_path else "unknown",
                "validator": e.validator,
                "validator_value": e.validator_value
            }
            
            raise LLMProtocolError(
                f"Invalid LLM response schema at '{error_path}': {e.message}",
                error_type="schema_validation",
                details=validation_details
            )
        except Exception as e:
            raise LLMProtocolError(
                f"Schema validation error: {str(e)}",
                error_type="validation_error"
            )
    
    def parse_response(self, response_text: str) -> Dict:
        """Parse and validate LLM response text as JSON with enhanced error handling"""
        original_response = response_text.strip()
        
        # Try to parse as JSON
        try:
            response_data = json.loads(original_response)
        except json.JSONDecodeError as e:
            # Log the invalid JSON for debugging
            self.logger.warning(
                f"LLM produced invalid JSON output. Error: {e.msg} at line {e.lineno}, column {e.colno}. "
                f"Raw output (first 500 chars): {original_response[:500]}"
            )
            
            # Create detailed error information for user
            json_error_details = {
                "error_msg": e.msg,
                "line": e.lineno,
                "column": e.colno,
                "position": e.pos,
                "raw_output_preview": original_response[:200] + "..." if len(original_response) > 200 else original_response
            }
            
            # Raise detailed error instead of falling back silently
            raise LLMProtocolError(
                f"LLM produced invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}",
                error_type="json_parse", 
                invalid_output=original_response,
                details=json_error_details
            )
        
        # Validate against schema
        try:
            self.validate_response(response_data)
        except LLMProtocolError as e:
            # Add the original response for debugging schema validation errors
            e.invalid_output = original_response
            self.logger.warning(
                f"LLM produced JSON that failed schema validation. Error: {e.message}. "
                f"Raw output (first 500 chars): {original_response[:500]}"
            )
            raise e
            
        return response_data
    def parse_response_with_fallback(self, response_text: str) -> Tuple[Dict, Optional[LLMProtocolError]]:
        """
        Parse LLM response with fallback behavior for invalid JSON/schema.
        Returns (parsed_response, error_info) where error_info is None if successful.
        """
        try:
            return self.parse_response(response_text), None
        except LLMProtocolError as e:
            # Log the error for debugging
            self.logger.error(f"LLM protocol error: {e.message}")
            
            # For JSON parse errors, try to fall back to treating as plain message
            if e.error_type == "json_parse":
                fallback_response = {
                    "action": "message",
                    "content": {
                        "text": response_text.strip()
                    }
                }
                # Validate the fallback response
                try:
                    self.validate_response(fallback_response)
                    return fallback_response, e
                except LLMProtocolError:
                    # Even fallback failed, return minimal response
                    minimal_response = {
                        "action": "message", 
                        "content": {
                            "text": "I apologize, but I produced an invalid response format. Please try rephrasing your request."
                        }
                    }
                    return minimal_response, e
            
            # For schema validation errors, return the original error without fallback
            return None, e
            
    def create_user_friendly_error_message(self, error: LLMProtocolError) -> str:
        """Create a user-friendly error message based on the LLM protocol error"""
        if error.error_type == "json_parse":
            return (
                "The AI model produced a response that wasn't in the expected format. "
                "This usually happens when the model is overloaded or the request is too complex. "
                "Please try again with a simpler request, or try using a different model."
            )
        elif error.error_type == "schema_validation":
            details = error.details or {}
            path = details.get("path", "unknown")
            return (
                f"The AI model's response was missing required information (field: {path}). "
                "This can happen with complex requests. Please try rephrasing your request "
                "or breaking it into smaller, more specific tasks."
            )
        else:
            return (
                "The AI model encountered an issue generating a proper response. "
                "Please try again, and if the problem persists, try using a different model "
                "or simplifying your request."
            )
    
    def generate_system_instructions(self, available_plugins: List[Dict]) -> str:
        """Generate enhanced system instructions that expose available plugins with detailed capabilities to the LLM"""
        
        base_instructions = """You are LibreAssistant, an AI assistant with access to various plugins for enhanced capabilities.

CRITICAL: You MUST respond using a specific JSON format for ALL responses. This is mandatory for proper system operation.

JSON Response Format (REQUIRED):
1. For regular user messages:
{
  "action": "message",
  "content": {
    "text": "Your response text here",
    "markdown": false
  }
}

2. For plugin invocations:
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "plugin_id",
    "input": { "your": "plugin_input" },
    "reason": "Clear explanation of why you're calling this plugin"
  }
}

AVAILABLE PLUGINS AND CAPABILITIES:"""
        
        if not available_plugins:
            base_instructions += "\nNo plugins are currently available."
        else:
            for plugin in available_plugins:
                plugin_id = plugin.get('id', 'unknown')
                plugin_name = plugin.get('name', 'Unknown')
                description = plugin.get('description', 'No description available')
                capabilities = plugin.get('capabilities', {})
                
                base_instructions += f"""

--- {plugin_name} ({plugin_id}) ---
Description: {description}"""
                
                if capabilities:
                    base_instructions += "\nCapabilities:"
                    for category, funcs in capabilities.items():
                        base_instructions += f"\n  {category.replace('_', ' ').title()}:"
                        for func_name, func_info in funcs.items():
                            func_desc = func_info.get('description', 'No description')
                            example = func_info.get('input_example', {})
                            use_cases = func_info.get('use_cases', [])
                            
                            base_instructions += f"""
    • {func_name}: {func_desc}
      Example input: {example}
      Use cases: {', '.join(use_cases) if use_cases else 'General purpose'}"""
                else:
                    base_instructions += "\n  No specific capabilities defined."
        
        base_instructions += """

PLUGIN USAGE GUIDELINES:
1. ANALYZE the user's request to determine if any plugin capabilities can enhance your response
2. USE plugins proactively when they can provide valuable information (e.g., read files for context, search for current information)
3. ALWAYS provide a clear, specific reason in the "reason" field when invoking plugins
4. FORMAT plugin inputs exactly as shown in the examples above
5. You can invoke MULTIPLE plugins sequentially - after each plugin call, you'll receive the results and can decide to call more plugins or respond to the user
6. RESPOND with a user message ONLY when you have all the information needed to fully address the user's request

DETAILED PLUGIN EXAMPLES:

For Brave Search (brave-search):
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "brave-search",
    "input": {"query": "latest developments in artificial intelligence 2024"},
    "reason": "User is asking about recent AI developments, need current web search results"
  }
}

For CourtListener (courtlistener):
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "courtlistener",
    "input": {"query": "copyright fair use", "court": "supreme"},
    "reason": "User needs legal precedent research on copyright fair use doctrine"
  }
}

For Local File I/O (local-fileio):
- Reading a file:
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "local-fileio", 
    "input": {"operation": "read", "path": "project_notes.txt"},
    "reason": "User wants me to read their project notes file for context"
  }
}

- Writing to a file:
{
  "action": "plugin_invoke",
  "content": {
    "plugin": "local-fileio",
    "input": {"operation": "write", "path": "summary.md", "content": "# Project Summary\\n\\nThis is the project summary..."},
    "reason": "User requested to save the generated summary to a markdown file"
  }
}

- Listing files:
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "local-fileio",
    "input": {"operation": "list", "path": "."},
    "reason": "User wants to see what files are available in their directory"
  }
}

MULTI-PLUGIN WORKFLOW EXAMPLE:
1. First, search for information: invoke brave-search with query
2. Then read related files: invoke local-fileio to read relevant files 
3. Finally respond with message action combining all information

ERROR HANDLING GUIDELINES:
When you receive information about plugin errors (timeout, connection issues, or other failures):
1. NEVER expose technical error details directly to users
2. ACKNOWLEDGE the limitation gracefully in user-friendly language
3. PROVIDE alternative approaches when possible:
   - Try a different plugin that serves the same purpose
   - Offer to help with a related task that doesn't require the failed plugin
   - Provide general information on the topic if you have relevant knowledge
4. SUGGEST practical next steps:
   - "Please try again in a moment" for temporary issues like timeouts
   - "Let me help you with [alternative approach]" for service unavailability
   - "I can assist you with [related task] instead" for feature limitations
5. MAINTAIN a helpful, conversational tone despite technical difficulties
6. When appropriate, EXPLAIN what you were trying to do without technical jargon

Example error handling responses:
- "I attempted to search for that information, but the search service is temporarily unavailable. Let me provide some general information I'm familiar with instead..."
- "I'm having trouble accessing that file right now. Could you try again in a moment, or would you like help with something else?"
- "The legal database I tried to access isn't responding at the moment. I can share some general information about that topic, or you could try your query again later."

CRITICAL REMINDERS:
- NEVER respond in plain text - always use the JSON format
- INVALID JSON responses will cause system errors
- ALWAYS validate that your JSON is properly formatted
- USE plugins to enhance your responses with real-time data and file access
- EXPLAIN to users when and why you're using plugins for transparency
- You can chain multiple plugin calls to gather comprehensive information
- Only provide final user message when you have sufficient information
- HANDLE plugin errors gracefully with user-friendly explanations

Remember: Your responses must be valid JSON following the exact format specified above. The user message content should only include text and markdown fields. No nested schemas within the final user message payload."""
        
        return base_instructions
    
    def is_plugin_invocation(self, parsed_response: Dict) -> bool:
        """Check if a parsed response is a plugin invocation"""
        return parsed_response.get("action") == "plugin_invoke"
    
    def is_user_message(self, parsed_response: Dict) -> bool:
        """Check if a parsed response is a user-facing message"""
        return parsed_response.get("action") == "message"
    
    def extract_plugin_call(self, parsed_response: Dict) -> Tuple[str, Any, Optional[str]]:
        """Extract plugin call details from a parsed response"""
        if not self.is_plugin_invocation(parsed_response):
            raise LLMProtocolError("Response is not a plugin invocation")
        
        content = parsed_response.get("content", {})
        plugin_id = content.get("plugin")
        plugin_input = content.get("input")
        reason = content.get("reason")
        
        if not plugin_id:
            raise LLMProtocolError("Plugin invocation missing plugin ID")
        if plugin_input is None:
            raise LLMProtocolError("Plugin invocation missing input data")
            
        return plugin_id, plugin_input, reason
    
    def extract_user_message(self, parsed_response: Dict) -> Tuple[str, bool]:
        """Extract user message details from a parsed response"""
        if not self.is_user_message(parsed_response):
            raise LLMProtocolError("Response is not a user message")
        
        content = parsed_response.get("content", {})
        text = content.get("text", "")
        markdown = content.get("markdown", False)
        
        return text, markdown
    
    def create_plugin_result_prompt(self, plugin_id: str, plugin_result: Dict, original_user_prompt: str) -> str:
        """Create a follow-up prompt for the LLM after plugin execution"""
        return f"""The user asked: "{original_user_prompt}"

I invoked the {plugin_id} plugin and received this result:
{json.dumps(plugin_result, indent=2)}

Based on this plugin result and the user's original request, you can now:
1. Call additional plugins if you need more information to fully address the request
2. Provide a comprehensive response to the user using the "message" action

Remember to respond in the required JSON format. If you need more information, invoke another plugin. If you have sufficient information, respond to the user with action "message"."""

    def create_plugin_error_prompt(self, plugin_id: str, error_details: Dict, original_user_prompt: str) -> str:
        """Create a follow-up prompt for the LLM after plugin execution fails"""
        return f"""The user asked: "{original_user_prompt}"

I attempted to invoke the {plugin_id} plugin, but it encountered an error:
{json.dumps(error_details, indent=2)}

You now have several options to handle this error gracefully:
1. Try a different plugin that might fulfill the same purpose
2. Provide a helpful response without the plugin data
3. Explain to the user what went wrong and suggest alternatives
4. If this was a temporary issue (like network timeout), you could suggest they try again

Please respond using the "message" action to provide a user-friendly response that handles this error situation gracefully. Avoid showing technical error details directly to the user unless necessary."""

# Global instance for use throughout the application
llm_protocol = LLMProtocol()
