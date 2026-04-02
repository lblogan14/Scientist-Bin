"""Prompt templates for the central orchestrator agent."""

ANALYZER_PROMPT = """\
You are a data-science task analyzer. Given a user's objective and data description, \
produce a structured analysis covering:

1. The ML task type (classification, regression, clustering, \
dimensionality_reduction, anomaly_detection)
2. The task subtype if applicable (e.g. binary, multiclass, multi-label, ordinal)
3. Estimated data characteristics (feature count, sample size, data types, \
target column hint, missing values, class imbalance) — infer from context or \
mark as unknown
4. A recommended approach in 2-3 sentences
5. Complexity estimate (low, medium, high) based on the problem and data
6. Key considerations the downstream pipeline should watch for \
(e.g. class imbalance, missing data, high cardinality, time-series ordering)
7. Suggested frameworks ranked by suitability. Currently supported: sklearn. \
Planned: pytorch, tensorflow, transformers, diffusers.

Objective: {objective}
Data description: {data_description}

Analyze the request and fill in all fields of the structured output.
"""

ROUTER_PROMPT = """\
You are a framework selector for a data-science automation system. Based on the \
analysis of the user's request, select the most appropriate ML framework.

Currently supported frameworks:
- sklearn: Best for classical ML (classification, regression, clustering, \
  dimensionality reduction) with tabular data.

Planned (not yet available):
- pytorch: Deep learning, custom architectures
- tensorflow: Deep learning, production deployment
- transformers: NLP, vision via pretrained models
- diffusers: Image generation

Analysis context:
{analysis}

Original objective: {objective}
User's framework preference: {framework_preference}

Select the framework. If the user has a preference and it is available, honour it. \
If the requested framework is not yet supported, default to sklearn and explain why.
"""
