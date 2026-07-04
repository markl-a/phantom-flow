"""End-to-end tests for the pipeline.generate block.

Hermetic + offline: this exercises registry dispatch through run_flow, with
deterministic generation output and no external LLM or MCP dependency.
"""

from __future__ import annotations

from phantom_flow.runner import BLOCK_REGISTRY, run_flow


def test_generate_block_runs_end_to_end_through_runner():
    flow = {
        "name": "generate-demo",
        "trigger": {"type": "manual"},
        "pipeline": [
            {
                "id": "asset",
                "block": "pipeline.generate",
                "tool": "image_generate",
                "prompt": "Create cover art for ${topic.name}",
                "spec": {"style": "clean editorial", "size": "1024x1024"},
            }
        ],
    }

    dry = run_flow(
        flow,
        dry_run=True,
        strict=True,
        initial_ctx={"topic": {"name": "local agents"}},
    )
    assert dry["plan"] == [
        "trigger: manual (-)",
        "pipeline.asset -> pipeline.generate",
    ]

    summary = run_flow(
        flow,
        dry_run=False,
        initial_ctx={"topic": {"name": "local agents"}},
    )

    assert "pipeline.generate" in BLOCK_REGISTRY
    assert summary["record"].status == "ok"
    assert [step.status for step in summary["record"].steps] == ["ok"]

    out = summary["context"]["asset"]
    assert out["tool"] == "image_generate"
    assert out["prompt"] == "Create cover art for local agents"
    assert out["spec"] == {"style": "clean editorial", "size": "1024x1024"}
    assert out["artifact"]["kind"] == "image"
    assert out["artifact"]["id"].startswith("gen-")
    assert "Create cover art for local agents" in out["output"]
    assert out["mcp_request"] == {
        "tool": "image_generate",
        "arguments": {
            "prompt": "Create cover art for local agents",
            "style": "clean editorial",
            "size": "1024x1024",
        },
    }
