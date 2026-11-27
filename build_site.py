#!/usr/bin/env python3
"""Generate the static, SEO-optimised site into ./site.

Usage:
  python3 build_site.py                       # local (API on same origin)
  SITE_URL=https://example.onrender.com API_BASE=https://example-api.onrender.com python3 build_site.py
"""
import html
import json
import os
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "site_src"
OUT = ROOT / "site"
SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000").rstrip("/")
API_BASE = os.environ.get("API_BASE", "").rstrip("/")
GITHUB_URL = os.environ.get("GITHUB_URL", "")
GSC_VERIFY = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
BING_VERIFY = os.environ.get("BING_SITE_VERIFICATION", "")
BRAND = "TagExtract"
TODAY = date.today().isoformat()

NAV = [
    ("/", "Tag Extractor"),
    ("/youtube-shorts-tag-extractor/", "Shorts Tags"),
    ("/youtube-hashtag-extractor/", "Hashtags"),
    ("/youtube-description-extractor/", "Description"),
    ("/youtube-thumbnail-downloader/", "Thumbnail"),
    ("/youtube-video-downloader/", "Downloader"),
]

TOOLS = {
    "/": ("YouTube Tag Extractor", "See and copy the hidden tags of any video."),
    "/youtube-shorts-tag-extractor/": ("Shorts Tag Extractor", "Get tags and hashtags from any YouTube Short."),
    "/youtube-hashtag-extractor/": ("Hashtag Extractor", "Pull every #hashtag from a title and description."),
    "/youtube-description-extractor/": ("Description Extractor", "Copy the full description and all its links."),
    "/youtube-thumbnail-downloader/": ("Thumbnail Downloader", "Save thumbnails in HD, SD and smaller sizes."),
    "/youtube-video-downloader/": ("Video Downloader", "Download as MP4 (360p–1080p) or MP3 audio."),
}

LOGO = '<svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#e11d2e"/><path d="M8 11.5a2 2 0 0 1 2-2h6.2l7.3 7.3a1.6 1.6 0 0 1 0 2.3l-4.2 4.2a1.6 1.6 0 0 1-2.3 0L9.7 16A2 2 0 0 1 8 14.2z" fill="#fff"/><circle cx="12" cy="13" r="1.6" fill="#e11d2e"/></svg>'
I = {  # small inline icons
    "tag": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8Z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
    "copy": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
    "bolt": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/></svg>',
    "lock": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "link": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/></svg>',
}
SUN_MOON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>'


def e(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- tool widget
TOOL_WIDGET = """
<section class="tool" id="tool" aria-label="{label}">
  <form class="search" id="form" novalidate>
    <label class="field">
      <span class="ico">{link}</span>
      <span class="skip">YouTube video or Shorts URL</span>
      <input id="url" type="url" inputmode="url" autocomplete="off" spellcheck="false" placeholder="Paste a YouTube video or Shorts link" required>
      <button type="button" class="paste" id="paste">Paste</button>
    </label>
    <button class="btn" id="go" type="submit">{cta}</button>
  </form>
  <div class="hint"><span>Works with youtube.com/watch, youtu.be and /shorts/ links</span><button type="button" data-example="https://www.youtube.com/watch?v=dQw4w9WgXcQ">Try an example</button></div>
  <div class="notice" id="notice" role="alert" aria-live="polite"></div>
  <div class="recent" id="recent" hidden></div>
</section>

<div class="skeleton" id="skeleton" aria-hidden="true">
  <div class="sk" style="height:132px"></div>
  <div class="sk" style="height:220px;margin-top:12px"></div>
</div>

<section class="results" id="results" hidden aria-live="polite">
  <div class="vid">
    <img id="v-thumb" width="200" height="113" alt="">
    <div><h2 id="v-title"></h2><div class="meta" id="v-meta"></div></div>
  </div>
  <div class="panel">
    <div class="tabs" role="tablist" aria-label="Video data">
      <button class="tab" role="tab" data-tab="tags">Tags<span class="n" id="n-tags"></span></button>
      <button class="tab" role="tab" data-tab="hashtags">Hashtags<span class="n" id="n-hash"></span></button>
      <button class="tab" role="tab" data-tab="description">Description</button>
      <button class="tab" role="tab" data-tab="thumbnails">Thumbnails</button>
      <button class="tab" role="tab" data-tab="download">Download</button>
      <button class="tab" role="tab" data-tab="details">Details</button>
    </div>
    <div class="pane" id="pane-tags" role="tabpanel">
      <div class="bar"><span class="stat" id="tagstat"></span>
        <div class="actions"><button class="btn sm" id="copy-tags">Copy all tags</button><button class="btn sm ghost" id="copy-tags-hash">Copy as #hashtags</button><button class="btn sm ghost" id="txt-tags">Save .txt</button><button class="btn sm ghost" id="reset-tags">Reset</button></div></div>
      <div class="chips" id="tags"></div>
      <p class="small">Click a tag to copy it, or × to remove it before copying all of them.</p>
    </div>
    <div class="pane" id="pane-hashtags" role="tabpanel" hidden>
      <div class="bar"><span class="stat">Hashtags found in the title and description</span><div class="actions"><button class="btn sm" id="copy-hash">Copy hashtags</button></div></div>
      <div class="chips" id="hashtags"></div>
    </div>
    <div class="pane" id="pane-description" role="tabpanel" hidden>
      <div class="bar"><span class="stat" id="descstat"></span><div class="actions"><button class="btn sm" id="copy-desc">Copy description</button><button class="btn sm ghost" id="txt-desc">Save .txt</button></div></div>
      <pre class="desc" id="desc"></pre>
      <ul class="links" id="links"></ul>
    </div>
    <div class="pane" id="pane-thumbnails" role="tabpanel" hidden><div class="thumbs" id="thumbs"></div></div>
    <div class="pane" id="pane-download" role="tabpanel" hidden>
      <div class="dl" id="dl"></div>
      <div class="notice err" id="dlerr" role="alert"></div>
      <p class="small" id="dlnote"></p>
    </div>
    <div class="pane" id="pane-details" role="tabpanel" hidden><dl class="details" id="details"></dl></div>
  </div>
</section>
"""

FEATURES = f"""
<section class="features" aria-label="Features">
  <div class="feature"><div class="fi">{I['bolt']}</div><h3>Instant and free</h3><p>No sign-up, no limits for normal use, no browser extension to install.</p></div>
  <div class="feature"><div class="fi">{I['tag']}</div><h3>Everything in one place</h3><p>Tags, hashtags, full description, links, thumbnails, stats and downloads.</p></div>
  <div class="feature"><div class="fi">{I['copy']}</div><h3>Copy in one click</h3><p>Copy all tags comma-separated or as hashtags, remove the ones you don't need.</p></div>
  <div class="feature"><div class="fi">{I['lock']}</div><h3>Private</h3><p>No account, no tracking cookies. We only read public YouTube data.</p></div>
</section>
"""


# ---------------------------------------------------------------- pages
def faq_html(faqs):
    items = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in faqs)
    return f'<section class="faq content" id="faq"><h2>Frequently asked questions</h2>{items}</section>'


