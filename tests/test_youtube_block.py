"""Tests for the YouTube video ID parsing logic."""

from __future__ import annotations

import pytest
from phantom_flow.runner import _youtube_video_id


def test_youtube_video_id_parsing():
    # 1. Bare 11-char ID
    assert _youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_video_id("  dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"

    # 2. watch?v=
    assert _youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ&feature=share") == "dQw4w9WgXcQ"

    # 3. youtu.be/
    assert _youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_video_id("https://youtu.be/dQw4w9WgXcQ?t=43") == "dQw4w9WgXcQ"

    # 4. /shorts/
    assert _youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_video_id("https://youtube.com/shorts/dQw4w9WgXcQ?foo=bar") == "dQw4w9WgXcQ"

    # 5. /embed/
    assert _youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _youtube_video_id("https://youtube.com/embed/dQw4w9WgXcQ?rel=0") == "dQw4w9WgXcQ"

    # 6. Unparseable input giving None
    assert _youtube_video_id("") is None
    assert _youtube_video_id("   ") is None
    assert _youtube_video_id("https://www.google.com") is None
    assert _youtube_video_id("dQw4w9WgXc") is None  # 10 chars, too short
    assert _youtube_video_id("dQw4w9WgXcQY") is None  # 12 chars, too long if bare
    assert _youtube_video_id("https://youtube.com/watch?v=dQw4w9WgXc") is None  # too short inside url
