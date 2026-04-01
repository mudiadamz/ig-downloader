"""Shared yt-dlp options and format strings."""

from __future__ import annotations

FORMAT_FOR_URL_EXTRACTION = "bestvideo*+bestaudio/best/worst"

FORMAT_FOR_FILE_DOWNLOAD = "best[ext=mp4]/best/bestvideo*+bestaudio/best/worst"
