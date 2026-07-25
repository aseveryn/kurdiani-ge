#!/usr/bin/env python3
"""Static site generator for kurdiani.ge.

Reads content/ and assets/, writes the finished site into docs/ (GitHub Pages).

Languages: Georgian (default, at /), Russian (/ru/), English (/en/).
Any string with no translation falls back to English, so a half-translated
site still builds and reads sensibly.

Content model, per project (content/projects/<slug>/):
  project.md   frontmatter: title, title_ka, title_ru, year, order, layout
               body: description text (optional, English)
  cover.jpg    cover image for the work grid (displayed 202:158)
  images/NN.*  project images, shown in filename order
  videos/NN.mp4  optional videos

layout tokens in document order, e.g. "video:1 grid:1-10 full:11":
  grid:a-b  justified grid of images a..b
  full:n    image n full-width
  video:n   video n centered
Missing layout -> one grid of all images.

Per-language page copy lives in content/about/about.<lang>.html and
content/footer.<lang>.html.

Usage: python3 build.py [--clean]
"""
import argparse
import hashlib
import html
import json
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
DOMAIN = "https://kurdiani.ge"
WHATSAPP_NUMBER = "995599505971"  # Paata, digits only — wa.me link format
PHONE_NUMBER = "+995599505971"  # Paata — same line as WhatsApp
MESSENGER_URL = "https://m.me/kurdiani.ge"  # facebook.com/kurdiani.ge

# Georgian is the default language and lives at the site root.
LANGS = [
    {"code": "ka", "label": "GE", "prefix": ""},
    {"code": "ru", "label": "RU", "prefix": "/ru"},
    {"code": "en", "label": "EN", "prefix": "/en"},
]
DEFAULT_LANG = "ka"

