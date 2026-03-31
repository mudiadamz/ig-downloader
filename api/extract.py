from http.server import BaseHTTPRequestHandler
import json
import re

import yt_dlp

IG_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+"
)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            return self._json(400, {"error": "Invalid JSON body"})

        url = body.get("url", "").strip()
        if not IG_RE.match(url):
            return self._json(400, {"error": "Invalid Instagram URL"})

        opts = {
            "quiet": True,
            "no_warnings": True,
            "format": "best[ext=mp4]/best",
            "socket_timeout": 15,
        }

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
            if "login" in msg.lower() or "private" in msg.lower():
                return self._json(403, {"error": "This post is private or requires login"})
            return self._json(500, {"error": f"Extraction failed: {msg}"})
        except Exception as exc:
            return self._json(500, {"error": f"Unexpected error: {exc}"})

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
