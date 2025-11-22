
# LibreAssistant

LibreAssistant is a small CLI wrapper that provides two local backends for chat-style text generation:

- an OpenVINO-based backend (heavy-weight — exports and runs Dolphin 3.0 / Llama 3.1 models as OpenVINO IR)
- an Ollama-backed client (talks to a local Ollama daemon / model)

This repository contains a tiny CLI (`main.py`) that chooses either backend and provides a unified chat loop.

## Project structure

- `main.py` — CLI and unified chat loop. Lets you select OpenVINO or Ollama and then converse with the chosen client.
- `openvino_client.py` — Drop-in client that (on first run) installs required Python packages, exports the Dolphin3.0→OpenVINO IR using `optimum-cli`, loads the OpenVINO LLM pipeline, and exposes a `call(prompt)` method.
- `ollama_client.py` — Thin wrapper around the `ollama` Python package. Exposes `OllamaClient` with `call(prompt)` and auto-pulls models on demand.
- `requirements.txt` — Contains all necessary dependencies for both backends, including OpenVINO, Torch, and Ollama.

## Quick start

1. (Optional) Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the CLI:

```bash
python3 main.py
```

Choose `1` to use the OpenVINO backend or `2` to use Ollama. Press Ctrl+C while in a chat to return to the main menu.

## OpenVINO backend notes

- `openvino_client.py` attempts to make the OpenVINO workflow smoother by:
	- Installing OpenVINO and related packages the first time (`ensure_packages()`)
	- Exporting the Dolphin3.0-Llama3.1-8B model to an OpenVINO IR directory via `optimum-cli export openvino` (this requires `huggingface-cli login` if you need to access gated HF models)
	- Loading the model with `openvino_genai.LLMPipeline` and providing a `call(prompt)` method compatible with the Ollama client interface.

- Important: exporting and running the model requires significant disk space and runtime resources (and may require GPU drivers / appropriate hardware). You will be prompted to authenticate with Hugging Face if needed. If the export directory already exists and is non-empty, the export step is skipped.

## Ollama backend notes

- `ollama_client.py` wraps the `ollama` Python package. `OllamaClient` will either use a model name provided at construction (defaults to `llama3:8b` in `main.py`) or pick the first available model reported by `ollama.list()` if used as a library.
- If a generate call fails with a 404 (model not found), the client will attempt to `ollama.pull(model)` and retry the generation.

Ensure you have the Ollama daemon/service running locally and the `ollama` Python package installed when using this backend.

## Example usage

- Start the CLI and select a backend, then type messages at the `You >` prompt. The assistant responds and you can continue the conversation.

## Troubleshooting & tips

- OpenVINO export may fail if `optimum-cli` or `optimum-intel` versions mismatch; if you run into issues, ensure your Python environment is clean and run `pip install --upgrade optimum-intel openvino openvino-genai`.
- If Hugging Face authentication is required, run:

```bash
huggingface-cli login
```

- For Ollama, make sure the Ollama daemon is running and reachable from your environment. Use `ollama list` to check available models.

## Safety & license

This project is a small convenience wrapper to run local LLMs. Check the licenses for any models and libraries you use (Hugging Face model licensing, Ollama terms, OpenVINO). Models may produce incorrect or unsafe outputs — use appropriate safety controls for production use.

## Contributing / Next steps

- Add more backend clients (e.g., local llama.cpp) or configuration options.
- Add a minimal tests harness for the client interfaces.

---

If anything in this README doesn't match your environment (for example a different model name or different install flow), edit `README.md` or the clients to match your local setup.