STRINGS = {
    "en": {
        "studio_alt": "Kurdiani Architects at work in the Tbilisi studio",
        "projects": "Projects",
        "all_projects": "All projects",
        "home": "Home",
        "projects_title": "Projects — Kurdiani Architects, Tbilisi",
        "projects_desc": "The complete portfolio of Kurdiani Architects: houses and villas, hotels, restaurants, offices, interiors and public buildings in Tbilisi and across Georgia.",
        "cat_residential": "Residential",
        "cat_hotel": "Hotel",
        "cat_restaurant": "Restaurant",
        "cat_office": "Office",
        "cat_public": "Public",
        "cat_interior": "Interior",
        "selected_work": "Selected work",
        "services": "Services",
        "service_list": "Architecture|Interior design|Reconstruction and renovation|Construction",
        "skip_to_content": "Skip to content",
        "open_menu": "Open menu",
        "close_menu": "Close menu",
        "menu_primary": "Primary",
        "menu_mobile": "Mobile menu",
        "view_image": "View larger",
        "lightbox": "Image viewer",
        "prev_image": "Previous image",
        "next_image": "Next image",
        "close": "Close",
        "work": "Work",
        "about": "About",
        "call": "Call",
        "back_to_top": "Back to Top",
        "about_title": "Paata and Keti Kurdiani",
        "site_title": "paata kurdiani",
        "not_found": "Page not found",
        "back_to_work": "Back to work",
        "brand": "Kurdiani Architects",
        "home_title": "Kurdiani Architects — Architecture Studio in Tbilisi, Georgia",
        "project_desc": (
            "{title} — an architecture project by Kurdiani Architects, "
            "the Tbilisi practice of Paata and Keti Kurdiani."
        ),
        "locale": "en_US",
        "prev": "Previous project",
        "next": "Next project",
        "site_description": (
            "Kurdiani Architects — architecture portfolio of Paata Kurdiani. "
            "Residential, hotel, restaurant and interior projects in Tbilisi, Georgia."
        ),
        "about_description": (
            "Kurdiani Architects, an architecture practice in Tbilisi, Georgia, "
            "led by Paata and Keti Kurdiani."
        ),
    },
    "ka": {
        "studio_alt": "ქურდიანი არქიტექტორები მუშაობის პროცესში თბილისის სტუდიაში",
        "projects": "პროექტები",
        "all_projects": "ყველა პროექტი",
        "home": "მთავარი",
        "projects_title": "პროექტები — ქურდიანი არქიტექტორები, თბილისი",
        "projects_desc": "ქურდიანი არქიტექტორების სრული პორტფოლიო: სახლები და ვილები, სასტუმროები, რესტორნები, ოფისები, ინტერიერები და საზოგადოებრივი შენობები თბილისსა და საქართველოში.",
        "cat_residential": "საცხოვრებელი",
        "cat_hotel": "სასტუმრო",
        "cat_restaurant": "რესტორანი",
        "cat_office": "ოფისი",
        "cat_public": "საზოგადოებრივი",
        "cat_interior": "ინტერიერი",
        "selected_work": "შერჩეული პროექტები",
        "services": "მომსახურება",
        "service_list": "არქიტექტურა|ინტერიერის დიზაინი|რეკონსტრუქცია და რენოვაცია|მშენებლობა",
        "skip_to_content": "შიგთავსზე გადასვლა",
        "open_menu": "მენიუს გახსნა",
        "close_menu": "მენიუს დახურვა",
        "menu_primary": "მთავარი",
        "menu_mobile": "მობილური მენიუ",
        "view_image": "გადიდება",
        "lightbox": "სურათების დათვალიერება",
        "prev_image": "წინა სურათი",
        "next_image": "შემდეგი სურათი",
        "close": "დახურვა",
        "work": "პროექტები",
        "about": "ჩვენ შესახებ",
        "call": "დარეკვა",
        "back_to_top": "ზემოთ",
        "about_title": "პაატა და ქეთი ქურდიანი",
        "site_title": "პაატა ქურდიანი",
        "not_found": "გვერდი ვერ მოიძებნა",
        "back_to_work": "პროექტებზე დაბრუნება",
        "brand": "ქურდიანი არქიტექტორები",
        "home_title": "ქურდიანი არქიტექტორები — არქიტექტურული სტუდია თბილისში",
        "project_desc": (
            "{title} — არქიტექტურული პროექტი. ქურდიანი არქიტექტორები, "
            "პაატა და ქეთი ქურდიანების სტუდია თბილისში."
        ),
        "locale": "ka_GE",
        "prev": "წინა პროექტი",
        "next": "შემდეგი პროექტი",
        "site_description": (
            "ქურდიანი არქიტექტორები — პაატა ქურდიანის არქიტექტურული პორტფოლიო. "
            "საცხოვრებელი სახლები, სასტუმროები, რესტორნები და ინტერიერები თბილისში."
        ),
        "about_description": (
            "ქურდიანი არქიტექტორები — არქიტექტურული სტუდია თბილისში, "
            "პაატა და ქეთი ქურდიანების ხელმძღვანელობით."
        ),
    },
    "ru": {
        "studio_alt": "Kurdiani Architects за работой в тбилисской студии",
        "projects": "Проекты",
        "all_projects": "Все проекты",
        "home": "Главная",
        "projects_title": "Проекты — Kurdiani Architects, Тбилиси",
        "projects_desc": "Полное портфолио Kurdiani Architects: дома и виллы, гостиницы, рестораны, офисы, интерьеры и общественные здания в Тбилиси и по всей Грузии.",
        "cat_residential": "Жильё",
        "cat_hotel": "Гостиница",
        "cat_restaurant": "Ресторан",
        "cat_office": "Офис",
        "cat_public": "Общественное",
        "cat_interior": "Интерьер",
        "selected_work": "Избранные проекты",
        "services": "Услуги",
        "service_list": "Архитектура|Дизайн интерьеров|Реконструкция и реновация|Строительство",
        "skip_to_content": "Перейти к содержанию",
        "open_menu": "Открыть меню",
        "close_menu": "Закрыть меню",
        "menu_primary": "Основное",
        "menu_mobile": "Мобильное меню",
        "view_image": "Увеличить",
        "lightbox": "Просмотр изображений",
        "prev_image": "Предыдущее изображение",
        "next_image": "Следующее изображение",
        "close": "Закрыть",
        "work": "Проекты",
        "about": "О нас",
        "call": "Позвонить",
        "back_to_top": "Наверх",
        "about_title": "Паата и Кети Курдиани",
        "site_title": "Паата Курдиани",
        "not_found": "Страница не найдена",
        "back_to_work": "К проектам",
        "brand": "Kurdiani Architects",
        "home_title": "Kurdiani Architects — архитектурное бюро в Тбилиси, Грузия",
        "project_desc": (
            "{title} — архитектурный проект бюро Kurdiani Architects, "
            "студии Пааты и Кети Курдиани в Тбилиси."
        ),
        "locale": "ru_RU",
        "prev": "Предыдущий проект",
        "next": "Следующий проект",
        "site_description": (
            "Kurdiani Architects — архитектурное портфолио Пааты Курдиани. "
            "Жилые дома, гостиницы, рестораны и интерьеры в Тбилиси, Грузия."
        ),
        "about_description": (
            "Kurdiani Architects — архитектурная практика в Тбилиси, Грузия, "
            "которую ведут Паата и Кети Курдиани."
        ),
    },
}


def t(lang, key):
    """Translated string, falling back to English."""
    return STRINGS.get(lang, {}).get(key) or STRINGS["en"][key]


def icon(paths):
    return (
        '<svg class="wa-icon" viewBox="0 0 24 24" aria-hidden="true">'
        + paths
        + "</svg>"
    )


