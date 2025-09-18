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
        """Generate system instructions that expose available plugins to the LLM"""
        
        base_instructions = """You are LibreAssistant, an AI assistant with access to various plugins for enhanced capabilities.

IMPORTANT: You must respond using a specific JSON format for ALL responses. This allows the system to properly route your requests.

Response Format:
1. For regular user messages, use:
{
  "action": "message",
  "content": {
    "text": "Your response text here",
    "markdown": false
  }
}

2. For plugin invocations, use:
{
  "action": "plugin_invoke", 
  "content": {
    "plugin": "plugin_id",
    "input": { "your": "plugin_input" },
    "reason": "Why you're calling this plugin"
  }
}

Available Plugins:"""
        
        if not available_plugins:
            base_instructions += "\nNo plugins are currently available."
        else:
            for plugin in available_plugins:
                plugin_info = f"""
- {plugin.get('name', 'Unknown')} ({plugin.get('id', 'unknown')})
  Description: {plugin.get('description', 'No description available')}
  Capabilities: {', '.join(plugin.get('capabilities', []))}"""
                base_instructions += plugin_info
        
        base_instructions += """

Plugin Usage Guidelines:
- Only invoke plugins when the user's request clearly requires external capabilities
- Always provide a clear reason for plugin invocations
- After getting plugin results, respond with a message to the user explaining the results
- Use appropriate plugin input format based on the plugin's capabilities
- If unsure about plugin capabilities, respond with a message asking for clarification

Remember: ALWAYS respond in the specified JSON format. Invalid responses will cause errors."""
        
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