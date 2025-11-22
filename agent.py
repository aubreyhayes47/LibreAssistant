import json
import re
from typing import List
from tools import Tool

class Agent:
    def __init__(self, client, tools: List[Tool]):
        self.client = client
        self.tools = {t.name: t for t in tools}
        self.history = []
        self.max_steps = 5

    def _build_system_prompt(self):
        tool_descriptions = "\n".join([t.to_string() for t in self.tools.values()])
        
        prompt = f"""You are a helpful AI assistant with access to the following tools:

{tool_descriptions}

You MUST respond in JSON format. The JSON should have the following structure:

{{
  "thought": "your reasoning here",
  "action": "the tool name to use",
  "action_input": "the input to the tool"
}}

If you know the final answer and do not need to use a tool, use "Final Answer" as the action:

{{
  "thought": "I have the answer",
  "action": "Final Answer",
  "action_input": "the final answer string"
}}

EXAMPLES:

User: What time is it?
Assistant:
{{
  "thought": "I need to check the current time.",
  "action": "get_current_time",
  "action_input": ""
}}
Observation: 2023-11-22 14:00:00
Assistant:
{{
  "thought": "I have the time.",
  "action": "Final Answer",
  "action_input": "The current time is 2023-11-22 14:00:00."
}}

User: Calculate 50 * 4
Assistant:
{{
  "thought": "I need to calculate 50 * 4.",
  "action": "calculate",
  "action_input": "50 * 4"
}}
Observation: 200
Assistant:
{{
  "thought": "I have the result.",
  "action": "Final Answer",
  "action_input": "The result is 200."
}}

User: Hello
Assistant:
{{
  "thought": "The user is greeting me.",
  "action": "Final Answer",
  "action_input": "Hello! How can I help you today?"
}}
"""
        return prompt

    def _parse_json_response(self, response: str):
        # Attempt to find JSON blob
        try:
            # Strip markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            return json.loads(clean_response.strip())
        except json.JSONDecodeError:
            # Fallback: try to find the first { and last }
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(response[start:end])
            except:
                pass
            return None

    def run(self, task: str):
        print(f"🤖 Task: {task}")
        
        self.history = [f"User: {task}"]
        system_prompt = self._build_system_prompt()
        
        step_count = 0
        while step_count < self.max_steps:
            step_count += 1
            
            # Construct full prompt
            # We don't need to append "Thought:" anymore since we want JSON
            full_prompt = f"{system_prompt}\n\n" + "\n".join(self.history) + "\nAssistant:"
            
            # Call LLM
            response = self.client.call(full_prompt)
            print(f"\nRAW LLM OUTPUT:\n{response}\n") # Debugging
            
            data = self._parse_json_response(response)
            
            if not data:
                print("⚠️  Could not parse JSON. Retrying or failing...")
                # For now, just fail or append raw response to history to see if it corrects?
                # Let's try to append and hope the model fixes it next turn, or just return error.
                # Actually, if we can't parse it, we can't act.
                return f"Error: Invalid JSON response from model: {response}"

            thought = data.get("thought", "")
            action = data.get("action", "")
            action_input = data.get("action_input", "")
            
            print(f"🤔 Thought: {thought}")
            
            if action == "Final Answer":
                return action_input
            
            # Update history with the assistant's JSON response
            # We should probably store the raw JSON or a simplified representation.
            # Storing the raw JSON ensures the model sees its own valid output history.
            self.history.append(f"Assistant: {json.dumps(data)}")
            
            print(f"🛠️  Executing {action}('{action_input}')...")
            
            if action in self.tools:
                try:
                    observation = self.tools[action].run(action_input)
                except Exception as e:
                    observation = f"Error: {e}"
            else:
                observation = f"Error: Tool '{action}' not found."
            
            print(f"👀 Observation: {observation}")
            self.history.append(f"Observation: {observation}")

        return "Error: Maximum steps reached."
