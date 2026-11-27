"""FastAPI app: YouTube tag / description / thumbnail extractor + downloader API.

Locally it also serves the static site from ./site, so one command runs everything.
On Render the site is deployed separately as a static site and calls this API.
"""
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

import extractor

SITE = Path(__file__).parent / "site"
ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
LIMITS = {  # endpoint -> (max requests, window seconds) per IP
    "info": (int(os.environ.get("RATE_INFO", "30")), 600),
    "download": (int(os.environ.get("RATE_DOWNLOAD", "6")), 600),
}
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def rate_limit(request: Request, kind: str):
    ip = (request.headers.get("x-forwarded-for") or request.client.host or "?").split(",")[0].strip()
    limit, window = LIMITS[kind]
    q = _hits[(kind, ip)]
    now = time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many requests. Please wait a few minutes and try again.")
    q.append(now)


def cleanup_old(max_age=3600):
    now = time.time()
    for f in extractor.DOWNLOAD_DIR.iterdir():
        if f.is_file() and now - f.stat().st_mtime > max_age:
            f.unlink(missing_ok=True)


@asynccontextmanager
async def lifespan(_app):
    cleanup_old()
    yield


app = FastAPI(title="YT Tag Extractor API", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)


class InfoReq(BaseModel):
    url: str


class DownloadReq(BaseModel):
    url: str
    quality: str = "720"


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/info")
async def info(req: InfoReq, request: Request):
    rate_limit(request, "info")
    try:
        return await run_in_threadpool(extractor.get_info, req.url)
    except extractor.ExtractError as e:
        raise HTTPException(400, str(e))


@app.post("/api/download")
async def download(req: DownloadReq, request: Request):
    rate_limit(request, "download")
    cleanup_old()
    try:
        path, name = await run_in_threadpool(extractor.download, req.url, req.quality)
    except extractor.ExtractError as e:
        raise HTTPException(400, str(e))
    return FileResponse(
        path,
        filename=name,
        media_type="application/octet-stream",
        background=BackgroundTask(lambda: path.unlink(missing_ok=True)),
    )


@app.get("/api/thumbnail/{vid}/{size}")
async def thumbnail(vid: str, size: str):
    try:
        data, name = await run_in_threadpool(extractor.fetch_thumbnail, vid, size)
    except extractor.ExtractError as e:
        raise HTTPException(404, str(e))
    return Response(data, media_type="image/jpeg",
                    headers={"Content-Disposition": f'attachment; filename="{name}"',
                             "Cache-Control": "public, max-age=86400"})


@app.middleware("http")
async def noindex_api(request: Request, call_next):
    resp = await call_next(request)
    if request.url.path.startswith("/api/"):
        resp.headers["X-Robots-Tag"] = "noindex"
    return resp


# Local mode: serve the generated static site (pretty URLs like /youtube-hashtag-extractor/).
# Disabled in production (SERVE_SITE=0) so the API host doesn't duplicate the real site.
if SITE.exists() and os.environ.get("SERVE_SITE", "1") != "0":
    app.mount("/", StaticFiles(directory=SITE, html=True), name="site")