PAGES = [
    {
        "path": "/",
        "title": "YouTube Tag Extractor – Copy Video Tags Free",
        "desc": "Free YouTube tag extractor. Paste any video or Shorts link to see and copy its hidden tags, hashtags, full description and thumbnail in one click.",
        "h1": "YouTube Tag Extractor",
        "lead": "See the hidden tags of any YouTube video or Short, then copy them in one click. You also get its hashtags, full description and thumbnails, plus a download.",
        "cta": "Extract tags",
        "focus": "tags",
        "content": """
<h2>What is a YouTube tag extractor?</h2>
<p>Every YouTube video can have <strong>tags</strong>: keywords the creator adds in YouTube Studio to describe what the video is about. Unlike the title and description, tags are <em>hidden</em> from viewers. A <strong>YouTube tag extractor</strong> reads a public video's metadata and shows you those tags, so you can study what keywords successful videos in your niche are targeting.</p>
<p>This tool goes further than most tag finders. One paste gives you the tags, every hashtag, the complete description (with all links listed separately), thumbnails in every size, view and like counts, the publish date, and a video or MP3 download.</p>

<h2>How to extract tags from a YouTube video</h2>
<ol>
<li><strong>Copy the video link.</strong> On desktop, copy the URL from the address bar. On the YouTube app, tap <em>Share → Copy link</em>.</li>
<li><strong>Paste it into the box above.</strong> Normal videos (<code>youtube.com/watch?v=…</code>), short links (<code>youtu.be/…</code>) and Shorts (<code>youtube.com/shorts/…</code>) all work.</li>
<li><strong>Click “Extract tags”.</strong> The tags appear as chips within a second or two.</li>
<li><strong>Copy what you need.</strong> Click a single tag to copy it, remove the ones that don't fit your video with ×, then use <em>Copy all tags</em> to get a comma-separated list ready for YouTube Studio.</li>
</ol>

<h2>Do YouTube tags still matter?</h2>
<p>Honestly, less than they used to. YouTube's own help center says tags “play a minimal role in your video's discovery” and are mostly useful when your main keyword is commonly misspelled. Your <strong>title, thumbnail, description and the first 15 seconds</strong> of the video matter far more.</p>
<p>But extracting tags is still one of the fastest ways to do <strong>keyword research</strong>:</p>
<ul>
<li><strong>Find the exact phrases</strong> top videos in your niche are built around.</li>
<li><strong>Spot misspellings and synonyms</strong> (“tutorial” vs “tutorail”, “PS5” vs “PlayStation 5”) worth adding to your own tags.</li>
<li><strong>Get title and description ideas.</strong> Tags often reveal the long-tail search terms a creator is aiming for.</li>
<li><strong>Audit your own videos</strong> to check what you actually added months ago.</li>
</ul>

<h2>Tips for using extracted tags</h2>
<div class="callout"><strong>Don't copy all tags blindly.</strong> Tags that don't describe your video are treated as misleading metadata under YouTube's spam policies. Keep only the ones that truly match your content.</div>
<ul>
<li><strong>Stay under 500 characters.</strong> That's YouTube's limit for all tags combined. The counter above shows where you are.</li>
<li><strong>Put your main keyword first,</strong> then variations, then broader topic tags.</li>
<li><strong>Use 5–15 focused tags</strong> instead of 40 loosely related ones.</li>
<li><strong>Compare several top videos.</strong> Tags that appear across many of them are the strongest signals for that topic.</li>
<li>Many popular videos have <strong>no tags at all</strong>. If a video shows zero tags, that's real, not an error.</li>
</ul>

<h2>Why use this tag extractor?</h2>
<table>
<tr><th>Feature</th><th>TagExtract</th><th>Typical tag finder</th></tr>
<tr><td>Tags + character count</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Hashtags from title &amp; description</td><td>Yes</td><td>Sometimes</td></tr>
<tr><td>Full description + all links</td><td>Yes</td><td>Rarely</td></tr>
<tr><td>HD thumbnail download</td><td>Yes</td><td>Separate tool</td></tr>
<tr><td>MP4 / MP3 download</td><td>Yes</td><td>No</td></tr>
<tr><td>Sign-up or extension required</td><td>No</td><td>Often</td></tr>
</table>
""",
        "faqs": [
            ("Is this YouTube tag extractor free?", "Yes. It's completely free, with no sign-up and no browser extension. Fair-use rate limits apply only to stop abuse."),
            ("Why does a video show no tags?", "Tags are optional and many creators, including big channels, don't add any. If the tool shows zero tags, the video really has none. The hashtags and description tabs often contain the keywords instead."),
            ("Can I see tags of any YouTube video?", "You can see the tags of any public or unlisted video you have the link to. Private videos can't be read by anyone except the owner."),
            ("Does it work with YouTube Shorts?", "Yes. Paste a youtube.com/shorts/ link and you'll get the Short's tags, hashtags and description. See our <a href=\"/youtube-shorts-tag-extractor/\">Shorts tag extractor</a> for Shorts-specific tips."),
            ("How many tags can a YouTube video have?", "There's no fixed number. The limit is 500 characters for all tags combined. Our counter shows the total so you can trim your list before pasting it into YouTube Studio."),
            ("Is it allowed to use another creator's tags?", "Tags are public metadata, so viewing them is fine. Only reuse tags that accurately describe your own video, because misleading tags go against YouTube's spam policy."),
        ],
    },
    {
        "path": "/youtube-shorts-tag-extractor/",
        "title": "YouTube Shorts Tag Extractor – Get Shorts Tags Free",
        "desc": "Extract tags and hashtags from any YouTube Short. Paste a /shorts/ link to copy its tags, hashtags and description instantly. Free, no sign-up.",
        "h1": "YouTube Shorts Tag Extractor",
        "lead": "Paste any YouTube Shorts link to reveal its hidden tags and hashtags, then copy them for your own Shorts research.",
        "cta": "Get Shorts tags",
        "focus": "tags",
        "content": """
<h2>Find the tags of any YouTube Short</h2>
<p>YouTube Shorts are discovered mostly through the <strong>Shorts feed</strong>, not search. But tags, hashtags and the title still help YouTube understand what a Short is about and who to show it to. This <strong>Shorts tag extractor</strong> shows you exactly which tags and hashtags a Short uses, including the ones hidden in YouTube Studio.</p>

<h2>How to get a Short's link</h2>
<ol>
<li>Open the Short in the YouTube app or on youtube.com.</li>
<li>Tap <em>Share</em> (the arrow icon) and choose <em>Copy link</em>. It looks like <code>youtube.com/shorts/abc123XYZ_0</code>.</li>
<li>Paste it into the box above and press <em>Get Shorts tags</em>.</li>
</ol>

<h2>Tags vs hashtags on Shorts</h2>
<table>
<tr><th></th><th>Tags</th><th>Hashtags</th></tr>
<tr><td>Where they're added</td><td>YouTube Studio → Details → Show more → Tags</td><td>In the title or description, e.g. <code>#cooking</code></td></tr>
<tr><td>Visible to viewers</td><td>No</td><td>Yes, clickable</td></tr>
<tr><td>Limit</td><td>500 characters total</td><td>More than 60 and YouTube ignores all of them</td></tr>
<tr><td>Best use</td><td>Misspellings and keyword variations</td><td>Topic and trend discovery</td></tr>
</table>
<p>Most Shorts creators rely on <strong>hashtags</strong> more than tags, so check both tabs in the results. Our <a href="/youtube-hashtag-extractor/">hashtag extractor</a> lists every hashtag from the title and description.</p>

<h2>How to use Shorts tags for growth</h2>
<ul>
<li><strong>Study Shorts that went viral in your niche.</strong> Extract their hashtags and note which ones repeat.</li>
<li><strong>Keep 3–5 relevant hashtags.</strong> A focused set like <code>#shorts #recipe #airfryer</code> beats 30 generic ones.</li>
<li><strong>Put the keyword in the title.</strong> Shorts titles are short, so the first words matter most.</li>
<li><strong>Add 5–10 tags</strong> covering your topic, common misspellings and the language you speak in the video.</li>
<li><strong>The <code>#shorts</code> hashtag is optional.</strong> YouTube detects vertical videos under 3 minutes as Shorts automatically.</li>
</ul>
<div class="callout">Retention is the biggest factor for Shorts. Tags help YouTube classify your Short, but viewers swiping away in the first second will limit reach no matter which tags you use.</div>
""",
        "faqs": [
            ("Can you add tags to YouTube Shorts?", "Yes. In YouTube Studio on desktop, open the Short → Details → Show more → Tags. The mobile app doesn't always show the tags field, so use a computer."),
            ("Why does my Short show no tags?", "Shorts uploaded from the phone app usually have no tags, because the app doesn't ask for them. Hashtags in the title or description are shown in the Hashtags tab."),
            ("Do I need #shorts in the title?", "No. YouTube classifies vertical or square videos up to 3 minutes as Shorts automatically. #shorts is optional and doesn't hurt."),
            ("Can I download a YouTube Short?", "Yes. Open the Download tab after extracting to save the Short as MP4 or MP3. Only download Shorts you own or have permission to use."),
        ],
    },
    {
        "path": "/youtube-hashtag-extractor/",
        "title": "YouTube Hashtag Extractor – Copy Video Hashtags",
        "desc": "Free YouTube hashtag extractor. Get every #hashtag from any video or Short's title and description and copy them all in one click.",
        "h1": "YouTube Hashtag Extractor",
        "lead": "Pull every #hashtag from a YouTube video or Short's title and description, and copy them all at once.",
        "cta": "Get hashtags",
        "focus": "hashtags",
        "content": """
<h2>What this hashtag extractor finds</h2>
<p>YouTube hashtags are words starting with <code>#</code> in a video's <strong>title or description</strong>. They become clickable links to a page showing other videos with the same hashtag. Up to three of them are also shown above the title. This tool scans both the title and the full description and lists every unique hashtag, ready to copy.</p>
<p>Want the hidden keywords too? The <strong>Tags</strong> tab in the results shows the video's Studio tags, which viewers never see.</p>

<h2>How to use it</h2>
<ol>
<li>Copy the link of a video or Short.</li>
<li>Paste it above and press <em>Get hashtags</em>.</li>
<li>Press <em>Copy hashtags</em> to get them space-separated, like <code>#travel #japan #vlog</code>, or click one to copy it alone.</li>
</ol>

<h2>YouTube hashtag rules you should know</h2>
<ul>
<li><strong>Use more than 60 hashtags and YouTube ignores all of them</strong> for that video. It may even remove the video from search.</li>
<li><strong>The first three hashtags</strong> in your description (if your title has none) appear above the title.</li>
<li><strong>No spaces.</strong> <code>#how to cook</code> only links <code>#how</code>.</li>
<li><strong>Hashtags must be relevant.</strong> Misleading or unrelated hashtags break YouTube's spam policy.</li>
<li><strong>No hate speech, harassment or profanity</strong> in hashtags. YouTube may remove the video.</li>
</ul>

<h2>Finding the best hashtags for your video</h2>
<p>Pick three or four top-performing videos in your niche and extract their hashtags. Hashtags that appear in several of them are proven for that topic. Mix in:</p>
<ul>
<li><strong>One broad hashtag</strong> (<code>#fitness</code>)</li>
<li><strong>One or two specific ones</strong> (<code>#homeworkout</code>, <code>#nogymworkout</code>)</li>
<li><strong>One branded hashtag</strong> for your channel or series</li>
</ul>
<p>Tip: the <em>Copy as #hashtags</em> button in the Tags tab turns a video's hidden tags into hashtag format, which is a quick way to find extra ideas.</p>
""",
        "faqs": [
            ("Where do YouTube hashtags come from?", "Creators type them in the title or description. This tool finds hashtags in both places and removes duplicates."),
            ("How many hashtags should a YouTube video have?", "Three to five relevant hashtags usually work best. With more than 60, YouTube ignores all of them."),
            ("Are hashtags the same as tags?", "No. Hashtags are visible and clickable. Tags are hidden keywords set in YouTube Studio. This tool shows both: hashtags in the Hashtags tab and tags in the Tags tab."),
            ("Does it work for Shorts?", "Yes. Paste a /shorts/ link. Shorts often rely on hashtags more than tags."),
        ],
    },
    {
        "path": "/youtube-description-extractor/",
        "title": "YouTube Description Extractor – Copy Full Description",
        "desc": "Copy the full description of any YouTube video or Short, with every link listed separately. Free YouTube description extractor, no sign-up.",
        "h1": "YouTube Description Extractor",
        "lead": "Get the complete, untruncated description of any YouTube video or Short, plus a clean list of every link in it.",
        "cta": "Get description",
        "focus": "description",
        "content": """
<h2>Copy any YouTube description in full</h2>
<p>On YouTube the description is collapsed behind “…more”, and selecting it on mobile is painful. This <strong>YouTube description extractor</strong> shows the whole description exactly as the creator wrote it, with line breaks, timestamps, links and hashtags intact. You can copy it with one click or save it as a <code>.txt</code> file.</p>
<p>Every URL in the description is also listed separately below it. That makes it easy to find affiliate links, sponsor links, social profiles, playlists and download links the creator shared.</p>

<h2>How to use it</h2>
<ol>
<li>Copy the video or Shorts link.</li>
<li>Paste it above and press <em>Get description</em>.</li>
<li>Press <em>Copy description</em>, <em>Save .txt</em>, or click any link to open it.</li>
</ol>

<h2>What you can learn from top descriptions</h2>
<ul>
<li><strong>Keyword placement.</strong> Successful videos usually repeat their main keyword in the first one or two sentences, which is also what shows in search results.</li>
<li><strong>Chapters.</strong> Timestamps like <code>0:00 Intro</code> create chapters in the progress bar and can show up in Google results.</li>
<li><strong>Structure.</strong> A summary, then links, then chapters, then social links, then hashtags is a common pattern.</li>
<li><strong>Calls to action.</strong> See how creators ask for subscriptions, link to related videos and promote products.</li>
</ul>

<h2>YouTube description limits</h2>
<table>
<tr><th>Item</th><th>Limit</th></tr>
<tr><td>Description length</td><td>5,000 characters</td></tr>
<tr><td>Visible before “…more”</td><td>About 100–150 characters</td></tr>
<tr><td>Hashtags shown above title</td><td>First 3</td></tr>
<tr><td>Chapters</td><td>At least 3 timestamps, first must be 0:00, each at least 10 seconds long</td></tr>
</table>
<p>The character counter in the results shows how much of the 5,000-character limit a video uses.</p>
<div class="callout">Use extracted descriptions for inspiration and structure. Don't republish someone else's description word for word. Write your own for your video.</div>
""",
        "faqs": [
            ("Does it get the full description?", "Yes. You get the complete description up to YouTube's 5,000-character limit, with line breaks and links preserved."),
            ("Can I extract the links from a description?", "Yes. Every URL found in the description is listed under it as a clickable link, with duplicates removed."),
            ("Can I save the description as a file?", "Yes. Press “Save .txt” to download it as a plain text file."),
            ("Does it work on mobile?", "Yes. The tool works in any mobile browser. Copy the link from the YouTube app's Share button and paste it here."),
        ],
    },
    {
        "path": "/youtube-thumbnail-downloader/",
        "title": "YouTube Thumbnail Downloader – HD, Free",
        "desc": "Download any YouTube video or Shorts thumbnail in HD (1280×720), SD, HQ and MQ sizes. Free YouTube thumbnail downloader, no sign-up.",
        "h1": "YouTube Thumbnail Downloader",
        "lead": "Save the thumbnail of any YouTube video or Short in full HD (1280×720) or smaller sizes, in one click.",
        "cta": "Get thumbnail",
        "focus": "thumbnails",
        "content": """
<h2>Download YouTube thumbnails in every size</h2>
<p>Paste a link and this <strong>YouTube thumbnail downloader</strong> shows every available size of the video's thumbnail. Click <em>Download</em> to save it as a JPG.</p>
<table>
<tr><th>Size</th><th>Resolution</th><th>Best for</th></tr>
<tr><td>MAXRES (HD)</td><td>1280×720</td><td>Studying designs, presentations, high-quality previews</td></tr>
<tr><td>SD</td><td>640×480</td><td>Blog posts, documents</td></tr>
<tr><td>HQ</td><td>480×360</td><td>Social posts, quick previews</td></tr>
<tr><td>MQ</td><td>320×180</td><td>Small cards, lists</td></tr>
</table>
<p>Older or low-resolution videos may not have a MAXRES version. In that case the tool only shows the sizes that exist.</p>

<h2>How to download a thumbnail</h2>
<ol>
<li>Copy the YouTube video or Shorts link.</li>
<li>Paste it above and press <em>Get thumbnail</em>.</li>
<li>Choose a size and press <em>Download</em>.</li>
</ol>

<h2>What to learn from top thumbnails</h2>
<ul>
<li><strong>One clear subject.</strong> Usually a face showing emotion, or one object.</li>
<li><strong>Three words or fewer.</strong> Text that adds to the title rather than repeating it.</li>
<li><strong>High contrast.</strong> Thumbnails must read at phone size, roughly 160 pixels wide.</li>
<li><strong>Consistency.</strong> Big channels reuse colours and layouts so viewers recognise them.</li>
</ul>
<div class="callout"><strong>Copyright:</strong> thumbnails belong to their creators. Downloading them for reference, research or commentary is common, but don't re-upload someone else's thumbnail as your own.</div>
<p>Need the video's tags or description too? They're in the other tabs of the same results, or try the <a href="/">YouTube tag extractor</a>.</p>
""",
        "faqs": [
            ("What size are YouTube thumbnails?", "The recommended upload size is 1280×720 (16:9). YouTube also creates smaller versions: 640×480, 480×360 and 320×180."),
            ("Why is there no HD thumbnail?", "Some older or low-resolution videos never got a 1280×720 version. The tool then shows only the sizes that exist."),
            ("Can I download a Shorts thumbnail?", "Yes. Paste the /shorts/ link. Shorts thumbnails are usually a frame picked from the video."),
            ("Is it free?", "Yes. It's free and needs no sign-up. Images download straight to your device as JPG files."),
        ],
    },
    {
        "path": "/youtube-video-downloader/",
        "title": "YouTube Video Downloader – MP4 & MP3, Free",
        "desc": "Download YouTube videos and Shorts as MP4 (360p, 720p, 1080p) or MP3 audio. Free, fast, no sign-up. Plus the video's tags and description.",
        "h1": "YouTube Video Downloader",
        "lead": "Download a YouTube video or Short as MP4 in 360p, 720p or 1080p, or as MP3 audio. Only download videos you own or have permission to use.",
        "cta": "Get video",
        "focus": "download",
        "content": """
<h2>Download YouTube videos as MP4 or MP3</h2>
<p>Paste a link, open the <strong>Download</strong> tab and choose a quality. The file is prepared on our server and saved straight to your device, named after the video title. Videos use H.264 video and AAC audio, so they play on every phone, computer, editor and messaging app.</p>
<table>
<tr><th>Option</th><th>Format</th><th>Use it for</th></tr>
<tr><td>360p</td><td>MP4</td><td>Small files, slow connections</td></tr>
<tr><td>720p</td><td>MP4 (HD)</td><td>Phones and most screens</td></tr>
<tr><td>1080p</td><td>MP4 (Full HD)</td><td>Editing, big screens</td></tr>
<tr><td>MP3</td><td>192 kbps audio</td><td>Podcasts, lectures, your own music</td></tr>
</table>

<h2>How to download</h2>
<ol>
<li>Copy the video or Shorts link.</li>
<li>Paste it above and press <em>Get video</em>.</li>
<li>In the <em>Download</em> tab, choose MP4 quality or MP3.</li>
<li>Wait a moment while the file is prepared. Longer videos take longer.</li>
</ol>

<h2>Use it responsibly</h2>
<div class="callout">Only download videos <strong>you own</strong> (for example, re-downloading your own uploads), content with a <strong>Creative Commons</strong> licence, or videos the copyright owner has given you <strong>permission</strong> to download. YouTube's Terms of Service don't allow downloading other content without permission. You are responsible for how you use downloaded files.</div>
<p>Good reasons creators use this tool:</p>
<ul>
<li>Recovering your own videos when the original file is lost.</li>
<li>Cutting your own long videos into Shorts. Our <a href="/youtube-shorts-tag-extractor/">Shorts tag extractor</a> helps you research tags for them.</li>
<li>Saving your own content for offline presentations.</li>
</ul>

<h2>Limits</h2>
<ul>
<li>Videos up to a fixed maximum length (shown in the tool) to keep the service free for everyone.</li>
<li>Private, members-only and some age-restricted videos can't be downloaded.</li>
<li>A few downloads per user every 10 minutes.</li>
</ul>
""",
        "faqs": [
            ("Is this YouTube downloader free?", "Yes. It's free with no sign-up. Fair-use limits keep it running for everyone."),
            ("Why is the downloaded video playing without sound?", "It shouldn't. We merge video and audio into one MP4. If you use a very old player, try VLC."),
            ("Can I download YouTube Shorts?", "Yes. Paste the /shorts/ link and choose MP4 or MP3."),
            ("Is downloading YouTube videos legal?", "Downloading your own videos or content you have permission for is fine. Downloading other copyrighted videos without permission goes against YouTube's Terms of Service and may break copyright law where you live."),
            ("Why did my download fail?", "The video may be private, too long, age-restricted, or YouTube may be temporarily limiting our server. Wait a few minutes and try again."),
        ],
    },
    {
        "path": "/how-to-find-youtube-video-tags/",
        "title": "How to Find YouTube Video Tags (3 Easy Ways, 2026)",
        "desc": "Learn how to find the tags of any YouTube video in 2026: with a free tag extractor, from the page source, or in YouTube Studio for your own videos.",
        "h1": "How to Find the Tags of Any YouTube Video",
        "lead": "YouTube hides video tags from viewers, but they're still public metadata. Here are three ways to see them, from fastest to most technical.",
        "article": True,
        "content": """
<h2>Method 1: Use a free tag extractor (fastest)</h2>
<p>The quickest way, and it works on phones too:</p>
<ol>
<li>Copy the video's link (on mobile: <em>Share → Copy link</em>).</li>
<li>Open our <a href="/">YouTube Tag Extractor</a> and paste the link.</li>
<li>The tags appear instantly. Click <em>Copy all tags</em> to get them comma-separated.</li>
</ol>
<p>You also get the video's hashtags, full description, thumbnails and stats in the same place.</p>

<h2>Method 2: View the page source (desktop only)</h2>
<ol>
<li>Open the video on youtube.com in Chrome, Edge or Firefox.</li>
<li>Press <code>Ctrl+U</code> (Windows/Linux) or <code>⌥⌘U</code> (Mac) to open the page source.</li>
<li>Press <code>Ctrl+F</code> and search for <code>"keywords"</code>.</li>
<li>The list after <code>"keywords":[</code> contains the video's tags.</li>
</ol>
<p>It works without any tool, but it's hard to read and copy, and it doesn't work on mobile.</p>

<h2>Method 3: YouTube Studio (your own videos)</h2>
<ol>
<li>Go to <a href="https://studio.youtube.com" rel="nofollow noopener" target="_blank">studio.youtube.com</a> → <em>Content</em>.</li>
<li>Click a video → <em>Details</em> → <em>Show more</em>.</li>
<li>The <em>Tags</em> field shows and lets you edit your tags.</li>
</ol>

<h2>Why some videos have no tags</h2>
<p>Tags are optional, and YouTube itself says they play a minimal role in discovery. Many large channels skip them entirely, and videos uploaded from the phone app usually have none. If every method shows nothing, the video simply has no tags.</p>

<h2>What to do with the tags you find</h2>
<ul>
<li>Compare the tags of 3–5 top videos for your topic. Repeated tags are the strongest keywords.</li>
<li>Reuse only tags that truly describe <em>your</em> video.</li>
<li>Keep your total under 500 characters and lead with your main keyword.</li>
<li>Spend more effort on your title, thumbnail and first 15 seconds. Those drive most views.</li>
</ul>
<p>Ready? <a href="/">Extract tags from a video now →</a></p>
""",
        "faqs": [
            ("Can you see tags on YouTube?", "Not on the watch page. Tags are hidden from viewers. Use a tag extractor, the page source, or YouTube Studio for your own videos."),
            ("Can I find tags on my phone?", "Yes. Copy the link from the YouTube app and paste it into a web-based tag extractor like ours. The page-source method doesn't work on mobile."),
            ("Are YouTube tags important in 2026?", "They're a minor factor. They help mostly with misspellings and understanding context. Titles, thumbnails, descriptions and viewer retention matter much more."),
        ],
    },
]

