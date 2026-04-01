"""Shared URL normalization and allowlist for Instagram."""

import re

IG_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+"
)


def normalize_url(url: str) -> str:
    out = url.strip()
    for sep in ("?", "#"):
        if sep in out:
            out = out.split(sep, 1)[0]
    return out.rstrip("/")


def is_supported_url(url: str) -> bool:
    return bool(IG_RE.match(normalize_url(url)))
