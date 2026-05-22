"""phantom-flow: event-driven workflow engine on top of phantom-mesh.

The wrapper layer in this package is intentionally thin. The substantive
implementation comes from two subtree-merged sister repos:

    ai_automation_framework/   <- markl-a/Automation_with_Agent
    data_analysis/             <- markl-a/Data-Analysis-with-Agents

`phantom_flow.runner` reads a YAML flow definition and dispatches each
pipeline step to either an in-process Python block, a subprocess shelling
into the merged framework, or a phantom-mesh provider call.
"""

__version__ = "0.1.0a0"

__all__ = ["__version__"]
