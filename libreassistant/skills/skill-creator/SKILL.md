---
name: skill-creator
description: Create new skills for LibreAssistant — teaches the SKILL.md format and helps you build, validate, and install skills
tools: read,write
---

## Skill Creator

This skill teaches you how to create new skills for LibreAssistant.  Skills are markdown files that teach you domain-specific behavior — they're loaded into your context on demand.

### Skill Format

Every skill is a directory with a `SKILL.md` file:

```
~/.libreassistant/skills/
├── tutorial/
│   └── SKILL.md
├── my-new-skill/
│   └── SKILL.md
└── ...
```

### SKILL.md Structure

```markdown
---
name: my-skill
description: Short description of what this skill does and when to use it
tools: terminal,read,write
profiles: default,code
---

# What I do
- Clear, actionable instructions
- Step-by-step workflows
- Examples and edge cases

# When to use me
Describe the triggers that should activate this skill.

# Guidelines
- Keep it focused — one skill, one purpose
- Be specific — LLMs follow concrete instructions better than vague ones
- Include examples — show, don't just tell
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase, hyphens only (e.g. `my-skill`). Must match directory name. |
| `description` | Yes | 1-1024 chars. This is what appears in the system prompt — make it clear when to use this skill. |
| `tools` | No | Comma-separated tool globs this skill needs (e.g. `terminal,read,write`). If omitted, skill works with all tools. Used for profile filtering — a skill requiring `terminal` won't load for profiles without terminal access. |
| `profiles` | No | Comma-separated profile names this skill targets (e.g. `default,code`). If omitted, skill loads for all profiles. |

### Creating a New Skill

When a user asks you to create a skill:

1. **Ask what it should do** — Understand the use case, triggers, and expected behavior
2. **Plan the content** — What instructions, examples, and guidelines belong in this skill?
3. **Choose frontmatter** — Pick a name, write a clear description, list required tools and target profiles
4. **Write SKILL.md** — Create the directory and file at `~/.libreassistant/skills/<name>/SKILL.md`
5. **Validate** — Check the frontmatter is valid YAML, name matches directory, description is clear

### Validation Checklist

Before finishing, verify:

- [ ] Directory name matches `name` field in frontmatter
- [ ] `name` is lowercase with hyphens only (no spaces, no underscores)
- [ ] `description` clearly states what the skill does AND when to use it
- [ ] `tools` lists only tools that exist (terminal, read, write, search_web, web_fetch, edit, file_ops, docs, mcp/*)
- [ ] `profiles` lists only valid profile names (default, legal, code)
- [ ] Markdown body is actionable — concrete steps, not vague advice
- [ ] Skill is focused — one clear purpose, not a kitchen sink

### Example: Creating a "git-release" Skill

User: "Create a skill for drafting GitHub releases"

You would create `~/.libreassistant/skills/git-release/SKILL.md`:

```markdown
---
name: git-release
description: Draft GitHub release notes from recent commits and PRs — use when preparing a tagged release
tools: terminal,read
profiles: default,code
---

## What I do
- Review recent commits and merged PRs since the last tag
- Draft release notes following a consistent format
- Suggest a version bump (major/minor/patch)
- Provide a copy-pasteable `gh release create` command

## Workflow
1. Run `git describe --tags --abbrev=0` to find the last tag
2. Run `git log <last-tag>..HEAD --oneline` to see commits
3. Group commits by type (features, fixes, chores)
4. Draft release notes in the repo's style
5. Suggest version bump based on commit types

## Format
## What's Changed
### Features
- feature description (#PR)
### Bug Fixes
- fix description (#PR)
### Contributors
@username
```

### Tips

- **Keep skills focused** — one skill, one workflow.  Multiple small skills beat one monolithic one.
- **Write for the LLM** — concrete instructions ("run `git log --oneline -10`") beat vague ones ("check recent history").
- **Include error handling** — what should the agent do if a command fails or returns unexpected output?
- **Test your skill** — load it with `/<skill-name>` and try realistic scenarios.
