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
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - keep dry-run usable without PyYAML
    yaml = None


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
    url = spec["url"]
    ua = spec.get("user_agent", "phantom-flow/0.1")
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=spec.get("timeout", 30)) as resp:
        raw = resp.read(spec.get("max_bytes", 50 * 1024))
        body = raw.decode(resp.headers.get_content_charset("utf-8"),
                          errors="replace")
        return {"url": url, "status": resp.status, "body": body,
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
    llm = PhantomLLM()
    text = spec.get("input", "")
    prompt = spec.get("prompt", "Summarise the following text in 2 bullets:")
    res = llm.complete(f"{prompt}\n\n{text[:4000]}")
    return {"summary": res.text, "backend": res.backend}


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
    """Escape hatch for heavy steps that live inside the merged subtree."""
    cmd = spec["cmd"]
    if isinstance(cmd, str):
        cmd = ["bash", "-lc", cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=spec.get("timeout", 120))
    return {"stdout": proc.stdout, "stderr": proc.stderr,
            "returncode": proc.returncode}


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
             strict: bool = False) -> Dict[str, Any]:
    """Execute (or, with ``dry_run``, only plan) a flow.

    ``strict`` validates that every ``block`` name resolves in
    ``BLOCK_REGISTRY`` even during a dry-run — useful for linting flow files
    in CI without touching the network or an LLM.
    """
    ctx: Dict[str, Any] = {}
    plan: List[str] = []

    trigger = flow.get("trigger", {})
    plan.append(f"trigger: {trigger.get('type', '?')} "
                f"({trigger.get('schedule') or trigger.get('url') or trigger.get('on') or '-'})")

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
        ctx[sid] = fn(spec, ctx)

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
        fn(spec, ctx)

    return {"plan": plan, "context": ctx, "dry_run": dry_run,
            "name": flow.get("name", "?")}


# ---------- CLI ----------

def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="phantom_flow.runner",
                                     description="Minimal YAML flow executor.")
    parser.add_argument("flow", help="path to flow YAML")
    parser.add_argument("--dry-run", action="store_true",
                        help="parse + plan only; no network / no filesystem writes")
    parser.add_argument("--strict", action="store_true",
                        help="validate every block name against the registry "
                             "(lints a flow file; pairs well with --dry-run)")
    parser.add_argument("--json", action="store_true",
                        help="emit a final JSON summary on stdout")
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

    print(f"phantom-flow runner :: {path.name}")
    print(f"  name    = {flow.get('name', '?')}")
    print(f"  version = {flow.get('version', '?')}")
    print(f"  mode    = {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print(f"  llm_cli = {shutil.which('phantom') or '<not installed>'}")

    summary = run_flow(flow, dry_run=args.dry_run, strict=args.strict)

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
                          "context": safe_ctx}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
