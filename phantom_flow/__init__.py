"""phantom-flow: a minimal local-first YAML workflow runner.

`phantom_flow.runner` reads a YAML flow definition and dispatches each
pipeline step to an in-process Python block (HTTP GET, regex/keyword
filters, an `if` gate, a `subprocess` escape hatch) or an optional
phantom-mesh provider call via `phantom_flow.llm_driver`. There is no
external framework dependency; the whole engine is ~500 LOC.
"""

__version__ = "0.1.0a0"

__all__ = ["__version__"]
