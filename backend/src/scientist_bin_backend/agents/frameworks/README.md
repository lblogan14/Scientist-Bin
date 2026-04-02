# Framework Agents

ML framework subagents that generate, execute, and iteratively refine training code. Each framework is a directory under `frameworks/`.

## Available Frameworks

| Framework | Directory | Status |
|-----------|-----------|--------|
| scikit-learn | `sklearn/` | Active |
| PyTorch | `pytorch/` | Planned |
| TensorFlow | `tensorflow/` | Planned |
| HuggingFace | `huggingface/` | Planned |

## Adding a New Framework

1. Create a directory: `frameworks/<name>/`
2. Extend `BaseFrameworkAgent` from `agents/base/agent.py`:

```python
from scientist_bin_backend.agents.base.agent import BaseFrameworkAgent
from scientist_bin_backend.agents.base.graph import build_framework_graph

class MyFrameworkAgent(BaseFrameworkAgent):
    framework_name = "<name>"

    def _build_graph(self, checkpointer):
        return build_framework_graph(
            state_class=MyFrameworkState,
            generate_code_node=generate_code,       # Your code gen node
            error_research_node=error_research,      # Optional
            checkpointer=checkpointer,
        )
```

3. Implement at minimum:
   - `nodes/code_generator.py` -- Framework-specific code generation (1 LLM call)
   - `prompts.py` -- Code generation prompt for the framework
   - `states.py` -- Extend `BaseMLState` with framework-specific fields (or thin alias)

4. Optional:
   - `nodes/error_researcher.py` -- Framework-specific error search
   - `schemas.py` -- Framework-specific Pydantic schemas
   - `skills/` -- SKILL.md files for task types

5. Register in `agents/central/nodes/router.py`:
```python
FRAMEWORK_REGISTRY = {
    "sklearn": "...agents.frameworks.sklearn.agent.SklearnAgent",
    "<name>": "...agents.frameworks.<name>.agent.MyFrameworkAgent",
}
```

6. Add model mapping in `utils/llm.py` `AGENT_MODELS` dict.

## What the Base Provides

Framework agents inherit the full iteration loop from `agents/base/`:
- **validate_code** -- Static analysis before execution (syntax, imports, markers)
- **execute_code** -- Sandboxed subprocess with timeout and metrics streaming
- **analyze_results** -- LLM-driven iteration decisions (IMPROVE pattern)
- **evaluate_on_test** -- Held-out test set evaluation after accepting a model
- **finalize** -- Final report generation
- **State management** -- `BaseMLState` with all pipeline fields
- **run() interface** -- Common invocation with standardized input/output

Framework agents only need to implement `generate_code` (and optionally `error_research`).
