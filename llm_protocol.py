"""
llm_protocol.py: JSON schema-based LLM communication protocol for LibreAssistant
- Enforces structured responses from LLM for deterministic parsing
- Handles routing between plugin invocations and user-facing messages
- Generates system instructions that expose available plugins to the LLM
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from jsonschema import validate, ValidationError

# Path to the LLM response schema
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "llm-response.schema.json")

class LLMProtocolError(Exception):
    """Exception raised for LLM protocol-related errors"""
    pass

class LLMProtocol:
    """Handles structured LLM communication with JSON schema validation"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path or SCHEMA_PATH
        self._schema = None
    
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
            raise LLMProtocolError(f"Invalid LLM response schema: {e.message}")
        except Exception as e:
            raise LLMProtocolError(f"Schema validation error: {str(e)}")
    
    def parse_response(self, response_text: str) -> Dict:
        """Parse and validate LLM response text as JSON"""
        try:
            # Try to parse as JSON
            response_data = json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            # If it's not valid JSON, treat it as a plain message
            response_data = {
                "action": "message",
                "content": {
                    "text": response_text.strip()
                }
            }
        
        # Validate against schema
        self.validate_response(response_data)
        return response_data
    
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
5. RESPOND with a user message after getting plugin results to explain what you found
6. COMBINE multiple plugin calls if needed to fully address the user's request

CRITICAL REMINDERS:
- NEVER respond in plain text - always use the JSON format
- INVALID JSON responses will cause system errors
- ALWAYS validate that your JSON is properly formatted
- USE plugins to enhance your responses with real-time data and file access
- EXPLAIN to users when and why you're using plugins for transparency

Remember: Your responses must be valid JSON following the exact format specified above."""
        
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

Please provide a helpful response to the user based on this plugin result. Remember to respond in the required JSON format with action "message"."""

# Global instance for use throughout the application
llm_protocol = LLMProtocol()