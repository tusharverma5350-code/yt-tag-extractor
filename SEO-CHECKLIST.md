# SEO checklist: getting TagExtract onto Google

Ranking #1 for "youtube tag extractor" can't be guaranteed. Page 1 is held by vidIQ, Keywords Everywhere, TunePocket, Geekflare and others with years of backlinks. The plan is to win the smaller, specific searches first, then climb.

## Already done in the code
- [x] One page per keyword, each with its own title (≤60 chars), meta description, H1 and 500–900 words of useful content
- [x] FAQ, WebApplication, Article and Breadcrumb structured data (JSON-LD)
- [x] Canonical URLs, Open Graph/Twitter image, sitemap.xml, robots.txt, manifest, icons
- [x] Fast static pages (~20 KB HTML, no frameworks, no render-blocking fonts), mobile-first, dark mode
- [x] Internal links between every tool, plus About, Privacy, Terms and Contact pages (trust signals)
- [x] API marked `noindex`, so there's no duplicate copy of the site

## Week 1 (do once)
1. **Google Search Console**: https://search.google.com/search-console → Add property → URL prefix → your site URL → choose "HTML tag" → copy the `content="..."` value → run `GOOGLE_SITE_VERIFICATION=xxxx ./deploy.sh` → click Verify.
   Then go to Sitemaps, submit `sitemap.xml`, and use URL Inspection → Request indexing for each tool page.
2. **Bing Webmaster Tools**: https://www.bing.com/webmasters → import from Search Console (one click). Bing also powers DuckDuckGo, Yahoo and ChatGPT search.
3. **Free YouTube API key** (makes the tool reliable): https://console.cloud.google.com → new project → enable "YouTube Data API v3" → Credentials → API key → restrict it to the YouTube Data API → add it as `YT_API_KEY` on the Render API service.

## Weeks 2–8 (backlinks)
- [ ] Post the site on **Product Hunt**, **AlternativeTo** (as an alternative to vidIQ / TunePocket), **SaaSHub**, **Futurepedia**-style tool lists, and **Indie Hackers**
- [ ] Keep the GitHub repo public with a good README (already links to the site)
- [ ] Answer real questions on **Reddit** (r/NewTubers, r/youtubers, r/PartneredYoutube) and **Quora** ("how to see tags of a YouTube video"). Link only when it really helps. Spam gets you banned.
- [ ] Ask YouTube-tips bloggers to add the tool to their "best free tag extractors" lists

## Ongoing
- [ ] Add one guide a week targeting a question (e.g. "how many tags should a YouTube video have", "youtube tags vs hashtags", "best tags for gaming videos"). Add it to `PAGES` in `build_site.py`, then run `./deploy.sh`.
- [ ] Check Search Console monthly. Improve pages ranking in positions 8–20 by adding content that answers what searchers want.
- [ ] Consider a real domain later (~$10/yr). Point it at Render under Settings → Custom domain, then rebuild with `SITE_URL=https://yourdomain.com`.

## Realistic timeline
- Indexed: a few days to 2 weeks after submitting the sitemap
- Long-tail searches ("youtube shorts tag extractor", "youtube description extractor"): 1–3 months
- Top 10 for "youtube tag extractor": needs dozens of quality backlinks, 6+ months, not guaranteed

## Known risks (you accepted these)
- The public video downloader can draw DMCA complaints (pages removed from Google) and makes AdSense approval unlikely.
- YouTube often blocks downloads from cloud servers like Render. Metadata keeps working with `YT_API_KEY`, but downloads may fail until you add `YT_COOKIES`.
- On Render's free plan the API sleeps after 15 minutes idle (first request takes ~1 min). The pages themselves are always fast.
