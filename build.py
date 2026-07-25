#!/usr/bin/env python3
"""Static site generator for kurdiani.ge.

Reads content/ and assets/, writes the finished site into docs/ (GitHub Pages).

Content model, per project (content/projects/<slug>/):
  project.md   frontmatter: title, year (optional), order, layout (optional)
               body: description text (optional)
  cover.jpg    cover image for the work grid (cropped or full; displayed 202:158)
  images/NN.*  project images, shown in filename order
  videos/NN.mp4  optional videos

layout tokens in document order, e.g. "video:1 grid:1-10 full:11":
  grid:a-b  justified grid of images a..b
  full:n    image n full-width
  video:n   video n centered
Missing layout -> one grid of all images.

Usage: python3 build.py [--clean]
"""
import argparse
import hashlib
import html
import os
import re
import shutil
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
ASSETS = os.path.join(ROOT, "assets")
DOCS = os.path.join(ROOT, "docs")

SITE_NAME = "kurdiani architects"
SITE_TITLE_PREFIX = "paata kurdiani"
DOMAIN = "https://kurdiani.ge"
WHATSAPP_NUMBER = "995599505971"  # Paata, digits only — wa.me link format
PHONE_NUMBER = "+995599505971"  # Paata — same line as WhatsApp
PHONE_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.28.67-.36 1.02-.25'
    '1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17'
    '0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02'
    'l-2.2 2.2z"/>'
    "</svg>"
)
MESSENGER_URL = "https://m.me/kurdiani.ge"  # facebook.com/kurdiani.ge
MESSENGER_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2C6.36 2 2 6.13 2 11.7c0 2.91 1.19 5.44 3.14 7.17.16.15.26.35.27.57'
    'l.05 1.78c.02.57.6.94 1.12.71l1.98-.87c.17-.07.36-.09.54-.04 1.09.3 2.25.46 3.4.46'
    '5.64 0 10-4.13 10-9.7S17.64 2 12 2zm6 7.46l-2.94 4.66c-.47.74-1.47.93-2.18.4'
    'l-2.34-1.75a.6.6 0 0 0-.72 0l-3.16 2.4c-.42.32-.97-.18-.69-.63l2.94-4.66'
    'c.47-.74 1.47-.93 2.18-.4l2.34 1.75a.6.6 0 0 0 .72 0l3.16-2.4c.42-.32.97.18.69.63z"/>'
    "</svg>"
)
WA_ICON = (
    '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.46 1.32 4.96L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2zm0 18.15h-.01a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.19 8.19 0 0 1-1.26-4.38c0-4.54 3.7-8.23 8.25-8.23 2.2 0 4.27.86 5.83 2.42a8.18 8.18 0 0 1 2.41 5.82c0 4.54-3.7 8.23-8.24 8.23zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.18-.54.06-.25-.12-1.05-.39-1.99-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.42-.56-.43h-.47c-.17 0-.43.06-.66.31-.23.25-.86.85-.86 2.06s.89 2.39 1.01 2.56c.12.16 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.15-1.18-.06-.1-.23-.16-.48-.28z"/>'
    "</svg>"
)
SITE_DESCRIPTION = (
    "Kurdiani Architects — architecture portfolio of Paata Kurdiani. "
    "Residential, hotel, restaurant and interior projects in Tbilisi, Georgia."
)
FAVICON = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAQMAAAAlPW0iAAAABGdBTUEAALGP"
    "C/xhBQAAAAFzUkdCAK7OHOkAAAADUExURUxpcU3H2DoAAAABdFJOUwBA5thmAAAADElEQVQI12NgIA0"
    "AAAAwAAHHqoWOAAAAAElFTkSuQmCC"
)

GRID_BASE = 260  # justified grid: item width = aspect * GRID_BASE px

