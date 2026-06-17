"""Regression: tools.http_get must never issue an UNBOUNDED read.

The `timeout: null/0` hole was fixed (`spec.get("timeout") or 30`), but the
analogous `max_bytes` was not: `resp.read(spec.get("max_bytes", 50*1024))`
means an explicit `null` makes `resp.read(None)` read the ENTIRE response
(unbounded memory), and `0` truncates the body to empty. Both must coerce to
the bounded default, exactly like timeout.
"""

from __future__ import annotations

import io

import phantom_flow.runner as runner


class _FakeResp:
    """Minimal urlopen() context manager that records the read() size arg."""

    def __init__(self, seen):
        self._seen = seen
        self._buf = io.BytesIO(b"x" * 200_000)  # larger than the 50KiB default
        self.status = 200
        self.headers = {}

    def read(self, n=None):
        self._seen.append(n)
        return self._buf.read(n if n is not None else -1)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch_urlopen(monkeypatch, seen):
    def _fake_urlopen(req, timeout=None):
        return _FakeResp(seen)
    monkeypatch.setattr(runner.urllib.request, "urlopen", _fake_urlopen)


def test_http_get_max_bytes_null_or_zero_coerces_to_bounded(monkeypatch):
    """null and 0 must both become a finite, positive read size (never None)."""
    for bad in (None, 0):
        seen = []
        _patch_urlopen(monkeypatch, seen)
        out = runner._block_http_get(
            {"url": "http://example.com", "max_bytes": bad}, {})
        assert seen and seen[0] is not None and seen[0] > 0, (bad, seen)
        # body is bounded to the default cap, not the full 200KB payload
        assert out["body_len"] <= 50 * 1024


def test_http_get_max_bytes_absent_uses_default(monkeypatch):
    seen = []
    _patch_urlopen(monkeypatch, seen)
    out = runner._block_http_get({"url": "http://example.com"}, {})
    assert seen[0] == 50 * 1024
    assert out["body_len"] <= 50 * 1024


def test_http_get_max_bytes_explicit_value_respected(monkeypatch):
    seen = []
    _patch_urlopen(monkeypatch, seen)
    runner._block_http_get(
        {"url": "http://example.com", "max_bytes": 1024}, {})
    assert seen[0] == 1024
