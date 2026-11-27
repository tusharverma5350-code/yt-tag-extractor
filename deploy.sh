#!/usr/bin/env bash
# Rebuild the site with production URLs and push; Render redeploys automatically.
set -e
cd "$(dirname "$0")"
SITE_URL="${SITE_URL:-https://yt-tag-extractor-hra2.onrender.com}" \
API_BASE="${API_BASE:-https://yt-tag-extractor-api.onrender.com}" \
GITHUB_URL="${GITHUB_URL:-https://github.com/tusharverma5350-code/yt-tag-extractor}" \
python3 build_site.py
git add -A
git commit -m "${1:-Update site}" || true
git push