INFO_PAGES = [
    {
        "path": "/about/",
        "title": f"About {BRAND} – Free YouTube Creator Tools",
        "desc": f"{BRAND} is a free set of YouTube tools: tag extractor, hashtag and description extractor, thumbnail downloader and video downloader.",
        "h1": f"About {BRAND}",
        "body": f"""
<p>{BRAND} is a small, free set of tools for YouTube creators and marketers. It started as a single tag extractor and grew into one place to read everything public about a video: tags, hashtags, description, links, thumbnails and stats.</p>
<h2>Our principles</h2>
<ul>
<li><strong>Free and fast.</strong> No sign-up, no browser extension, lightweight pages.</li>
<li><strong>Honest.</strong> We tell you when tags don't matter much, instead of selling you a “tag score”.</li>
<li><strong>Private.</strong> No accounts and no tracking cookies. See our <a href="/privacy/">privacy policy</a>.</li>
</ul>
<h2>How it works</h2>
<p>When you paste a link, our server reads the video's public metadata from YouTube and sends it back to your browser. We don't store the videos you look up.</p>
<p>{BRAND} is not affiliated with, endorsed by or sponsored by YouTube or Google. YouTube is a trademark of Google LLC.</p>
""",
    },
    {
        "path": "/privacy/",
        "title": f"Privacy Policy – {BRAND}",
        "desc": f"How {BRAND} handles your data: no accounts, no tracking cookies, no stored lookups.",
        "h1": "Privacy Policy",
        "body": f"""
<p><em>Last updated: {TODAY}</em></p>
<h2>What we collect</h2>
<ul>
<li><strong>Video links you submit</strong> are sent to our server to fetch public data from YouTube. We don't save them.</li>
<li><strong>IP addresses</strong> are kept in memory for up to 10 minutes to apply rate limits, then discarded. Our hosting provider may keep standard server logs.</li>
<li><strong>Downloaded files</strong> are created temporarily and deleted right after they're sent to you, or within one hour at most.</li>
</ul>
<h2>What stays on your device</h2>
<p>Your theme choice and your last five looked-up videos (“Recent”) are saved in your browser's local storage. They never leave your device. Clear your browser data to remove them.</p>
<h2>Cookies</h2>
<p>We don't use tracking or advertising cookies. If that changes, for example to show ads, we'll update this page and ask for consent where required.</p>
<h2>Third parties</h2>
<p>Video data and thumbnail images come from YouTube (Google). Loading thumbnails connects your browser to <code>i.ytimg.com</code>. See <a href="https://policies.google.com/privacy" rel="nofollow noopener" target="_blank">Google's privacy policy</a>.</p>
<h2>Contact</h2>
<p>Questions? See the <a href="/contact/">contact page</a>.</p>
""",
    },
    {
        "path": "/terms/",
        "title": f"Terms of Use – {BRAND}",
        "desc": f"Terms of use for {BRAND}'s free YouTube tools.",
        "h1": "Terms of Use",
        "body": f"""
<p><em>Last updated: {TODAY}</em></p>
<ol>
<li><strong>The service.</strong> {BRAND} provides free tools to read public YouTube video data and to download videos. It's provided “as is”, without warranties, and may change or stop at any time.</li>
<li><strong>Your responsibility.</strong> You may only download videos you own, that have a licence allowing it (such as Creative Commons), or that the copyright owner has given you permission to download. You are solely responsible for how you use any data or files you get from this site and for following YouTube's Terms of Service and the copyright laws where you live.</li>
<li><strong>No abuse.</strong> Don't use automated scripts, bypass rate limits, or try to overload or attack the service.</li>
<li><strong>Not affiliated with YouTube.</strong> {BRAND} isn't affiliated with or endorsed by YouTube or Google. All video content, thumbnails and trademarks belong to their owners.</li>
<li><strong>Copyright complaints.</strong> We don't host videos. If you believe the site is used to infringe your rights, contact us via the <a href="/contact/">contact page</a>.</li>
<li><strong>Limitation of liability.</strong> To the extent permitted by law, we aren't liable for any damages arising from your use of the service.</li>
</ol>
""",
    },
    {
        "path": "/contact/",
        "title": f"Contact – {BRAND}",
        "desc": f"Contact {BRAND}: report a bug, suggest a tool or send a copyright request.",
        "h1": "Contact",
        "body": f"""
<p>Found a bug, have an idea for a new tool, or need to send a copyright request? We'd like to hear from you.</p>
{f'<p><a class="btn" href="{e(GITHUB_URL)}/issues/new" rel="noopener" target="_blank">Open an issue on GitHub</a></p><p>The project is open source: <a href="{e(GITHUB_URL)}" rel="noopener" target="_blank">{e(GITHUB_URL)}</a>.</p>' if GITHUB_URL else '<p>Contact details will be added here soon.</p>'}
<p>Please include the video link and what you expected to happen when reporting a problem.</p>
""",
    },
]


