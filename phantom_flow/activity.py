"""In-process activity tracker for phantom-flow (mesh activity reporter).

Mirrors the phantom-mesh core ``job_registry`` ``ActivitySnapshot`` concept in
Python so this satellite shows up in the mesh's live "what is each machine
doing" grid (``GET /api/mesh/activity``). A single process-wide registry records
the satellite's CURRENT work as ``{task, tool, status, started_at, pid}`` and can
emit an ActivitySnapshot whose JSON matches the mesh wire contract EXACTLY::

    {"node", "status", "task", "tool", "pid", "elapsed_s", "last_ok_ts"}

``status`` is one of ``"idle" | "executing" | "error"`` — the mesh dashboard's
coarse per-node state. The ``/activity`` HTTP endpoint wraps one snapshot for
THIS node in the same envelope the mesh serve handler returns::

    {"nodes": [<snapshot>], "generated_at": <unix_ms>}

One phantom-flow process == one mesh "node". The node name defaults to
``phantom-flow`` and can be overridden with ``PHANTOM_FLOW_NODE``.
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Iterator, Optional


DEFAULT_NODE = os.environ.get("PHANTOM_FLOW_NODE", "phantom-flow")
DEFAULT_ACTIVITY_PORT = int(os.environ.get("PHANTOM_FLOW_ACTIVITY_PORT", "8787"))


def _now_ms() -> int:
    """Milliseconds since the unix epoch (wall clock) — matches the mesh's
    ``generated_at`` / ``last_ok_ts`` unit."""
    return int(time.time() * 1000)


class ActivityRegistry:
    """Thread-safe single-node activity registry.

    Holds the node's current ``status`` and the ``task``/``tool`` it is running,
    plus ``last_ok_ts`` (the wall-clock ms of the last successful completion) so
    a freshly-idle node still reports a meaningful heartbeat. ``_active`` is a
    nesting/concurrency depth so overlapping :meth:`track` blocks (e.g. the
    threaded webhook server) only fall back to a terminal state once the LAST
    in-flight unit of work finishes.
    """

    def __init__(self, node: str = DEFAULT_NODE) -> None:
        self.node = node
        self._lock = threading.Lock()
        self._active = 0                          # in-flight work depth
        self._task: Optional[str] = None
        self._tool: Optional[str] = None
        self._started_at: Optional[float] = None  # monotonic seconds
        self._status = "idle"
        self._pid = os.getpid()
        self._last_ok_ts = _now_ms()              # init heartbeat = process start

    def begin(self, task: str, tool: Optional[str] = None) -> None:
        """Mark the node as executing ``task`` (optionally via ``tool``)."""
        with self._lock:
            self._active += 1
            self._task = task
            self._tool = tool
            self._started_at = time.monotonic()
            self._status = "executing"

    def end(self, ok: bool = True) -> None:
        """Finish one unit of work. When the last one finishes, fall back to
        ``idle`` (``ok``) or ``error``. A successful end always refreshes
        ``last_ok_ts``."""
        with self._lock:
            if self._active > 0:
                self._active -= 1
            if ok:
                self._last_ok_ts = _now_ms()
            if self._active == 0:
                self._status = "idle" if ok else "error"
                self._task = None
                self._tool = None
                self._started_at = None
            # else: work still in flight -> stay "executing"

    def snapshot(self) -> Dict[str, Any]:
        """A point-in-time ActivitySnapshot for THIS node, field-for-field
        matching the mesh ``/api/mesh/activity`` node contract."""
        with self._lock:
            elapsed_s = (
                int(time.monotonic() - self._started_at)
                if self._started_at is not None
                else 0
            )
            return {
                "node": self.node,
                "status": self._status,
                "task": self._task,
                "tool": self._tool,
                "pid": self._pid,
                "elapsed_s": elapsed_s,
                "last_ok_ts": self._last_ok_ts,
            }

    def mesh_activity_payload(self) -> Dict[str, Any]:
        """Wrap this node's snapshot in the mesh ``/api/mesh/activity``
        envelope: ``{"nodes": [snapshot], "generated_at": <unix_ms>}``."""
        return {"nodes": [self.snapshot()], "generated_at": _now_ms()}

    @contextmanager
    def track(self, task: str, tool: Optional[str] = None) -> Iterator[None]:
        """Context manager: ``executing`` for the body, then ``idle`` on clean
        exit or ``error`` if the body raises (the exception still propagates)."""
        self.begin(task, tool)
        ok = True
        try:
            yield
        except BaseException:
            ok = False
            raise
        finally:
            self.end(ok=ok)


# ── process-wide singleton (mirrors job_registry's global registry) ──────────

_REGISTRY: Optional[ActivityRegistry] = None
_REGISTRY_LOCK = threading.Lock()


def registry() -> ActivityRegistry:
    """Return the process-wide :class:`ActivityRegistry` (lazily created)."""
    global _REGISTRY
    if _REGISTRY is None:
        with _REGISTRY_LOCK:
            if _REGISTRY is None:
                _REGISTRY = ActivityRegistry()
    return _REGISTRY


def track(task: str, tool: Optional[str] = None):
    """Shorthand for ``registry().track(...)``."""
    return registry().track(task, tool)


def snapshot() -> Dict[str, Any]:
    """Shorthand for ``registry().snapshot()``."""
    return registry().snapshot()


def mesh_activity_payload() -> Dict[str, Any]:
    """Shorthand for ``registry().mesh_activity_payload()``."""
    return registry().mesh_activity_payload()


# ── stdlib HTTP endpoint: GET /activity ──────────────────────────────────────

def make_activity_server(
    host: str = "127.0.0.1",
    port: int = DEFAULT_ACTIVITY_PORT,
    reg: Optional[ActivityRegistry] = None,
) -> HTTPServer:
    """Build (but do NOT start) a stdlib HTTPServer exposing ``GET /activity``.

    Bind ``port=0`` for an ephemeral port (tests read
    ``server.server_address[1]``). The response body matches the phantom-mesh
    ``/api/mesh/activity`` contract exactly::

        {"nodes": [{...one entry for this node...}], "generated_at": <unix_ms>}
    """
    reg = reg if reg is not None else registry()

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr logging
            pass

        def _send_json(self, code: int, payload: Dict[str, Any]) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            # tolerate an optional query string (e.g. cache-buster)
            if self.path.split("?", 1)[0] != "/activity":
                self._send_json(404, {"error": "not found", "path": self.path})
                return
            self._send_json(200, reg.mesh_activity_payload())

    return HTTPServer((host, port), _Handler)


def serve_activity(host: str = "127.0.0.1", port: int = DEFAULT_ACTIVITY_PORT) -> None:
    """Start the ``/activity`` listener (blocking) until interrupted."""
    server = make_activity_server(host, port)
    bound_host, bound_port = server.server_address[0], server.server_address[1]
    print(
        f"phantom-flow activity :: listening on "
        f"http://{bound_host}:{bound_port}/activity"
    )
    print(f"  node = {registry().node!r}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nphantom-flow activity :: shutting down")
    finally:
        server.server_close()
