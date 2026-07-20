"""PmSkillsLoader - Load pm-skills from local files."""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional

# Base path for pm-skills repository
PM_SKILLS_BASE = Path(__file__).parent / "pm-skills"


def _extract_skill_metadata(skill_md_content: str) -> dict:
    """Extract metadata from SKILL.md content."""
    metadata = {
        "name": "",
        "description": "",
    }

    # Extract name and description from YAML frontmatter
    frontmatter_match = re.match(r"---\s*\n(.*?)\n---", skill_md_content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        name_match = re.search(r'name:\s*"?([^"\n]+)"?', frontmatter)
        desc_match = re.search(r'description:\s*"([^"]+)"', frontmatter)
        if name_match:
            metadata["name"] = name_match.group(1).strip()
        if desc_match:
            metadata["description"] = desc_match.group(1).strip()

    return metadata


def _compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_skill(skill_id: str) -> Optional[dict]:
    """Load a single pm-skill by its ID.

    Args:
        skill_id: Skill ID in format "pm-skills/<plugin>/<skill>" or just "<plugin>/<skill>"

    Returns:
        dict with skill metadata and content, or None if not found
    """
    # Normalize skill_id
    if skill_id.startswith("pm-skills/"):
        skill_id = skill_id[len("pm-skills/") :]

    # skill_id is now "<plugin>/<skill>"
    parts = skill_id.split("/")
    if len(parts) != 2:
        return None

    plugin, skill = parts
    skill_path = PM_SKILLS_BASE / plugin / "skills" / skill / "SKILL.md"

    if not skill_path.exists():
        return None

    content = skill_path.read_text(encoding="utf-8")
    metadata = _extract_skill_metadata(content)

    return {
        "id": f"pm-skills/{skill_id}",
        "plugin": plugin,
        "skill": skill,
        "name": metadata["name"] or skill,
        "description": metadata["description"],
        "content": content,
        "methodology_ref": str(skill_path.relative_to(PM_SKILLS_BASE)),
        "hash": _compute_file_hash(skill_path),
    }


def list_skills(plugin: Optional[str] = None) -> list[dict]:
    """List all available pm-skills.

    Args:
        plugin: Optional plugin name to filter by

    Returns:
        List of skill metadata dicts
    """
    skills = []

    if plugin:
        plugins = [plugin]
    else:
        # List all plugin directories
        plugins = []
        if PM_SKILLS_BASE.exists():
            for item in PM_SKILLS_BASE.iterdir():
                if item.is_dir() and item.name.startswith("pm-"):
                    plugins.append(item.name)

    for p in plugins:
        skills_dir = PM_SKILLS_BASE / p / "skills"
        if not skills_dir.exists():
            continue

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            content = skill_md.read_text(encoding="utf-8")
            metadata = _extract_skill_metadata(content)

            skills.append(
                {
                    "id": f"pm-skills/{p}/{skill_dir.name}",
                    "plugin": p,
                    "skill": skill_dir.name,
                    "name": metadata["name"] or skill_dir.name,
                    "description": metadata["description"],
                    "methodology_ref": str(skill_md.relative_to(PM_SKILLS_BASE)),
                }
            )

    return skills


def list_plugins() -> list[str]:
    """List all available pm-skills plugins."""
    plugins = []
    if PM_SKILLS_BASE.exists():
        for item in PM_SKILLS_BASE.iterdir():
            if item.is_dir() and item.name.startswith("pm-"):
                plugins.append(item.name)
    return sorted(plugins)


def scan_skills() -> list[dict]:
    """Scan all pm-skills and return their metadata.

    Returns:
        List of skill metadata dicts with id, plugin, skill, name, description
    """
    return list_skills()


def get_skill_content(skill_id: str) -> Optional[str]:
    """Get the raw content of a skill's SKILL.md file.

    Args:
        skill_id: Skill ID in format "pm-skills/<plugin>/<skill>"

    Returns:
        Raw SKILL.md content or None if not found
    """
    skill = load_skill(skill_id)
    return skill["content"] if skill else None
