"""Prompt templates for the central orchestrator agent."""

ANALYZER_PROMPT = """\
You are a data-science task analyzer. Given a user's objective and data description, \
determine:

1. The type of ML task (classification, regression, clustering, etc.)
2. Key data characteristics (feature count, sample size, data types if mentioned)
3. Recommended approach at a high level
4. Which framework(s) would be most appropriate

Objective: {objective}
Data description: {data_description}

Provide a clear, concise analysis.
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
