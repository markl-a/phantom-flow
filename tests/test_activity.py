"""Activity reporter contract tests.

Assert (1) the ActivitySnapshot / mesh-envelope JSON shape matches the
phantom-mesh /api/mesh/activity contract, (2) a tracked task flips status to
"executing" with a real task label, and (3) the wiring inside run_flow flips
THIS node to "executing" mid-run and back to "idle" when the flow finishes.
"""

import http.client
import json
import threading

import phantom_flow.activity as activity
from phantom_flow.activity import ActivityRegistry, make_activity_server
from phantom_flow.runner import BLOCK_REGISTRY, run_flow


# the exact field set the mesh /api/mesh/activity node objects carry
NODE_FIELDS = {"node", "status", "task", "tool", "pid", "elapsed_s", "last_ok_ts"}


def _get(server, path):
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        status = resp.status
        raw = resp.read().decode("utf-8")
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        t.join(timeout=5)
    return status, (json.loads(raw) if raw else None)


def _assert_node_shape(node):
    assert set(node.keys()) == NODE_FIELDS, node
    assert isinstance(node["node"], str) and node["node"]
    assert node["status"] in {"idle", "executing", "error"}
    assert isinstance(node["pid"], int)
    assert isinstance(node["elapsed_s"], int)
    assert isinstance(node["last_ok_ts"], int)


def test_idle_snapshot_shape():
    reg = ActivityRegistry(node="phantom-flow")
    payload = reg.mesh_activity_payload()
    assert set(payload.keys()) == {"nodes", "generated_at"}
    assert isinstance(payload["generated_at"], int)
    assert len(payload["nodes"]) == 1
    node = payload["nodes"][0]
    _assert_node_shape(node)
    # a fresh registry is idle with no current task/tool
    assert node["status"] == "idle"
    assert node["task"] is None
    assert node["tool"] is None
    assert node["node"] == "phantom-flow"


def test_tracked_task_reports_executing():
    reg = ActivityRegistry(node="phantom-flow")
    with reg.track("jobseek-daily", tool="phantom-flow"):
        node = reg.snapshot()
        _assert_node_shape(node)
        assert node["status"] == "executing"
        assert node["task"] == "jobseek-daily"
        assert node["tool"] == "phantom-flow"
    # back to idle once the tracked block exits cleanly
    assert reg.snapshot()["status"] == "idle"


def test_tracked_error_reports_error():
    reg = ActivityRegistry(node="phantom-flow")
    try:
        with reg.track("boom", tool="phantom-flow"):
            raise RuntimeError("kaboom")
    except RuntimeError:
        pass
    assert reg.snapshot()["status"] == "error"


def test_activity_endpoint_shape_and_executing():
    reg = ActivityRegistry(node="phantom-flow")

    # idle: endpoint returns the wrapped envelope with a well-formed node
    server = make_activity_server("127.0.0.1", 0, reg=reg)
    status, body = _get(server, "/activity")
    assert status == 200
    assert set(body.keys()) == {"nodes", "generated_at"}
    _assert_node_shape(body["nodes"][0])
    assert body["nodes"][0]["status"] == "idle"

    # executing: while a task is tracked the endpoint reports status=executing
    reg.begin("digest-run", tool="phantom-flow")
    try:
        server = make_activity_server("127.0.0.1", 0, reg=reg)
        status, body = _get(server, "/activity")
    finally:
        reg.end(ok=True)
    assert status == 200
    node = body["nodes"][0]
    assert node["status"] == "executing"
    assert node["task"] == "digest-run"
    assert node["tool"] == "phantom-flow"


def test_activity_endpoint_unknown_path_404():
    reg = ActivityRegistry(node="phantom-flow")
    server = make_activity_server("127.0.0.1", 0, reg=reg)
    status, _ = _get(server, "/nope")
    assert status == 404


def test_run_flow_flips_status_executing_then_idle():
    """Wiring proof: a real (non-dry-run) run_flow marks the process-wide node
    'executing' with the flow name WHILE a block runs, then 'idle' after."""
    # isolate the process-wide singleton for a deterministic assertion
    activity._REGISTRY = ActivityRegistry(node="phantom-flow")

    captured = {}

    def _capture_block(spec, ctx):
        # observe the live activity state from INSIDE a running flow block
        captured["mid_run"] = activity.snapshot()
        return {"ok": True}

    BLOCK_REGISTRY["test.capture_activity"] = _capture_block
    try:
        flow = {
            "name": "activity-probe",
            "version": 0,
            "pipeline": [{"id": "probe", "block": "test.capture_activity"}],
        }
        summary = run_flow(flow)  # dry_run=False -> real work
        assert summary["record"].status == "ok"
    finally:
        del BLOCK_REGISTRY["test.capture_activity"]

    mid = captured["mid_run"]
    assert mid["status"] == "executing"
    assert mid["task"] == "activity-probe"
    assert mid["tool"] == "phantom-flow"

    # after the run the node has fallen back to idle
    assert activity.snapshot()["status"] == "idle"
