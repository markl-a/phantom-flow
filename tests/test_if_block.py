"""Unit tests for phantom_flow.runner._block_if (pipeline.if).

Hermetic + offline: pure function, no network, no LLM. Covers each
supported operator (>, <, ==), the ValueError-to-false guard on
non-numeric comparisons, and the no-operator true/false flags.
"""

from __future__ import annotations

from phantom_flow.runner import _block_if


def test_greater_than_true():
    result = _block_if({"condition": "5 > 3"}, {})
    assert result == {"true": True, "false": False, "condition": "5 > 3"}


def test_greater_than_false():
    result = _block_if({"condition": "1 > 3"}, {})
    assert result == {"true": False, "false": True, "condition": "1 > 3"}


def test_less_than_true():
    result = _block_if({"condition": "1 < 3"}, {})
    assert result == {"true": True, "false": False, "condition": "1 < 3"}


def test_less_than_false():
    result = _block_if({"condition": "5 < 3"}, {})
    assert result == {"true": False, "false": True, "condition": "5 < 3"}


def test_equals_true_for_matching_strings():
    result = _block_if({"condition": "done == done"}, {})
    assert result == {"true": True, "false": False, "condition": "done == done"}


def test_equals_false_for_mismatched_strings():
    result = _block_if({"condition": "done == pending"}, {})
    assert result == {
        "true": False,
        "false": True,
        "condition": "done == pending",
    }


def test_value_error_on_non_numeric_greater_than_is_false_not_raised():
    # "abc" can't be coerced to float — the ValueError-to-false guard must
    # catch it and yield a plain false result, never propagate.
    result = _block_if({"condition": "abc > 3"}, {})
    assert result == {"true": False, "false": True, "condition": "abc > 3"}


def test_value_error_on_non_numeric_less_than_is_false_not_raised():
    result = _block_if({"condition": "3 < xyz"}, {})
    assert result == {"true": False, "false": True, "condition": "3 < xyz"}


def test_no_operator_condition_is_false():
    result = _block_if({"condition": "just some text"}, {})
    assert result == {
        "true": False,
        "false": True,
        "condition": "just some text",
    }


def test_missing_condition_defaults_to_empty_and_false():
    result = _block_if({}, {})
    assert result == {"true": False, "false": True, "condition": ""}
