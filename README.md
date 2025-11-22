# LibreAssistant

LibreAssistant is a local, open-source AI agent capable of using tools to solve tasks. It supports two backends:

- **OpenVINO**: Runs optimized models (like Dolphin 3.0 / Llama 3.1) locally on CPU/GPU.
- **Ollama**: Connects to a local Ollama daemon.

Unlike simple chatbots, LibreAssistant uses a **ReAct (Reasoning + Acting)** loop to think, plan, and execute actions using available tools.

## Features

- 🧠 **Agentic Core**: Uses a JSON-based ReAct loop to reason and act.
- 🛠️ **Tool Support**: Built-in tools for Time, Math, and **Web Search**.
- ⚙️ **Configurable**: Manage models and system prompts via `config.json`.
- 🔌 **Dual Backend**: Switch between OpenVINO and Ollama seamlessly.

## Project Structure

- `main.py`: The entry point. Initializes the Agent and handles the user input loop.
- `agent.py`: Implements the ReAct agent logic, handling JSON parsing and tool execution.
- `tools.py`: Definitions for available tools (`get_current_time`, `calculate`, `search_web`).
- `config.json`: Configuration file for models, devices, and system prompts.
- `openvino_client.py`: Backend for OpenVINO models.
- `ollama_client.py`: Backend for Ollama models.

## Quick Start

1.  **Install Dependencies**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure**:
    Edit `config.json` to set your preferred model or system prompt.
    ```json
    {
      "system_prompt": "You are a helpful assistant...",
      "ollama": { "model": "llama3:8b" },
      "openvino": { "device": "AUTO" }
    }
    ```

3.  **Run**:
    ```bash
    python3 main.py
    ```

4.  **Interact**:
    Select your backend, then give the agent a task:
    ```text
    Task > What is 123 * 45?
    Task > What time is it?
    ```

## Tool Calling

LibreAssistant uses a structured JSON format for tool calling. The agent outputs:

```json
{
  "thought": "I need to calculate...",
  "action": "calculate",
  "action_input": "123 * 45"
}
```

You can add new tools in `tools.py` and they will be automatically available to the agent.

## Troubleshooting

- **Infinite Loops**: If the agent keeps repeating an action, ensure the system prompt (in `agent.py`) includes clear examples of how to finish a task.
- **JSON Errors**: The agent attempts to parse JSON strictly. If the model outputs malformed JSON, the agent may fail. Using a capable model (Llama 3, Dolphin) is recommended.
- **OpenVINO Export**: The first run with OpenVINO will export the model, which requires significant disk space and time.

## License

Open Source. Check the licenses of the models and libraries used.