PHONE_ICON = icon(
    '<path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.28.67-.36 1.02-.25'
    "1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17"
    "0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02"
    'l-2.2 2.2z"/>'
)
MESSENGER_ICON = icon(
    '<path d="M12 2C6.36 2 2 6.13 2 11.7c0 2.91 1.19 5.44 3.14 7.17.16.15.26.35.27.57'
    "l.05 1.78c.02.57.6.94 1.12.71l1.98-.87c.17-.07.36-.09.54-.04 1.09.3 2.25.46 3.4.46"
    "5.64 0 10-4.13 10-9.7S17.64 2 12 2zm6 7.46l-2.94 4.66c-.47.74-1.47.93-2.18.4"
    "l-2.34-1.75a.6.6 0 0 0-.72 0l-3.16 2.4c-.42.32-.97-.18-.69-.63l2.94-4.66"
    'c.47-.74 1.47-.93 2.18-.4l2.34 1.75a.6.6 0 0 0 .72 0l3.16-2.4c.42-.32.97.18.69.63z"/>'
)
WA_ICON = icon(
    '<path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.46 1.32 4.96L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2zm0 18.15h-.01a8.2 8.2 0 0 1-4.19-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.19 8.19 0 0 1-1.26-4.38c0-4.54 3.7-8.23 8.25-8.23 2.2 0 4.27.86 5.83 2.42a8.18 8.18 0 0 1 2.41 5.82c0 4.54-3.7 8.23-8.24 8.23zm4.52-6.16c-.25-.12-1.47-.72-1.69-.81-.23-.08-.39-.12-.56.13-.16.24-.64.8-.78.97-.14.16-.29.18-.54.06-.25-.12-1.05-.39-1.99-1.23-.74-.66-1.24-1.47-1.38-1.72-.15-.25-.02-.38.11-.5.11-.11.25-.29.37-.43.13-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.56-1.34-.76-1.84-.2-.48-.4-.42-.56-.43h-.47c-.17 0-.43.06-.66.31-.23.25-.86.85-.86 2.06s.89 2.39 1.01 2.56c.12.16 1.75 2.67 4.23 3.74.59.26 1.05.41 1.41.52.59.19 1.13.16 1.56.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.15-1.18-.06-.1-.23-.16-.48-.28z"/>'
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
            "titles": {
                "en": meta.get("title", slug),
                "ka": meta.get("title_ka", ""),
                "ru": meta.get("title_ru", ""),
            },
            "category": meta.get("category", ""),
            "year": meta.get("year", ""),
            "order": int(meta.get("order", 9999)),
            "layout": meta.get("layout", ""),
            # frontmatter is line-based, so a literal \n marks a paragraph break
            "descs": {
                code: (meta.get(key, "") or fallback).replace("\\n", "\n")
                for code, key, fallback in (
                    ("en", "desc", body), ("ka", "desc_ka", ""), ("ru", "desc_ru", "")
                )
            },
            "images": images,
            "videos": videos,
            "cover": cover if os.path.exists(cover) else None,
        })
    projects.sort(key=lambda p: p["order"])
    return projects


def title_of(project, lang):
    return project["titles"].get(lang) or project["titles"]["en"]


def desc_of(project, lang):
    return project["descs"].get(lang) or project["descs"]["en"]


def read_lang_file(directory, stem, lang):
    """content/<dir>/<stem>.<lang>.html, falling back to English."""
    for code in (lang, "en"):
        path = os.path.join(directory, f"{stem}.{code}.html")
        if os.path.exists(path):
            return open(path, encoding="utf-8").read()
    return ""


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
    """Generate derivatives; return (stem, srcset, full_url, aspect)."""
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
    return stem, srcset, entries[-1][1], w / h


# ---------------------------------------------------------------- html

def url_for(lang, path=""):
    """Site-absolute URL for a page in a given language ('' = home)."""
    prefix = next(l["prefix"] for l in LANGS if l["code"] == lang)
    return f"{prefix}/{path}"


def head(lang, title, path, og_image=None, description=None, og_type="website",
         jsonld=None, alternates=True):
    """path is the page path without language prefix ('' = home)."""
    canonical = f"{DOMAIN}{url_for(lang, path)}"
    desc = description or t(lang, "site_description")
    image = og_image or f"{DOMAIN}/img/about/portrait-1200.jpg"

    # only pages that genuinely exist in every language may advertise
    # alternates — the 404 page is served from the root only
    alts = ""
    if alternates:
        alts = "\n".join(
            f'  <link rel="alternate" hreflang="{l["code"]}" '
            f'href="{DOMAIN}{url_for(l["code"], path)}">'
            for l in LANGS
        )
        alts += (f'\n  <link rel="alternate" hreflang="x-default" '
                 f'href="{DOMAIN}{url_for(DEFAULT_LANG, path)}">')

    other_locales = "\n".join(
        f'  <meta property="og:locale:alternate" content="{t(l["code"], "locale")}">'
        for l in LANGS if l["code"] != lang
    )

    # Preload the face that renders this language's body copy, so the first
    # paint isn't held up switching from the fallback font.
    preload_font = ("/fonts/NotoSansGeorgian-georgian-400.woff2" if lang == "ka"
                    else "/fonts/Montserrat-400.woff2")

    structured = ""
    if jsonld:
        structured = ('\n  <script type="application/ld+json">'
                      + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
                      + "</script>")

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <meta name="theme-color" content="#222222">
  <link rel="canonical" href="{canonical}">
{alts}
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="{html.escape(t(lang, "brand"))}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{image}">
  <meta property="og:locale" content="{t(lang, "locale")}">
{other_locales}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(desc)}">
  <meta name="twitter:image" content="{image}">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preload" as="font" type="font/woff2" href="{preload_font}" crossorigin>
  <link rel="stylesheet" href="/css/main.css?v={ASSET_TAGS['css']}">{structured}
