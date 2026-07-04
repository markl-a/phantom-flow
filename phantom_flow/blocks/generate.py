"""Deterministic generation adapter for phantom-flow pipeline steps."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


_RESERVED_KEYS = {"prompt", "input", "spec", "tool"}
_KIND_BY_TOOL = {
    "image_generate": "image",
    "music_generate": "music",
    "video_generate": "video",
    "tts_generate": "audio",
    "speech_generate": "audio",
    "text_generate": "text",
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _tool_kind(tool: str) -> str:
    if tool in _KIND_BY_TOOL:
        return _KIND_BY_TOOL[tool]
    if tool.endswith("_generate"):
        return tool[:-9] or "generated"
    return "generated"


def _prompt_from_spec(spec: Dict[str, Any]) -> str:
    prompt = str(spec.get("prompt") or spec.get("input") or "").strip()
    raw_spec = spec.get("spec")
    if prompt:
        return prompt
    if isinstance(raw_spec, str):
        return raw_spec.strip()
    if isinstance(raw_spec, dict):
        for key in ("prompt", "description", "topic"):
            value = raw_spec.get(key)
            if value:
                return str(value).strip()
    return ""


def _generation_params(spec: Dict[str, Any]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    raw_spec = spec.get("spec")
    if isinstance(raw_spec, dict):
        params.update(
            {k: v for k, v in raw_spec.items() if k not in {"prompt", "tool"}}
        )
    elif raw_spec is not None:
        params["spec"] = raw_spec

    for key, value in spec.items():
        if key not in _RESERVED_KEYS:
            params[key] = value
    return params


def _render_output(tool: str, prompt: str, params: Dict[str, Any],
                   request_id: str) -> str:
    kind = _tool_kind(tool)
    details = ", ".join(
        f"{key}={params[key]}" for key in sorted(params)
    ) or "default settings"
    return (
        f"{kind.capitalize()} generation {request_id}: {prompt}. "
        f"Tool={tool}; constraints={details}."
    )


def _block_generate(spec: Dict[str, Any], _ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Build a deterministic generated artifact manifest from prompt/spec input.

    The mesh MCP generators are not wired into this runner yet, so this block
    returns the exact request payload plus a stable local artifact description
    instead of shelling out to an external service.
    """
    prompt = _prompt_from_spec(spec)
    if not prompt:
        raise ValueError("pipeline.generate requires a non-empty prompt or input")

    raw_spec = spec.get("spec")
    tool = str(spec.get("tool") or "").strip()
    if not tool and isinstance(raw_spec, dict):
        tool = str(raw_spec.get("tool") or "").strip()
    tool = tool or "text_generate"

    params = _generation_params(spec)
    arguments = {"prompt": prompt, **params}
    fingerprint = _stable_json({"tool": tool, "arguments": arguments})
    request_id = "gen-" + hashlib.sha256(
        fingerprint.encode("utf-8")
    ).hexdigest()[:12]
    output = _render_output(tool, prompt, params, request_id)
    kind = _tool_kind(tool)

    return {
        "tool": tool,
        "kind": kind,
        "prompt": prompt,
        "spec": params,
        "request_id": request_id,
        "backend": "deterministic-template",
        "output": output,
        "artifact": {
            "id": request_id,
            "kind": kind,
            "content": output,
        },
        "mcp_request": {
            "tool": tool,
            "arguments": arguments,
        },
    }
