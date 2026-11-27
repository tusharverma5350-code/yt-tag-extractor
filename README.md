# TagExtract: free YouTube Tag Extractor

Paste any YouTube video or Shorts link to get its **tags, hashtags, full description, links, thumbnails (HD)**, stats and an **MP4 / MP3 download**.

**Live site:** https://yt-tag-extractor.netlify.app

Tools:
- [YouTube Tag Extractor](https://yt-tag-extractor.netlify.app/)
- [YouTube Shorts Tag Extractor](https://yt-tag-extractor.netlify.app/youtube-shorts-tag-extractor/)
- [YouTube Hashtag Extractor](https://yt-tag-extractor.netlify.app/youtube-hashtag-extractor/)
- [YouTube Description Extractor](https://yt-tag-extractor.netlify.app/youtube-description-extractor/)
- [YouTube Thumbnail Downloader](https://yt-tag-extractor.netlify.app/youtube-thumbnail-downloader/)
- [YouTube Video Downloader](https://yt-tag-extractor.netlify.app/youtube-video-downloader/)

## Run locally
```bash
pip3 install --target .deps -r requirements.txt
./run.sh            # http://localhost:8000
```

## Project layout
| Path | What |
|---|---|
| `app.py` | FastAPI API (`/api/info`, `/api/download`, `/api/thumbnail`), serves `site/` locally |
| `extractor.py` | YouTube Data API v3 (if `YT_API_KEY` set) or yt-dlp for metadata; yt-dlp + ffmpeg for downloads |
| `build_site.py` | Generates every SEO page into `site/` (titles, meta, JSON-LD, sitemap) |
| `site_src/` | Shared CSS/JS/icons copied into `site/` |
| `render.yaml` | Render Blueprint: static site + free Python API |
| `deploy.sh` | Rebuild with production URLs, commit, push (Render auto-deploys) |

## Config (env vars on the API)
`YT_API_KEY` (optional, recommended), `ALLOWED_ORIGINS`, `MAX_DURATION_MIN`, `MAX_HEIGHT`, `RATE_INFO`, `RATE_DOWNLOAD`, `YT_COOKIES` (cookies.txt content, to get past YouTube bot checks), `SERVE_SITE=0` in production.

Only download videos you own or have permission to use. Not affiliated with YouTube or Google.
