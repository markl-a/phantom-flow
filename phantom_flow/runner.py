"""Minimal n8n-style YAML flow executor for phantom-flow (Tier 1).

A flow is a YAML file with this shape::

    name: my-flow
    trigger:
      type: cron | webhook | event | manual
      schedule: "0 9 * * *"      # cron only
      url: "/hooks/my-flow"      # webhook only
    pipeline:
      - id: step_id
        block: <namespaced.block.name>
        ...block-specific keys (url, pattern, input, etc.)
    outbound:
      - block: <namespaced.action.name>
        when: "${step.field}"    # optional gate
        ...action-specific keys

Each `block` resolves through `BLOCK_REGISTRY`. Heavy blocks (LLM, scrape,
data-analysis) shell out to the subtree-merged framework rather than reimport
its Python directly — keeps the wrapper light and lets the LLM driver swap
happen incrementally.

Run::

    python -m phantom_flow.runner flows/jobseek-daily.yaml --dry-run
    python -m phantom_flow.runner flows/jobseek-daily.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - keep dry-run usable without PyYAML
    yaml = None


# ---------- schema validation + structured run records (P2-1) ----------

VALID_TRIGGER_TYPES = {"cron", "webhook", "event", "manual"}


class FlowValidationError(ValueError):
    """Raised when a flow definition fails schema validation.

    Carries the full list of problems in ``.errors`` so a linter can show
    every issue at once instead of one-at-a-time.
    """

    def __init__(self, errors: List[str]) -> None:
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


class FlowExecutionError(RuntimeError):
    """Raised when a pipeline/outbound block fails during execution.

    Carries the partial :class:`RunRecord` (``.record``) captured up to and
    including the failed step, with the underlying exception chained.
    """

    def __init__(self, message: str, record: "RunRecord") -> None:
        self.record = record
        super().__init__(message)


@dataclass
class StepRecord:
    id: str
    block: str
    status: str  # "ok" | "error"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "block": self.block, "status": self.status,
                "error": self.error}


@dataclass
class RunRecord:
    """Structured record of a single flow run (or dry-run plan)."""

    name: str
    version: Any
    trigger_type: str
    dry_run: bool
    status: str  # "ok" | "error"
    started_at: str
    finished_at: str
    steps: List[StepRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "trigger_type": self.trigger_type,
            "dry_run": self.dry_run,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [s.to_dict() for s in self.steps],
        }


def validate_flow(flow: Any) -> Dict[str, Any]:
    """Validate a flow's shape; return it unchanged on success.

    Checks: flow is a mapping; ``name`` present + non-empty; ``trigger.type``
    is one of ``VALID_TRIGGER_TYPES`` (when a trigger is given); ``pipeline``
    is a list; every pipeline step is a mapping carrying a ``block`` name.
    Collects ALL problems before raising a single ``FlowValidationError``.
    """
    errors: List[str] = []

    if not isinstance(flow, dict):
        raise FlowValidationError(["flow must be a mapping (YAML object)"])

    name = flow.get("name")
    if not name or not str(name).strip():
        errors.append("flow.name is required and must be non-empty")

    trigger = flow.get("trigger")
    if trigger is not None:
        if not isinstance(trigger, dict):
            errors.append("flow.trigger must be a mapping")
        else:
            ttype = trigger.get("type")
            if ttype is not None and ttype not in VALID_TRIGGER_TYPES:
                errors.append(
                    f"flow.trigger.type {ttype!r} is not one of "
                    f"{sorted(VALID_TRIGGER_TYPES)}"
                )

    pipeline = flow.get("pipeline", [])
    if not isinstance(pipeline, list):
        errors.append("flow.pipeline must be a list")
    else:
        for i, step in enumerate(pipeline):
            if not isinstance(step, dict):
                errors.append(f"flow.pipeline[{i}] must be a mapping")
                continue
            if not step.get("block"):
                errors.append(f"flow.pipeline[{i}] is missing a 'block' name")

    outbound = flow.get("outbound", [])
    if not isinstance(outbound, list):
        errors.append("flow.outbound must be a list")
    else:
        for i, action in enumerate(outbound):
            if not isinstance(action, dict):
                errors.append(f"flow.outbound[{i}] must be a mapping")
            elif not action.get("block"):
                errors.append(f"flow.outbound[{i}] is missing a 'block' name")

    if errors:
        raise FlowValidationError(errors)
    return flow


# ---------- context + variable substitution ----------

_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve(value: Any, ctx: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        def sub(match: "re.Match[str]") -> str:
            expr = match.group(1).strip()
            return str(_lookup(expr, ctx))
        return _PLACEHOLDER_RE.sub(sub, value)
    if isinstance(value, list):
        return [_resolve(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: _resolve(v, ctx) for k, v in value.items()}
    return value


def _lookup(expr: str, ctx: Dict[str, Any]) -> Any:
    # Supports ${step.field}, ${date.today}, ${env.HOME}.
    if expr == "date.today":
        return date.today().isoformat()
    if expr == "date.now":
        return datetime.now().isoformat(timespec="seconds")
    if expr.startswith("env."):
        return os.environ.get(expr[4:], "")
    parts = expr.split(".")
    cur: Any = ctx
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return ""
    return cur


# ---------- blocks ----------

def _block_http_get(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch a URL's body. Supports ``http(s)://`` and ``file://`` (stdlib
    urllib), the latter letting example flows exercise the exact same code
    path fully offline against a bundled sample file."""
    url = spec["url"]
    ua = spec.get("user_agent", "phantom-flow/0.1")
    # file:// handlers reject extra request headers; only set UA for http(s).
    headers = {} if url.startswith("file:") else {"User-Agent": ua}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=(spec.get("timeout") or 30)) as resp:
        # bounded: coerce null/0 to the default cap so an explicit `max_bytes:
        # null` can never become resp.read(None) (an UNBOUNDED full-body read),
        # mirroring the timeout null/0 coercion above.
        raw = resp.read(spec.get("max_bytes") or 50 * 1024)
        charset = "utf-8"
        get_charset = getattr(resp.headers, "get_content_charset", None)
        if callable(get_charset):
            charset = get_charset() or "utf-8"
        body = raw.decode(charset, errors="replace")
        # file:// responses have status None; normalise to 200 (read OK).
        status = getattr(resp, "status", None)
        if status is None:
            status = 200
        return {"url": url, "status": status, "body": body,
                "body_len": len(raw)}


