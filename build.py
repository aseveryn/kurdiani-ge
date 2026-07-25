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
    contact = ' class="active"' if active == "contact" else ""
    links = (f'<a href="/"{work}>Work</a>\n      '
             f'<a href="/about/"{about}>About</a>\n      '
             f'<a href="/contact/"{contact}>Contact</a>')
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
    return f"""{btt}
    </main>
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
            "Kurdiani & Kurdiani, an architecture practice in Tbilisi, Georgia, "
            "led by Paata and Keti Kurdiani."
        ),
    )
    page += header_nav("about")
    page += f"""
      <div class="page-container">
        <header class="page-header about-header">
          <h1>Kurdiani &amp; Kurdiani</h1>
        </header>
        <div class="about">{portrait}
          <div class="about-text">
            {body}
          </div>
        </div>
      </div>"""
    page += footer()
    write(os.path.join(DOCS, "about", "index.html"), page)


def render_contact():
    body = open(os.path.join(CONTENT, "contact.html"), encoding="utf-8").read()
    page = head(f"{SITE_TITLE_PREFIX} - Contact", f"{DOMAIN}/contact/")
    page += header_nav("contact")
    page += f"""
      <div class="page-container">
        <header class="page-header contact-header">
          <h1>Contact</h1>
        </header>
        <div class="contact-body">
          {body}
        </div>
      </div>"""
    page += footer()
    write(os.path.join(DOCS, "contact", "index.html"), page)


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
    render_contact()
    render_404()

    urls = ([f"{DOMAIN}/", f"{DOMAIN}/about/", f"{DOMAIN}/contact/"]
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
