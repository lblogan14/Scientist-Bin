"""State schema for the FLAML AutoML subagent.

``FlamlState`` extends ``BaseMLState`` with FLAML-specific fields for
time budgets, estimator selection, and time series forecasting.
"""

from __future__ import annotations

from scientist_bin_backend.agents.base.states import BaseMLState


class FlamlState(BaseMLState, total=False):
    """Typed state for the FLAML subagent graph.

    Inherits every field from ``BaseMLState``.  FLAML-specific fields
    capture AutoML configuration that the code generator needs.
    """

    time_budget: int | None  # seconds for AutoML search
    estimator_list: list[str] | None  # which estimators to try
    flaml_metric: str | None  # optimization metric override
    ts_period: int | None  # forecast horizon for ts_forecast tasks
