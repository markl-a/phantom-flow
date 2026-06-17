"""phantom-flow: a small, local-first YAML workflow runner.

`phantom_flow.runner` reads a YAML flow definition (trigger + pipeline of
named blocks) and executes — or, with ``--dry-run``, only plans — it. Each
step resolves through a pluggable block registry: an in-process Python block,
a bounded subprocess, or an LLM call routed through the phantom-mesh `phantom`
CLI (with a deterministic stub fallback).

The engine is intentionally near-stdlib (the only hard dependency is PyYAML).
It does NOT import the two subtree-merged sister repos:

    ai_automation_framework/   <- markl-a/Automation_with_Agent
    data_analysis/             <- markl-a/Data-Analysis-with-Agents

Those are kept as a *staged source* of tools to wrap into blocks over time
(see DESIGN.md §4 and ROADMAP.md), not as a runtime dependency.
"""

__version__ = "0.1.0a0"

__all__ = ["__version__"]
