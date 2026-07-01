"""Unit tests for phantom_flow.runner._block_filter (pipeline.filter).

Hermetic + offline: pure function, no network, no LLM. Covers the
comma-separated-string keywords branch (existing tests only pass a list),
plus list keywords, case-insensitive matching, and the
passes/matched_count outputs.
"""

from __future__ import annotations

from phantom_flow.runner import _block_filter


def test_comma_separated_string_keywords_are_split_and_matched():
    result = _block_filter(
        {"input": "we want LLM and agent roles", "keywords": "LLM, nope, agent"},
        {},
    )
    assert result["matched"] == ["LLM", "agent"]
    assert result["matched_count"] == 2
    assert result["passes"] is True


def test_comma_separated_string_strips_whitespace_and_drops_empties():
    result = _block_filter(
        {"input": "hello world", "keywords": " hello ,, world , "},
        {},
    )
    assert result["matched"] == ["hello", "world"]
    assert result["matched_count"] == 2
    assert result["passes"] is True


def test_list_keywords_still_work():
    result = _block_filter(
        {"input": "we want LLM and agent roles", "keywords": ["LLM", "nope", "agent"]},
        {},
    )
    assert result["matched"] == ["LLM", "agent"]
    assert result["matched_count"] == 2
    assert result["passes"] is True


def test_case_insensitive_matching():
    result = _block_filter(
        {"input": "We Want LLM Roles", "keywords": ["llm", "AGENT"]},
        {},
    )
    assert result["matched"] == ["llm"]
    assert result["matched_count"] == 1
    assert result["passes"] is True


def test_no_matches_gives_passes_false_and_zero_count():
    result = _block_filter(
        {"input": "totally unrelated text", "keywords": "LLM,agent"},
        {},
    )
    assert result["matched"] == []
    assert result["matched_count"] == 0
    assert result["passes"] is False


def test_missing_input_and_keywords_defaults_to_no_match():
    result = _block_filter({}, {})
    assert result == {"matched": [], "matched_count": 0, "passes": False}
