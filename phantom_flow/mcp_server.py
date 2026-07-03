"""MCP server for phantom-flow.

Exposes the *existing*, tested local YAML flow engine (``phantom_flow.runner``)
as Model Context Protocol tools so the phantom-mesh can drive flows over
JSON-RPC. This module adds NO new engine features — every tool is a thin
wrapper around already-shipped functions:

- ``flow_run``        -> ``load_flow`` + ``run_flow`` + ``build_run_artifact``
- ``flow_list_blocks``-> reads ``BLOCK_REGISTRY``

Run as a server (what the mesh launches)::

    python -m phantom_flow.mcp_server
    phantom-flow-mcp
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from phantom_flow.runner import (
    BLOCK_REGISTRY,
    FlowExecutionError,
    build_run_artifact,
    load_flow,
    run_flow,
)

mcp = FastMCP("phantom-flow")


@mcp.tool()
def flow_run(path: str, dry_run: bool = False) -> Dict[str, Any]:
    """Run a local phantom-flow YAML flow file and return its run artifact.

    Wraps the tested engine: loads the flow (``load_flow``), executes it
    (``run_flow``), and returns the stable, JSON-serialisable run artifact
    (``build_run_artifact``) carrying the plan + structured RunRecord. A flow
    that fails or is blocked on approval still returns an artifact — with the
    partial record and a redacted ``error`` string — instead of raising.

    Args:
        path: Path to the flow YAML file.
        dry_run: If true, only plan the flow (no network / filesystem writes).
    """
    flow_path = pathlib.Path(path).expanduser().resolve()
    if not flow_path.exists():
        raise FileNotFoundError(f"flow file not found: {flow_path}")

    flow = load_flow(flow_path)
    try:
        summary = run_flow(flow, dry_run=dry_run)
    except FlowExecutionError as exc:
        # Covers ApprovalRequiredError too (subclass). Surface the partial
        # record as an artifact rather than a raw exception.
        summary = {
            "name": exc.record.name,
            "dry_run": dry_run,
            "record": exc.record,
            "plan": exc.plan,
        }
        return build_run_artifact(summary, flow_path=flow_path, error=str(exc))

    return build_run_artifact(summary, flow_path=flow_path)


@mcp.tool()
def flow_list_blocks() -> Dict[str, Any]:
    """Return the names of every flow block registered in the local engine.

    Reads ``BLOCK_REGISTRY`` — the same registry ``run_flow`` dispatches
    through — so callers can discover which ``block:`` values a flow may use.
    """
    blocks = sorted(BLOCK_REGISTRY.keys())
    return {"blocks": blocks, "count": len(blocks)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
