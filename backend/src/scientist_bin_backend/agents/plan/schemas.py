"""Pydantic models for the plan agent's structured I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RewrittenQuery(BaseModel):
    """Structured output from the query rewriter node.

    Enriches the user's raw objective with ML-specific details,
    explicit requirements, and constraints inferred from context.
    """

    enhanced_objective: str = Field(
        ...,
        description=(
            "A clear, detailed restatement of the user's objective "
            "enriched with ML-specific terminology and scope"
        ),
    )
    key_requirements: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit requirements extracted or inferred from the objective "
            "(e.g., 'multi-class classification', 'handle missing values', "
            "'interpretable model preferred')"
        ),
    )
    constraints: list[str] = Field(
        default_factory=list,
        description=(
            "Constraints on the solution (e.g., 'must run under 5 minutes', "
            "'no deep learning', 'scikit-learn only')"
        ),
    )


class ExecutionPlan(BaseModel):
    """Structured output from the plan writer node.

    A comprehensive execution plan covering every stage of the ML pipeline,
    from data preprocessing through model evaluation.
    """

    approach_summary: str = Field(
        ...,
        description="High-level summary of the overall approach and rationale",
    )
    problem_type: str = Field(
        ...,
        description=(
            "The ML problem type: classification, regression, clustering, "
            "dimensionality_reduction, anomaly_detection, etc."
        ),
    )
    target_column: str | None = Field(
        default=None,
        description="The target / label column name, if applicable",
    )
    algorithms_to_try: list[str] = Field(
        ...,
        description=(
            "Ordered list of algorithms to try, from simplest to most complex "
            "(e.g., ['LogisticRegression', 'RandomForestClassifier', 'GradientBoostingClassifier'])"
        ),
    )
    preprocessing_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered preprocessing steps "
            "(e.g., 'drop ID column', 'impute missing numerics with median', "
            "'one-hot encode categoricals', 'standard-scale numeric features')"
        ),
    )
    feature_engineering_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Feature engineering steps to apply "
            "(e.g., 'create polynomial features for top-3 numeric columns', "
            "'extract date components', 'bin continuous variable X')"
        ),
    )
    evaluation_metrics: list[str] = Field(
        ...,
        description=(
            "Metrics to evaluate models "
            "(e.g., ['accuracy', 'f1_weighted', 'roc_auc_ovr'] for classification)"
        ),
    )
    cv_strategy: str = Field(
        default="5-fold stratified",
        description=(
            "Cross-validation strategy "
            "(e.g., '5-fold stratified', '10-fold', 'leave-one-out', 'time-series split')"
        ),
    )
    success_criteria: dict = Field(
        default_factory=dict,
        description=(
            "Metric thresholds that define a satisfactory result "
            "(e.g., {'accuracy': 0.90, 'f1_weighted': 0.85})"
        ),
    )
    data_split_strategy: str = Field(
        default="stratified 70/15/15",
        description=(
            "How to split the data into train/validation/test sets "
            "(e.g., 'stratified 70/15/15', '80/20 random', 'time-based 70/15/15')"
        ),
    )
