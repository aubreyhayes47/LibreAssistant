"""Tests for skills.py (skill loader, frontmatter parsing, filtering, bundled install)."""
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from libreassistant.skills import (
    Skill,
    _parse_frontmatter,
    _skill_matches_profile,
    load_skills,
    get_skill_names_descriptions,
    get_skill_content,
    install_bundled_skills,
)


# --- Frontmatter parsing ---

class TestParseFrontmatter:
    def test_basic_frontmatter(self):
        text = "---\nname: test\ndescription: A test skill\n---\n\nBody content here"
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "test"
        assert meta["description"] == "A test skill"
        assert body == "Body content here"

    def test_no_frontmatter(self):
        text = "Just a markdown file with no frontmatter"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_unclosed_frontmatter(self):
        text = "---\nname: test\nNo closing delimiter"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_comma_separated_tools(self):
        text = "---\nname: test\ntools: terminal,read,write\n---\n\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["tools"] == ["terminal", "read", "write"]

    def test_comma_separated_profiles(self):
        text = "---\nname: test\nprofiles: default,legal\n---\n\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["profiles"] == ["default", "legal"]

    def test_single_tool_no_split(self):
        text = "---\nname: test\ntools: terminal\n---\n\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["tools"] == "terminal"  # Single value stays as string

    def test_description_comma_not_split(self):
        text = "---\nname: test\ndescription: Does alpha, beta, and gamma\n---\n\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta["description"] == "Does alpha, beta, and gamma"

    def test_horizontal_rule_in_body_not_confused(self):
        """Markdown --- in body should NOT be treated as frontmatter delimiter."""
        text = "---\nname: test\n---\n\n# Title\n\nSome text\n\n---\n\nMore text"
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "test"
        assert "More text" in body
        assert body.startswith("# Title")

    def test_empty_frontmatter(self):
        text = "---\n---\n\nBody"
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == "Body"


# --- Skill matching ---

class TestSkillMatching:
    def test_skill_with_no_restrictions_matches_all(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=[], profiles=[])
        assert _skill_matches_profile(skill, None) is True
        assert _skill_matches_profile(skill, ["read", "write"]) is True

    def test_skill_requires_tool_not_available(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=["terminal"], profiles=[])
        assert _skill_matches_profile(skill, ["read", "write"]) is False

    def test_skill_requires_tool_available(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=["terminal"], profiles=[])
        assert _skill_matches_profile(skill, ["terminal", "read"]) is True

    def test_skill_requires_tool_glob_match(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=["mcp/courtlistener/*"], profiles=[])
        assert _skill_matches_profile(skill, ["mcp/courtlistener/*", "read"]) is True
        assert _skill_matches_profile(skill, ["mcp/*", "read"]) is True

    def test_skill_targets_specific_profile(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=[], profiles=["legal"])
        assert _skill_matches_profile(skill, None, "legal") is True
        assert _skill_matches_profile(skill, None, "default") is False

    def test_skill_targets_all_profiles_when_empty(self):
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=[], profiles=[])
        assert _skill_matches_profile(skill, None, "default") is True
        assert _skill_matches_profile(skill, None, "legal") is True

    def test_profile_none_tool_patterns_means_all_tools(self):
        """When profile_tool_patterns is None, all tools are allowed."""
        skill = Skill(name="test", description="desc", content="", path=Path("."), tools=["terminal"], profiles=[])
        assert _skill_matches_profile(skill, None) is True


# --- Skill loading from disk ---

