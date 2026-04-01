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
- Cross-validation and hyperparameter tuning (GridSearchCV, RandomizedSearchCV)
- Metric evaluation (accuracy, precision, recall, F1, ROC-AUC, confusion matrix)
- Class imbalance handling (stratified splits, class weights, SMOTE)

## When to Use

Use this skill when the objective involves predicting a categorical label from input features. Examples:

- "Classify iris species from petal measurements"
- "Predict customer churn (yes/no)"
- "Categorize emails as spam or not spam"
- "Detect fraudulent transactions"

## Approach

1. Load and inspect the dataset (automated EDA)
2. Identify feature types (numeric vs categorical)
3. Detect class imbalance and adjust strategy
4. Build a preprocessing pipeline (imputer -> scaler/encoder via ColumnTransformer)
5. Start with simple models (LogisticRegression) as baseline
6. Progress to ensemble methods (RandomForest, GradientBoosting)
7. Tune hyperparameters via cross-validated search
8. Compare metrics across algorithms and select best model
9. Generate final evaluation report with interpretation
