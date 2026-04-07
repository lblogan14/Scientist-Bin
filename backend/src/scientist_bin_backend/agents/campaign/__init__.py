"""Campaign Orchestrator agent.

Wraps the existing 5-agent pipeline (central -> analyst -> plan -> sklearn -> summary)
in an autonomous research loop. The orchestrator generates hypotheses, runs experiments
via the inner pipeline, extracts insights, and iterates until the budget is exhausted
or results converge.
"""