# ---------------------------------------------------------------- layout
def head(p, jsonld):
    canonical = SITE_URL + p["path"]
    verify = ""
    if GSC_VERIFY:
        verify += f'<meta name="google-site-verification" content="{e(GSC_VERIFY)}">'
    if BING_VERIFY:
        verify += f'<meta name="msvalidate.01" content="{e(BING_VERIFY)}">'
    api_pre = f'<link rel="preconnect" href="{e(API_BASE)}" crossorigin>' if API_BASE else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p['title'])}</title>
<meta name="description" content="{e(p['desc'])}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#e11d2e">
<meta name="api-base" content="{e(API_BASE)}">
{verify}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(p['title'])}">
<meta property="og:description" content="{e(p['desc'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(p['title'])}">
<meta name="twitter:description" content="{e(p['desc'])}">
<meta name="twitter:image" content="{SITE_URL}/og.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="manifest" href="/manifest.json">
<link rel="preconnect" href="https://i.ytimg.com">
{api_pre}
<script>document.documentElement.dataset.theme=localStorage.getItem("theme")||"light"</script>
<link rel="stylesheet" href="/app.css?v={VERSION}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>
</head>"""


def header(path):
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == path else ""}>{e(label)}</a>' for href, label in NAV
    )
    return f"""<body data-focus="{{focus}}">
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
  <a class="logo" href="/" aria-label="{BRAND} home">{LOGO}<span>{BRAND}</span></a>
  <button class="icon-btn menu-btn" id="menu" aria-label="Menu" aria-expanded="false"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
  <nav class="nav" aria-label="Tools">{links}</nav>
  <button class="icon-btn" id="theme" aria-label="Toggle dark mode">{SUN_MOON}</button>
