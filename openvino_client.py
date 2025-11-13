"""
openvino_client.py
A drop-in replacement for OllamaClient that:
- Installs OpenVINO + Optimum-Intel (first run only)
- Downloads & exports Dolphin3.0-Llama3.1-8B → OpenVINO IR
- Runs text-generation with KV cache
- Offers a .call(prompt) method identical to OllamaClient

Steps 0–8 are internalized into this module.
"""

import os
import subprocess
import sys
from pathlib import Path


# ============================================================
# STEP 0 — environment setup
# ============================================================

def ensure_packages():
    REQUIRED = [
        "openvino",
        "openvino-genai",
        "optimum-intel",
        "transformers",
        "huggingface_hub",
        "accelerate",
        "nncf",
        "openvino-tokenizers",
    ]

    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    if missing:
        print("🚀 Installing OpenVINO dependencies…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


# ============================================================
# ChatML formatting for Dolphin 3.0
# ============================================================

def chatml_prompt(system_prompt: str, user_prompt: str) -> str:
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


# ============================================================
# STEP 2–4 — Export → OpenVINO IR
# ============================================================

def export_dolphin(
    model_id: str = "dphn/Dolphin3.0-Llama3.1-8B",
    out_dir: str = "ov_dolphin3p0_llama3p1_8b_int4",
    weight_format: str = "int4"
):
    from huggingface_hub import login

    print("🔐 Checking HuggingFace authentication…")
    try:
        login()
    except Exception:
        print("⚠️  Please run: huggingface-cli login")
        raise

    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        print(f"✅ OpenVINO model already exists: {out_dir}")
        return out_dir

    print("📦 Exporting Dolphin3.0-Llama3.1-8B → OpenVINO IR…")

    cmd = [
        "optimum-cli", "export", "openvino",
        "--model", model_id,
        "--task", "text-generation-with-past",
        "--weight-format", weight_format,
        out_dir
    ]

    subprocess.check_call(cmd)
    return out_dir


# ============================================================
# STEP 5 — Load pipeline + chat loop wrapper
# ============================================================

class OpenVINOClient:
    def __init__(
        self,
        model_dir: str = "ov_dolphin3p0_llama3p1_8b_int4",
        device: str = "AUTO",
        weight_format: str = "int4",
        system_prompt: str =
            "You are LibreAssistant, a free and open-source, helpful assistant. "
            "Follow instructions accurately and respond clearly."
    ):
        ensure_packages()

        self.model_dir = model_dir
        self.device = device
        self.weight_format = weight_format
        self.system_prompt = system_prompt

        if not Path(model_dir).exists():
            export_dolphin(out_dir=model_dir, weight_format=weight_format)

        print("📡 Loading OpenVINO LLM pipeline…")
        import openvino_genai as ov_genai
        self.pipe = ov_genai.LLMPipeline(self.model_dir, self.device)

        self.pipe.start_chat()

    # ============================================
    # STEP 6 — Call interface
    # ============================================
    def call(self, prompt: str) -> str:
        # ✅ ChatML formatting
        formatted = chatml_prompt(self.system_prompt, prompt)

        chunks = []

        def stream(token: str):
            chunks.append(token)

        self.pipe.generate(
            formatted,
            streamer=stream,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.95
        )
        return "".join(chunks)

    # ============================================
    # STEP 7 — Switch device
    # ============================================
    def set_device(self, device: str):
        print(f"🔄 Switching device → {device}")
        import openvino_genai as ov_genai
        self.device = device
        self.pipe = ov_genai.LLMPipeline(self.model_dir, self.device)
        self.pipe.start_chat()

    # ============================================
    # STEP 8 — Cleanup
    # ============================================
    def finish(self):
        self.pipe.finish_chat()


# ============================================================
# CLI test
# ============================================================

if __name__ == "__main__":
    client = OpenVINOClient()
    while True:
        try:
            user = input("\nYou > ")
            print("AI >", client.call(user))
        except KeyboardInterrupt:
            client.finish()
            break
