"""Packaging hygiene tests (P1-5).

The engine is intentionally near-stdlib. These tests pin the *core* runtime
dependency surface to exactly what the engine genuinely imports, so the
requirements never drift back toward the heavy vendored stack (LangChain,
Selenium, pandas, ...). They also confirm every engine import resolves.
"""

from __future__ import annotations

import sys
import tomllib  # py3.11+
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read_requirements() -> list[str]:
    req = ROOT / "requirements.txt"
    assert req.exists(), "root requirements.txt must exist"
    lines = []
    for raw in req.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def _dist_name(spec: str) -> str:
    for sep in ("==", ">=", "<=", "~=", ">", "<", "!=", "["):
        if sep in spec:
            return spec.split(sep, 1)[0].strip().lower()
    return spec.strip().lower()


def test_requirements_are_core_only():
    """requirements.txt holds exactly the engine's genuinely-used core dep."""
    names = {_dist_name(s) for s in _read_requirements()}
    # PyYAML is the single hard runtime dep (flow parsing).
    assert "pyyaml" in names
    # The heavy vendored stack must NOT leak into the engine requirements.
    banned = {
        "langchain", "langchain-core", "openai", "anthropic", "selenium",
        "playwright", "pandas", "numpy", "scikit-learn", "streamlit",
        "redis", "celery", "prefect", "temporalio", "fastapi", "uvicorn",
    }
    leaked = names & banned
    assert not leaked, f"heavy vendored deps leaked into core requirements: {leaked}"
    # Keep the core surface tiny.
    assert len(names) <= 2, f"core requirements grew unexpectedly: {names}"


def test_pyproject_core_dependencies_match():
    """pyproject.toml [project].dependencies stays core-only and consistent."""
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.exists(), "root pyproject.toml must exist"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data["project"]
    deps = {_dist_name(d) for d in project.get("dependencies", [])}
    assert deps == {"pyyaml"}, f"core dependencies must be just pyyaml, got {deps}"
    # youtube fetching is genuinely optional -> lives in an extra, not core.
    extras = project.get("optional-dependencies", {})
    yt = {_dist_name(d) for grp in extras.values() for d in grp}
    assert "youtube-transcript-api" in yt


def test_all_engine_imports_resolve():
    """Importing the engine (and re-importing fresh) must not raise."""
    for mod in ("phantom_flow", "phantom_flow.runner", "phantom_flow.llm_driver"):
        sys.modules.pop(mod, None)
    import phantom_flow  # noqa: F401
    import phantom_flow.llm_driver  # noqa: F401
    import phantom_flow.runner as r

    # The registry resolved and is populated -> module body executed cleanly.
    assert r.BLOCK_REGISTRY
    assert callable(r.run_flow)
