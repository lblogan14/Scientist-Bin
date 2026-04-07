---
name: evaluation
description: Cross-validation strategies, hyperparameter tuning, and model comparison patterns for scikit-learn
---

# Evaluation & Model Selection Skill

This skill provides cross-validation strategies, hyperparameter tuning approaches,
and model comparison patterns for scikit-learn workflows.

## Capabilities

- Cross-validation strategies (StratifiedKFold, KFold, TimeSeriesSplit, LeaveOneOut)
- Hyperparameter tuning (GridSearchCV, RandomizedSearchCV)
- Common hyperparameter grids for major algorithm families
- Model comparison with statistical significance
- Learning curves for overfitting/underfitting diagnosis
- Validation curves for single hyperparameter effects
- Model persistence with metadata

## When to Use

Use this skill when deciding how to evaluate and tune models. Examples:

- "Which cross-validation strategy for this imbalanced dataset?"
- "What hyperparameter grid should I use for GradientBoosting?"
- "How to compare multiple models fairly?"
- "How to diagnose overfitting with learning curves?"

## Reference

See `reference.md` in this directory for detailed cross-validation strategies,
hyperparameter grids per algorithm, model comparison patterns, and scoring references.
