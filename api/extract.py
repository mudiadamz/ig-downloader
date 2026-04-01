from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Vercel runs this file without adding api/ to sys.path; sibling modules won't resolve.
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

import yt_dlp

from media_urls import is_supported_url, normalize_url
from ydl_helpers import merge_youtube_opts


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            return self._json(400, {"error": "Invalid JSON body"})

        url = body.get("url", "").strip()
        if not is_supported_url(url):
            return self._json(
                400,
                {
                    "error": "Invalid URL. Use an Instagram post/reel or YouTube video link.",
                },
            )

        url = normalize_url(url)

        base_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "best[ext=mp4]/best",
            "socket_timeout": 15,
        }
        opts, cookie_cleanup = merge_youtube_opts(base_opts)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if info.get("_type") == "playlist":
                entries = list(info.get("entries", []))
                videos = [e for e in entries if e and e.get("ext") != "jpg"]
                if not videos:
                    return self._json(404, {"error": "No video found in this post"})
                info = videos[0]

            video_url = info.get("url")
            if not video_url:
                for key in ("requested_formats", "formats"):
                    fmts = info.get(key) or []
                    for f in reversed(fmts):
                        if f.get("url") and f.get("vcodec", "none") != "none":
                            video_url = f["url"]
                            break
                    if video_url:
                        break

            if not video_url:
                return self._json(404, {"error": "No downloadable video found"})

            return self._json(200, {
                "url": video_url,
                "thumbnail": info.get("thumbnail"),
                "title": (info.get("title") or info.get("description") or "")[:120],
                "uploader": info.get("uploader") or info.get("channel"),
                "duration": info.get("duration"),
                "filesize": info.get("filesize") or info.get("filesize_approx"),
            })

        except yt_dlp.utils.DownloadError as exc:
            msg = str(exc)
            low = msg.lower()
            if "login" in low or "private" in low:
                return self._json(403, {"error": "This post is private or requires login"})
            if "sign in" in low and "bot" in low:
                return self._json(
                    503,
                    {
                        "error": (
                            "YouTube blocked this server (bot check). "
                            "Add Netscape cookies: set env YT_DLP_COOKIES (file contents) or "
                            "YT_DLP_COOKIE_FILE on Vercel, or run download.py locally with "
                            "--cookies or --cookies-from-browser. "
                            "See yt-dlp wiki: exporting YouTube cookies."
                        ),
                    },
                )
            return self._json(500, {"error": f"Extraction failed: {msg}"})
        except Exception as exc:
            return self._json(500, {"error": f"Unexpected error: {exc}"})
        finally:
            cookie_cleanup()

    def _json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
