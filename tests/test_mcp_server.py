"""Tests for the phantom-flow MCP server.

Verifies the module imports, the two tools register on the FastMCP instance,
and that each tool actually wraps the tested engine (block registry + a real
hermetic flow run). No network, no LLM.
"""

import pytest

pytest.importorskip("mcp")

from phantom_flow import mcp_server
from phantom_flow.mcp_server import flow_list_blocks, flow_run
from phantom_flow.runner import BLOCK_REGISTRY


def _registered_tool_names():
    # FastMCP keeps registered tools in its tool manager; list_tools() is sync.
    return {t.name for t in mcp_server.mcp._tool_manager.list_tools()}


def test_tools_register_on_mcp_instance():
    names = _registered_tool_names()
    assert "flow_run" in names
    assert "flow_list_blocks" in names


def test_flow_list_blocks_returns_registry_names():
    result = flow_list_blocks()
    assert isinstance(result, dict)
    assert result["count"] == len(BLOCK_REGISTRY)
    assert set(result["blocks"]) == set(BLOCK_REGISTRY.keys())
    # A couple of known shipped blocks must be present.
    assert "pipeline.filter" in result["blocks"]
    assert "actions.stdout" in result["blocks"]


def _write_flow(tmp_path):
    flow = tmp_path / "hermetic.yaml"
    flow.write_text(
        "name: mcp-hermetic\n"
        "version: 1\n"
        "trigger:\n"
        "  type: manual\n"
        "pipeline:\n"
        "  - id: matched\n"
        "    block: pipeline.filter\n"
        "    input: \"this page mentions AI and agents and RAG\"\n"
        "    keywords: \"AI, agent, RAG, nonexistent\"\n",
        encoding="utf-8",
    )
    return flow


def test_flow_run_executes_real_flow_and_returns_artifact(tmp_path):
    flow = _write_flow(tmp_path)

    artifact = flow_run(path=str(flow))

    assert isinstance(artifact, dict)
    assert artifact["schema_version"] == 1
    assert artifact["flow"]["name"] == "mcp-hermetic"
    assert artifact["dry_run"] is False
    assert artifact["error"] is None
    record = artifact["record"]
    assert record["status"] == "ok"
    assert record["name"] == "mcp-hermetic"
    assert [s["id"] for s in record["steps"]] == ["matched"]
    assert record["steps"][0]["status"] == "ok"


def test_flow_run_dry_run_only_plans(tmp_path):
    flow = _write_flow(tmp_path)

    artifact = flow_run(path=str(flow), dry_run=True)

    assert artifact["dry_run"] is True
    assert artifact["record"]["dry_run"] is True
    # Dry-run plans but does not execute steps.
    assert artifact["record"]["steps"] == []
    assert artifact["plan"]


def test_flow_run_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        flow_run(path=str(tmp_path / "does-not-exist.yaml"))