def _block_regex_count(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    text = spec.get("input", "")
    pattern = spec.get("pattern", "")
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    return {"value": len(matches), "pattern": pattern}


def _block_filter(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    # Tier 1: a soft "keyword filter on body" used by jobseek-daily.
    text = spec.get("input", "")
    keywords = spec.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    hits = [k for k in keywords if k.lower() in text.lower()]
    return {"matched": hits, "matched_count": len(hits),
            "passes": len(hits) > 0}


_YT_ID_RE = re.compile(
    r"(?:v=|/shorts/|/embed/|youtu\.be/|/v/)([A-Za-z0-9_-]{11})"
)


def _youtube_video_id(url_or_id: str) -> Optional[str]:
    """Extract an 11-char YouTube video id from a URL or bare id."""
    s = (url_or_id or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _YT_ID_RE.search(s)
    return m.group(1) if m else None


def _block_youtube_transcript(spec: Dict[str, Any],
                              _ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch a YouTube video's transcript via youtube_transcript_api.

    spec keys:
      url           : YouTube URL or bare 11-char video id (required)
      languages     : list of preferred language codes (default ["en"])
      cache_file    : path to a bundled sample transcript used as a fallback
                      if the live fetch fails (so demos still run on real text)

    Returns a dict with `text`, `text_len`, `source` ("live" | "cached"),
    `video_id`, and `error` (set when live fetch failed).
    """
    url = spec.get("url", "")
    video_id = _youtube_video_id(url)
    languages = spec.get("languages") or ["en"]
    if isinstance(languages, str):
        languages = [s.strip() for s in languages.split(",") if s.strip()]

    error: Optional[str] = None
    if not video_id:
        error = f"could not parse a YouTube video id from {url!r}"
    else:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
            text = " ".join(
                snip.text for snip in fetched if snip.text.strip()
            ).strip()
            if text:
                print(f"  [youtube_transcript] live fetch OK "
                      f"({video_id}, {len(text)} chars)", file=sys.stderr)
                return {"text": text, "text_len": len(text),
                        "source": "live", "video_id": video_id, "error": ""}
            error = "transcript was empty"
        except ImportError as exc:  # pragma: no cover
            error = f"youtube_transcript_api not installed: {exc}"
        except Exception as exc:  # noqa: BLE001 - many API-specific subclasses
            error = f"{type(exc).__name__}: {exc}"

    # ---- cached fallback so the demo still summarises REAL transcript text ----
    cache_file = spec.get("cache_file")
    if cache_file:
        cache_path = Path(os.path.expanduser(cache_file))
        if not cache_path.is_absolute():
            cache_path = (Path(__file__).resolve().parent.parent
                          / cache_file)
        if cache_path.exists():
            text = cache_path.read_text(encoding="utf-8").strip()
            print(f"  [youtube_transcript] live fetch failed "
                  f"({error}); using CACHED transcript {cache_path.name} "
                  f"({len(text)} chars)", file=sys.stderr)
            return {"text": text, "text_len": len(text), "source": "cached",
                    "video_id": video_id or "", "error": error or ""}

    raise RuntimeError(
        f"youtube_transcript failed and no usable cache_file: {error}"
    )


def _block_llm_summarize(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    from phantom_flow.llm_driver import PhantomLLM
    # Wire the driver's offline/test + bounding knobs through from the flow
    # spec so they're reachable on the production path (not just unit tests):
    #   force_stub : request the deterministic stub per-step (offline/test),
    #                independent of the global PHANTOM_FLOW_STUB_LLM env var.
    #   timeout    : bounded; null/0 coerce to the driver default so a flow
    #                can never make the LLM call block forever.
    #   model_hint : provider/model routing hint passed to the driver.
    kwargs: Dict[str, Any] = {"force_stub": bool(spec.get("force_stub", False))}
    if spec.get("timeout"):  # null/0 -> keep the bounded driver default
        kwargs["timeout"] = spec["timeout"]
    if spec.get("model_hint"):
        kwargs["model_hint"] = spec["model_hint"]
    llm = PhantomLLM(**kwargs)
    text = spec.get("input", "")
    prompt = spec.get("prompt", "Summarise the following text in 2 bullets:")
    res = llm.complete(f"{prompt}\n\n{text[:4000]}")
    # Surface the degrade reason (LLMResult.error) so per-step reporting is
    # honest about a silent fall-back to the stub instead of dropping it.
    return {"summary": res.text, "backend": res.backend, "error": res.error or ""}


def _block_if(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    condition = str(spec.get("condition", "")).strip()
    # Tier 1: only support `<lhs> > <rhs>` / `<lhs> == <rhs>` numeric/string.
    truthy = False
    for op, fn in (
        (">", lambda a, b: float(a) > float(b)),
        ("<", lambda a, b: float(a) < float(b)),
        ("==", lambda a, b: str(a).strip() == str(b).strip()),
    ):
        if op in condition:
            lhs, rhs = (s.strip() for s in condition.split(op, 1))
            try:
                truthy = fn(lhs, rhs)
            except ValueError:
                truthy = False
            break
    return {"true": truthy, "false": not truthy, "condition": condition}


def _block_subprocess(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Escape hatch for heavy steps that live inside the merged subtree.

    Hardened boundary: the timeout is always finite, a missing binary or a
    timeout is reported as a structured result (``returncode`` != 0 +
    ``stderr`` + ``timed_out``) instead of propagating an exception that would
    abort the whole flow.
    """
    cmd = spec["cmd"]
    if isinstance(cmd, str):
        cmd = ["bash", "-lc", cmd]
    timeout = spec.get("timeout") or 120  # bounded: coerce null/0 to the default so it's always finite
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {"stdout": exc.stdout or "",
                "stderr": f"subprocess timed out after {timeout}s",
                "returncode": 124, "timed_out": True}
    except FileNotFoundError as exc:
        return {"stdout": "",
                "stderr": f"command not found: {exc}",
                "returncode": 127, "timed_out": False}
    except OSError as exc:
        return {"stdout": "", "stderr": f"OSError: {exc}",
                "returncode": 126, "timed_out": False}
    return {"stdout": proc.stdout, "stderr": proc.stderr,
            "returncode": proc.returncode, "timed_out": False}


def _action_log_append(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(os.path.expanduser(spec["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    line = spec.get("line", "")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")
    return {"path": str(path), "appended": line}


def _action_stdout(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    line = spec.get("line", "")
    sys.stdout.write(line.rstrip() + "\n")
    sys.stdout.flush()
    return {"line": line}


BLOCK_REGISTRY: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {
    "tools.http_get": _block_http_get,
    "tools.youtube_transcript": _block_youtube_transcript,
    "pipeline.regex_count": _block_regex_count,
    "pipeline.filter": _block_filter,
    "pipeline.llm_summarize": _block_llm_summarize,
    "pipeline.if": _block_if,
    "pipeline.subprocess": _block_subprocess,
    "actions.log_append": _action_log_append,
    "actions.stdout": _action_stdout,
}


# ---------- load + run ----------

def load_flow(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise RuntimeError(
            "PyYAML not installed; run `pip install pyyaml` to parse flow files. "
            "Dry-run does not need PyYAML if you pass --raw."
        )
    return yaml.safe_load(text)


def _gate_passes(when: Optional[str], ctx: Dict[str, Any]) -> bool:
    if not when:
        return True
    resolved = _resolve(when, ctx).strip().lower()
    return resolved in {"true", "1", "yes"}


def run_flow(flow: Dict[str, Any], *, dry_run: bool = False,
             strict: bool = False, validate: bool = False,
             initial_ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute (or, with ``dry_run``, only plan) a flow.

    ``strict`` validates that every ``block`` name resolves in
    ``BLOCK_REGISTRY`` even during a dry-run — useful for linting flow files
    in CI without touching the network or an LLM.

    ``validate`` runs full schema validation (:func:`validate_flow`) first and
    raises ``FlowValidationError`` on any problem.

    Always returns a structured :class:`RunRecord` under the ``record`` key. A
    block that raises mid-execution is recorded as a failed ``StepRecord`` and
    re-surfaced as :class:`FlowExecutionError` carrying the partial record.
    """
    if validate:
        validate_flow(flow)

    ctx: Dict[str, Any] = dict(initial_ctx) if initial_ctx else {}
    plan: List[str] = []
    steps: List[StepRecord] = []
    started_at = datetime.now().isoformat(timespec="seconds")

    trigger = flow.get("trigger", {})
    trigger_type = trigger.get("type", "manual") if isinstance(trigger, dict) else "manual"
    plan.append(f"trigger: {trigger.get('type', '?')} "
                f"({trigger.get('schedule') or trigger.get('url') or trigger.get('on') or '-'})")

    def _finish(status: str) -> RunRecord:
        return RunRecord(
            name=str(flow.get("name", "?")),
            version=flow.get("version", "?"),
            trigger_type=trigger_type,
            dry_run=dry_run,
            status=status,
            started_at=started_at,
            finished_at=datetime.now().isoformat(timespec="seconds"),
            steps=steps,
        )

    for step in flow.get("pipeline", []):
        sid = step.get("id") or step.get("block", "?")
        block_name = step.get("block", "?")
        plan.append(f"pipeline.{sid} -> {block_name}")
        if strict and block_name not in BLOCK_REGISTRY:
            raise KeyError(f"unknown block: {block_name}")
        if dry_run:
            continue
        fn = BLOCK_REGISTRY.get(block_name)
        if fn is None:
            raise KeyError(f"unknown block: {block_name}")
        spec = _resolve({k: v for k, v in step.items()
                         if k not in {"id", "block"}}, ctx)
        try:
            ctx[sid] = fn(spec, ctx)
        except Exception as exc:  # noqa: BLE001 - record then re-surface
            steps.append(StepRecord(id=sid, block=block_name, status="error",
                                    error=f"{type(exc).__name__}: {exc}"))
            raise FlowExecutionError(
                f"pipeline step {sid!r} ({block_name}) failed: {exc}",
                _finish("error"),
            ) from exc
        steps.append(StepRecord(id=sid, block=block_name, status="ok"))

    for action in flow.get("outbound", []):
        block_name = action.get("block", "?")
        when = action.get("when")
        plan.append(f"outbound -> {block_name}"
                    + (f"  [gated by {when}]" if when else ""))
        if strict and block_name not in BLOCK_REGISTRY:
            raise KeyError(f"unknown action: {block_name}")
        if dry_run:
            continue
        if not _gate_passes(when, ctx):
            continue
        fn = BLOCK_REGISTRY.get(block_name)
        if fn is None:
            raise KeyError(f"unknown action: {block_name}")
        spec = _resolve({k: v for k, v in action.items()
                         if k not in {"block", "when"}}, ctx)
        try:
            fn(spec, ctx)
        except Exception as exc:  # noqa: BLE001 - record then re-surface
            steps.append(StepRecord(id=f"outbound:{block_name}",
                                    block=block_name, status="error",
                                    error=f"{type(exc).__name__}: {exc}"))
            raise FlowExecutionError(
                f"outbound action {block_name} failed: {exc}",
                _finish("error"),
            ) from exc

    record = _finish("ok")
    return {"plan": plan, "context": ctx, "dry_run": dry_run,
            "name": flow.get("name", "?"), "record": record}


# ---------- CLI ----------

def _flow_webhook_path(flow):
    """Return the flow's webhook trigger URL path, or None if the flow is not a webhook flow."""
    trigger = flow.get("trigger", {})
    if not isinstance(trigger, dict):
        return None
    if trigger.get("type") != "webhook":
        return None
    return trigger.get("url")


def make_webhook_server(flow, host="127.0.0.1", port=0):
    """Build (but do NOT start) a stdlib HTTPServer that turns POSTs to the flow's
    trigger.url path into real run_flow executions with ctx['event'] seeded.
    Bind port=0 for an ephemeral port (tests read server.server_address[1])."""
    webhook_path = _flow_webhook_path(flow)

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default stderr logging
            pass

        def _send_json(self, code, payload):
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if webhook_path is None or self.path != webhook_path:
                self._send_json(404, {"error": "no flow mapped to this path",
                                      "path": self.path})
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
            try:
                body = json.loads(raw) if raw else None
            except (ValueError, TypeError):
                body = raw
            event = {
                "body": body,
                "raw": raw,
                "headers": {k: v for k, v in self.headers.items()},
                "method": "POST",
                "path": self.path,
            }
            try:
                summary = run_flow(flow, initial_ctx={"event": event})
            except FlowExecutionError as exc:
                self._send_json(500, {"status": "error",
                                      "record": exc.record.to_dict()})
                return
            record = summary["record"]
            self._send_json(200, {"name": summary.get("name", "?"),
                                  "status": record.status,
                                  "record": record.to_dict()})

    return HTTPServer((host, port), _Handler)


def serve_flow(flow, host="127.0.0.1", port=8000):
    """Start the webhook listener (blocking) until interrupted."""
    server = make_webhook_server(flow, host, port)
    bound_host, bound_port = server.server_address[0], server.server_address[1]
    path = _flow_webhook_path(flow)
    print(f"phantom-flow serve :: listening on http://{bound_host}:{bound_port}")
    print(f"  POST {path or '<no webhook trigger.url>'} -> run flow {flow.get('name', '?')!r}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nphantom-flow serve :: shutting down")
    finally:
        server.server_close()


def _serve_main(argv):
    parser = argparse.ArgumentParser(prog="phantom-flow serve",
                                     description="Start a stdlib HTTP webhook listener for a flow.")
    parser.add_argument("flow", help="path to webhook flow YAML")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    path = Path(args.flow).expanduser().resolve()
    if not path.exists():
        print(f"error: flow file not found: {path}", file=sys.stderr)
        return 2
    flow = load_flow(path)
    if _flow_webhook_path(flow) is None:
        print("error: flow has no webhook trigger.url to serve", file=sys.stderr)
        return 2
    serve_flow(flow, args.host, args.port)
    return 0


def _main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "serve":
        return _serve_main(argv[1:])

    parser = argparse.ArgumentParser(prog="phantom_flow.runner",
                                     description="Minimal YAML flow executor.")
    parser.add_argument("flow", help="path to flow YAML")
    parser.add_argument("--dry-run", action="store_true",
                        help="parse + plan only; no network / no filesystem writes")
    parser.add_argument("--strict", action="store_true",
                        help="validate every block name against the registry "
                             "(lints a flow file; pairs well with --dry-run)")
    parser.add_argument("--validate", action="store_true",
                        help="run full schema validation (name/trigger/pipeline) "
                             "before planning/executing")
    parser.add_argument("--json", action="store_true",
                        help="emit a final JSON summary (incl. run record) on stdout")
    args = parser.parse_args(argv)

    path = Path(args.flow).expanduser().resolve()
    if not path.exists():
        print(f"error: flow file not found: {path}", file=sys.stderr)
        return 2

    try:
        flow = load_flow(path)
    except Exception as exc:  # pragma: no cover
        print(f"error: failed to load {path}: {exc}", file=sys.stderr)
        return 2

    if args.validate:
        try:
            validate_flow(flow)
        except FlowValidationError as exc:
            print(f"error: invalid flow {path.name}:", file=sys.stderr)
            for problem in exc.errors:
                print(f"  - {problem}", file=sys.stderr)
            return 2

    print(f"phantom-flow runner :: {path.name}")
    print(f"  name    = {flow.get('name', '?')}")
    print(f"  version = {flow.get('version', '?')}")
    print(f"  mode    = {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"  llm_cli = {shutil.which('phantom') or '<not installed>'}")

    try:
        summary = run_flow(flow, dry_run=args.dry_run, strict=args.strict)
    except FlowExecutionError as exc:
        print(f"error: flow execution failed: {exc}", file=sys.stderr)
        if args.json:
            print(json.dumps({"record": exc.record.to_dict()}, indent=2))
        return 1

    print("--- plan ---")
    for line in summary["plan"]:
        print(f"  {line}")

    if args.json:
        # Strip non-serialisable / huge body fields for the dump.
        safe_ctx = {k: {kk: (vv if not isinstance(vv, str) or len(vv) < 200
                             else f"<{len(vv)} chars>")
                        for kk, vv in (v.items() if isinstance(v, dict) else [])}
                    for k, v in summary["context"].items()}
        print("--- json ---")
        print(json.dumps({"name": summary["name"],
                          "dry_run": summary["dry_run"],
                          "record": summary["record"].to_dict(),
                          "context": safe_ctx}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
