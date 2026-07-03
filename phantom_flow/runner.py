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
from contextlib import contextmanager, redirect_stdout
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
from typing import Any, Callable, Dict, Iterator, List, Optional, Set

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - keep dry-run usable without PyYAML
    yaml = None

# Mesh activity reporter: a real (non-dry-run) flow execution flips THIS node
# to "executing" in the process-wide registry, so the satellite surfaces in the
# phantom-mesh /api/mesh/activity grid; back to idle/error when the run ends.
from phantom_flow import activity


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

    def __init__(self, message: str, record: "RunRecord",
                 plan: Optional[List[str]] = None) -> None:
        self.record = record
        self.plan = list(plan or [])
        super().__init__(message)


class ApprovalRequiredError(FlowExecutionError):
    """Raised when an approval-gated step/action is reached without approval."""


@dataclass
class StepRecord:
    id: str
    block: str
    status: str  # "ok" | "error" | "blocked"
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
    run_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "name": self.name,
            "version": self.version,
            "trigger_type": self.trigger_type,
            "dry_run": self.dry_run,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [s.to_dict() for s in self.steps],
        }


RUN_ARTIFACT_SCHEMA_VERSION = 1


def build_run_artifact(summary: Dict[str, Any], *, flow_path: Optional[Path] = None,
                       error: Optional[str] = None) -> Dict[str, Any]:
    """Build the stable public run artifact.

    The artifact intentionally records the plan and RunRecord only. It omits
    the execution context because block outputs may contain fetched content,
    prompts, subprocess output, or future secret-bearing values.
    """
    record = summary["record"]
    if not isinstance(record, RunRecord):
        raise TypeError("summary['record'] must be a RunRecord")
    return {
        "schema_version": RUN_ARTIFACT_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "flow": {
            "name": summary.get("name", record.name),
            "file": flow_path.name if flow_path else None,
        },
        "dry_run": bool(summary.get("dry_run", record.dry_run)),
        "record": record.to_dict(),
        "plan": list(summary.get("plan", [])),
        "error": error,
    }


