# Sklearn Skills

Modular skill definitions following the [Anthropic Agent Skills specification](https://agentskills.io/specification). Each skill provides problem-type-specific algorithm guidance, parameter grids, and code patterns that are injected into the code generator's LLM prompt.

## Directory Structure

Each skill lives in its own subdirectory with two files:

```
skills/
├── classification/
│   ├── SKILL.md          — Lightweight routing entry (metadata + when-to-use)
│   └── reference.md      — Comprehensive algorithm decision trees and parameter grids
├── regression/
│   ├── SKILL.md
│   └── reference.md
├── clustering/
│   ├── SKILL.md
│   └── reference.md
├── evaluation/
│   ├── SKILL.md
│   └── reference.md
├── preprocessing/
│   ├── SKILL.md
│   └── reference.md
└── __init__.py
```

### File Roles

| File | Size | Purpose |
|------|------|---------|
| `SKILL.md` | ~100 tokens | YAML frontmatter (`name`, `description`) + brief markdown body. Used for skill routing and selection. Defines capabilities, when-to-use examples, and high-level approach. |
| `reference.md` | ~2000-6000 chars | Comprehensive technical reference injected into the code generation prompt. Contains algorithm decision trees, parameter grids, evaluation metric guidance, and code patterns. |

## How Skills Are Discovered and Injected

The skill system is implemented in `utils/skill_loader.py` with two key functions:

### `discover_skills(skills_dir)`

Recursively scans the `skills/` directory for `SKILL.md` files. For each file found:
1. Parses YAML frontmatter (name, description, license, compatibility, metadata)
2. Extracts the markdown body (instructions)
3. Discovers supporting files in the same directory (e.g., `reference.md`)
4. Returns a sorted list of `Skill` dataclass instances

### `match_skill(skills, problem_type)`

Finds the best skill match for a given problem type using a 3-tier strategy:
1. **Exact name match** -- skill `name` equals `problem_type` (e.g., `"clustering"`)
2. **Keyword match** -- `problem_type` appears in the skill's `description`
3. **Fuzzy match** -- word overlap between the objective and skill descriptions (requires >= 2 matching words)

### Injection in Code Generation

In `nodes/code_generator.py`, the `generate_code` function:
1. Calls `discover_skills(_SKILLS_DIR)` to find all available skills
2. Calls `match_skill(skills, problem_type)` to select the relevant skill
3. Reads `reference.md` from the matched skill's `supporting_files`
4. Truncates to 6000 characters (configurable via `_MAX_REFERENCE_CHARS`)
5. Prepends the content as a `== SKILL REFERENCE ==` block in the prompt

This ensures the LLM has access to curated algorithm selection logic and parameter grids specific to the problem type being solved.

## Available Skills

| Skill | Problem Type | Algorithms Covered | Key Metrics |
|-------|---|---|---|
| `classification` | Supervised (categorical target) | LogisticRegression, RandomForest, GradientBoosting, SVM, KNN | accuracy, F1, precision, recall, ROC-AUC |
| `regression` | Supervised (continuous target) | LinearRegression, Ridge, Lasso, ElasticNet, RandomForest, GBR, SVR | MAE, RMSE, R2, explained variance |
| `clustering` | Unsupervised (no target) | KMeans, MiniBatchKMeans, DBSCAN, HDBSCAN, OPTICS, Agglomerative | silhouette, Calinski-Harabasz, Davies-Bouldin |
| `evaluation` | Cross-cutting | StratifiedKFold, KFold, TimeSeriesSplit, GridSearchCV, RandomizedSearchCV | (strategy guidance, not algorithms) |
| `preprocessing` | Cross-cutting | StandardScaler, MinMaxScaler, OneHotEncoder, SimpleImputer, ColumnTransformer | (pipeline patterns, not metrics) |

## Three-Level Loading Strategy

Per the Anthropic Agent Skills spec, skills use a progressive loading approach:

1. **Metadata** (~100 tokens) -- `name` + `description` from YAML frontmatter. Always available for skill selection decisions.
2. **Instructions** (<5000 tokens) -- `SKILL.md` body. Loaded when a skill is activated for routing context.
3. **Resources** (as needed) -- Supporting files like `reference.md`. Loaded and injected into prompts only when generating code for the matched problem type.

## Key Files

| File | Purpose |
|------|---------|
| `utils/skill_loader.py` | `discover_skills()`, `match_skill()`, `parse_skill()`, `format_skill_listing()` |
| `nodes/code_generator.py` | `_load_skill_reference()` -- loads and truncates `reference.md` for prompt injection |