</head>
<body class="fade">"""


def organization_ld(lang):
    """The practice itself — reused as publisher/creator across page types."""
    return {
        "@type": "ArchitecturalService",
        "@id": f"{DOMAIN}/#organization",
        "name": t(lang, "brand"),
        "alternateName": "Kurdiani Architects",
        "url": DOMAIN + url_for(lang),
        "image": f"{DOMAIN}/img/about/portrait-1200.jpg",
        "logo": f"{DOMAIN}/apple-touch-icon.png",
        "description": t(lang, "site_description"),
        "telephone": PHONE_NUMBER,
        "email": "kurdiani.paata@gmail.com",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Aleksidze str. N 6, 52 B",
            "addressLocality": "Tbilisi",
            "postalCode": "0193",
            "addressCountry": "GE",
        },
        "areaServed": {"@type": "Country", "name": "Georgia"},
        "founder": {
            "@type": "Person",
            "name": "Paata Kurdiani",
            "jobTitle": "Chief Architect",
        },
        "sameAs": ["https://www.facebook.com/kurdiani.ge"],
        "knowsLanguage": ["ka", "ru", "en"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": t(lang, "services"),
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {"@type": "Service", "name": name,
                                    "serviceType": name,
                                    "provider": {"@id": f"{DOMAIN}/#organization"},
                                    "areaServed": {"@type": "Country", "name": "Georgia"}},
                }
                for name in t(lang, "service_list").split("|")
            ],
        },
    }


def graph(lang, *nodes):
    return {"@context": "https://schema.org", "@graph": list(nodes)}


def breadcrumb_ld(lang, trail):
    """trail: [(name, path), ...] where path is language-less ('' = home)."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": f"{DOMAIN}{url_for(lang, path)}",
            }
            for i, (name, path) in enumerate(trail, start=1)
        ],
    }


def contact_buttons(lang, extra_class=""):
    return (
        f'<a class="wa-btn call-btn {extra_class}" href="tel:{PHONE_NUMBER}" '
        f'aria-label="{t(lang, "call")}" title="{t(lang, "call")}">'
        f'{PHONE_ICON}<span>{t(lang, "call")}</span></a>\n      '
        f'<a class="wa-btn {extra_class}" href="https://wa.me/{WHATSAPP_NUMBER}" '
        f'target="_blank" rel="noopener" aria-label="WhatsApp" title="WhatsApp">'
        f"{WA_ICON}<span>WhatsApp</span></a>\n      "
        f'<a class="wa-btn msgr-btn {extra_class}" href="{MESSENGER_URL}" '
        f'target="_blank" rel="noopener" aria-label="Messenger" title="Messenger">'
        f"{MESSENGER_ICON}<span>Messenger</span></a>"
    )


def lang_switcher(lang, path):
    """GE / RU / EN links pointing at the same page in each language."""
    items = []
    for l in LANGS:
        active = ' class="active"' if l["code"] == lang else ""
        items.append(
            f'<a href="{url_for(l["code"], path)}"{active} '
            f'hreflang="{l["code"]}">{l["label"]}</a>'
        )
    return '<div class="lang-switch">' + "".join(items) + "</div>"


def header_nav(lang, active, path=""):
    projects = ' class="active"' if active in ("projects", "work") else ""
    about = ' class="active"' if active == "about" else ""
    home = ' class="active"' if active == "home" else ""
    links = (
        f'<a href="{url_for(lang)}"{home}>{t(lang, "home")}</a>\n      '
        f'<a href="{url_for(lang, "projects/")}"{projects}>{t(lang, "projects")}</a>\n      '
        f'<a href="{url_for(lang, "about/")}"{about}>{t(lang, "about")}</a>\n      '
        '<span class="nav-cta">' + contact_buttons(lang) + "</span>"
    )
    switcher = lang_switcher(lang, path)
    return f"""
  <a class="skip-link" href="#main">{html.escape(t(lang, "skip_to_content"))}</a>
  <div class="responsive-nav" id="mobile-nav">
    <button class="close-nav" type="button"
            aria-label="{html.escape(t(lang, "close_menu"))}"></button>
    <nav aria-label="{html.escape(t(lang, "menu_mobile"))}">
      {links}
      {switcher}
    </nav>
  </div>
  <div class="site-container">
    <header class="site-header">
      <div class="logo-wrap"><div class="logo">
        <a href="{url_for(lang)}">{SITE_NAME}</a>
      </div></div>
      <nav aria-label="{html.escape(t(lang, "menu_primary"))}">
      {links}
      {switcher}
      </nav>
      <button class="hamburger" type="button" aria-expanded="false"
              aria-controls="mobile-nav"
              aria-label="{html.escape(t(lang, "open_menu"))}"><i></i><i></i><i></i></button>
    </header>
    <main id="main">"""