class TestLoadSkills:
    def test_load_skills_from_temp_dir(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: my-skill\ndescription: Test skill\ntools: read\n---\n\n# My Skill\n\nDo stuff.")

        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()

        assert len(skills) == 1
        assert skills[0].name == "my-skill"
        assert skills[0].description == "Test skill"
        assert skills[0].tools == ["read"]
        assert "# My Skill" in skills[0].content

    def test_load_skills_empty_dir(self, tmp_path):
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
        assert skills == []

    def test_load_skills_ignores_non_directories(self, tmp_path):
        (tmp_path / "readme.md").write_text("not a skill")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
        assert skills == []

    def test_load_skills_ignores_dirs_without_skill_md(self, tmp_path):
        skill_dir = tmp_path / "incomplete"
        skill_dir.mkdir()
        (skill_dir / "notes.md").write_text("not SKILL.md")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
        assert skills == []

    def test_load_skills_ignores_flat_files(self, tmp_path):
        """Old-style flat .md files should not be loaded — only skills/<name>/SKILL.md directories."""
        (tmp_path / "old-style.md").write_text("---\nname: old\ndescription: Old\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
        assert skills == []

    def test_load_skills_multiple(self, tmp_path):
        for name in ["alpha", "beta"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name} skill\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
        assert len(skills) == 2
        assert [s.name for s in skills] == ["alpha", "beta"]


# --- get_skill_names_descriptions ---

class TestGetSkillNamesDescriptions:
    def test_returns_empty_when_no_skills(self, tmp_path):
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_names_descriptions()
        assert result == ""

    def test_returns_listing(self, tmp_path):
        d = tmp_path / "test-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test-skill\ndescription: Does testing\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_names_descriptions()
        assert "test-skill" in result
        assert "Does testing" in result
        assert "Available Skills" in result

    def test_filters_by_profile_tool_patterns(self, tmp_path):
        d = tmp_path / "terminal-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: terminal-skill\ndescription: Needs terminal\ntools: terminal\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_names_descriptions(["read", "write"])  # No terminal access
        assert result == ""  # Filtered out

    def test_filters_by_profile_name(self, tmp_path):
        d = tmp_path / "legal-only"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: legal-only\ndescription: Legal skill\nprofiles: legal\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_names_descriptions(None, "default")
        assert result == ""  # Filtered out — default doesn't match profiles: legal


# --- get_skill_content ---

class TestGetSkillContent:
    def test_returns_content_for_matching_skill(self, tmp_path):
        d = tmp_path / "test"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test\ndescription: Test\n---\n\n# Instructions\n\nDo the thing.")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_content("test")
        assert result is not None
        assert "# Instructions" in result
        assert "Skill: test" in result

    def test_returns_none_for_unknown_skill(self, tmp_path):
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_content("nonexistent")
        assert result is None

    def test_returns_none_when_tool_filtered(self, tmp_path):
        d = tmp_path / "restricted"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: restricted\ndescription: Needs terminal\ntools: terminal\n---\n\nBody")
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_content("restricted", ["read", "write"])  # No terminal
        assert result is None


# --- install_bundled_skills ---

class TestInstallBundledSkills:
    def test_installs_bundled_skills(self, tmp_path):
        bundled = tmp_path / "bundled"
        bundled.mkdir()
        skill_dir = bundled / "tutorial"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: tutorial\ndescription: Tutorial\n---\n\nBody")

        target = tmp_path / "user_skills"
        with patch("libreassistant.skills.SKILLS_DIR", target), \
             patch("libreassistant.skills._BUNDLED_DIR", bundled):
            installed = install_bundled_skills()

        assert installed == ["tutorial"]
        assert (target / "tutorial" / "SKILL.md").exists()

    def test_skips_existing_skills(self, tmp_path):
        bundled = tmp_path / "bundled"
        bundled.mkdir()
        skill_dir = bundled / "tutorial"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: tutorial\ndescription: Tutorial\n---\n\nBody")

        target = tmp_path / "user_skills"
        target.mkdir()
        existing = target / "tutorial"
        existing.mkdir()
        (existing / "SKILL.md").write_text("---\nname: tutorial\ndescription: My custom version\n---\n\nCustom")

        with patch("libreassistant.skills.SKILLS_DIR", target), \
             patch("libreassistant.skills._BUNDLED_DIR", bundled):
            installed = install_bundled_skills()

        assert installed == []  # Skipped — already exists
        assert (target / "tutorial" / "SKILL.md").read_text().startswith("---\nname: tutorial\ndescription: My custom version")

    def test_returns_empty_when_no_bundled_dir(self, tmp_path):
        bundled = tmp_path / "nonexistent"
        with patch("libreassistant.skills._BUNDLED_DIR", bundled):
            installed = install_bundled_skills()
        assert installed == []


# --- Built-in skills exist ---

class TestBuiltinSkills:
    def test_tutorial_skill_exists(self):
        """The bundled tutorial skill should be present in the package."""
        from libreassistant.skills import _BUNDLED_DIR
        tutorial_md = _BUNDLED_DIR / "tutorial" / "SKILL.md"
        assert tutorial_md.exists(), f"Bundled tutorial missing at {tutorial_md}"

    def test_skill_creator_skill_exists(self):
        """The bundled skill-creator skill should be present in the package."""
        from libreassistant.skills import _BUNDLED_DIR
        creator_md = _BUNDLED_DIR / "skill-creator" / "SKILL.md"
        assert creator_md.exists(), f"Bundled skill-creator missing at {creator_md}"

    def test_tutorial_frontmatter_valid(self):
        """Tutorial skill should have valid frontmatter with required fields."""
        from libreassistant.skills import _BUNDLED_DIR
        text = (_BUNDLED_DIR / "tutorial" / "SKILL.md").read_text()
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "tutorial"
        assert meta["description"]
        assert body  # Non-empty body

    def test_skill_creator_frontmatter_valid(self):
        """Skill-creator skill should have valid frontmatter with required fields."""
        from libreassistant.skills import _BUNDLED_DIR
        text = (_BUNDLED_DIR / "skill-creator" / "SKILL.md").read_text()
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "skill-creator"
        assert meta["description"]
        assert body


# --- Skills tool ---

class TestSkillsTool:
    def _make_registry(self, tmp_path, profile_name="default"):
        """Create a minimal ToolRegistry with current_profile set for testing."""
        from libreassistant.tool_registry import ToolRegistry
        reg = ToolRegistry()
        reg.current_profile = profile_name
        return reg

    def test_handle_skills_list(self, tmp_path):
        """Listing skills returns names and descriptions."""
        from libreassistant.tools import register_all
        d = tmp_path / "test-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: test-skill\ndescription: A test skill\n---\n\nBody")

        reg = self._make_registry(tmp_path)
        # We need to test handle_skills directly, but it's defined inside register_all.
        # Instead, test via the skills module functions which the tool wraps.
        from libreassistant.skills import load_skills, _skill_matches_profile
        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            skills = load_skills()
            matching = [s for s in skills if _skill_matches_profile(s, None, "default")]
        assert len(matching) == 1
        assert matching[0].name == "test-skill"

    def test_handle_skills_read(self, tmp_path):
        """Reading a specific skill returns its full content."""
        from libreassistant.skills import get_skill_content
        d = tmp_path / "my-skill"
        d.mkdir()
        (d / "SKILL.md").write_text("---\nname: my-skill\ndescription: Does stuff\n---\n\n# Instructions\n\nDo the thing.")

        with patch("libreassistant.skills.SKILLS_DIR", tmp_path):
            result = get_skill_content("my-skill")
        assert result is not None
        assert "# Instructions" in result
        assert "my-skill" in result
