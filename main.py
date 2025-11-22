#!/usr/bin/env python3
import sys
import os
import json

# Import your backends
from openvino_client import OpenVINOClient
from ollama_client import OllamaClient  # adjust if your file is named differently


def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Failed to load config.json: {e}")
        return {}


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def menu():
    clear()
    print("=====================================")
    print("        LibreAssistant (CLI)         ")
    print("=====================================")
    print("1) Use OpenVINO (GPU/CPU)")
    print("2) Use Ollama (local Llama)")
    print("3) Exit")
    print("-------------------------------------")
    return input("Select an option: ").strip()


def chat_loop(client):
    """Unified chat loop for both OpenVINO and Ollama."""
    print("\nType Ctrl+C to return to menu.\n")
    while True:
        try:
            user = input("You > ").strip()
            if not user:
                continue

            response = client.call(user)
            print("AI >", response)

        except KeyboardInterrupt:
            print("\nReturning to main menu...\n")
            break


def main():
    config = load_config()
    system_prompt = config.get("system_prompt", "You are LibreAssistant, a helpful and open-source AI assistant.")
    
    while True:
        choice = menu()

        if choice == "1":
            clear()
            print("🔧 Loading OpenVINO client…")
            ov_config = config.get("openvino", {})
            try:
                client = OpenVINOClient(
                    model_dir=ov_config.get("model_dir", "ov_dolphin3p0_llama3p1_8b_int4"),
                    device=ov_config.get("device", "AUTO"),
                    system_prompt=system_prompt
                )
                chat_loop(client)
                client.finish()
            except Exception as e:
                print("⚠️  Failed to load OpenVINO:", e)
                input("\nPress Enter to continue...")

        elif choice == "2":
            clear()
            print("🔧 Loading Ollama client…")
            ollama_config = config.get("ollama", {})
            try:
                client = OllamaClient(
                    default_model=ollama_config.get("model", "llama3:8b"),
                    system_prompt=system_prompt
                )
                chat_loop(client)
            except Exception as e:
                print("⚠️  Failed to load Ollama:", e)
                input("\nPress Enter to continue...")

        elif choice == "3":
            print("Goodbye!")
            sys.exit(0)

        else:
            print("Invalid option.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