</div></header>"""


def footer():
    tools = "".join(f'<li><a href="{h}">{e(TOOLS[h][0])}</a></li>' for h in TOOLS)
    gh = f'<li><a href="{e(GITHUB_URL)}" rel="noopener">GitHub</a></li>' if GITHUB_URL else ""
    return f"""<footer><div class="wrap">
  <div class="about"><a class="logo" href="/">{LOGO}<span>{BRAND}</span></a><p>Free YouTube tools for creators: extract tags, hashtags and descriptions, download thumbnails and videos. No sign-up.</p></div>
  <div><h4>Tools</h4><ul>{tools}</ul></div>
  <div><h4>Site</h4><ul><li><a href="/how-to-find-youtube-video-tags/">How to find video tags</a></li><li><a href="/about/">About</a></li><li><a href="/privacy/">Privacy</a></li><li><a href="/terms/">Terms</a></li><li><a href="/contact/">Contact</a></li>{gh}</ul></div>
</div><div class="legal">© {date.today().year} {BRAND}. Not affiliated with YouTube or Google.</div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="/app.js?v={VERSION}" defer></script>
</body></html>"""


def crumbs_ld(p):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    if p["path"] != "/":
        items.append({"@type": "ListItem", "position": 2, "name": p["h1"], "item": SITE_URL + p["path"]})
    return {"@type": "BreadcrumbList", "itemListElement": items}


def crumbs_html(p):
    if p["path"] == "/":
        return ""
    return f'<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › {e(p["h1"])}</nav>'


def related(path):
    cards = "".join(
        f'<a href="{h}">{e(n)}<span>{e(d)}</span></a>' for h, (n, d) in TOOLS.items() if h != path
    )
    return f'<section class="content"><h2>More free YouTube tools</h2><div class="related">{cards}</div></section>'


def strip_tags(s):
    import re
    return re.sub(r"<[^>]+>", "", s)


def build_tool_page(p):
    is_article = p.get("article")
    graph = [crumbs_ld(p)]
    if not is_article:
        graph.append({
            "@type": "WebApplication",
            "name": p["h1"],
            "url": SITE_URL + p["path"],
            "description": p["desc"],
            "applicationCategory": "MultimediaApplication",
            "operatingSystem": "Any (web browser)",
            "browserRequirements": "Requires JavaScript",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "publisher": {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/"},
        })
    else:
        graph.append({
            "@type": "Article",
            "headline": p["h1"],
            "description": p["desc"],
            "datePublished": TODAY,
            "dateModified": TODAY,
            "author": {"@type": "Organization", "name": BRAND, "url": SITE_URL + "/about/"},
            "publisher": {"@type": "Organization", "name": BRAND, "logo": {"@type": "ImageObject", "url": SITE_URL + "/icon-512.png"}},
            "image": SITE_URL + "/og.png",
            "mainEntityOfPage": SITE_URL + p["path"],
        })
    if p["path"] == "/":
        graph.append({"@type": "WebSite", "name": BRAND, "url": SITE_URL + "/"})
    if p.get("faqs"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in p["faqs"]],
        })
    jsonld = {"@context": "https://schema.org", "@graph": graph}

    if is_article:
        body = f"""<main id="main" class="wrap"><article class="article">
