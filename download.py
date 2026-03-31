import sys
import os
import re
import argparse
from datetime import datetime

import yt_dlp


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")

IG_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/"
    r"(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Download Instagram videos")
    parser.add_argument("urls", nargs="+", help="Instagram post/reel URLs")
    parser.add_argument(
        "-o", "--output-dir",
        default=DOWNLOADS_DIR,
        help=f"Output directory (default: {DOWNLOADS_DIR})",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    return parser.parse_args()


def validate_url(url: str) -> bool:
    return IG_URL_PATTERN.search(url) is not None


def download_video(url: str, output_dir: str, quiet: bool = False) -> str | None:
    os.makedirs(output_dir, exist_ok=True)

    outtmpl = os.path.join(output_dir, "%(uploader)s_%(id)s.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "format": "best",
        "merge_output_format": "mp4",
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": quiet,
        "retries": 5,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            final = base + ".mp4"
            if os.path.exists(final):
                return final
            if os.path.exists(filename):
                return filename
            return final
    except yt_dlp.utils.DownloadError as e:
        print(f"[ERROR] Failed to download {url}: {e}", file=sys.stderr)
        return None


def main():
    args = parse_args()

    invalid = [u for u in args.urls if not validate_url(u)]
    if invalid:
        print("[ERROR] Invalid Instagram URL(s):", file=sys.stderr)
        for u in invalid:
            print(f"  - {u}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading {len(args.urls)} video(s) to {args.output_dir}\n")

    results = {"ok": [], "fail": []}

    for i, url in enumerate(args.urls, 1):
        print(f"[{i}/{len(args.urls)}] {url}")
        path = download_video(url, args.output_dir, quiet=args.quiet)
        if path:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  -> Saved: {path} ({size_mb:.1f} MB)\n")
            results["ok"].append(path)
        else:
            print(f"  -> FAILED\n")
            results["fail"].append(url)

    print("=" * 50)
    print(f"Done: {len(results['ok'])} succeeded, {len(results['fail'])} failed")

    if results["fail"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
