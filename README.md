<h1 align="center">LibreAssistant</h1>


> ### 📢 Announcement
>
> LibreAssistant is in **early development**! This is a brand-new fork of [Reor](https://github.com/reorproject/reor) aiming to become a **true local-first alternative** to cloud-based AI assistants like ChatGPT or Google Gemini. Your feedback and contributions are welcome ❤️

---

## About

**LibreAssistant** is an **open-source, local-first AI assistant** you can run on your own machine.  

Unlike cloud services that process your data on someone else’s servers, LibreAssistant is being built to give you:

✅ A *fully local* AI-powered assistant  
✅ User control over models and API keys  
✅ A clean, calm interface for asking questions, editing text, summarizing, and drafting—all with your own private data  

---

### ⚡ Current Status

This repo is **a fresh fork** of [Reor](https://github.com/reorproject/reor).  

✅ Right now, LibreAssistant **retains all of Reor’s base features**:  
- Local markdown vault  
- Semantic search over your own notes  
- Basic Retrieval-Augmented Generation (RAG) Q&A  
- Related note suggestions via vector embeddings  
- Local model support (Ollama, Transformers.js)  
- BYOK support for cloud LLM providers (OpenAI, Anthropic, etc.)

✅ **It works today** as a local semantic search and Q&A tool over your own text files.  

⚠️ It does **not yet** have the advanced assistant features described below.  

---

## Mission

> **"Your Assistant. Your Models. Your Data. Your Control."**

LibreAssistant’s mission is to **transform this fork** into a full-fledged, user-owned AI assistant:

⭐ A *real alternative* to Gemini or ChatGPT  
⭐ Fully local-first by default  
⭐ User-controlled BYOK for any LLM provider  
⭐ No forced cloud lock-in or data harvesting  

---

## How It Works (Right Now)

LibreAssistant is a local desktop app that:

✅ Lets you choose a folder of markdown notes (your vault)  
✅ Uses local embeddings + vector DB to index your notes  
✅ Supports local models via Ollama / Transformers.js  
✅ Lets you add your own cloud API keys (OpenAI-compatible)  
✅ Enables basic Q&A over your notes via RAG

**It’s already usable** for:  
✔️ Private semantic search  
✔️ Asking questions about your local files  

---

## Roadmap: Turning It Into an Assistant

LibreAssistant 1.0 will *expand on this base* to become a **true local AI assistant**.  

**Key next milestone:**  
✅ Building the **AI Editing Layer** that moves beyond search/Q&A into full text interaction:

✅ Summarize selected text  
✅ Rewrite / simplify passages  
✅ Extend and continue drafts  
✅ Command-based insertion and edits  
✅ Contextual suggestions and related content  
✅ Change tracking / version history

These features will make LibreAssistant feel like **your private ChatGPT**—but running on your own machine, on your own terms.

---

## Planned Features (High-Level)

✅ Local-first, Obsidian-style markdown vault  
✅ Fully local semantic search and embeddings  
✅ Inline AI editing commands  
✅ Contextual AI sidebar with suggestions  
✅ Web page distillation and summarization  
✅ Secure BYOK integration for cloud models  
✅ Plugin system for future extensibility  

---

## Getting Started

LibreAssistant right now works like Reor:  
1️⃣ **Download** from [Releases](https://github.com/aubreyhayes47/LibreAssistant/releases).  
2️⃣ **Choose a vault folder** of markdown files.  
3️⃣ **Add your local models** via Ollama or Transformers.js.  
4️⃣ **Configure your own API keys** for cloud LLMs if desired.  
5️⃣ **Ask questions** about your notes using the built-in chat.

---

### Running Local Models

LibreAssistant supports **Ollama** and **Transformers.js** for local LLMs.  

- Go to **Settings → Add New Local LLM**.  
- Download models via [Ollama's library](https://ollama.com/library).  
- Enjoy offline Q&A and semantic search.  

Also supports **OpenAI-compatible APIs** for BYOK setups.

---

### Building from Source

Make sure you have [Node.js](https://nodejs.org/en/download) installed.

#### Clone the repo

```

git clone [https://github.com/aubreyhayes47/LibreAssistant.git](https://github.com/aubreyhayes47/LibreAssistant.git)

```

#### Install dependencies

```

npm install

```

#### Run for development

```

npm run dev

```

#### Build

```

npm run build

```

---

### Interested in Contributing?

This is **early days** for LibreAssistant.  

✅ We’re looking for contributors to help:  
- Implement the AI Editing Layer  
- Improve local model integration  
- Build web page distillation tools  
- Design a friendly, calm UI  
- Squash bugs and improve stability

Check our [issues](https://github.com/aubreyhayes47/LibreAssistant/issues) to get involved.

---

## License

AGPL-3.0 license. See `LICENSE` for details.

---

LibreAssistant: **A local-first, user-controlled AI assistant you truly own.**

```