<div class="hero">{crumbs_html(p)}<h1>{e(p['h1'])}</h1><p class="lead">{e(p['lead'])}</p></div>
<div class="content" style="margin-top:8px">{p['content']}</div>
{faq_html(p['faqs'])}
</article>{related(None)}</main>"""
        focus = ""
    else:
        body = f"""<main id="main" class="wrap">
<section class="hero">{crumbs_html(p)}<h1>{e(p['h1'])}</h1><p class="lead">{e(p['lead'])}</p></section>
{TOOL_WIDGET.format(label=e(p['h1']), cta=e(p['cta']), link=I['link'])}
{FEATURES}
<article class="content">{p['content']}</article>
{faq_html(p['faqs'])}
{related(p['path'])}
</main>"""
        focus = p["focus"]
    return head(p, jsonld) + "\n" + header(p["path"]).replace("{focus}", focus) + "\n" + body + "\n" + footer()


def build_info_page(p):
    jsonld = {"@context": "https://schema.org", "@graph": [crumbs_ld(p), {"@type": "WebPage", "name": p["title"], "url": SITE_URL + p["path"]}]}
    body = f"""<main id="main" class="wrap"><article class="article">
<div class="hero">{crumbs_html(p)}<h1>{e(p['h1'])}</h1></div>
<div class="content" style="margin-top:0">{p['body']}</div></article>{related(None)}</main>"""
    return head(p, jsonld) + "\n" + header(p["path"]).replace("{focus}", "") + "\n" + body + "\n" + footer()


def build_404():
    p = {"path": "/404.html", "title": f"Page not found – {BRAND}", "desc": "This page doesn't exist.", "h1": "Page not found"}
    h = head(p, {"@context": "https://schema.org", "@type": "WebPage", "name": p["title"]}).replace(
        '<meta name="robots" content="index, follow, max-image-preview:large">', '<meta name="robots" content="noindex">')
    body = f"""<main id="main" class="wrap"><section class="hero"><h1>Page not found</h1><p class="lead">The page you're looking for doesn't exist. Try one of our free tools instead.</p><p><a class="btn" href="/">Go to the tag extractor</a></p></section>{related(None)}</main>"""
    return h + "\n" + header("").replace("{focus}", "") + "\n" + body + "\n" + footer()


def write(path, text):
    f = OUT / path.lstrip("/")
    if path.endswith("/"):
        f = f / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def main():
    global VERSION
    VERSION = str(int(max((SRC / n).stat().st_mtime for n in ("app.css", "app.js"))))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for p in PAGES:
        write(p["path"], build_tool_page(p))
    for p in INFO_PAGES:
        write(p["path"], build_info_page(p))
    write("/404.html", build_404())

    for f in SRC.iterdir():
        if f.is_file():
            shutil.copy(f, OUT / f.name)

    priority = {"/": "1.0"}
    urls = "".join(
        f"<url><loc>{SITE_URL}{p['path']}</loc><lastmod>{TODAY}</lastmod><priority>{priority.get(p['path'], '0.8' if p in PAGES else '0.3')}</priority></url>"
        for p in PAGES + INFO_PAGES
    )
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    (OUT / "manifest.json").write_text(json.dumps({
        "name": f"{BRAND} – YouTube Tag Extractor", "short_name": BRAND, "start_url": "/", "display": "standalone",
        "background_color": "#f7f7f9", "theme_color": "#e11d2e",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, indent=1))
    print(f"Built {len(PAGES) + len(INFO_PAGES) + 1} pages into {OUT} (SITE_URL={SITE_URL}, API_BASE={API_BASE or 'same origin'})")


VERSION = "1"
if __name__ == "__main__":
    main()
