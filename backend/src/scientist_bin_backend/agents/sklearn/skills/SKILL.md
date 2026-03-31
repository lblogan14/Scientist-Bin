---
name: classification
description: Scikit-learn classification skill for supervised learning tasks with categorical targets
---

# Classification Skill

This skill handles supervised classification tasks using scikit-learn.

## Capabilities

- Binary and multi-class classification
- Algorithm selection (LogisticRegression, RandomForest, GradientBoosting, SVM, KNN)
- Preprocessing pipelines (scaling, encoding, imputation)
- Cross-validation and hyperparameter tuning
- Metric evaluation (accuracy, precision, recall, F1, ROC-AUC)

## When to Use

Use this skill when the objective involves predicting a categorical label from input features. Examples:

- "Classify iris species from petal measurements"
- "Predict customer churn (yes/no)"
- "Categorize emails as spam or not spam"

## Approach

1. Load and inspect the dataset
2. Identify feature types (numeric vs categorical)
3. Build a preprocessing pipeline (imputer → scaler/encoder)
4. Train multiple classifiers with cross-validation
5. Compare metrics and select the best model
6. Output final evaluation report
