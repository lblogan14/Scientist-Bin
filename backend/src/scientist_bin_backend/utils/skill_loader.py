"""Runtime discovery of SKILL.md files from agent skill directories."""

from __future__ import annotations

from pathlib import Path


def discover_skills(skills_dir: Path) -> list[dict]:
    """Walk *skills_dir* and return metadata for every ``SKILL.md`` found.

    Each returned dict has keys ``name``, ``description``, ``path``, and
    ``content``.  The name and description are extracted from YAML-style
    frontmatter (``---`` delimited) if present; otherwise the filename stem
    is used as the name.
    """
    skills: list[dict] = []
    if not skills_dir.is_dir():
        return skills

    for skill_path in sorted(skills_dir.rglob("SKILL.md")):
        raw = skill_path.read_text(encoding="utf-8")
        name, description, content = _parse_skill(raw, skill_path)
        skills.append(
            {
                "name": name,
                "description": description,
                "path": str(skill_path),
                "content": content,
            }
        )
    return skills


def _parse_skill(raw: str, path: Path) -> tuple[str, str, str]:
    """Extract frontmatter fields and body from a SKILL.md file."""
    name = path.parent.name or path.stem
    description = ""
    content = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            content = parts[2].strip()
            for line in frontmatter.splitlines():
                line = line.strip()
                if line.lower().startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.lower().startswith("description:"):
                    description = line.split(":", 1)[1].strip()

    return name, description, content
