import ollama


def ollama_call(model: str, prompt: str) -> str:
    """Basic wrapper for ollama.generate() with auto-pull fallback."""
    try:
        res = ollama.generate(model=model, prompt=prompt)
        return res.response

    except ollama.ResponseError as e:
        print("Ollama error:", e.error)

        # Auto-pull missing models
        if e.status_code == 404:
            print(f"Model '{model}' not found. Pulling now...")
            ollama.pull(model)
            res = ollama.generate(model=model, prompt=prompt)
            return res.response

        raise


def select_model() -> str:
    """
    Returns the first available model from `ollama.list().models`.

    If no models exist, raises an exception (or you could auto-pull a default).
    """
    models_info = ollama.list()
    models = models_info.models  # List[ModelInfo]

    if not models:
        raise RuntimeError("No models found in Ollama. Pull one first.")

    # The list returns dict-like ModelInfo objects with .name
    default_model = models[0].name
    return default_model


class OllamaClient:
    """
    A convenient client class that can be imported and reused.
    """

    def __init__(self, default_model: str | None = None):
        if default_model:
            self.model = default_model
        else:
            self.model = select_model()

    def call(self, prompt: str) -> str:
        sys_instruction = "You are LibreAssistant, a helpful and open-source AI assistant. Answer all questions accurately and succinctly. User prompt:"
        full_prompt = f"{sys_instruction}\n{prompt}"
        return ollama_call(self.model, full_prompt)

    def set_model(self, model_name: str):
        self.model = model_name
