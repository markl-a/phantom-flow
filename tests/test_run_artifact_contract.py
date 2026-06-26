from __future__ import annotations

import json

import phantom_flow.runner as runner


def _write_flow(path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_cli_record_out_writes_success_artifact(tmp_path):
    flow = tmp_path / "ok.yaml"
    artifact = tmp_path / "artifacts" / "run.json"
    _write_flow(
        flow,
        "name: artifact-demo\n"
        "version: 1\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: count\n"
        "    block: pipeline.regex_count\n"
        "    input: 'AI ai'\n"
        "    pattern: AI\n",
    )

    rc = runner._main([str(flow), "--validate", "--record-out", str(artifact)])

    assert rc == 0
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["flow"]["name"] == "artifact-demo"
    assert payload["flow"]["file"] == "ok.yaml"
    assert payload["dry_run"] is False
    assert payload["record"]["status"] == "ok"
    assert payload["record"]["steps"][0]["id"] == "count"
    assert payload["record"]["steps"][0]["status"] == "ok"
    assert "plan" in payload
    assert "context" not in payload


def test_cli_record_out_writes_dry_run_plan_without_steps(tmp_path):
    flow = tmp_path / "dry.yaml"
    artifact = tmp_path / "run-dry.json"
    _write_flow(
        flow,
        "name: dry-artifact-demo\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: count\n"
        "    block: pipeline.regex_count\n"
        "    input: 'AI ai'\n"
        "    pattern: AI\n",
    )

    rc = runner._main(
        [str(flow), "--validate", "--dry-run", "--strict", "--record-out", str(artifact)]
    )

    assert rc == 0
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert payload["record"]["status"] == "ok"
    assert payload["record"]["steps"] == []
    assert payload["plan"] == [
        "trigger: manual (-)",
        "pipeline.count -> pipeline.regex_count",
    ]
    assert "context" not in payload


def test_cli_record_out_writes_error_artifact(tmp_path):
    flow = tmp_path / "bad-runtime.yaml"
    artifact = tmp_path / "run-error.json"
    _write_flow(
        flow,
        "name: failing-artifact-demo\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: count\n"
        "    block: pipeline.regex_count\n"
        "    input: 'AI ai'\n"
        "    pattern: '['\n",
    )

    rc = runner._main([str(flow), "--validate", "--record-out", str(artifact)])

    assert rc == 1
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["record"]["status"] == "error"
    assert payload["record"]["steps"][0]["id"] == "count"
    assert payload["record"]["steps"][0]["status"] == "error"
    assert "unterminated" in payload["record"]["steps"][0]["error"].lower()
    assert payload["error"]
    assert "context" not in payload


def test_cli_record_out_redacts_secret_like_error_text(tmp_path, monkeypatch):
    flow = tmp_path / "secret-runtime.yaml"
    artifact = tmp_path / "run-secret-error.json"
    _write_flow(
        flow,
        "name: secret-error-demo\n"
        "trigger:\n  type: manual\n"
        "pipeline:\n"
        "  - id: fail\n"
        "    block: pipeline.secret_fail\n",
    )

    def _secret_fail(_spec, _ctx):
        raise RuntimeError(
            "failed https://example.test/path?token=abc123&ok=1 "
            "api_key=xyz789 Bearer rawbearer"
        )

    monkeypatch.setitem(runner.BLOCK_REGISTRY, "pipeline.secret_fail", _secret_fail)

    rc = runner._main([str(flow), "--validate", "--record-out", str(artifact)])

    assert rc == 1
    payload_text = artifact.read_text(encoding="utf-8")
    assert "abc123" not in payload_text
    assert "xyz789" not in payload_text
    assert "rawbearer" not in payload_text
    assert "<redacted>" in payload_text