BTT_SVG = (
    '<svg viewBox="0 0 26 26"><path d="M13 2 4 11l1.5 1.5L12 6v18h2V6l6.5 6.5L22 11z"/></svg>'
)


def footer(lang, back_to_top=True):
    btt = ""
    if back_to_top:
        btt = f"""
      <section class="back-to-top">
        <a href="#"><span class="arrow" aria-hidden="true">&uarr;</span>{t(lang, "back_to_top")}</a>
      </section>
      <a class="btt-fixed" href="#"
         aria-label="{html.escape(t(lang, "back_to_top"))}">{BTT_SVG}</a>"""
    contact = read_lang_file(CONTENT, "footer", lang)
    # labels the lightbox needs at runtime, in the page's language
    i18n = json.dumps(
        {k: t(lang, v) for k, v in (
            ("lightbox", "lightbox"), ("prev", "prev_image"),
            ("next", "next_image"), ("close", "close"),
        )},
        ensure_ascii=False,
    )
    return f"""{btt}
    </main>
    <footer class="site-footer">
      <div class="footer-inner">
        {contact}
        <div class="footer-col footer-cta">
          {contact_buttons(lang)}
        </div>
      </div>
    </footer>
  </div>
  <script>window.__i18n={i18n};</script>
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


def render_project_page(p, lang, prev=None, nxt=None):
    slug = p["slug"]
    title = title_of(p, lang)
    imgdir = os.path.join(p["dir"], "images")
    built = {i: build_image(slug, imgdir, f) for i, f in enumerate(p["images"], start=1)}

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
                    f'data-lightbox="{full}" role="button" tabindex="0" '
                    f'aria-label="{html.escape(title)} — {html.escape(t(lang, "view_image"))} ({i})" '
                    f'alt="{html.escape(title)} ({i})" loading="lazy" decoding="async">'
                    f"</div>"
                )
            parts.append('<div class="pgrid">' + "".join(items) + "</div>")
        elif kind == "full":
            stem, srcset, full, ar = built[payload]
            parts.append(
                f'<div class="module-full">'
                f'<img src="{full}" srcset="{srcset}" sizes="100vw" '
                f'data-lightbox="{full}" role="button" tabindex="0" '
                f'aria-label="{html.escape(title)} — {html.escape(t(lang, "view_image"))}" '
                f'alt="{html.escape(title)} ({payload})" loading="lazy" decoding="async">'
                f"</div>"
            )
        elif kind == "video":
            fname = p["videos"][payload - 1]
            vsrc = os.path.join(p["dir"], "videos", fname)
            vdest = os.path.join(DOCS, "video", slug, fname)
            os.makedirs(os.path.dirname(vdest), exist_ok=True)
            if not os.path.exists(vdest) or os.path.getmtime(vdest) < os.path.getmtime(vsrc):
                shutil.copy2(vsrc, vdest)
            # a poster keeps the player from showing a black rectangle while
            # the file loads, and gives something to look at if it never does
            poster = f' poster="{built[1][2]}"' if built else ""
            parts.append(
                f'<div class="module-video">'
                f'<video src="/video/{slug}/{fname}" controls preload="metadata" '
                f'playsinline{poster} '
                f'aria-label="{html.escape(title)}"></video>'
                f"</div>"
            )

    body_text = desc_of(p, lang)
    desc_html = ""
    if body_text:
        paras = "".join(
            f"<p>{html.escape(para.strip())}</p>"
            for para in body_text.split("\n") if para.strip()
        )
        desc_html = f'\n            <div class="description">{paras}</div>'

    og_image = f"{DOMAIN}/img/{slug}/cover-1280.jpg" if p["cover"] else None
    path = f"{slug}/"
    # a written description makes a far better search snippet than the
    # generic template, so prefer it when there is one
    if body_text:
        flat = " ".join(body_text.split())
        description = flat if len(flat) <= 300 else flat[:297].rsplit(" ", 1)[0] + "…"
    else:
        description = t(lang, "project_desc").format(title=title)

    work_ld = {
        "@type": "CreativeWork",
        "@id": f"{DOMAIN}{url_for(lang, path)}#project",
        "name": title,
        "url": f"{DOMAIN}{url_for(lang, path)}",
        "description": description,
        "inLanguage": lang,
        "creator": {"@id": f"{DOMAIN}/#organization"},
        "image": [f"{DOMAIN}{full}" for _, _, full, _ in built.values()][:8],
    }
    if p["year"]:
        work_ld["dateCreated"] = p["year"]
    jsonld = graph(lang, organization_ld(lang), work_ld,
                   breadcrumb_ld(lang, [(t(lang, "projects"), "projects/"), (title, path)]))

    # prev/next give crawlers a path through every project and readers a way
    # to keep going without returning to the grid
    nav = ""
    if prev or nxt:
        left = (f'<a class="pn-prev" href="{url_for(lang, prev["slug"] + "/")}">'
                f'<span class="pn-label">{t(lang, "prev")}</span>'
                f'<span class="pn-title">{html.escape(title_of(prev, lang))}</span></a>'
                if prev else "<span></span>")
        right = (f'<a class="pn-next" href="{url_for(lang, nxt["slug"] + "/")}">'
                 f'<span class="pn-label">{t(lang, "next")}</span>'
                 f'<span class="pn-title">{html.escape(title_of(nxt, lang))}</span></a>'
                 if nxt else "<span></span>")
        nav = f'<nav class="project-nav">{left}{right}</nav>'

    page = head(lang, f'{title} — {t(lang, "brand")}', path, og_image,
                description=description, og_type="article", jsonld=jsonld)
    page += header_nav(lang, "projects", path)
    page += f"""
      <div class="page-container">
        <article>
          <header class="page-header">
            <h1>{html.escape(title)}</h1>{desc_html}
          </header>
          <div class="modules">
            {"".join(parts)}
          </div>
        </article>
        {nav}
      </div>"""
    page += footer(lang)
    write(os.path.join(DOCS, *filter(None, [lang_dir(lang), slug]), "index.html"), page)


def lang_dir(lang):
    """Output subdirectory for a language ('' for the default language)."""
    return next(l["prefix"] for l in LANGS if l["code"] == lang).lstrip("/")


def studio_shots(lang, dirname):
    """Wide photographs of the practice at work, from content/<dir>/studio/.
    Drop more images in and they join the column in filename order."""
    sdir = os.path.join(CONTENT, dirname, "studio")
    if not os.path.isdir(sdir):
        return ""
    shots = []
    for fname in sorted(f for f in os.listdir(sdir)
                        if f.lower().endswith((".jpg", ".jpeg", ".png"))):
        stem = os.path.splitext(fname)[0]
        outdir = os.path.join(DOCS, "img", "studio")
        entries = []
        for width in (600, 1200, 1800):
            w, _ = derivative(os.path.join(sdir, fname),
                              os.path.join(outdir, f"{stem}-{width}.jpg"), width)
            entries.append((w, f"/img/studio/{stem}-{width}.jpg"))
        srcset = ", ".join(f"{u} {w}w" for w, u in entries)
        shots.append(
            f'<figure class="about-shot">'
            f'<img src="{entries[1][1]}" srcset="{srcset}" '
            f'sizes="(max-width: 932px) 100vw, 440px" '
            f'alt="{html.escape(t(lang, "studio_alt"))}" '
            f'loading="lazy" decoding="async">'
            f"</figure>"
        )
    return "".join(shots)


def home_hero(lang):
    """Portrait, short bio, services and the numbers — the landing block."""
    hdir = os.path.join(CONTENT, "home")
    intro = read_lang_file(hdir, "intro", lang)
    stats = read_lang_file(hdir, "stats", lang)
    services = read_lang_file(os.path.join(CONTENT, "about"), "services", lang)

    portrait = ""
    src = os.path.join(CONTENT, "about", "portrait.jpg")
    if os.path.exists(src):
        outdir = os.path.join(DOCS, "img", "about")
        entries = []
        for width in (600, 1200):
            w, _ = derivative(src, os.path.join(outdir, f"portrait-{width}.jpg"), width)
            entries.append((w, f"/img/about/portrait-{width}.jpg"))
        srcset = ", ".join(f"{u} {w}w" for w, u in entries)
        # this is the largest thing above the fold, so it loads eagerly
        portrait = f"""
          <figure class="hero-portrait">
            <img src="{entries[0][1]}" srcset="{srcset}"
                 sizes="(max-width: 932px) 100vw, 440px"
                 alt="{html.escape(t(lang, 'about_title'))}"
                 loading="eager" fetchpriority="high" decoding="async">
          </figure>"""

    stats_block = f'<div class="stats-band">{stats}</div>' if stats else ""

    return f"""
      <section class="hero">{portrait}
        <div class="hero-text">
          <h1>{html.escape(t(lang, "about_title"))}</h1>
          <div class="hero-intro">{intro}</div>
          <div class="hero-cta">
            {contact_buttons(lang)}
          </div>
        </div>
      </section>
      {stats_block}
      <section class="home-services">{services}</section>
      <h2 class="section-heading">{html.escape(t(lang, "selected_work"))}</h2>"""


def project_tile(p, lang, eager=False, first=False):
    """One thumbnail with its name and category underneath."""
    slug = p["slug"]
    title = title_of(p, lang)
    outdir = os.path.join(DOCS, "img", slug)
    w640, _ = derivative(p["cover"], os.path.join(outdir, "cover-640.jpg"), 640)
    w1280, _ = derivative(p["cover"], os.path.join(outdir, "cover-1280.jpg"), 1280)
    cat = t(lang, "cat_" + p["category"]) if p["category"] else ""
    meta = " · ".join(x for x in (cat, p["year"]) if x)
    loading = ('loading="eager" fetchpriority="high"' if first
               else 'loading="eager"' if eager else 'loading="lazy"')
    return f"""
        <a class="tile" href="{url_for(lang, slug + '/')}">
          <div class="tile-img">
            <img src="/img/{slug}/cover-640.jpg"
                 srcset="/img/{slug}/cover-640.jpg {w640}w, /img/{slug}/cover-1280.jpg {w1280}w"
                 sizes="(max-width: 540px) 100vw, (max-width: 932px) 50vw, 360px"
                 alt="{html.escape(title)}" {loading} decoding="async">
          </div>
          <div class="tile-name">{html.escape(title)}</div>
          <div class="tile-meta">{html.escape(meta)}</div>
        </a>"""


def grid_jsonld(projects, lang, path, name):
    return graph(
        lang,
        organization_ld(lang),
        {
            "@type": "CollectionPage",
            "@id": f"{DOMAIN}{url_for(lang, path)}#page",
            "url": f"{DOMAIN}{url_for(lang, path)}",
            "name": name,
            "inLanguage": lang,
            "isPartOf": {"@id": f"{DOMAIN}/#website"},
            "mainEntity": {
                "@type": "ItemList",
                "numberOfItems": len(projects),
                "itemListElement": [
                    {"@type": "ListItem", "position": i,
                     "url": f"{DOMAIN}{url_for(lang, p['slug'] + '/')}",
                     "name": title_of(p, lang)}
                    for i, p in enumerate(projects, start=1)
                ],
            },
        },
    )


HOME_TILES = 9  # a taste of the work; the rest live on /projects/


def render_home(projects, lang):
    shown = [p for p in projects if p["cover"]][:HOME_TILES]
    tiles = "".join(project_tile(p, lang, eager=(i < 3), first=(i == 0))
                    for i, p in enumerate(shown))
    jsonld = graph(
        lang,
        organization_ld(lang),
        {
            "@type": "WebSite",
            "@id": f"{DOMAIN}/#website",
            "url": DOMAIN + url_for(lang),
            "name": t(lang, "brand"),
            "description": t(lang, "site_description"),
            "inLanguage": lang,
            "publisher": {"@id": f"{DOMAIN}/#organization"},
        },
    )
    page = head(lang, t(lang, "home_title"), "", jsonld=jsonld)
    page += header_nav(lang, "home", "")
    page += home_hero(lang)
    page += f"""
      <div class="tile-grid">{tiles}</div>
      <p class="grid-more">
        <a class="more-link" href="{url_for(lang, 'projects/')}">
          {html.escape(t(lang, "all_projects"))} <span aria-hidden="true">&rarr;</span>
        </a>
      </p>"""
    page += footer(lang, back_to_top=False)
    write(os.path.join(DOCS, *filter(None, [lang_dir(lang)]), "index.html"), page)


def render_projects(projects, lang):
    shown = [p for p in projects if p["cover"]]
    tiles = "".join(project_tile(p, lang, eager=(i < 6), first=(i == 0))
                    for i, p in enumerate(shown))
    path = "projects/"
    page = head(lang, t(lang, "projects_title"), path,
                description=t(lang, "projects_desc"),
                jsonld=grid_jsonld(shown, lang, path, t(lang, "projects_title")))
    page += header_nav(lang, "projects", path)
    page += f"""
      <header class="page-header grid-header">
        <h1>{html.escape(t(lang, "projects"))}</h1>
      </header>
      <div class="tile-grid">{tiles}</div>"""
    page += footer(lang)
    write(os.path.join(DOCS, *filter(None, [lang_dir(lang), "projects"]), "index.html"), page)


def render_about(lang):
    adir = os.path.join(CONTENT, "about")
    body = read_lang_file(adir, "about", lang)
    services = read_lang_file(adir, "services", lang)
    if services:
        body += '\n<section class="services-block">' + services + "</section>"

    shots = []
    src = os.path.join(adir, "portrait.jpg")
    if os.path.exists(src):
        outdir = os.path.join(DOCS, "img", "about")
        entries = []
        for width in (600, 1200):
            w, _ = derivative(src, os.path.join(outdir, f"portrait-{width}.jpg"), width)
            entries.append((w, f"/img/about/portrait-{width}.jpg"))
        srcset = ", ".join(f"{u} {w}w" for w, u in entries)
        shots.append(
            f'<figure class="about-shot">'
            f'<img src="{entries[0][1]}" srcset="{srcset}" '
            f'sizes="(max-width: 932px) 100vw, 440px" '
            f'alt="{html.escape(t(lang, "about_title"))}" decoding="async">'
            f"</figure>"
        )
    shots.append(studio_shots(lang, "about"))
    portrait = f'<div class="about-images">{"".join(shots)}</div>'

    path = "about/"
    jsonld = graph(
        lang,
        organization_ld(lang),
        {
            "@type": "AboutPage",
            "@id": f"{DOMAIN}{url_for(lang, path)}#page",
            "url": f"{DOMAIN}{url_for(lang, path)}",
            "name": t(lang, "about_title"),
            "description": t(lang, "about_description"),
            "inLanguage": lang,
            "about": {"@id": f"{DOMAIN}/#organization"},
        },
        {
            "@type": "Person",
            "@id": f"{DOMAIN}/#paata",
            "name": "Paata Kurdiani",
            "jobTitle": "Chief Architect",
            "worksFor": {"@id": f"{DOMAIN}/#organization"},
            "image": f"{DOMAIN}/img/about/portrait-1200.jpg",
            "alumniOf": {
                "@type": "CollegeOrUniversity",
                "name": "Tbilisi Polytechnic University",
            },
            "knowsLanguage": ["ka", "ru", "en"],
        },
        breadcrumb_ld(lang, [(t(lang, "projects"), "projects/"), (t(lang, "about"), path)]),
    )
    page = head(
        lang,
        f'{t(lang, "about_title")} — {t(lang, "brand")}',
        path,
        og_image=f"{DOMAIN}/img/about/portrait-1200.jpg" if portrait else None,
        description=t(lang, "about_description"),
        og_type="profile",
        jsonld=jsonld,
    )
    page += header_nav(lang, "about", path)
    page += f"""
      <div class="page-container">
        <header class="page-header about-header">
          <h1>{html.escape(t(lang, "about_title"))}</h1>
        </header>
        <div class="about">{portrait}
          <div class="about-text">
            {body}
          </div>
        </div>
      </div>"""
    page += footer(lang)
    write(os.path.join(DOCS, *filter(None, [lang_dir(lang), "about"]), "index.html"), page)


def render_404():
    lang = DEFAULT_LANG
    page = head(lang, f'{t(lang, "site_title")} - {t(lang, "not_found")}', "404.html",
                alternates=False)
    page += header_nav(lang, "", "")
    page += f"""
      <div class="notfound">
        <h1>404</h1>
        <p>{html.escape(t(lang, "not_found"))}</p>
        <p><a href="/">&larr; {html.escape(t(lang, "back_to_work"))}</a></p>
      </div>"""
    page += footer(lang, back_to_top=False)
    write(os.path.join(DOCS, "404.html"), page)


def render_redirect(path, note=""):
    """Keep a retired URL working by bouncing it to the home page."""
    write(os.path.join(DOCS, path, "index.html"), f"""<!DOCTYPE html>
