---
name: tutorial
description: Interactive tutorial for new users — teaches how to use LibreAssistant
tools: terminal,read,write,search_web
profiles: default
---

## Welcome to LibreAssistant!

This is a general-purpose AI assistant with access to tools and background task delegation.

### Getting Started

**Try these things:**

1. **Ask me anything** — I can answer questions, explain concepts, help with tasks
2. **Use web search** — "Search the web for recent AI news"
3. **Read a file** — "Read the file ~/somefile.txt"
4. **Delegate work** — "Research this topic for me" (I can delegate to specialist agents)

### How Background Tasks Work (The Kitchen Analogy)

Think of LibreAssistant like a restaurant kitchen:

- **You** are the customer placing orders
- **The main agent** is the head chef — it talks to you directly
- **Specialist profiles** (legal, code) are sous-chefs with expertise
- **The TaskPool** is the kitchen pass — where orders get queued and dispatched

When you say "research copyright law," the head chef has two options:

1. **Do it itself** — directly researches and responds (single turn, blocks until done)
2. **Delegate to a sous-chef** — hands off to the `legal` specialist, keeps talking to you while the specialist works in the background

Delegated tasks run in **parallel**. The head chef doesn't wait — it keeps cooking. When the sous-chef finishes, the result appears as a system message the head chef can reference.

The specialist agents have their own workspace, their own tools, and a smaller budget (30K context, 20 rounds max). This keeps costs down and prevents runaway loops.

Try it: say "delegate research on fair use doctrine to the legal agent" and watch the head chef hand off the work.

### Commands

Type these in the chat:

- `/help` — Show all available commands
- `/skills` — List installed skill modules
- `/tutorial` — Reload this tutorial
- `/agent <name>` — Switch to a specialist profile (try: legal, code)
- `/tasks` — View background tasks
- `/task <id>` — Inspect a specific task
- `/task <id> stop` — Cancel a running task
- `/task <id> output` — See a task's full output
- `/mcp` — List connected MCP servers
- `/sessions` — List saved sessions
- `/save <name>` — Save current session
- `/load <name>` — Load a saved session
- `/new` — Start fresh conversation
- `/quit` — Save and exit

### Specialist Profiles

- **default** — General purpose (all tools)
- **legal** — Legal research with CourtListener
- **code** — Software development and debugging

Switch with `/agent legal` or `/agent code`.

### CLI Flags

When launching from the terminal:

- `libre` — Start normally (interactive REPL)
- `libre --tutorial` — Start with this tutorial pre-loaded
- `libre --exec "message"` — Run one turn, print result, exit (non-interactive)
- `libre --exec-task "message"` — Submit as background task, wait for result, exit
- `libre --agent legal` — Start with a specific profile
- `libre --no-terminal` — Disable shell access entirely
- `libre --sandbox-root ~/project` — Restrict file access to a directory
- `libre --kms` — Disable all safety confirmations (requires typing "yes")

### Tips

- Ask me to explain how I work — I can describe my own architecture
- Delegate complex research to background tasks for parallel execution
- Use `/task <id> output` to see delegated task results
- Try `--exec` mode for quick one-shot questions from the terminal
