"""Shared URL normalization and allowlist for Instagram + YouTube."""

import re
from urllib.parse import parse_qs, urlparse

IG_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+"
)

YOUTUBE_WATCH_RE = re.compile(
    r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}$"
)

_VIDEO_ID = re.compile(r"^[\w-]{11}$")


def normalize_url(url: str) -> str:
    u = url.strip()
    parsed = urlparse(u)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""

    if host == "youtu.be":
        vid = path.strip("/").split("/")[0]
        if _VIDEO_ID.fullmatch(vid):
            return f"https://www.youtube.com/watch?v={vid}"
    elif "youtube.com" in host:
        if path.startswith("/shorts/"):
            parts = path.split("/")
            if len(parts) > 2:
                vid = parts[2].split("?")[0]
                if _VIDEO_ID.fullmatch(vid):
                    return f"https://www.youtube.com/watch?v={vid}"
        for prefix in ("/embed/", "/v/"):
            if path.startswith(prefix):
                parts = path.split("/")
                if len(parts) > 2:
                    vid = parts[2].split("?")[0]
                    if _VIDEO_ID.fullmatch(vid):
                        return f"https://www.youtube.com/watch?v={vid}"
        if path == "/watch" or path.startswith("/watch"):
            v = (parse_qs(parsed.query).get("v") or [None])[0]
            if v and _VIDEO_ID.fullmatch(v):
                return f"https://www.youtube.com/watch?v={v}"

    out = u
    for sep in ("?", "#"):
        if sep in out:
            out = out.split(sep, 1)[0]
    return out.rstrip("/")


def is_supported_url(url: str) -> bool:
    u = normalize_url(url)
    return bool(IG_RE.match(u)) or bool(YOUTUBE_WATCH_RE.match(u))