<html lang="{DEFAULT_LANG}">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=/">
  <link rel="canonical" href="{DOMAIN}/">
  <meta name="robots" content="noindex">
  <title>{t(DEFAULT_LANG, "site_title")}</title>
</head>
<body><p><a href="/">kurdiani.ge</a></p></body>
</html>
""")


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

    for sub in ("css", "js", "fonts"):
        src = os.path.join(ASSETS, sub)
        dst = os.path.join(DOCS, sub)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    # favicons and friends live at the site root
    for fname in os.listdir(os.path.join(ASSETS, "static")):
        shutil.copy2(os.path.join(ASSETS, "static", fname), os.path.join(DOCS, fname))
    ASSET_TAGS["css"] = fingerprint(os.path.join(DOCS, "css", "main.css"))
    ASSET_TAGS["js"] = fingerprint(os.path.join(DOCS, "js", "site.js"))

    projects = load_projects()
    if not projects:
        sys.exit("no projects found in content/projects/")

    paths = ["", "projects/", "about/"] + [p["slug"] + "/" for p in projects]
    for lang_def in LANGS:
        lang = lang_def["code"]
        render_home(projects, lang)
        render_projects(projects, lang)
        for i, p in enumerate(projects):
            render_project_page(
                p, lang,
                prev=projects[i - 1] if i > 0 else None,
                nxt=projects[i + 1] if i + 1 < len(projects) else None,
            )
        render_about(lang)

    render_redirect("contact")   # indexed for years on the previous site
    render_redirect("work")      # used to duplicate the home page
    render_404()

    # every URL declares its translations, so Google serves the right one
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
               ' xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in paths:
        for lang_def in LANGS:
            lang = lang_def["code"]
            sitemap.append("  <url>")
            sitemap.append(f"    <loc>{DOMAIN}{url_for(lang, path)}</loc>")
            for alt in LANGS:
                sitemap.append(
                    f'    <xhtml:link rel="alternate" hreflang="{alt["code"]}"'
                    f' href="{DOMAIN}{url_for(alt["code"], path)}"/>'
                )
            sitemap.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default"'
                f' href="{DOMAIN}{url_for(DEFAULT_LANG, path)}"/>'
            )
            sitemap.append(f"    <priority>{'1.0' if path == '' else '0.8'}</priority>")
            sitemap.append("  </url>")
    sitemap.append("</urlset>")
    write(os.path.join(DOCS, "sitemap.xml"), "\n".join(sitemap) + "\n")
    write(os.path.join(DOCS, "robots.txt"),
          f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    write(os.path.join(DOCS, "CNAME"), "kurdiani.ge\n")

    total = 0
    for dirpath, _, files in os.walk(DOCS):
        total += sum(os.path.getsize(os.path.join(dirpath, f)) for f in files)
    print(f"built {len(projects)} projects x {len(LANGS)} languages -> docs/ "
          f"({_processed} images processed, {_skipped} up to date, "
          f"site {total // (1 << 20)} MB)")


if __name__ == "__main__":
    main()
