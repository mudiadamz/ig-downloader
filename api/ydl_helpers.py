"""Shared yt-dlp options: cookies from env, YouTube client preferences."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from typing import Any


def _prepare_cookiefile_from_env() -> tuple[str | None, Callable[[], None]]:
    """
    Resolve cookie file for yt-dlp from environment.

    - YT_DLP_COOKIE_FILE: path to a Netscape-format cookies file (local / mounted volume).
    - YT_DLP_COOKIES: raw Netscape cookie file contents (e.g. Vercel secret); written to a temp file.

    Returns (path_or_none, cleanup). Call cleanup() after YoutubeDL is done.
    """
    explicit = os.environ.get("YT_DLP_COOKIE_FILE", "").strip()
    if explicit and os.path.isfile(explicit):
        return explicit, lambda: None

    raw = os.environ.get("YT_DLP_COOKIES", "").strip()
    if not raw:
        return None, lambda: None

    fd, path = tempfile.mkstemp(suffix="_yt_dlp_cookies.txt", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception:
        if os.path.isfile(path):
            os.unlink(path)
        raise

    def cleanup() -> None:
        if os.path.isfile(path):
            try:
                os.unlink(path)
            except OSError:
                pass

    return path, cleanup


def merge_youtube_opts(base: dict[str, Any]) -> tuple[dict[str, Any], Callable[[], None]]:
    """
    Copy base opts, add cookiefile if configured, and set YouTube extractor_args
    that often work better for automated / datacenter requests (still may require cookies).
    """
    opts: dict[str, Any] = dict(base)
    cleanup: Callable[[], None] = lambda: None
    if "cookiefile" not in opts and "cookiesfrombrowser" not in opts:
        path, cleanup = _prepare_cookiefile_from_env()
        if path:
            opts["cookiefile"] = path

    existing = dict(opts.get("extractor_args") or {})
    yt = dict(existing.get("youtube") or {})
    if "player_client" not in yt:
        yt["player_client"] = ["android", "web", "ios"]
    existing["youtube"] = yt
    opts["extractor_args"] = existing

    return opts, cleanup
