# 🗺️ LibreAssistant Development Roadmap

**Welcome to LibreAssistant!**  
LibreAssistant is an **open-source, local-first AI assistant** you truly own.  

Built as an alternative to cloud-based tools like Google Gemini or ChatGPT, LibreAssistant is designed to run **on your own machine**, keeping your data private and giving you full control over how AI helps you think, write, learn, and retrieve information.

---

## 📌 What is LibreAssistant?

LibreAssistant aims to be:

✅ A **true personal AI assistant**, not just a note searcher  
✅ Fully **local-first**, respecting your privacy by default  
✅ **BYOK (Bring Your Own Keys)** friendly for cloud providers  
✅ Flexible with **local LLMs** via Ollama or Transformers.js  
✅ Modular, **plugin-extensible** for future customization  

---

## ⚠️ Current Status

LibreAssistant is a **new fork** of [Reor](https://github.com/reorproject/reor) in **early development**.  

✅ Right now, it retains Reor's base features:  
- Local markdown vault support  
- Semantic search over your notes  
- Basic Q&A using Retrieval-Augmented Generation (RAG)  
- Related note suggestions via vector embeddings  
- Support for local models (Ollama / Transformers.js)  
- BYOK cloud API key integration  

✅ *It works today* as a local semantic search and Q&A tool over your own files.  

**BUT** LibreAssistant is not yet the assistant experience we’re aiming for. That’s what this roadmap is designed to build.

---

## 🌟 The Roadmap to LibreAssistant 1.0

Below is the **ordered development plan** for turning this fork into LibreAssistant 1.0—a *usable, local-first AI assistant* anyone can install and trust.

Each section includes **a commitment to minimal UI/UX integration at that stage**, ensuring features stay coherent and usable *even before the final design polish*.

---

### 1️⃣ Neutral BYOK Platform

**Goal:** Give users total freedom to choose their AI sources.

✔️ Advanced API key management UI (Add/Remove/Label keys)  
✔️ Secure local storage (encrypted)  
✔️ Per-task model selection (chat, summarization, embeddings)  
✔️ Support for local and cloud models side by side  
✔️ Transparency in UI about which model is used for each request  

**Minimal UI/UX commitment:**  
✅ Clean, functional key management screen  
✅ Clear model selection dropdowns/settings  
✅ Basic error handling and feedback messages

✅ **Outcome:** Foundational user sovereignty over models and providers.

---

### 2️⃣ AI Editing Layer

**Goal:** Transform LibreAssistant from a read-only search tool into an interactive writing and editing partner.

✔️ Inline summarization of selected text  
✔️ Rewriting and simplification with tone/style options  
✔️ Extension / completion of partial drafts  
✔️ Command-based text insertion  
✔️ In-editor sidebar with contextual AI suggestions  
✔️ Change tracking and basic version history

**Minimal UI/UX commitment:**  
✅ Intuitive buttons or context menus in the editor  
✅ Simple, readable side panel for suggestions  
✅ Clear user prompts and result formatting  

✅ **Outcome:** A local-first AI assistant that actively helps you *write, revise, and refine* your text.

---

### 3️⃣ Web Distillation Engine

**Goal:** Replace messy, ad-filled web pages with clean, AI-generated answers.

✔️ Paste a URL to fetch and parse the page  
✔️ Local readability-style cleaning  
✔️ AI-generated distilled summaries with bullet points  
✔️ Source attribution with URLs  
✔️ Conversational refinement (follow-up Q&A about the page)  
✔️ Integration with BYOK search APIs for multi-source answers

**Minimal UI/UX commitment:**  
✅ Input field for pasting URLs  
✅ Clean, readable "distilled view" layout  
✅ Attribution links clearly shown  
✅ Follow-up chat integration

✅ **Outcome:** Turns LibreAssistant into *your personal, private web answer engine*.

---

### 4️⃣ Extensible Plugin System

**Goal:** Future-proof LibreAssistant by enabling modular extension and customization.

✔️ Plugin management UI within the app  
✔️ Support for loading user-defined plugins or scripts  
✔️ Defined API for plugins to interact with vault, models, and UI  
✔️ System designed to support future features like:  
  - Reflection & Journaling modules  
  - Knowledge Graph & Linking Enhancements  
  - Specialized domain tools (legal forms, note templates, etc.)  

**Minimal UI/UX commitment:**  
✅ Usable in-app plugin management screen  
✅ Clear enable/disable controls  
✅ Basic permissions/description view  

✅ **Outcome:** Keeps LibreAssistant lean and user-focused while enabling *customization and community growth*.

---

### 5️⃣ UI/UX Polish

**Goal:** Make LibreAssistant not just powerful, but **delightful and accessible**.

✔️ Clean, calm, single-column assistant chat interface  
✔️ Light/dark modes with accessible color choices  
✔️ Minimalist, consistent design language  
✔️ First-run onboarding flow explaining setup and BYOK  
✔️ Clear error messages and confirmations  
✔️ Contextual help popovers explaining features  
✔️ Adaptive suggestions and command prompts  
✔️ Accessibility features (font scaling, keyboard navigation, screen reader support)

✅ **Outcome:** Delivers *powerful AI* in an experience *anyone can use confidently*.

---

## ✅ Development Philosophy

**Feature-First, with Minimal UI in Each Phase.**  
> *“Build the functionality first—but always keep it usable.”*

We won't defer all UX work to the end. Every phase includes **minimal, necessary UI** so that each feature:  
✅ Works end-to-end  
✅ Can be tested clearly  
✅ Avoids design debt  

Final UI/UX polish will then unify and refine the whole experience before the 1.0 release.

---

## ✅ Contributing

LibreAssistant is **open source** and **community-driven**.  

We welcome help on:  
- Building the AI Editing Layer  
- Improving local model integration  
- Developing the Web Distillation Engine  
- Designing the Plugin System  
- UI/UX design and accessibility improvements  
- Bug fixing and documentation

If you care about **local-first AI** and **user privacy**, this project is for you!

Check our [issues](https://github.com/YourUser/LibreAssistant/issues) and [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## ✅ License

AGPL-3.0 license. See `LICENSE` for details.

---

> **LibreAssistant**  
> **Your Assistant. Your Models. Your Data. Your Control.**
