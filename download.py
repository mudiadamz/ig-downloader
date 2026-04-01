import sys
import os
import argparse
from pathlib import Path

import yt_dlp

_api_dir = Path(__file__).resolve().parent / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from media_urls import is_supported_url, normalize_url
from ydl_helpers import merge_youtube_opts


DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download Instagram and YouTube videos",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="Instagram post/reel or YouTube video URLs",
    )
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
    parser.add_argument(
        "--cookies",
        metavar="FILE",
        help="Netscape cookie file (helps with YouTube bot checks; see yt-dlp wiki)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        dest="cookies_from_browser",
        metavar="BROWSER",
        help="Load cookies from browser (e.g. chrome, firefox, safari, edge)",
    )
    args = parser.parse_args()
    if args.cookies and args.cookies_from_browser:
        parser.error("use only one of --cookies and --cookies-from-browser")
    return args


def validate_url(url: str) -> bool:
    return is_supported_url(url)


def download_video(
    url: str,
    output_dir: str,
    *,
    quiet: bool = False,
    cookies: str | None = None,
    cookies_from_browser: str | None = None,
) -> str | None:
    os.makedirs(output_dir, exist_ok=True)

    outtmpl = os.path.join(output_dir, "%(uploader)s_%(id)s.%(ext)s")

    opts: dict = {
        "outtmpl": outtmpl,
        "format": "best",
        "merge_output_format": "mp4",
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": quiet,
        "retries": 5,
        "socket_timeout": 30,
    }
    if cookies:
        opts["cookiefile"] = cookies
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    opts, cookie_cleanup = merge_youtube_opts(opts)
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
    finally:
        cookie_cleanup()


def main():
    args = parse_args()

    invalid = [u for u in args.urls if not validate_url(u)]
    if invalid:
        print("[ERROR] Invalid URL(s) — need Instagram or YouTube video links:", file=sys.stderr)
        for u in invalid:
            print(f"  - {u}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading {len(args.urls)} video(s) to {args.output_dir}\n")

    results = {"ok": [], "fail": []}

    for i, url in enumerate(args.urls, 1):
        norm = normalize_url(url.strip())
        print(f"[{i}/{len(args.urls)}] {norm}")
        path = download_video(
            norm,
            args.output_dir,
            quiet=args.quiet,
            cookies=args.cookies,
            cookies_from_browser=args.cookies_from_browser,
        )
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
