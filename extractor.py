"""Fetch YouTube metadata (YouTube Data API or yt-dlp) and download videos (yt-dlp)."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

BASE = Path(__file__).parent
DOWNLOAD_DIR = BASE / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Config via environment variables (see README).
YT_API_KEY = os.environ.get("YT_API_KEY", "").strip()
MAX_DURATION = int(os.environ.get("MAX_DURATION_MIN", "60")) * 60
MAX_HEIGHT = int(os.environ.get("MAX_HEIGHT", "1080"))

# Optional cookies.txt to get past YouTube's "confirm you're not a bot" on servers.
COOKIE_FILE = None
if os.environ.get("YT_COOKIES"):
    COOKIE_FILE = BASE / ".cookies.txt"
    COOKIE_FILE.write_text(os.environ["YT_COOKIES"])
elif (BASE / "cookies.txt").exists():
    COOKIE_FILE = BASE / "cookies.txt"

ID_RE = re.compile(
    r"^(?:https?://)?(?:www\.|m\.|music\.)?"
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/)|youtu\.be/)"
    r"([\w-]{11})"
)
URL_RE = re.compile(r"https?://[^\s<>\"')]+")
HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
ISO_DUR_RE = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")

THUMB_SIZES = {
    "maxres": ("maxresdefault", "1280×720"),
    "sd": ("sddefault", "640×480"),
    "hq": ("hqdefault", "480×360"),
    "mq": ("mqdefault", "320×180"),
}

YT_CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music", "15": "Pets & Animals",
    "17": "Sports", "19": "Travel & Events", "20": "Gaming", "22": "People & Blogs",
    "23": "Comedy", "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology", "29": "Nonprofits & Activism",
}


def _fmt(h):
    lim = f"[height<={h}]"
    # Prefer H.264 + AAC (plays everywhere), fall back to any codec.
    return f"bestvideo{lim}[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo{lim}+bestaudio/best{lim}"


QUALITIES = {
    "360": _fmt(360),
    "720": _fmt(720),
    "1080": _fmt(1080),
    "best": _fmt(MAX_HEIGHT) if MAX_HEIGHT < 4320 else "bestvideo+bestaudio/best",
    "mp3": "bestaudio/best",
}


class ExtractError(Exception):
    pass


def video_id(url: str) -> str:
    m = ID_RE.match((url or "").strip())
    if not m:
        raise ExtractError("Please paste a valid YouTube video or Shorts link.")
    return m.group(1)


def thumbnails(vid: str) -> list[dict]:
    return [
        {"key": k, "label": label, "url": f"https://i.ytimg.com/vi/{vid}/{name}.jpg"}
        for k, (name, label) in THUMB_SIZES.items()
    ]


def _friendly(err: Exception) -> str:
    msg = str(err)
    low = msg.lower()
    if "private" in low:
        return "This video is private."
    if "sign in to confirm your age" in low or "age-restricted" in low:
        return "This video is age-restricted and needs a logged-in account."
    if "not a bot" in low:
        return "YouTube is temporarily blocking this server. Please try again in a few minutes."
    if "unavailable" in low or "removed" in low:
        return "This video is unavailable or has been removed."
    if "longer than" in low:
        return f"Videos longer than {MAX_DURATION // 60} minutes can't be downloaded here."
    return re.sub(r"^ERROR:\s*(\[\w+\]\s*[\w-]+:\s*)?", "", msg)[:300]


def _ydl_opts(**extra) -> dict:
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "noprogress": True}
    if COOKIE_FILE:
        opts["cookiefile"] = str(COOKIE_FILE)
    opts.update(extra)
    return opts


def _qualities(max_h: int) -> list[str]:
    qs = ["360"] + [q for q in ("720", "1080") if max_h >= int(q) and MAX_HEIGHT >= int(q)]
    if max_h > 1080 and MAX_HEIGHT > 1080:
        qs.append("best")
    return qs + ["mp3"]


def _build(vid, url, *, title, description, tags, channel, channel_url, upload_date, duration,
           views, likes, comments, categories, is_short, max_h) -> dict:
    description = description or ""
    hashtags = list(dict.fromkeys(HASHTAG_RE.findall(description + " " + (title or ""))))
    return {
        "id": vid,
        "url": url,
        "title": title,
        "description": description,
        "tags": tags or [],
        "hashtags": hashtags,
        "links_in_description": list(dict.fromkeys(URL_RE.findall(description))),
        "channel": channel,
        "channel_url": channel_url,
        "upload_date": upload_date,
        "duration": duration,
        "view_count": views,
        "like_count": likes,
        "comment_count": comments,
        "categories": categories or [],
        "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        "thumbnails": thumbnails(vid),
        "is_short": is_short,
        "max_height": max_h,
        "qualities": _qualities(max_h),
        "max_duration_min": MAX_DURATION // 60,
    }


def _int(v):
    return int(v) if v not in (None, "") else None


def _info_api(vid: str, url: str) -> dict:
    q = urllib.parse.urlencode({"part": "snippet,contentDetails,statistics", "id": vid, "key": YT_API_KEY})
    try:
        with urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/videos?{q}", timeout=10) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise ExtractError(f"YouTube API error ({e.code}).") from e
    items = data.get("items") or []
    if not items:
        raise ExtractError("This video is private, removed, or doesn't exist.")
    it = items[0]
    sn, cd, st = it["snippet"], it["contentDetails"], it.get("statistics", {})
    d, h, m, s = (int(x or 0) for x in ISO_DUR_RE.match(cd.get("duration", "")).groups())
    duration = d * 86400 + h * 3600 + m * 60 + s
    return _build(
        vid, url,
        title=sn.get("title"),
        description=sn.get("description"),
        tags=sn.get("tags"),
        channel=sn.get("channelTitle"),
        channel_url=f"https://www.youtube.com/channel/{sn.get('channelId')}",
        upload_date=(sn.get("publishedAt") or "")[:10].replace("-", ""),
        duration=duration,
        views=_int(st.get("viewCount")),
        likes=_int(st.get("likeCount")),
        comments=_int(st.get("commentCount")),
        categories=[YT_CATEGORIES.get(sn.get("categoryId"), "")] if sn.get("categoryId") in YT_CATEGORIES else [],
        is_short="/shorts/" in url or duration <= 60,
        max_h=1080 if cd.get("definition") == "hd" else 360,
    )


def _info_ytdlp(vid: str, url: str) -> dict:
    try:
        with YoutubeDL(_ydl_opts(skip_download=True)) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as e:
        raise ExtractError(_friendly(e)) from e
    heights = [f["height"] for f in info.get("formats", []) if f.get("height") and f.get("vcodec") != "none"]
    return _build(
        vid, f"https://www.youtube.com/watch?v={vid}",
        title=info.get("title"),
        description=info.get("description"),
        tags=info.get("tags"),
        channel=info.get("channel") or info.get("uploader"),
        channel_url=info.get("channel_url"),
        upload_date=info.get("upload_date"),
        duration=info.get("duration"),
        views=info.get("view_count"),
        likes=info.get("like_count"),
        comments=info.get("comment_count"),
        categories=info.get("categories"),
        is_short="/shorts/" in url or ((info.get("height") or 0) > (info.get("width") or 0) > 0),
        max_h=max(heights, default=0),
    )


def get_info(url: str) -> dict:
    vid = video_id(url)
    if YT_API_KEY:
        try:
            return _info_api(vid, f"https://www.youtube.com/watch?v={vid}" if "/shorts/" not in url else url)
        except ExtractError as e:
            if "API error" not in str(e):
                raise
            # API quota/key problem: fall back to yt-dlp.
    return _info_ytdlp(vid, url)


def download(url: str, quality: str) -> tuple[Path, str]:
    """Download the video; returns (file_path, suggested_filename)."""
    vid = video_id(url)
    if quality not in QUALITIES:
        raise ExtractError("Unknown quality option.")

    job = uuid.uuid4().hex
    opts = _ydl_opts(
        format=QUALITIES[quality],
        outtmpl=str(DOWNLOAD_DIR / f"{job}.%(ext)s"),
        ffmpeg_location=FFMPEG,
        match_filter=lambda i, *_: "Video is longer than allowed." if (i.get("duration") or 0) > MAX_DURATION else None,
    )
    if quality == "mp3":
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
    else:
        opts["merge_output_format"] = "mp4"

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
    except DownloadError as e:
        raise ExtractError(_friendly(e)) from e

    files = [f for f in DOWNLOAD_DIR.glob(f"{job}.*") if not f.name.endswith(".part")]
    if not files:
        raise ExtractError(f"Download failed. Videos longer than {MAX_DURATION // 60} minutes aren't supported.")
    path = files[0]
    title = re.sub(r'[\\/:*?"<>|\n\r]+', "_", info.get("title") or job).strip()[:120]
    return path, f"{title}{path.suffix}"


def fetch_thumbnail(vid: str, size: str) -> tuple[bytes, str]:
    """Proxy a thumbnail so the browser can save it (cross-origin images can't use <a download>)."""
    if not re.fullmatch(r"[\w-]{11}", vid) or size not in THUMB_SIZES:
        raise ExtractError("Bad thumbnail request.")
    name = THUMB_SIZES[size][0]
    for candidate in (name, "hqdefault"):  # maxres doesn't exist for every video
        try:
            with urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/{candidate}.jpg", timeout=10) as r:
                return r.read(), f"{vid}-{candidate}.jpg"
        except urllib.error.HTTPError:
            continue
    raise ExtractError("Thumbnail not available.")
