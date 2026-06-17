"""Guards that the docs stay honest (P2-3 / P3-1).

These pin the de-claiming done in this round so the aspirational marketing
(cluster-aware / event-driven / visual editor / "30+ tools" / n8n-replacement)
cannot silently creep back into README/DESIGN as if it were shipped. Such
claims belong in ROADMAP.md, which must exist and mark them as future.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_roadmap_exists_and_marks_future_work():
    text = _read("ROADMAP.md").lower()
    assert "not implemented" in text or "aspirational" in text
    # the over-claimed features are explicitly listed as future
    for feature in ("cluster", "visual flow editor", "webhook", "marketplace"):
        assert feature in text


def test_readme_does_not_overclaim_present_capabilities():
    text = _read("README.md")
    low = text.lower()
    # The old tagline claimed these as shipped differentiators. They are not.
    # (These are the *positive* marketing phrasings; a disclaimer like
    # "is not ... 600+ integrations" is fine and intentionally allowed.)
    banned_present_claims = [
        "cluster-aware + ai-native + cross-device",
        "first self-hosted + cluster-aware",
        "self-hosted + cluster-aware + ai-native",
        "7,000+ apps",
        "phantom-flow runs on 5 oses",
        "phantom-flow is event-driven",
    ]
    for claim in banned_present_claims:
        assert claim not in low, f"README still over-claims: {claim!r}"
    # And it must point at the roadmap + state the local-first reality.
    assert "ROADMAP.md" in text
    assert "local-first" in low


def test_readme_states_vendored_not_imported():
    low = _read("README.md").lower()
    assert "not imported by the engine" in low or "not be imported" in low \
        or "are not imported" in low


def test_design_declaims_event_driven_cluster_aware():
    low = _read("DESIGN.md").lower()
    # DESIGN must contain an explicit honesty note + a roadmap pointer.
    assert "roadmap" in low
    assert "cluster-aware" in low  # mentioned, but as future/not-implemented
    # the staged-keep decision for the vendored subtrees is preserved
    assert "ai_automation_framework" in low
