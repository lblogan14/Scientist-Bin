"""Runtime discovery and loading of SKILL.md files following the Anthropic Agent Skills spec.

Spec reference: https://agentskills.io/specification (December 2025)

A skill is a directory containing a SKILL.md file with YAML frontmatter and
markdown body. The frontmatter provides metadata (name, description, etc.)
and the body provides instructions for the agent.

Skills are discovered recursively from a root directory. Each SKILL.md found
produces a ``Skill`` dataclass with parsed metadata, body content, and
references to supporting files in the skill directory.

Three-level loading strategy (per spec):
  1. Metadata (~100 tokens): name + description, always loaded
  2. Instructions (<5000 tokens): SKILL.md body, loaded when skill is activated
  3. Resources (as needed): supporting files in the skill directory
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    """A parsed SKILL.md following the Anthropic Agent Skills specification."""

    # Required fields (spec)
    name: str
    description: str

    # Body content (instructions)
    body: str

    # File paths
    path: Path  # Path to the SKILL.md file
    directory: Path  # Skill directory (parent of SKILL.md)

    # Optional spec fields
    license: str = ""
    compatibility: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    # Supporting files discovered in the skill directory
    supporting_files: list[Path] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """One-line summary suitable for skill selection context."""
        return f"{self.name}: {self.description}"

    def format_for_prompt(self, include_body: bool = True) -> str:
        """Format skill for injection into an LLM prompt.

        When include_body=False, returns only metadata (for skill listing).
        When include_body=True, returns full instructions (for activated skill).
        """
        if not include_body:
            return f"- **{self.name}**: {self.description}"

        sections = [f"# Skill: {self.name}", f"_{self.description}_", "", self.body]
        return "\n".join(sections)


def discover_skills(skills_dir: Path) -> list[Skill]:
    """Recursively discover and parse all SKILL.md files under *skills_dir*.

    Returns a list of ``Skill`` objects sorted by name.
    Returns an empty list if the directory does not exist.
    """
    if not skills_dir.is_dir():
        return []

    skills: list[Skill] = []
    for skill_path in sorted(skills_dir.rglob("SKILL.md")):
        try:
            raw = skill_path.read_text(encoding="utf-8")
            skill = parse_skill(raw, skill_path)
            skills.append(skill)
        except Exception:
            # Skip malformed skill files
            continue

    return skills


def parse_skill(raw: str, path: Path) -> Skill:
    """Parse a SKILL.md file into a ``Skill`` dataclass.

    Extracts YAML frontmatter (``---`` delimited) and markdown body.
    Supports all Anthropic spec fields: name, description, license,
    compatibility, metadata.

    Falls back to the parent directory name if ``name:`` is missing.
    """
    skill_dir = path.parent
    default_name = skill_dir.name or path.stem

    frontmatter, body = _split_frontmatter(raw)
    fields = _parse_frontmatter(frontmatter)

    name = fields.pop("name", default_name)
    description = fields.pop("description", "")
    license_val = fields.pop("license", "")
    compatibility = fields.pop("compatibility", "")

    # Everything else goes into metadata
    metadata = fields.pop("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    # Any remaining top-level fields that aren't part of the spec
    # go into metadata as well
    for k, v in fields.items():
        if isinstance(v, str):
            metadata[k] = v

    # Discover supporting files (non-SKILL.md files in the directory)
    supporting_files = _discover_supporting_files(skill_dir)

    return Skill(
        name=name,
        description=description,
        body=body,
        path=path,
        directory=skill_dir,
        license=license_val,
        compatibility=compatibility,
        metadata=metadata,
        supporting_files=supporting_files,
    )


def match_skill(skills: list[Skill], problem_type: str, objective: str = "") -> Skill | None:
    """Find the best matching skill for a given problem type and objective.

    Uses exact name match first, then keyword matching in description.
    Returns None if no match is found.
    """
    problem_lower = problem_type.lower().strip()
    objective_lower = objective.lower()

    # Exact name match
    for skill in skills:
        if skill.name.lower() == problem_lower:
            return skill

    # Keyword match in description
    for skill in skills:
        desc_lower = skill.description.lower()
        if problem_lower in desc_lower:
            return skill

    # Fuzzy match: check if any word from the objective appears in skill descriptions
    if objective_lower:
        objective_words = set(objective_lower.split())
        best_skill = None
        best_overlap = 0
        for skill in skills:
            desc_words = set(skill.description.lower().split())
            overlap = len(objective_words & desc_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_skill = skill
        if best_overlap >= 2:
            return best_skill

    return None


def format_skill_listing(skills: list[Skill]) -> str:
    """Format all skills as a compact listing for prompt injection.

    This is the "metadata level" — only names and descriptions,
    suitable for always-loaded context (~100 tokens per skill).
    """
    if not skills:
        return "No skills available."
    return "\n".join(skill.format_for_prompt(include_body=False) for skill in skills)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_frontmatter(raw: str) -> tuple[str, str]:
    """Split SKILL.md content into frontmatter and body.

    Returns (frontmatter_str, body_str). If no frontmatter is found,
    returns ("", raw).
    """
    if not raw.startswith("---"):
        return "", raw.strip()

    # Find the closing --- delimiter
    # The first --- is at position 0, find the next one
    match = re.search(r"\n---\s*\n", raw[3:])
    if match is None:
        return "", raw.strip()

    end_of_frontmatter = 3 + match.end()
    frontmatter = raw[3 : 3 + match.start()].strip()
    body = raw[end_of_frontmatter:].strip()

    return frontmatter, body


def _parse_frontmatter(frontmatter: str) -> dict:
    """Parse YAML-style frontmatter into a dict.

    Handles simple key: value pairs and nested metadata maps.
    Does NOT require a full YAML parser — intentionally lightweight.
    """
    if not frontmatter:
        return {}

    result: dict = {}
    current_key: str | None = None
    current_map: dict[str, str] | None = None

    for line in frontmatter.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check for indented key-value (nested map entry)
        if line.startswith("  ") and current_key and ":" in stripped:
            if current_map is None:
                current_map = {}
            k, v = stripped.split(":", 1)
            current_map[k.strip()] = v.strip().strip('"').strip("'")
            continue

        # Flush any accumulated map
        if current_map is not None and current_key:
            result[current_key] = current_map
            current_map = None

        # Top-level key: value
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            key = k.strip().lower()
            value = v.strip().strip('"').strip("'")

            if not value:
                # Could be start of a nested map
                current_key = key
                current_map = {}
            else:
                result[key] = value
                current_key = key
        else:
            current_key = None

    # Flush final map
    if current_map is not None and current_key:
        result[current_key] = current_map

    return result


def _discover_supporting_files(skill_dir: Path) -> list[Path]:
    """Find supporting files in a skill directory (non-SKILL.md files)."""
    if not skill_dir.is_dir():
        return []

    supporting = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file() and p.name != "SKILL.md" and not p.name.startswith("."):
            supporting.append(p)
    return supporting