def write_run_artifact(path: Path, artifact: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


STATE_ARTIFACT_SCHEMA_VERSION = 1


def _default_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"run-{stamp}-{os.getpid()}"


def build_state_artifact(
    summary: Dict[str, Any],
    *,
    run_id: str,
    flow_path: Optional[Path] = None,
    approvals: Optional[Set[str]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    record = summary["record"]
    if not isinstance(record, RunRecord):
        raise TypeError("summary['record'] must be a RunRecord")
    return {
        "schema_version": STATE_ARTIFACT_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "flow": {
            "name": summary.get("name", record.name),
            "file": flow_path.name if flow_path else None,
        },
        "dry_run": bool(summary.get("dry_run", record.dry_run)),
        "approvals": sorted(approvals or set()),
        "record": record.to_dict(),
        "plan": list(summary.get("plan", [])),
        "error": error,
    }


def write_state_artifacts(state_dir: Path, artifact: Dict[str, Any]) -> None:
    run_id = str(artifact["run_id"])
    run_dir = state_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "state.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    events = []
    for step in artifact["record"].get("steps", []):
        events.append(
            {
                "schema_version": STATE_ARTIFACT_SCHEMA_VERSION,
                "run_id": run_id,
                "step_id": step.get("id"),
                "block": step.get("block"),
                "status": step.get("status"),
                "error": step.get("error"),
            }
        )
    (run_dir / "events.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    index_entry = {
        "schema_version": STATE_ARTIFACT_SCHEMA_VERSION,
        "run_id": run_id,
        "flow": artifact["flow"],
        "status": artifact["record"].get("status"),
        "dry_run": artifact["dry_run"],
        "state_file": str((Path("runs") / run_id / "state.json").as_posix()),
        "events_file": str((Path("runs") / run_id / "events.jsonl").as_posix()),
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(index_entry, sort_keys=True) + "\n")


@contextmanager
def _temporary_env(values: Dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


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
            if ttype == "cron" and not trigger.get("schedule"):
                errors.append(
                    "flow.trigger.schedule is required when trigger.type == 'cron'"
                )
            if ttype == "webhook" and not trigger.get("url"):
                errors.append(
                    "flow.trigger.url is required when trigger.type == 'webhook'"
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
_SECRET_QUERY_RE = re.compile(
    r"(?i)([?&](?:api[_-]?key|token|access[_-]?token|password|secret|signature|auth)=)[^&\s]+"
)
_SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|access[_-]?token|password|secret|authorization)\s*[:=]\s*([^\s,;]+)"
)
_AUTH_BEARER_ASSIGN_RE = re.compile(
    r"(?i)\bauthorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/=-]+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")


def _redact_error_text(text: str) -> str:
    text = _AUTH_BEARER_ASSIGN_RE.sub("Authorization: Bearer <redacted>", text)
    text = _BEARER_RE.sub("Bearer <redacted>", text)
    text = _SECRET_QUERY_RE.sub(r"\1<redacted>", text)
    text = _SECRET_ASSIGN_RE.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    return text


def _safe_exception_text(exc: BaseException) -> str:
    return _redact_error_text(f"{type(exc).__name__}: {exc}")


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


def _approval_needed(spec: Dict[str, Any]) -> bool:
    return bool(spec.get("requires_approval"))


def _approval_allowed(identifier: str, block_name: str, approvals: Set[str]) -> bool:
    return bool({"all", identifier, block_name} & approvals)


def _approval_error(identifier: str, block_name: str, reason: Any = None) -> str:
    msg = f"approval required for {identifier} ({block_name})"
    if reason:
        msg += f": {_redact_error_text(str(reason))}"
    return msg


def run_flow(flow: Dict[str, Any], *, dry_run: bool = False,
             strict: bool = False, validate: bool = False,
             initial_ctx: Optional[Dict[str, Any]] = None,
             approvals: Optional[Set[str]] = None,
             run_id: Optional[str] = None) -> Dict[str, Any]:
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
    approved = set(approvals or set())
    effective_run_id = run_id or _default_run_id()
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
            run_id=effective_run_id,
        )

    # Mesh activity: a REAL (non-dry-run) execution flips this node to
    # "executing" with the flow name as the task label; dry-runs (planning
    # only) are not "work" and are not reported. `_run_ok` stays False until we
    # reach the clean return, so any raise (execution/approval error) makes the
    # `finally` fall back to "error".
    _tracking = not dry_run
    if _tracking:
        activity.registry().begin(str(flow.get("name", "?")), tool="phantom-flow")
    _run_ok = False
    try:
        for step in flow.get("pipeline", []):
            sid = step.get("id") or step.get("block", "?")
            block_name = step.get("block", "?")
            needs_approval = _approval_needed(step)
            plan.append(
                f"pipeline.{sid} -> {block_name}"
                + (" [requires approval]" if needs_approval else "")
            )
            if strict and block_name not in BLOCK_REGISTRY:
                raise KeyError(f"unknown block: {block_name}")
            if dry_run:
                continue
            fn = BLOCK_REGISTRY.get(block_name)
            if fn is None:
                safe_error = f"unknown block: {block_name}"
                steps.append(StepRecord(id=str(sid), block=block_name, status="error",
                                        error=safe_error))
                raise FlowExecutionError(
                    f"pipeline step {sid!r} ({block_name}) failed: {safe_error}",
                    _finish("error"),
                    plan,
                )
            if needs_approval and not _approval_allowed(str(sid), block_name, approved):
                safe_error = _approval_error(str(sid), block_name, step.get("risk_reason"))
                steps.append(StepRecord(id=str(sid), block=block_name, status="blocked",
                                        error=safe_error))
                raise ApprovalRequiredError(
                    f"pipeline step {sid!r} ({block_name}) blocked: {safe_error}",
                    _finish("blocked"),
                    plan,
                )
            spec = _resolve({k: v for k, v in step.items()
                             if k not in {"id", "block", "requires_approval",
                                          "risk_reason"}}, ctx)
            try:
                ctx[sid] = fn(spec, ctx)
            except Exception as exc:  # noqa: BLE001 - record then re-surface
                safe_error = _safe_exception_text(exc)
                steps.append(StepRecord(id=sid, block=block_name, status="error",
                                        error=safe_error))
                raise FlowExecutionError(
                    f"pipeline step {sid!r} ({block_name}) failed: {safe_error}",
                    _finish("error"),
                    plan,
                ) from exc
            steps.append(StepRecord(id=sid, block=block_name, status="ok"))

        for action in flow.get("outbound", []):
            action_id = str(action.get("id") or f"outbound:{action.get('block', '?')}")
            block_name = action.get("block", "?")
            when = action.get("when")
            needs_approval = _approval_needed(action)
            plan.append(f"outbound -> {block_name}"
                        + (f"  [gated by {when}]" if when else "")
                        + (" [requires approval]" if needs_approval else ""))
            if strict and block_name not in BLOCK_REGISTRY:
                raise KeyError(f"unknown action: {block_name}")
            if dry_run:
                continue
            if not _gate_passes(when, ctx):
                continue
            fn = BLOCK_REGISTRY.get(block_name)
            if fn is None:
                safe_error = f"unknown action: {block_name}"
                steps.append(StepRecord(id=action_id, block=block_name,
                                        status="error", error=safe_error))
                raise FlowExecutionError(
                    f"outbound action {block_name} failed: {safe_error}",
                    _finish("error"),
                    plan,
                )
            if needs_approval and not _approval_allowed(action_id, block_name, approved):
                safe_error = _approval_error(action_id, block_name, action.get("risk_reason"))
                steps.append(StepRecord(id=action_id, block=block_name, status="blocked",
                                        error=safe_error))
                raise ApprovalRequiredError(
                    f"outbound action {block_name} blocked: {safe_error}",
                    _finish("blocked"),
                    plan,
                )
            spec = _resolve({k: v for k, v in action.items()
                             if k not in {"id", "block", "when",
                                          "requires_approval", "risk_reason"}}, ctx)
            try:
                fn(spec, ctx)
            except Exception as exc:  # noqa: BLE001 - record then re-surface
                safe_error = _safe_exception_text(exc)
                steps.append(StepRecord(id=action_id, block=block_name, status="error",
                                        error=safe_error))
                raise FlowExecutionError(
                    f"outbound action {block_name} failed: {safe_error}",
                    _finish("error"),
                    plan,
                ) from exc
            steps.append(StepRecord(id=action_id, block=block_name, status="ok"))

        record = _finish("ok")
        _run_ok = True
        return {"plan": plan, "context": ctx, "dry_run": dry_run,
                "name": flow.get("name", "?"), "record": record}
    finally:
        if _tracking:
            activity.registry().end(ok=_run_ok)


def _cron_field(field: str, lo: int, hi: int) -> set:
    """Parse one cron field into the set of matching ints. Supports '*', 'a,b' lists,
    'a-b' ranges, and '*/n' or 'a-b/n' steps. Values outside [lo,hi] raise ValueError."""
    out = set()
    for part in field.split(","):
        part = part.strip()
        step = 1
        if "/" in part:
            base, _, step_s = part.partition("/")
            step = int(step_s)
            if step <= 0:
                raise ValueError(f"invalid step in cron field: {part!r}")
        else:
            base = part
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, _, b = base.partition("-")
            start, end = int(a), int(b)
        else:
            start = end = int(base)
        if start < lo or end > hi or start > end:
            raise ValueError(f"cron field out of range [{lo},{hi}]: {part!r}")
        out.update(range(start, end + 1, step))
    return out


def schedule_matches(expr: str, dt: datetime) -> bool:
    """Return True if the 5-field cron expression `expr` (minute hour day-of-month
    month day-of-week) fires at datetime `dt`. Pure stdlib, no croniter.

    day-of-week is 0-6 (Sun..Sat); 7 is also accepted as Sunday. As in standard
    cron, day-of-month and day-of-week are OR-ed when BOTH are restricted; if either
    is '*' only the other constrains the match.
    """
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"cron expression must have 5 fields, got {len(fields)}: {expr!r}")
    minute, hour, dom, mon, dow = fields
    min_ok = dt.minute in _cron_field(minute, 0, 59)
    hour_ok = dt.hour in _cron_field(hour, 0, 23)
    mon_ok = dt.month in _cron_field(mon, 1, 12)
    if not (min_ok and hour_ok and mon_ok):
        return False
    dom_set = _cron_field(dom, 1, 31)
    dow_set = _cron_field(dow, 0, 7)
    if 7 in dow_set:
        dow_set.add(0)
    cur_dow = (dt.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0..Sat=6
    dom_restricted = dom.strip() != "*"
    dow_restricted = dow.strip() != "*"
    dom_ok = dt.day in dom_set
    dow_ok = cur_dow in dow_set
    if dom_restricted and dow_restricted:
        return dom_ok or dow_ok
    if dom_restricted:
        return dom_ok
    if dow_restricted:
        return dow_ok
    return True


# ---------- CLI ----------

def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _approval_gate_ids(flow: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for step in flow.get("pipeline", []):
        if isinstance(step, dict) and _approval_needed(step):
            ids.append(str(step.get("id") or step.get("block", "?")))
    for action in flow.get("outbound", []):
        if isinstance(action, dict) and _approval_needed(action):
            ids.append(str(action.get("id") or f"outbound:{action.get('block', '?')}"))
    return ids


def _run_and_write_artifact(
    flow: Dict[str, Any],
    *,
    flow_path: Path,
    artifact_path: Path,
    dry_run: bool,
    strict: bool,
    approvals: Set[str],
    run_id: str,
    state_dir: Optional[Path],
) -> Dict[str, Any]:
    error_text: Optional[str] = None
    try:
        summary = run_flow(
            flow,
            dry_run=dry_run,
            strict=strict,
            approvals=approvals,
            run_id=run_id,
        )
        exit_code = 0
    except ApprovalRequiredError as exc:
        error_text = str(exc)
        summary = {
            "name": exc.record.name,
            "dry_run": dry_run,
            "record": exc.record,
            "plan": exc.plan,
        }
        exit_code = 3
    except FlowExecutionError as exc:
        error_text = str(exc)
        summary = {
            "name": exc.record.name,
            "dry_run": dry_run,
            "record": exc.record,
            "plan": exc.plan,
        }
        exit_code = 1

    artifact = build_run_artifact(summary, flow_path=flow_path, error=error_text)
    write_run_artifact(artifact_path, artifact)
    if state_dir:
        write_state_artifacts(
            state_dir,
            build_state_artifact(
                summary,
                run_id=run_id,
                flow_path=flow_path,
                approvals=approvals,
                error=error_text,
            ),
        )
    return {"exit_code": exit_code, "artifact": artifact}


def _scenario_main(argv: List[str]) -> int:
    root = _repo_root()
    default_flow = root / "flows" / "examples" / "local-automation-scenario.yaml"
    default_sample = root / "flows" / "samples" / "ai-jobs-sample.txt"
    parser = argparse.ArgumentParser(
        prog="phantom-flow scenario",
        description="Run the local automation scenario proof and write evidence artifacts.",
    )
    parser.add_argument("flow", nargs="?", default=str(default_flow),
                        help="approval-gated flow YAML to exercise")
    parser.add_argument("--sample", type=Path, default=default_sample,
                        help="local text fixture exposed as PHANTOM_FLOW_SAMPLE")
    parser.add_argument("--out-dir", type=Path,
                        default=Path("artifacts") / "local-automation-scenario",
                        help="directory for plan/blocked/approved artifacts")
    parser.add_argument("--approve", action="append", default=[],
                        help="approval id for the approved run (default: all gates in the flow)")
    parser.add_argument("--run-id-prefix", default="local-automation-scenario",
                        help="stable prefix for state/log run ids")
    args = parser.parse_args(argv)

    flow_path = Path(args.flow).expanduser().resolve()
    sample_path = args.sample.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    state_dir = out_dir / "state"
    scenario_log = out_dir / "scenario.log"
    stdout_log = out_dir / "stdout.log"

    if not flow_path.exists():
        print(f"error: flow file not found: {flow_path}", file=sys.stderr)
        return 2
    if not sample_path.exists():
        print(f"error: sample file not found: {sample_path}", file=sys.stderr)
        return 2

    try:
        flow = load_flow(flow_path)
        validate_flow(flow)
    except FlowValidationError as exc:
        print(f"error: invalid flow {flow_path.name}:", file=sys.stderr)
        for problem in exc.errors:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"error: failed to load {flow_path}: {exc}", file=sys.stderr)
        return 2

    approval_ids = _approval_gate_ids(flow)
    if not approval_ids:
        print("error: scenario flows must include at least one requires_approval gate",
              file=sys.stderr)
        return 2

    approvals = set(args.approve or approval_ids)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = {
        "PHANTOM_FLOW_SAMPLE": sample_path.as_uri(),
        "PHANTOM_FLOW_STUB_LLM": "1",
        "PHANTOM_FLOW_SCENARIO_LOG": str(scenario_log),
    }
    with _temporary_env(env), stdout_log.open("w", encoding="utf-8") as stdout_fh:
        plan = _run_and_write_artifact(
            flow,
            flow_path=flow_path,
            artifact_path=out_dir / "plan.json",
            dry_run=True,
            strict=True,
            approvals=set(),
            run_id=f"{args.run_id_prefix}-plan",
            state_dir=state_dir,
        )
        with redirect_stdout(stdout_fh):
            blocked = _run_and_write_artifact(
                flow,
                flow_path=flow_path,
                artifact_path=out_dir / "blocked.json",
                dry_run=False,
                strict=True,
                approvals=set(),
                run_id=f"{args.run_id_prefix}-blocked",
                state_dir=state_dir,
            )
            approved = _run_and_write_artifact(
                flow,
                flow_path=flow_path,
                artifact_path=out_dir / "approved.json",
                dry_run=False,
                strict=True,
                approvals=approvals,
                run_id=f"{args.run_id_prefix}-approved",
                state_dir=state_dir,
            )

    ok = (
        plan["exit_code"] == 0
        and blocked["exit_code"] == 3
        and approved["exit_code"] == 0
    )
    summary = {
        "schema_version": 1,
        "status": "ok" if ok else "error",
        "flow": {"name": flow.get("name", "?"), "file": flow_path.name},
        "sample": sample_path.name,
        "approvals": sorted(approvals),
        "artifacts": {
            "plan": "plan.json",
            "blocked": "blocked.json",
            "approved": "approved.json",
            "state_dir": "state",
            "scenario_log": "scenario.log",
            "stdout_log": "stdout.log",
        },
        "phase_results": {
            "plan": {
                "exit_code": plan["exit_code"],
                "record_status": plan["artifact"]["record"]["status"],
            },
            "blocked": {
                "exit_code": blocked["exit_code"],
                "record_status": blocked["artifact"]["record"]["status"],
            },
            "approved": {
                "exit_code": approved["exit_code"],
                "record_status": approved["artifact"]["record"]["status"],
            },
        },
    }
    (out_dir / "scenario-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1

def _demo_validate_main(argv: List[str]) -> int:
    """Self-contained validate + dry-run-PLAN demo (no external args required).

    Loads a BUNDLED example flow (``flows/examples/demo-validate.yaml``), runs
    full schema validation, then a strict dry-run so every block name is
    checked against the registry without touching the network / an LLM / the
    filesystem, and prints a JSON validation+plan summary. Exits 0 on a valid,
    fully-resolvable flow.
    """
    root = _repo_root()
    default_flow = root / "flows" / "examples" / "demo-validate.yaml"
    parser = argparse.ArgumentParser(
        prog="phantom-flow demo-validate",
        description="Validate + dry-run-PLAN a bundled example flow and print a JSON summary.",
    )
    parser.add_argument("flow", nargs="?", default=str(default_flow),
                        help="flow YAML to validate + plan (default: bundled demo flow)")
    args = parser.parse_args(argv)

    flow_path = Path(args.flow).expanduser().resolve()
    if not flow_path.exists():
        print(f"error: flow file not found: {flow_path}", file=sys.stderr)
        return 2

    try:
        flow = load_flow(flow_path)
    except Exception as exc:  # pragma: no cover - load/parse failure
        print(f"error: failed to load {flow_path}: {exc}", file=sys.stderr)
        return 2

    validation_errors: List[str] = []
    try:
        validate_flow(flow)
    except FlowValidationError as exc:
        validation_errors = list(exc.errors)

    try:
        # strict dry-run: PLAN only, but assert every block resolves.
        summary = run_flow(flow, dry_run=True, strict=True)
    except KeyError as exc:
        validation_errors.append(f"unknown block: {exc}")
        summary = None

    ok = not validation_errors and summary is not None
    approval_gates = _approval_gate_ids(flow)
    out = {
        "schema_version": 1,
        "command": "demo-validate",
        "status": "ok" if ok else "error",
        "flow": {"name": flow.get("name", "?"), "file": flow_path.name},
        "validation": {
            "valid": not validation_errors,
            "errors": validation_errors,
        },
        "dry_run": True,
        "approval_gates": approval_gates,
        "plan": list(summary["plan"]) if summary else [],
        "record": summary["record"].to_dict() if summary else None,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if ok else 1


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

        def do_GET(self):
            # Mesh activity reporter: the running webhook listener also serves
            # GET /activity so this node surfaces in /api/mesh/activity while it
            # waits for (and runs) webhook-triggered flows.
            if self.path.split("?", 1)[0] == "/activity":
                self._send_json(200, activity.mesh_activity_payload())
                return
            self._send_json(404, {"error": "not found", "path": self.path})

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


def _schedule_main(argv):
    parser = argparse.ArgumentParser(prog="phantom-flow schedule",
                                     description="Run a flow if its cron trigger.schedule matches a given time (time-injectable, no daemon).")
    parser.add_argument("flow", help="path to flow YAML with a cron trigger.schedule")
    parser.add_argument("--now", default=None,
                        help="ISO-8601 datetime to evaluate the schedule against (default: real clock)")
    parser.add_argument("--once", action="store_true",
                        help="evaluate the schedule once against --now and run the flow if due, else print 'not due'")
    args = parser.parse_args(argv)
    path = Path(args.flow).expanduser().resolve()
    if not path.exists():
        print(f"error: flow file not found: {path}", file=sys.stderr)
        return 2
    flow = load_flow(path)
    trigger = flow.get("trigger", {})
    schedule = trigger.get("schedule") if isinstance(trigger, dict) else None
    if not schedule:
        print("error: flow has no cron trigger.schedule", file=sys.stderr)
        return 2
    now = datetime.fromisoformat(args.now) if args.now else datetime.now()
    if not args.once:
        # The continuous wall-clock daemon (sleep-loop ticking on the real clock)
        # is intentionally OUT OF SCOPE here (env/time-blocked). Ship the hermetic core.
        print("phantom-flow schedule :: daemon loop is not implemented (use --once with --now).")
        print(f"  flow={flow.get('name', '?')!r} schedule={schedule!r}")
        return 0
    if schedule_matches(schedule, now):
        print(f"phantom-flow schedule :: DUE at {now.isoformat()} (schedule {schedule!r}) -> running {flow.get('name', '?')!r}")
        summary = run_flow(flow)
        record = summary["record"]
        print(f"  status={record.status} steps={len(record.steps)}")
        return 0
    print(f"phantom-flow schedule :: not due at {now.isoformat()} (schedule {schedule!r})")
    return 0


def _activity_main(argv):
    parser = argparse.ArgumentParser(
        prog="phantom-flow activity",
        description="Start a stdlib HTTP server exposing GET /activity so this "
                    "node surfaces in the phantom-mesh /api/mesh/activity grid.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=activity.DEFAULT_ACTIVITY_PORT)
    args = parser.parse_args(argv)
    activity.serve_activity(args.host, args.port)
    return 0


def _main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "serve":
        return _serve_main(argv[1:])
    if argv and argv[0] == "activity":
        return _activity_main(argv[1:])
    if argv and argv[0] == "schedule":
        return _schedule_main(argv[1:])
    if argv and argv[0] == "scenario":
        return _scenario_main(argv[1:])
    if argv and argv[0] == "demo-validate":
        return _demo_validate_main(argv[1:])

    parser = argparse.ArgumentParser(
        prog="phantom_flow.runner",
        description=(
            "Minimal YAML flow executor. Subcommands: serve, activity, "
            "schedule, scenario, demo-validate."
        ),
    )
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
    parser.add_argument("--record-out", type=Path, default=None,
                        help="write a stable run artifact JSON with plan and run record only")
    parser.add_argument("--approve", action="append", default=[],
                        help="approve a requires_approval step/action by id, block name, or 'all'")
    parser.add_argument("--run-id", default=None,
                        help="stable run id for state/log artifacts (default: timestamp + process id)")
    parser.add_argument("--state-dir", type=Path, default=None,
                        help="write local state/log artifacts under this directory")
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

    approvals = set(args.approve or [])
    run_id = args.run_id or _default_run_id()

    try:
        summary = run_flow(
            flow,
            dry_run=args.dry_run,
            strict=args.strict,
            approvals=approvals,
            run_id=run_id,
        )
    except ApprovalRequiredError as exc:
        print(f"error: approval required: {exc}", file=sys.stderr)
        error_text = str(exc)
        summary = {
            "name": exc.record.name,
            "dry_run": args.dry_run,
            "record": exc.record,
            "plan": exc.plan,
        }
        if args.record_out:
            artifact = build_run_artifact(
                summary,
                flow_path=path,
                error=error_text,
            )
            write_run_artifact(args.record_out, artifact)
        if args.state_dir:
            write_state_artifacts(
                args.state_dir,
                build_state_artifact(
                    summary,
                    run_id=run_id,
                    flow_path=path,
                    approvals=approvals,
                    error=error_text,
                ),
            )
        if args.json:
            print(json.dumps({"record": exc.record.to_dict()}, indent=2))
        return 3
    except FlowExecutionError as exc:
        print(f"error: flow execution failed: {exc}", file=sys.stderr)
        error_text = str(exc)
        summary = {
            "name": exc.record.name,
            "dry_run": args.dry_run,
            "record": exc.record,
            "plan": exc.plan,
        }
        if args.record_out:
            artifact = build_run_artifact(
                summary,
                flow_path=path,
                error=error_text,
            )
            write_run_artifact(args.record_out, artifact)
        if args.state_dir:
            write_state_artifacts(
                args.state_dir,
                build_state_artifact(
                    summary,
                    run_id=run_id,
                    flow_path=path,
                    approvals=approvals,
                    error=error_text,
                ),
            )
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

    if args.record_out:
        write_run_artifact(
            args.record_out,
            build_run_artifact(summary, flow_path=path),
        )

    if args.state_dir:
        write_state_artifacts(
            args.state_dir,
            build_state_artifact(
                summary,
                run_id=run_id,
                flow_path=path,
                approvals=approvals,
            ),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
