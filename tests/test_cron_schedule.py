from datetime import datetime

import pytest
import yaml

from phantom_flow.runner import _main, schedule_matches


def _write_flow(tmp_path, logfile):
    flow = {
        "name": "cron-test",
        "version": 0,
        "trigger": {"type": "cron", "schedule": "0 9 * * *"},
        "outbound": [
            {"block": "actions.log_append", "path": str(logfile), "line": "cron-fired"},
        ],
    }
    p = tmp_path / "flow.yaml"
    p.write_text(yaml.safe_dump(flow), encoding="utf-8")
    return p


def test_matches_basic():
    assert schedule_matches("0 9 * * *", datetime(2026, 6, 12, 9, 0)) is True
    assert schedule_matches("0 9 * * *", datetime(2026, 6, 12, 9, 1)) is False


def test_matches_step():
    for minute in (0, 15, 30, 45):
        assert schedule_matches(
            "*/15 * * * *", datetime(2026, 6, 12, 9, minute)
        ) is True
    for minute in (7, 20):
        assert schedule_matches(
            "*/15 * * * *", datetime(2026, 6, 12, 9, minute)
        ) is False


def test_matches_list_and_range():
    assert schedule_matches("0,30 9 * * *", datetime(2026, 6, 12, 9, 30)) is True
    assert schedule_matches("0,30 9 * * *", datetime(2026, 6, 12, 9, 15)) is False
    assert schedule_matches("0 9-17 * * *", datetime(2026, 6, 12, 14, 0)) is True
    assert schedule_matches("0 9-17 * * *", datetime(2026, 6, 12, 18, 0)) is False


def test_matches_bad_field_count():
    with pytest.raises(ValueError):
        schedule_matches("* * *", datetime(2026, 6, 12, 9, 0))


def test_schedule_due_runs_flow_side_effect(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    logfile = tmp_path / "cron.log"
    flowpath = _write_flow(tmp_path, logfile)
    rc = _main(["schedule", str(flowpath), "--now", "2026-06-12T09:00:00", "--once"])
    assert rc == 0
    # the side effect proves run_flow actually executed
    assert logfile.exists()
    assert "cron-fired" in logfile.read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert "DUE" in out


def test_schedule_not_due_skips_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PHANTOM_FLOW_STUB_LLM", "1")
    logfile = tmp_path / "cron.log"
    flowpath = _write_flow(tmp_path, logfile)
    rc = _main(["schedule", str(flowpath), "--now", "2026-06-12T09:01:00", "--once"])
    assert rc == 0
    # not due -> run_flow must NOT have fired -> no side effect file
    assert not logfile.exists()
    out = capsys.readouterr().out
    assert "not due" in out
