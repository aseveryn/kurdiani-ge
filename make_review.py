#!/usr/bin/env python3
"""Generate REVIEW.md — every piece of site text, for the architects to correct.

The Georgian and Russian were drafted by machine translation and need a
native speaker's eye. This collects all of it into one file that can be
edited in place and handed back; apply the edits with:

    python3 apply_review.py            (or just tell Claude to apply them)

Usage: python3 make_review.py
"""
import io
import os
import re

import build as B

ROOT = os.path.dirname(os.path.abspath(__file__))

# UI strings worth reviewing (skip internal/SEO-only ones marked below)
UI_KEYS = [
    ("work", "Main menu: link to the project grid"),
    ("about", "Main menu: link to the About page"),
    ("call", "Button that dials the studio"),
    ("back_to_top", "Link at the foot of a page"),
    ("prev", "Label above the previous project link"),
    ("next", "Label above the next project link"),
    ("about_title", "Heading at the top of the About page"),
    ("site_title", "Short site name used in browser tabs"),
    ("brand", "Practice name as shown in titles"),
    ("home_title", "Home page title — what Google shows as the headline"),
    ("site_description", "Google search snippet for the site"),
    ("about_description", "Google search snippet for the About page"),
    ("not_found", "Shown on a broken link"),
    ("back_to_work", "Link on the broken-link page"),
]

HEADER = """# Text review — kurdiani.ge

Everything written on the website, in all three languages, in one place.

**The Georgian and Russian were drafted automatically and have not been
checked by a native speaker.** The English is the original.

## How to use this

Edit the `GE:` and `RU:` lines directly — type over what is there. Leave the
`EN:` lines alone unless the English is also wrong. Anything you are happy
with, just leave as it is. Send the file back when you are done and the
corrections will be put straight onto the site.

If a line should say something completely different, write what it should
say — don't worry about matching the English word for word.

---
"""


def esc(s):
    return (s or "").strip()


def block(out, label, note, en, ka, ru):
    out.write(f"\n### {label}\n")
    if note:
        out.write(f"_{note}_\n\n")
    out.write(f"- EN: {esc(en)}\n")
    out.write(f"- GE: {esc(ka)}\n")
    out.write(f"- RU: {esc(ru)}\n")


def multiline_block(out, label, note, texts):
    out.write(f"\n### {label}\n")
    if note:
        out.write(f"_{note}_\n\n")
    for code, name in (("en", "EN"), ("ka", "GE"), ("ru", "RU")):
        out.write(f"\n**{name}**\n\n```\n{texts.get(code, '').strip()}\n```\n")


def strip_html(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</(p|div|section|h2|li)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&rarr;", "->").replace("&nbsp;", " ")
    lines = [l.strip() for l in s.splitlines()]
    return "\n".join(l for l in lines if l)


def main():
    out = io.StringIO()
    out.write(HEADER)

    out.write("\n## 1. Menu, buttons and page titles\n")
    for key, note in UI_KEYS:
        block(out, key.replace("_", " ").title(), note,
              B.STRINGS["en"].get(key), B.STRINGS["ka"].get(key),
              B.STRINGS["ru"].get(key))

    out.write("\n---\n\n## 2. About page\n")
    texts = {}
    for code in ("en", "ka", "ru"):
        path = os.path.join(ROOT, "content", "about", f"about.{code}.html")
        texts[code] = strip_html(io.open(path, encoding="utf-8").read()) \
            if os.path.exists(path) else ""
    multiline_block(out, "About page text", "The whole About page, paragraph by paragraph.", texts)

    out.write("\n---\n\n## 3. Footer\n")
    texts = {}
    for code in ("en", "ka", "ru"):
        path = os.path.join(ROOT, "content", f"footer.{code}.html")
        texts[code] = strip_html(io.open(path, encoding="utf-8").read()) \
            if os.path.exists(path) else ""
    multiline_block(out, "Footer", "Practice name, address and contacts.", texts)

    projects = B.load_projects()

    out.write("\n---\n\n## 4. Project names\n")
    out.write("\n_One block per project, in the order they appear on the site._\n")
    for i, p in enumerate(projects, start=1):
        block(out, f"{i}. {p['slug']}", f"Year shown on the site: {p['year'] or '—'}",
              p["titles"]["en"], p["titles"]["ka"], p["titles"]["ru"])

    with_desc = [p for p in projects if any(p["descs"].values())]
    out.write("\n---\n\n## 5. Project descriptions\n")
    if not with_desc:
        out.write("\n_Not written yet — this section will be filled in once the "
                  "descriptions are drafted._\n")
    else:
        out.write("\n_A short paragraph shown under each project title, and used "
                  "as the Google search snippet. These were written from the "
                  "photographs, so please correct anything factually wrong — "
                  "materials, purpose, location, dates._\n")
        for i, p in enumerate(with_desc, start=1):
            multiline_block(
                out, f"{i}. {p['titles']['en']}", f"`{p['slug']}`",
                {c: p["descs"].get(c, "") for c in ("en", "ka", "ru")},
            )

    out.write("\n---\n\n## 6. Project years\n")
    out.write(
        "\n_The old site showed **2022** against every project, which was the date it "
        "was migrated rather than when anything was built. Seven years below were read "
        "straight off the CV and are already on the site. The rest are blank — the site "
        "shows no date at all rather than a wrong one. Please fill in what you can; a "
        "single year or a range like 2014–2018 both work._\n"
    )
    try:
        import year_mapping
        mapping = year_mapping.M
    except Exception:
        mapping = {}
    by_slug = {p["slug"]: p for p in projects}
    for group, heading in (
        ("CONFIDENT", "Taken from the CV — please confirm"),
        ("AMBIGUOUS", "The CV has more than one possible match — which is it?"),
        ("ABSENT", "Not in the CV at all — year unknown"),
    ):
        rows = [(s, v) for s, v in mapping.items() if v[1] == group]
        if not rows:
            continue
        out.write(f"\n### {heading}\n\n")
        for slug, (year, _conf, why) in sorted(rows):
            name = by_slug[slug]["titles"]["en"] if slug in by_slug else slug
            shown = year or "(blank)"
            out.write(f"- **{name}** — currently `{shown}`\n")
            out.write(f"  - why: {why}\n")
            out.write(f"  - correct year: \n")

    dupes = {}
    for p in projects:
        dupes.setdefault(p["titles"]["en"], []).append(p["slug"])
    repeated = {k: v for k, v in dupes.items() if len(v) > 1}
    if repeated:
        out.write("\n---\n\n## 7. Projects sharing the same name\n")
        out.write(
            "\n_These appear identically in the grid and in search results, so nobody "
            "can tell them apart. A distinguishing name would help — the district, the "
            "building type, or the year._\n\n"
        )
        for title, slugs in repeated.items():
            out.write(f"**{title}** — {len(slugs)} projects:\n\n")
            for s in slugs:
                out.write(f"- `{s}` — better name: \n")
            out.write("\n")

    path = os.path.join(ROOT, "REVIEW.md")
    io.open(path, "w", encoding="utf-8").write(out.getvalue())
    words = len(out.getvalue().split())
    print(f"wrote REVIEW.md — {len(projects)} projects, "
          f"{len(with_desc)} with descriptions, ~{words} words")


if __name__ == "__main__":
    main()
