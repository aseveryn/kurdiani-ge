#!/usr/bin/env python3
"""
Flatten the Kutaisi land page from its self-extracting bundle into plain HTML.

The source page is a single file: an asset manifest and the page template stored
as JSON on two long lines, unpacked at runtime by a JS runtime that rewrites the
DOM. That format is right for a portable artifact and wrong for a hosted page —
nothing renders until ~1.9 MB has arrived and executed, and a crawler without JS
sees the string "Unpacking…".

This does at publish time what the runtime did at page load:

  <helmet>…</helmet>        -> contents moved into <head>
  <x-dc>, <sc-if>           -> unwrapped (showGaming defaults true)
  <sc-raw-table> etc.       -> real <table>/<thead>/<tbody>/<tr>/<td>/<th>
  <image-slot src="uuid">   -> <img src="assets/img/…" loading="lazy">
  base64 fonts and images   -> files under assets/
  all runtime <script>s     -> removed

Result: real HTML that streams, images the browser can lazy-load, and no
JavaScript required to read the page.
"""
import base64
import gzip
import html as htmllib
import json
import os
import re

RAW_TAGS = ("table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
            "ul", "ol", "li", "dl", "dt", "dd")

# alt text per slot id — the bundle carries only editor placeholders, which are
# instructions to the author ("Drop the render here"), not descriptions
ALT = {
    "hero-plot": "Aerial view of the proposed resort masterplan on the site beside Kutaisi International Airport",
    "cadastral-plan": "Satellite view of parcel 29.11.34.255 outlined between the airport road and the railway line",
    "location-map": "Map showing the parcel in relation to the passenger terminal, the airport road and Kopitnari station",
    "terminal-interior": "Interior of the 2021 passenger terminal at Kutaisi International Airport",
    "masterplan-render": "Masterplan render of the proposed two hotels, casino, aquapark, retail and parking",
    "concept-approach": "Street-level render of the scheme seen from the approach road",
    "concept-gateway": "Render of the gateway structure on the site boundary",
    "concept-hotel": "Render of one of the two ring hotels with its interior pool court",
}
NAME = {  # stable, descriptive filenames
    "hero-plot": "hero-masterplan-aerial",
    "cadastral-plan": "parcel-satellite",
    "location-map": "location-map",
    "terminal-interior": "kutaisi-terminal",
    "masterplan-render": "masterplan-aerial",
    "concept-approach": "concept-approach",
    "concept-gateway": "concept-gateway",
    "concept-hotel": "concept-hotel",
}
EXT = {"image/jpeg": "jpg", "image/png": "png", "font/woff2": "woff2"}


def _decode(entry):
    raw = base64.b64decode(entry["data"])
    return gzip.decompress(raw) if entry.get("compressed") else raw


def _drop_tag(text, tag, keep_inner=True):
    """Remove <tag ...> … </tag>, optionally keeping the inner HTML."""
    pat = re.compile(rf"<{tag}\b[^>]*>(.*?)</{tag}>", re.S | re.I)
    prev = None
    while prev != text:                     # nested instances
        prev = text
        text = pat.sub((lambda m: m.group(1)) if keep_inner else "", text)
    # unmatched opener/closer, if any
    text = re.sub(rf"</?{tag}\b[^>]*>", "", text, flags=re.I)
    return text


def flatten(page_html, asset_prefix):
    """page_html -> (flat_html, {relpath: bytes}). asset_prefix is '' or '../'."""
    lines = page_html.split("\n")
    mi = next(i for i, l in enumerate(lines) if l.startswith('{"'))
    ti = next(i for i, l in enumerate(lines) if l.startswith('"<!DOCTYPE'))
    manifest = json.loads(lines[mi])
    doc = json.loads(lines[ti])
    assets = {}

    # ---------- fonts ----------
    for uuid, entry in manifest.items():
        if entry["mime"] != "font/woff2" or uuid not in doc:
            continue
        rel = f"assets/fonts/{uuid[:8]}.woff2"
        assets[rel] = _decode(entry)
        doc = doc.replace(f'"{uuid}"', f'"{asset_prefix}{rel}"')

    # ---------- images: <image-slot> -> <img> ----------
    def slot_to_img(m):
        tag = m.group(0)
        attr = lambda n: (re.search(rf'{n}="([^"]*)"', tag) or [None, ""])[1]
        sid, src, credit = attr("id"), attr("src"), attr("credit")
        entry = manifest.get(src)
        if entry is None:
            return tag
        base = NAME.get(sid, sid or src[:8])
        rel = f"assets/img/{base}.{EXT.get(entry['mime'], 'jpg')}"
        assets[rel] = _decode(entry)
        alt = htmllib.escape(ALT.get(sid, ""), quote=True)
        # the hero is the LCP element: it must not be lazy
        eager = sid == "hero-plot"
        lazy = "" if eager else 'loading="lazy" '
        img = (f'<img src="{asset_prefix}{rel}" alt="{alt}" '
               f'{lazy}decoding="async" '
               f'style="width:100%;height:100%;object-fit:cover;display:block">')
        if credit:
            img = ('<span style="position:relative;display:block;width:100%;height:100%">' + img +
                   f'<span style="position:absolute;left:8px;bottom:6px;font-size:11px;'
                   f'color:rgba(255,255,255,0.85);text-shadow:0 1px 2px rgba(0,0,0,0.55)">'
                   f'{htmllib.escape(credit)}</span></span>')
        return img

    doc = re.sub(r'<image-slot\b[^>]*>\s*</image-slot>', slot_to_img, doc)
    doc = re.sub(r'<image-slot\b[^>]*>', slot_to_img, doc)

    # ---------- runtime scripts ----------
    doc = re.sub(r'<script\b[^>]*>.*?</script>', "", doc, flags=re.S | re.I)

    # ---------- <helmet> contents belong in <head> ----------
    hm = re.search(r"<helmet\b[^>]*>(.*?)</helmet>", doc, re.S | re.I)
    helmet = hm.group(1) if hm else ""
    if hm:
        doc = doc[:hm.start()] + doc[hm.end():]
    if helmet:
        doc = doc.replace("</head>", helmet + "\n</head>", 1)

    # ---------- structural custom elements ----------
    doc = _drop_tag(doc, "x-dc")
    doc = _drop_tag(doc, "sc-if")          # showGaming defaults true -> keep
    for tag in RAW_TAGS:
        doc = re.sub(rf"<sc-raw-{tag}\b", f"<{tag}", doc, flags=re.I)
        doc = re.sub(rf"</sc-raw-{tag}>", f"</{tag}>", doc, flags=re.I)
    doc = re.sub(r"</?sc-raw-[a-z0-9-]+\b[^>]*>", "", doc, flags=re.I)

    leftovers = re.findall(r"<(sc-[a-z-]+|x-dc|helmet|image-slot)\b", doc, re.I)
    assert not leftovers, f"unconverted custom elements: {set(leftovers)}"
    assert "-b3c6-4851-" not in doc, "runtime uuid still referenced"
    return doc, assets


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    out, assets = flatten(open(src, encoding="utf-8").read(), "")
    print(f"{src}: {len(out)/1024:.0f} KB html, {len(assets)} assets, "
          f"{sum(len(v) for v in assets.values())/1024/1024:.2f} MB")
