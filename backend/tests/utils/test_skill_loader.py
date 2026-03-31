"""Tests for the SKILL.md loader following the Anthropic Agent Skills spec."""

from pathlib import Path

from scientist_bin_backend.utils.skill_loader import (
    Skill,
    discover_skills,
    format_skill_listing,
    match_skill,
    parse_skill,
)

SKLEARN_SKILLS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "scientist_bin_backend"
    / "agents"
    / "sklearn"
    / "skills"
)


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def test_parse_skill_full_frontmatter():
    raw = """\
---
name: classification
description: Classify things into categories
license: Apache-2.0
compatibility: Requires scikit-learn
metadata:
  author: test-org
  version: "1.0"
---

# Classification

Some instructions here.
"""
    path = Path("/fake/classification/SKILL.md")
    skill = parse_skill(raw, path)

    assert skill.name == "classification"
    assert skill.description == "Classify things into categories"
    assert skill.license == "Apache-2.0"
    assert skill.compatibility == "Requires scikit-learn"
    assert skill.metadata["author"] == "test-org"
    assert skill.metadata["version"] == "1.0"
    assert "# Classification" in skill.body
    assert "Some instructions here." in skill.body


def test_parse_skill_minimal_frontmatter():
    raw = """\
---
name: regression
description: Predict numbers
---

Body content.
"""
    path = Path("/fake/regression/SKILL.md")
    skill = parse_skill(raw, path)

    assert skill.name == "regression"
    assert skill.description == "Predict numbers"
    assert skill.license == ""
    assert skill.body == "Body content."


def test_parse_skill_no_frontmatter():
    raw = "# Just a title\n\nSome content without frontmatter."
    path = Path("/fake/my-skill/SKILL.md")
    skill = parse_skill(raw, path)

    assert skill.name == "my-skill"  # Falls back to directory name
    assert skill.description == ""
    assert "Just a title" in skill.body


def test_parse_skill_name_fallback_to_directory():
    raw = """\
---
description: Only a description, no name
---

Content.
"""
    path = Path("/fake/auto-name/SKILL.md")
    skill = parse_skill(raw, path)

    assert skill.name == "auto-name"
    assert skill.description == "Only a description, no name"


def test_parse_skill_quoted_values():
    raw = """\
---
name: "quoted-name"
description: 'single-quoted description'
---

Body.
"""
    path = Path("/fake/skill/SKILL.md")
    skill = parse_skill(raw, path)

    assert skill.name == "quoted-name"
    assert skill.description == "single-quoted description"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def test_discover_skills_from_real_directory():
    """Test discovery against the actual sklearn skills directory."""
    skills = discover_skills(SKLEARN_SKILLS_DIR)

    assert len(skills) >= 3
    names = {s.name for s in skills}
    assert "classification" in names
    assert "regression" in names
    assert "clustering" in names


def test_discover_skills_classification_content():
    """Verify the classification skill is properly parsed."""
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    classification = next(s for s in skills if s.name == "classification")

    assert "categorical targets" in classification.description
    assert "LogisticRegression" in classification.body
    assert "RandomForest" in classification.body
    assert classification.directory.name == "classification"


def test_discover_skills_regression_content():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    regression = next(s for s in skills if s.name == "regression")

    assert "continuous numeric" in regression.description
    assert "LinearRegression" in regression.body


def test_discover_skills_empty_directory(tmp_path):
    skills = discover_skills(tmp_path)
    assert skills == []


def test_discover_skills_nonexistent_directory():
    skills = discover_skills(Path("/does/not/exist"))
    assert skills == []


def test_discover_skills_with_temp_skills(tmp_path):
    """Create temp skill files and verify discovery."""
    (tmp_path / "skill-a").mkdir()
    (tmp_path / "skill-a" / "SKILL.md").write_text(
        "---\nname: skill-a\ndescription: First skill\n---\n\nBody A.",
        encoding="utf-8",
    )
    (tmp_path / "skill-b").mkdir()
    (tmp_path / "skill-b" / "SKILL.md").write_text(
        "---\nname: skill-b\ndescription: Second skill\n---\n\nBody B.",
        encoding="utf-8",
    )

    skills = discover_skills(tmp_path)
    assert len(skills) == 2
    assert skills[0].name == "skill-a"
    assert skills[1].name == "skill-b"


def test_discover_skills_with_supporting_files(tmp_path):
    """Verify supporting files are discovered."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: Test\n---\n\nBody.",
        encoding="utf-8",
    )
    (skill_dir / "REFERENCE.md").write_text("Reference docs", encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "helper.py").write_text("print('hi')", encoding="utf-8")

    skills = discover_skills(tmp_path)
    assert len(skills) == 1
    supporting = [p.name for p in skills[0].supporting_files]
    assert "REFERENCE.md" in supporting
    assert "helper.py" in supporting


# ---------------------------------------------------------------------------
# Skill matching
# ---------------------------------------------------------------------------


def test_match_skill_exact_name():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    matched = match_skill(skills, "classification")
    assert matched is not None
    assert matched.name == "classification"


def test_match_skill_case_insensitive():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    matched = match_skill(skills, "Classification")
    assert matched is not None
    assert matched.name == "classification"


def test_match_skill_regression():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    matched = match_skill(skills, "regression")
    assert matched is not None
    assert matched.name == "regression"


def test_match_skill_clustering():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    matched = match_skill(skills, "clustering")
    assert matched is not None
    assert matched.name == "clustering"


def test_match_skill_no_match():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    matched = match_skill(skills, "reinforcement_learning")
    assert matched is None


def test_match_skill_by_objective_keywords():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    # Use words that overlap with classification description:
    # "supervised learning tasks with categorical targets"
    matched = match_skill(
        skills, "unknown_type", objective="supervised learning categorical targets"
    )
    assert matched is not None
    assert matched.name == "classification"


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def test_format_skill_listing():
    skills = discover_skills(SKLEARN_SKILLS_DIR)
    listing = format_skill_listing(skills)

    assert "classification" in listing
    assert "regression" in listing
    assert "clustering" in listing
    # Listing should be compact (no full body)
    assert "LogisticRegression" not in listing


def test_format_skill_listing_empty():
    assert format_skill_listing([]) == "No skills available."


def test_skill_format_for_prompt_metadata_only():
    skill = Skill(
        name="test",
        description="A test skill",
        body="Long body content here",
        path=Path("/fake/SKILL.md"),
        directory=Path("/fake"),
    )
    output = skill.format_for_prompt(include_body=False)
    assert "test" in output
    assert "A test skill" in output
    assert "Long body content" not in output


def test_skill_format_for_prompt_full():
    skill = Skill(
        name="test",
        description="A test skill",
        body="Long body content here",
        path=Path("/fake/SKILL.md"),
        directory=Path("/fake"),
    )
    output = skill.format_for_prompt(include_body=True)
    assert "# Skill: test" in output
    assert "Long body content here" in output


def test_skill_summary():
    skill = Skill(
        name="test",
        description="A test skill",
        body="",
        path=Path("/fake/SKILL.md"),
        directory=Path("/fake"),
    )
    assert skill.summary == "test: A test skill"
