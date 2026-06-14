"""Tests for the phantom-flow engine (phantom_flow.runner + llm_driver).

Covers: load_flow, the dry-run planner, ${...} placeholder resolution, the
core blocks (filter / regex_count / if), and the stub-LLM path. All synthetic
data — no network, no real secrets.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from phantom_flow.llm_driver import LLMResult, PhantomLLM
from phantom_flow.runner import (
    BLOCK_REGISTRY,
    _block_filter,
    _block_if,
    _block_regex_count,
    _gate_passes,
    _lookup,
    _resolve,
    _youtube_video_id,
    load_flow,
    run_flow,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------- load_flow ----------

def test_load_flow_reads_yaml(tmp_path: Path) -> None:
    flow_file = tmp_path / "demo.yaml"
    flow_file.write_text(
        "name: demo\n"
        "trigger:\n"
        "  type: manual\n"
        "pipeline:\n"
        "  - id: step1\n"
        "    block: pipeline.regex_count\n"
        "    input: aaa\n"
        "    pattern: a\n",
        encoding="utf-8",
    )
    flow = load_flow(flow_file)
    assert flow["name"] == "demo"
    assert flow["trigger"]["type"] == "manual"
    assert flow["pipeline"][0]["id"] == "step1"


def test_load_flow_on_bundled_sample() -> None:
    flow = load_flow(REPO_ROOT / "flows" / "jobseek-daily.yaml")
    assert flow["name"] == "jobseek-daily"
    assert flow["trigger"]["type"] == "cron"
    # Every block named in the bundled flow must exist in the registry.
    for step in flow["pipeline"]:
        assert step["block"] in BLOCK_REGISTRY
    for action in flow.get("outbound", []):
        assert action["block"] in BLOCK_REGISTRY


# ---------- dry-run planner ----------

def test_dry_run_builds_plan_without_side_effects() -> None:
    flow = {
        "name": "planme",
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "pipeline": [
            {"id": "a", "block": "tools.http_get", "url": "http://x"},
            {"id": "b", "block": "pipeline.if", "condition": "1 > 0"},
        ],
        "outbound": [
            {"block": "actions.stdout", "when": "${b.true}", "line": "hi"},
        ],
    }
    result = run_flow(flow, dry_run=True)
    assert result["dry_run"] is True
    # No block actually executed -> context stays empty.
    assert result["context"] == {}
    plan = result["plan"]
    assert plan[0] == "trigger: cron (0 9 * * *)"
    assert "pipeline.a -> tools.http_get" in plan
    assert "pipeline.b -> pipeline.if" in plan
    assert any("gated by ${b.true}" in line for line in plan)


def test_run_flow_unknown_block_raises() -> None:
    flow = {
        "name": "bad",
        "pipeline": [{"id": "x", "block": "does.not.exist"}],
    }
    with pytest.raises(KeyError):
        run_flow(flow, dry_run=False)


# ---------- placeholder resolution ----------

def test_resolve_step_field_reference() -> None:
    ctx = {"scrape": {"status": 200, "body": "hello"}}
    assert _resolve("${scrape.status}", ctx) == "200"
    assert _resolve("got ${scrape.body}!", ctx) == "got hello!"


def test_resolve_unknown_reference_is_empty_string() -> None:
    assert _resolve("${missing.field}", {}) == ""


def test_resolve_recurses_into_dicts_and_lists() -> None:
    ctx = {"s": {"n": 3}}
    out = _resolve({"k": ["${s.n}", "x"], "m": {"deep": "${s.n}"}}, ctx)
    assert out == {"k": ["3", "x"], "m": {"deep": "3"}}


def test_lookup_env_and_date() -> None:
    os.environ["PHANTOM_FLOW_TEST_VAR"] = "synthetic-value"
    assert _lookup("env.PHANTOM_FLOW_TEST_VAR", {}) == "synthetic-value"
    assert _lookup("env.DEFINITELY_NOT_SET_XYZ", {}) == ""
    today = _lookup("date.today", {})
    assert len(today) == 10 and today.count("-") == 2


def test_gate_passes() -> None:
    ctx = {"g": {"true": True}}
    assert _gate_passes("${g.true}", ctx) is True
    assert _gate_passes(None, ctx) is True  # no gate -> always pass
    assert _gate_passes("${g.false}", ctx) is False


# ---------- block: filter ----------

def test_block_filter_matches_keywords() -> None:
    out = _block_filter(
        {"input": "We need an AI engineer with RAG experience",
         "keywords": "AI, RAG, kubernetes"},
        {},
    )
    assert out["matched_count"] == 2
    assert set(out["matched"]) == {"AI", "RAG"}
    assert out["passes"] is True


def test_block_filter_no_match() -> None:
    out = _block_filter({"input": "nothing here", "keywords": ["xyz"]}, {})
    assert out["matched"] == []
    assert out["passes"] is False


# ---------- block: regex_count ----------

def test_block_regex_count() -> None:
    out = _block_regex_count(
        {"input": "AI ai Ai aI bob", "pattern": "ai"}, {})
    assert out["value"] == 4  # case-insensitive
    assert out["pattern"] == "ai"


# ---------- block: if ----------

def test_block_if_numeric_gt() -> None:
    out = _block_if({"condition": "5 > 3"}, {})
    assert out["true"] is True
    assert out["false"] is False


def test_block_if_numeric_lt_false() -> None:
    out = _block_if({"condition": "5 < 3"}, {})
    assert out["true"] is False


def test_block_if_string_eq() -> None:
    out = _block_if({"condition": "lead == lead"}, {})
    assert out["true"] is True
    out2 = _block_if({"condition": "lead == spam"}, {})
    assert out2["true"] is False


def test_block_if_non_numeric_gt_is_false() -> None:
    out = _block_if({"condition": "abc > 3"}, {})
    assert out["true"] is False


# ---------- stub-LLM path ----------

def test_stub_llm_when_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    # PHANTOM_FLOW_STUB_LLM=1 forces the stub regardless of CLI presence.
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    llm = PhantomLLM()
    assert llm.available is False
    res = llm.complete("Summarise: synthetic input line one\nline two")
    assert isinstance(res, LLMResult)
    assert res.backend == "stub"
    assert res.text.startswith("[stub-llm]")
    assert "synthetic input line one" in res.text


def test_llm_summarize_block_uses_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    fn = BLOCK_REGISTRY["pipeline.llm_summarize"]
    out = fn({"input": "synthetic body", "prompt": "Summarise:"}, {})
    assert out["backend"] == "stub"
    assert "summary" in out


# ---------- end-to-end (no network, no LLM) ----------

def test_end_to_end_filter_gate_log(tmp_path: Path,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    log_file = tmp_path / "out.log"
    flow = {
        "name": "e2e",
        "trigger": {"type": "manual"},
        "pipeline": [
            {"id": "filt", "block": "pipeline.filter",
             "input": "AI role open", "keywords": ["AI"]},
            {"id": "cnt", "block": "pipeline.regex_count",
             "input": "AI AI", "pattern": "AI"},
            {"id": "gate", "block": "pipeline.if",
             "condition": "${cnt.value} > 0"},
        ],
        "outbound": [
            {"block": "actions.log_append", "when": "${gate.true}",
             "path": str(log_file),
             "line": "matched=${filt.matched_count} hits=${cnt.value}"},
        ],
    }
    result = run_flow(flow, dry_run=False)
    assert result["context"]["filt"]["matched_count"] == 1
    assert result["context"]["cnt"]["value"] == 2
    assert result["context"]["gate"]["true"] is True
    assert log_file.read_text(encoding="utf-8").strip() == "matched=1 hits=2"


# ---------- helper: youtube id parsing (pure, no network) ----------

def test_youtube_video_id_parsing() -> None:
    assert _youtube_video_id("https://www.youtube.com/watch?v=abcdefghijk") == "abcdefghijk"
    assert _youtube_video_id("abcdefghijk") == "abcdefghijk"
    assert _youtube_video_id("not a url") is None
