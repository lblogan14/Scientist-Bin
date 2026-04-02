"""State schema for the scikit-learn subagent.

``SklearnState`` inherits all fields from ``BaseMLState``.  Currently sklearn
needs no extra state fields beyond what the base provides, so this is a thin
alias.  If sklearn-specific state is needed later (e.g. a
``use_grid_search`` flag), add it here.
"""

from __future__ import annotations

from scientist_bin_backend.agents.base.states import BaseMLState


class SklearnState(BaseMLState, total=False):
    """Typed state for the sklearn subagent graph.

    Inherits every field from ``BaseMLState``.  Add sklearn-specific
    fields below this docstring when needed.
    """
