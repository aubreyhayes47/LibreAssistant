"""Skill loader — discovers, filters, and loads SKILL.md files from ~/.libreassistant/skills/.

Skills follow the AgentSkills standard (compatible with opencode, Codex, OpenClaw):
  - Each skill lives in a named subdirectory: skills/<name>/SKILL.md
  - SKILL.md has YAML frontmatter (name, description, tools, profiles) + markdown body
  - At startup, skill names+descriptions are listed in the system prompt (lazy loading)
  - Users load full skill content on demand via /<skill-name>
  - Built-in skills auto-install to the user's skills dir on first run
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from .config import CONFIG_DIR

SKILLS_DIR = CONFIG_DIR / "skills"

# Where built-in skills live inside the installed package.
# importlib.resources is the标准 way, but for PyInstaller/appimage compatibility
# we fall back to __file__ resolution.
_BUNDLED_DIR = Path(__file__).parent / "skills"


@dataclass
class Skill:
    """A loaded skill with its metadata and content."""
    name: str
    description: str
    content: str  # The markdown body (everything after frontmatter)
    path: Path
    tools: list[str] = field(default_factory=list)  # Tool globs this skill requires (e.g. ["terminal", "read"]); empty = all tools OK
    profiles: list[str] = field(default_factory=list)  # Profile names this skill targets; empty = all profiles


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from a skill SKILL.md file. Returns (metadata_dict, body).

    Frontmatter is delimited by --- lines at the top of the file.
    Supports simple key: value pairs.  Comma-separated values are split into lists
    (e.g. "tools: terminal,read" -> ["terminal", "read"]).

    Why a custom parser instead of importing pyyaml?  Skills are user-authored .md
    files — keeping the dependency graph minimal avoids breakage from missing packages.
    The key: value format is enough for skill metadata (name, description, tools, profiles).
    """
    if not text.startswith("---"):
        return {}, text

    # Find closing --- (must be on its own line, no trailing content).
    # This prevents markdown horizontal rules (---) in the body from being
    # misinterpreted as frontmatter delimiters.
    lines = text[3:].split("\n")
    end_line = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            end_line = i
            break
    if end_line == -1:
        return {}, text

    meta_text = "\n".join(lines[:end_line]).strip()
    body = "\n".join(lines[end_line + 1:]).strip()

    _LIST_FIELDS = {"tools", "profiles"}
    meta = {}
    for line in meta_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            if "," in value and key.strip() in _LIST_FIELDS:
                value = [v.strip() for v in value.split(",") if v.strip()]
            meta[key.strip()] = value

    return meta, body


def _skill_matches_profile(skill: Skill, profile_tool_patterns: list[str] | None, profile_name: str | None = None) -> bool:
    """Check if a skill is applicable to a given profile.

    A skill matches if:
      1. Its profiles list is empty (applies to all) OR profile_name is in the list
      2. Its tools list is empty (no tool requirements) OR all required tools
         match at least one of the profile's tool_patterns
    """
    # Profile name filter
    if profile_name and skill.profiles and profile_name not in skill.profiles:
        return False

    # Tool access filter: skill's required tools must be a subset of what the profile allows
    if skill.tools and profile_tool_patterns is not None:
        for required_tool in skill.tools:
            if not any(fnmatch(required_tool, pat) for pat in profile_tool_patterns):
                return False

    return True


def load_skills() -> list[Skill]:
    """Discover and load all SKILL.md files from SKILLS_DIR.

    Skills live in named subdirectories: SKILLS_DIR/<name>/SKILL.md
    This follows the AgentSkills standard used by opencode, Codex, and OpenClaw.

    Why runtime loading (not compiled-in)?  Skills are user-contributed content
    meant to be dropped into ~/.libreassistant/skills/ without restarting or
    recompiling.  Discovery happens on demand (at startup and /skills command)
    so new files appear immediately.
    """
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            text = skill_md.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(text)
            tools = meta.get("tools", [])
            profiles = meta.get("profiles", [])
            # Normalize: single string -> list
            if isinstance(tools, str):
                tools = [tools]
            if isinstance(profiles, str):
                profiles = [profiles]
            skills.append(Skill(
                name=meta.get("name", skill_dir.name),
                description=meta.get("description", ""),
                content=body,
                path=skill_md,
                tools=tools,
                profiles=profiles,
            ))
        except Exception:
            continue
    return skills


def get_skill_names_descriptions(profile_tool_patterns: list[str] | None = None, profile_name: str | None = None) -> str:
    """Return a compact list of available skill names and descriptions for the system prompt.

    This is the "lazy loading" pattern from opencode/Codex: only names and descriptions
    are injected into context at startup.  Full skill content is loaded on demand via
    get_skill_content() when the user triggers /<skill-name>.
    """
    skills = load_skills()
    matching = [s for s in skills if _skill_matches_profile(s, profile_tool_patterns, profile_name)]
    if not matching:
        return ""

    parts = ["## Available Skills\n"]
    parts.append("Load a skill with /<skill-name> (e.g. /tutorial)\n")
    for skill in matching:
        parts.append(f"- **{skill.name}**: {skill.description}")
    return "\n".join(parts)


def get_skill_content(name: str, profile_tool_patterns: list[str] | None = None, profile_name: str | None = None) -> str | None:
    """Load a specific skill by name and return its full content for injection into context.

    Returns None if the skill doesn't exist or doesn't match the current profile.
    """
    skills = load_skills()
    for skill in skills:
        if skill.name == name and _skill_matches_profile(skill, profile_tool_patterns, profile_name):
            return f"## Skill: {skill.name}\n\n{skill.content}"
    return None


def install_bundled_skills() -> list[str]:
    """Copy built-in skills from the package to ~/.libreassistant/skills/.

    Only copies if the target directory doesn't exist yet (preserves user edits).
    Returns a list of skill names that were installed.

    Why auto-install?  When LibreAssistant is distributed as an executable or appimage,
    users won't have a ~/.libreassistant/skills/ directory.  This ensures built-in
    skills (tutorial, skill-creator) are available on first run.
    """
    installed = []
    if not _BUNDLED_DIR.exists():
        return installed

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    for skill_dir in _BUNDLED_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        target = SKILLS_DIR / skill_dir.name
        if target.exists():
            continue  # Don't overwrite user edits
        shutil.copytree(skill_dir, target)
        installed.append(skill_dir.name)

    return installed
