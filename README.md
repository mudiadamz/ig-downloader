# IG Downloader

Small tools to extract and download Instagram (and, via the CLI, YouTube) video using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## What’s included

- **Web UI** (`index.html`) — Paste an Instagram post, reel, or TV URL. The page calls a serverless API to resolve a direct video URL, then previews it and lets you save it in the browser.
- **API** (`api/extract.py`) — Vercel Python function: `POST /api/extract` with JSON `{ "url": "<instagram url>" }`. Returns metadata and a playable URL when extraction succeeds.
- **CLI** (`download.py`) — Download one or more videos to disk. Supports **Instagram** (`/p/`, `/reel/`, `/reels/`, `/tv/`) and **YouTube** (watch, shorts, youtu.be, embed). Output defaults to a `downloads/` folder next to the script.

## Requirements

- Python **3.10+** (for the CLI and API code).
- Dependencies: see `requirements.txt` (currently `yt-dlp`).

```bash
pip install -r requirements.txt
```

## CLI usage

```bash
python download.py "https://www.instagram.com/reel/VIDEO_ID/"
python download.py "https://www.youtube.com/watch?v=VIDEO_ID" -o ./my-downloads
python download.py URL1 URL2 --quiet
```

Optional cookie helpers (when sites block or rate-limit):

```bash
python download.py URL --cookies cookies.txt
python download.py URL --cookies-from-browser chrome
```

Use only one of `--cookies` or `--cookies-from-browser`.

## Web app locally

The UI is static HTML. The extract endpoint must be served so `POST /api/extract` exists (as on Vercel). For local development, use the [Vercel CLI](https://vercel.com/docs/cli):

```bash
vercel dev
```

Then open the URL the CLI prints (static files and `api/` routes are wired like production).

## Deploy (Vercel)

The repo includes `vercel.json` so `api/extract.py` bundles the shared helpers. Connect the repo in Vercel or run `vercel` from the project root; set **Python** runtime if prompted. After deploy, open the site root to use `index.html`.

## Legal note

Only download content you have the right to access and use. Respect platform terms of service, copyright, and privacy. This project is a thin wrapper around yt-dlp; availability of any given URL depends on the platform and yt-dlp.
