# FLAML AutoML Framework Agent

The FLAML agent uses [FLAML (Fast and Lightweight AutoML)](https://github.com/microsoft/FLAML) by Microsoft Research for automated model selection and hyperparameter tuning.

## Supported Problem Types

| Problem Type | FLAML Task | Default Estimators |
|-------------|------------|-------------------|
| Classification | `classification` | lgbm, xgboost, catboost, rf, extra_tree, lrl1 |
| Regression | `regression` | lgbm, rf, catboost, xgboost, extra_tree |
| Time Series Forecasting | `ts_forecast` | lgbm, xgboost, rf, prophet, arima, sarimax |

## Architecture

Follows the standard framework agent pattern:

```
flaml/
├── agent.py           # FlamlAgent(BaseFrameworkAgent)
├── states.py          # FlamlState(BaseMLState) with time_budget, estimator_list
├── schemas.py         # FlamlStrategyPlan
├── prompts.py         # 3 prompts: classification, regression, ts_forecast
├── nodes/
│   ├── code_generator.py   # Generates FLAML AutoML training code
│   └── error_researcher.py # Web search for FLAML error resolution
└── skills/
    ├── classification/     # Estimator and metric guidance
    ├── regression/         # Regression-specific reference
    └── ts_forecast/        # Time series forecasting reference
```

## How It Works

1. The code generator creates a self-contained Python script using `flaml.AutoML`
2. FLAML automatically handles model selection and hyperparameter tuning within the time budget
3. The script outputs `===RESULTS===` JSON with standard metrics plus FLAML-specific enrichments:
   - `trial_history`: All FLAML trials with configs and losses
   - `best_estimator_type`: The winning estimator name
   - `estimator_comparison`: Best config/loss per estimator type
   - `forecast_data`: (TS only) Actual vs predicted with timestamps

## Running in Isolation

```bash
cd backend
uv run python -m scientist_bin_backend.agents.frameworks.flaml.agent
```