# Content fingerprints appended to /css and /js URLs. GitHub Pages serves
# assets with max-age=600, so without these a returning visitor keeps the
# stale stylesheet for ten minutes after a deploy. Set in main().
ASSET_TAGS = {"css": "", "js": ""}


def fingerprint(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


# ---------------------------------------------------------------- content

def parse_frontmatter(path):
    """Return (meta dict, body str) from a file with ----delimited frontmatter."""
    text = open(path, encoding="utf-8").read()
    meta, body = {}, text
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body.strip()


def load_projects():
    projects = []
    pdir = os.path.join(CONTENT, "projects")
    for slug in sorted(os.listdir(pdir)):
        d = os.path.join(pdir, slug)
        md = os.path.join(d, "project.md")
        if not os.path.isdir(d) or not os.path.exists(md):
            continue
        meta, body = parse_frontmatter(md)
        imgdir = os.path.join(d, "images")
        images = []
        if os.path.isdir(imgdir):
            images = sorted(
                f for f in os.listdir(imgdir)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            )
        videos = []
        viddir = os.path.join(d, "videos")
        if os.path.isdir(viddir):
            videos = sorted(f for f in os.listdir(viddir) if f.lower().endswith(".mp4"))
        cover = os.path.join(d, "cover.jpg")
        projects.append({
            "slug": slug,
            "dir": d,
            "title": meta.get("title", slug),
            "year": meta.get("year", ""),
            "order": int(meta.get("order", 9999)),
            "layout": meta.get("layout", ""),
            "description": body,
            "images": images,
            "videos": videos,
            "cover": cover if os.path.exists(cover) else None,
        })
    projects.sort(key=lambda p: p["order"])
    return projects


# ---------------------------------------------------------------- images

_processed = 0
_skipped = 0


def derivative(src, dest, max_width, quality=85):
    """Write a resized JPEG derivative of src (skips when up to date)."""
    global _processed, _skipped
    if os.path.exists(dest) and os.path.getmtime(dest) >= os.path.getmtime(src):
        _skipped += 1
        with Image.open(dest) as im:
            return im.size
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            background = Image.new("RGB", im.size, "#222222")
            im = im.convert("RGBA")
            background.paste(im, mask=im.split()[-1])
            im = background
        elif im.mode == "L":
            im = im.convert("RGB")
        if im.width > max_width:
            im = im.resize(
                (max_width, round(im.height * max_width / im.width)), Image.LANCZOS
            )
        im.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
        _processed += 1
        return im.size


def image_size(path):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return im.size


def build_image(slug, imgdir, fname):
    """Generate 600/1200/1920 derivatives; return (stem, srcset, full_url, aspect)."""
    stem = os.path.splitext(fname)[0]
    src = os.path.join(imgdir, fname)
    w, h = image_size(src)
    outdir = os.path.join(DOCS, "img", slug)
    widths = sorted({wd for wd in (600, 1200) if wd < w} | {min(w, 1920)})
    entries = []
    for width in widths:
        eff_w, _ = derivative(src, os.path.join(outdir, f"{stem}-{width}.jpg"), width)
        entries.append((eff_w, f"/img/{slug}/{stem}-{width}.jpg"))
    srcset = ", ".join(f"{u} {ew}w" for ew, u in entries)
    full = entries[-1][1]
    return stem, srcset, full, w / h


# ---------------------------------------------------------------- html

def head(title, canonical, og_image=None, description=SITE_DESCRIPTION):
    og = f'\n  <meta property="og:image" content="{og_image}">' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <meta property="og:title" content="{html.escape(title)}">{og}
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="{FAVICON}">
  <link rel="stylesheet" href="/css/main.css?v={ASSET_TAGS['css']}">
</head>
<body class="fade">"""


def header_nav(active):
    work = ' class="active"' if active == "work" else ""
    about = ' class="active"' if active == "about" else ""
    links = (f'<a href="/"{work}>Work</a>\n      '
             f'<a href="/about/"{about}>About</a>\n      '
             f'<a class="wa-btn call-btn" href="tel:{PHONE_NUMBER}" '
             f'aria-label="Call the studio" title="Call the studio">'
             f'{PHONE_ICON}<span>Call</span></a>\n      '
             f'<a class="wa-btn" href="https://wa.me/{WHATSAPP_NUMBER}" '
             f'target="_blank" rel="noopener" aria-label="Message on WhatsApp" '
             f'title="Message on WhatsApp">{WA_ICON}<span>WhatsApp</span></a>\n      '
             f'<a class="wa-btn msgr-btn" href="{MESSENGER_URL}" '
             f'target="_blank" rel="noopener" aria-label="Message on Facebook Messenger" '
             f'title="Message on Facebook Messenger">{MESSENGER_ICON}<span>Messenger</span></a>')
    return f"""
  <div class="responsive-nav">
    <div class="close-nav"></div>
    <nav>
      {links}
    </nav>
  </div>
  <div class="site-container">
    <header class="site-header">
      <div class="logo-wrap"><div class="logo"><a href="/">{SITE_NAME}</a></div></div>
      <nav>
      {links}
      </nav>
      <div class="hamburger"><i></i><i></i><i></i></div>
    </header>
    <main>"""


BTT_SVG = (
    '<svg viewBox="0 0 26 26"><path d="M13 2 4 11l1.5 1.5L12 6v18h2V6l6.5 6.5L22 11z"/></svg>'
)


def footer(back_to_top=True):
    btt = ""
    if back_to_top:
        btt = f"""
      <section class="back-to-top">
        <a href="#"><span class="arrow">&uarr;</span>Back to Top</a>
      </section>
      <a class="btt-fixed" href="#">{BTT_SVG}</a>"""
    contact = open(os.path.join(CONTENT, "footer.html"), encoding="utf-8").read()
    return f"""{btt}
    </main>
    <footer class="site-footer">
      <div class="footer-inner">
        {contact}
        <div class="footer-col footer-cta">
          <a class="wa-btn call-btn" href="tel:{PHONE_NUMBER}">{PHONE_ICON}<span>Call</span></a>
          <a class="wa-btn" href="https://wa.me/{WHATSAPP_NUMBER}"
             target="_blank" rel="noopener">{WA_ICON}<span>WhatsApp</span></a>
          <a class="wa-btn msgr-btn" href="{MESSENGER_URL}"
             target="_blank" rel="noopener">{MESSENGER_ICON}<span>Messenger</span></a>
        </div>
      </div>
    </footer>
  </div>
  <script src="/js/site.js?v={ASSET_TAGS['js']}"></script>
</body>
</html>"""


def parse_layout(layout, n_images):
    """Return ordered module list [(kind, payload)] from a layout string."""
    if not layout.strip():
        return [("grid", list(range(1, n_images + 1)))] if n_images else []
    modules = []
    for token in layout.split():
        kind, _, arg = token.partition(":")
        if kind == "grid":
            a, _, b = arg.partition("-")
            modules.append(("grid", list(range(int(a), int(b or a) + 1))))
        elif kind == "full":
            modules.append(("full", int(arg)))
        elif kind == "video":
            modules.append(("video", int(arg)))
        else:
            raise ValueError(f"unknown layout token {token!r}")
    return modules


def render_project_page(p):
    slug = p["slug"]
    imgdir = os.path.join(p["dir"], "images")
    built = {}
    for i, fname in enumerate(p["images"], start=1):
        built[i] = build_image(slug, imgdir, fname)

    parts = []
    for kind, payload in parse_layout(p["layout"], len(p["images"])):
        if kind == "grid":
            items = []
            for i in payload:
                stem, srcset, full, ar = built[i]
                # percentage base width keeps row grouping identical at every
                # viewport (matches the original's proportional mobile grid)
                items.append(
                    f'<div class="it" style="width:{ar * GRID_BASE / 15.76:.3f}%;'
                    f'flex-grow:{ar * GRID_BASE:.1f}">'
                    f'<span class="fill" style="padding-bottom:{100 / ar:.4f}%"></span>'
                    f'<img src="{full}" srcset="{srcset}" sizes="100vw" '
                    f'data-lightbox="{full}" alt="{html.escape(p["title"])}" loading="lazy">'
                    f"</div>"
                )
            parts.append('<div class="pgrid">' + "".join(items) + "</div>")
        elif kind == "full":
            stem, srcset, full, ar = built[payload]
            parts.append(
                f'<div class="module-full">'
                f'<img src="{full}" srcset="{srcset}" sizes="100vw" '
                f'data-lightbox="{full}" alt="{html.escape(p["title"])}" loading="lazy">'
                f"</div>"
            )
        elif kind == "video":
            fname = p["videos"][payload - 1]
            vsrc = os.path.join(p["dir"], "videos", fname)
            vdest = os.path.join(DOCS, "video", slug, fname)
            os.makedirs(os.path.dirname(vdest), exist_ok=True)
            if not os.path.exists(vdest) or os.path.getmtime(vdest) < os.path.getmtime(vsrc):
                shutil.copy2(vsrc, vdest)
            parts.append(
                f'<div class="module-video">'
                f'<video src="/video/{slug}/{fname}" controls preload="metadata" playsinline></video>'
                f"</div>"
            )

    desc_html = ""
    if p["description"]:
        desc_html = f'\n        <p class="description">{html.escape(p["description"])}</p>'

    og_image = f"{DOMAIN}/img/{slug}/cover-1280.jpg" if p["cover"] else None
    title = f"{SITE_TITLE_PREFIX} - {p['title']}"
    page = head(title, f"{DOMAIN}/{slug}/", og_image, description=p["title"])
    page += header_nav("work")
    page += f"""
      <div class="page-container">
        <header class="page-header">
          <h1>{html.escape(p["title"])}</h1>{desc_html}
        </header>
        <div class="modules">
          {"".join(parts)}
        </div>
      </div>"""
    page += footer()
    write(os.path.join(DOCS, slug, "index.html"), page)


def render_work_page(projects, path, canonical):
    tiles = []
    for p in projects:
        if not p["cover"]:
            continue
        slug = p["slug"]
        outdir = os.path.join(DOCS, "img", slug)
        w640, _ = derivative(p["cover"], os.path.join(outdir, "cover-640.jpg"), 640)
        w1280, _ = derivative(p["cover"], os.path.join(outdir, "cover-1280.jpg"), 1280)
        year = f'<div class="date">{html.escape(p["year"])}</div>' if p["year"] else ""
        tiles.append(f"""
        <a class="project-cover" href="/{slug}/">
          <div class="cover-box">
            <img src="/img/{slug}/cover-640.jpg"
                 srcset="/img/{slug}/cover-640.jpg {w640}w, /img/{slug}/cover-1280.jpg {w1280}w"
                 sizes="(max-width: 540px) 100vw, (max-width: 932px) 50vw, 400px"
                 alt="{html.escape(p["title"])}" loading="lazy">
          </div>
          <div class="details-wrap">
            <div class="details">
              <div class="title">{html.escape(p["title"])}</div>
              {year}
            </div>
          </div>
        </a>""")
    page = head(SITE_TITLE_PREFIX, canonical)
    page += header_nav("work")
    page += f"""
      <div class="project-covers">{"".join(tiles)}
      </div>"""
    page += footer(back_to_top=False)
    write(path, page)


def render_about():
    """About page: studio portrait alongside the practice/bio text."""
    adir = os.path.join(CONTENT, "about")
    body = open(os.path.join(adir, "about.html"), encoding="utf-8").read()

    portrait = ""
    src = os.path.join(adir, "portrait.jpg")
    if os.path.exists(src):
        outdir = os.path.join(DOCS, "img", "about")
        entries = []
        for width in (600, 1200):
            w, _ = derivative(src, os.path.join(outdir, f"portrait-{width}.jpg"), width)
            entries.append((w, f"/img/about/portrait-{width}.jpg"))
        srcset = ", ".join(f"{u} {w}w" for w, u in entries)
        portrait = f"""
          <figure class="about-portrait">
            <img src="{entries[0][1]}" srcset="{srcset}"
                 sizes="(max-width: 932px) 100vw, 420px"
                 alt="Paata and Keti Kurdiani in the studio in Tbilisi">
          </figure>"""

    page = head(
        f"{SITE_TITLE_PREFIX} - About",
        f"{DOMAIN}/about/",
        og_image=f"{DOMAIN}/img/about/portrait-1200.jpg" if portrait else None,
        description=(
            "Kurdiani Architects, an architecture practice in Tbilisi, Georgia, "
            "led by Paata and Keti Kurdiani."
        ),
    )
    page += header_nav("about")
    page += f"""
      <div class="page-container">
        <header class="page-header about-header">
          <h1>Paata and Keti Kurdiani</h1>
        </header>
        <div class="about">{portrait}
          <div class="about-text">
            {body}
          </div>
        </div>
      </div>"""
    page += footer()
    write(os.path.join(DOCS, "about", "index.html"), page)


def render_contact_redirect():
    """The Contact page is gone; keep /contact/ pointing home so old links
    (the previous site had it indexed for years) don't dead-end."""
    write(os.path.join(DOCS, "contact", "index.html"), f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=/">
  <link rel="canonical" href="{DOMAIN}/">
  <meta name="robots" content="noindex">
  <title>{SITE_TITLE_PREFIX}</title>
</head>
<body><p><a href="/">Continue to kurdiani.ge</a></p></body>
</html>
""")


def render_404():
    page = head(f"{SITE_TITLE_PREFIX} - Page Not Found", f"{DOMAIN}/404.html")
    page += header_nav("")
    page += """
      <div class="notfound">
        <h1>404</h1>
        <p><a href="/">&larr; Back to work</a></p>
      </div>"""
    page += footer(back_to_top=False)
    write(os.path.join(DOCS, "404.html"), page)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="wipe docs/ before building")
    args = ap.parse_args()

    if args.clean and os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(DOCS, exist_ok=True)

    # static assets
    for sub in ("css", "js", "fonts"):
        src = os.path.join(ASSETS, sub)
        dst = os.path.join(DOCS, sub)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    ASSET_TAGS["css"] = fingerprint(os.path.join(DOCS, "css", "main.css"))
    ASSET_TAGS["js"] = fingerprint(os.path.join(DOCS, "js", "site.js"))

    projects = load_projects()
    if not projects:
        sys.exit("no projects found in content/projects/")

    render_work_page(projects, os.path.join(DOCS, "index.html"), f"{DOMAIN}/")
    render_work_page(projects, os.path.join(DOCS, "work", "index.html"), f"{DOMAIN}/")
    for p in projects:
        render_project_page(p)
    render_about()
    render_contact_redirect()
    render_404()

    urls = ([f"{DOMAIN}/", f"{DOMAIN}/about/"]
            + [f"{DOMAIN}/{p['slug']}/" for p in projects])
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    sitemap += "</urlset>\n"
    write(os.path.join(DOCS, "sitemap.xml"), sitemap)
    write(os.path.join(DOCS, "robots.txt"), f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    write(os.path.join(DOCS, "CNAME"), "kurdiani.ge\n")

    total = 0
    for dirpath, _, files in os.walk(DOCS):
        total += sum(os.path.getsize(os.path.join(dirpath, f)) for f in files)
    print(f"built {len(projects)} projects -> docs/ "
          f"({_processed} images processed, {_skipped} up to date, "
          f"site {total // (1 << 20)} MB)")


if __name__ == "__main__":
    main()
