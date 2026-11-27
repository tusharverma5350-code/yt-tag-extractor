"""Generate favicon.svg, app icons and the Open Graph share image into site_src/."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "site_src"
RED, WHITE, INK, MUTED = (225, 29, 46), (255, 255, 255), (20, 22, 27), (93, 100, 114)
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

(OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#e11d2e"/><path d="M8 11.5a2 2 0 0 1 2-2h6.2l7.3 7.3a1.6 1.6 0 0 1 0 2.3l-4.2 4.2a1.6 1.6 0 0 1-2.3 0L9.7 16A2 2 0 0 1 8 14.2z" fill="#fff"/><circle cx="12" cy="13" r="1.6" fill="#e11d2e"/></svg>\n')

def logo(size):
    s = size / 32
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(8 * s), fill=RED)
    tag = [(8, 9.5), (16.2, 9.5), (23.5, 16.8), (23.5, 19.1), (19.3, 23.3), (17, 23.3), (8, 14.2)]
    d.polygon([(x * s, y * s) for x, y in tag], fill=WHITE)
    d.ellipse([(12 - 1.6) * s, (13 - 1.6) * s, (12 + 1.6) * s, (13 + 1.6) * s], fill=RED)
    return im

for n in (192, 512):
    logo(n).save(OUT / f"icon-{n}.png", optimize=True)

og = Image.new("RGB", (1200, 630), (247, 247, 249))
d = ImageDraw.Draw(og)
d.rectangle([0, 0, 1200, 12], fill=RED)
og.paste(logo(96), (80, 80), logo(96))
d.text((196, 104), "TagExtract", font=ImageFont.truetype(B, 44), fill=INK)
d.text((80, 230), "YouTube Tag Extractor", font=ImageFont.truetype(B, 76), fill=INK)
d.text((80, 330), "Copy tags, hashtags, descriptions & thumbnails", font=ImageFont.truetype(R, 36), fill=MUTED)
d.text((80, 378), "of any video or Short. Free, no sign-up.", font=ImageFont.truetype(R, 36), fill=MUTED)
x = 80
for t in ("travel vlog", "how to cook", "#shorts", "gaming setup", "tutorial"):
    f = ImageFont.truetype(R, 30)
    w = d.textlength(t, font=f)
    d.rounded_rectangle([x, 480, x + w + 44, 536], radius=28, fill=(241, 242, 245), outline=(227, 229, 234), width=2)
    d.text((x + 22, 491), t, font=f, fill=INK)
    x += w + 60
og.save(OUT / "og.png", optimize=True)
print("images written")
