"""Pydantic models for the plan agent's structured I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """Structured output from the plan writer node.

    A comprehensive execution plan covering algorithm selection, sklearn
    pipeline preprocessing, feature engineering, evaluation strategy, and
    hyperparameter tuning.

    Note: Data cleaning and train/val/test splitting are handled by the
    upstream analyst agent. This plan focuses on what the sklearn agent
    controls inside the training pipeline.
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
    pipeline_preprocessing_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered sklearn-pipeline-level preprocessing steps that run inside "
            "the training pipeline (e.g., 'StandardScaler on numeric features', "
            "'OneHotEncoder on categorical features', 'ColumnTransformer to combine'). "
            "These are NOT data-cleaning steps — the analyst agent handles cleaning."
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
    hyperparameter_tuning_approach: str = Field(
        default="GridSearchCV for small search spaces, RandomizedSearchCV for large ones",
        description=(
            "Strategy for hyperparameter tuning per algorithm "
            "(e.g., 'GridSearchCV for LogisticRegression, "
            "RandomizedSearchCV with 50 iterations for ensemble methods')"
        ),
    )
