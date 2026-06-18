import json
import threading
import http.client

from phantom_flow.runner import make_webhook_server


def _post(server, path, body_bytes, method="POST"):
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            method,
            path,
            body=body_bytes,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        status = resp.status
        raw = resp.read().decode("utf-8")
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        t.join(timeout=5)
    parsed = json.loads(raw) if raw else None
    return status, parsed


def test_webhook_post_drives_run_flow_and_side_effect(tmp_path):
    logfile = tmp_path / "hook.log"
    flow = {
        "name": "test-webhook",
        "version": 0,
        "trigger": {"type": "webhook", "url": "/hooks/test"},
        "outbound": [
            {
                "block": "actions.log_append",
                "path": str(logfile),
                "line": "${event.body}",
            },
        ],
    }
    server = make_webhook_server(flow, "127.0.0.1", 0)
    payload = json.dumps({"intent": "new-job-lead"}).encode("utf-8")
    status, body = _post(server, "/hooks/test", payload)
    assert status == 200
    assert body["status"] == "ok"
    assert body["record"]["status"] == "ok"
    # the side effect: the POSTed body actually reached run_flow via ctx["event"]
    assert logfile.exists()
    contents = logfile.read_text(encoding="utf-8")
    assert "new-job-lead" in contents


def test_webhook_unmapped_path_404(tmp_path):
    logfile = tmp_path / "hook.log"
    flow = {
        "name": "test-webhook",
        "version": 0,
        "trigger": {"type": "webhook", "url": "/hooks/test"},
        "outbound": [
            {
                "block": "actions.log_append",
                "path": str(logfile),
                "line": "${event.body}",
            },
        ],
    }
    server = make_webhook_server(flow, "127.0.0.1", 0)
    status, body = _post(server, "/nope", b"{}")
    assert status == 404
    assert not logfile.exists()  # nothing ran


def test_webhook_pipeline_error_500_partial_record(tmp_path):
    flow = {
        "name": "test-webhook-boom",
        "version": 0,
        "trigger": {"type": "webhook", "url": "/hooks/boom"},
        "pipeline": [
            {"id": "boom", "block": "pipeline.subprocess"},
        ],
    }
    server = make_webhook_server(flow, "127.0.0.1", 0)
    status, body = _post(server, "/hooks/boom", b"{}")
    assert status == 500
    assert body["status"] == "error"
    assert body["record"]["status"] == "error"
    # the partial record names the failed step
    assert any(
        s["id"] == "boom" and s["status"] == "error"
        for s in body["record"]["steps"]
    )
