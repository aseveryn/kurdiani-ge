# kutaisi-land

Investor page for 36,318 sq m of development land 900 m from Kutaisi International Airport (KUT), Imereti, Georgia — cadastre 29.11.34.255.

**Live at <https://kurdiani.ge/kutaisi-project/>** (English), with `/ge/` and `/ru/` editions.
This repo is the source only — its own GitHub Pages is disabled.

## Contents

- `index.html`, `ge/index.html`, `ru/index.html` — the page in three languages. Each is a self-contained bundle: no build step, no dependencies, no network calls.
- `briefs/` — audience one-pagers linked from the page (hotel, air cargo).
- `og.jpg` — link-preview image.

## Publishing

`~/projects/kurdiani_ge/sync_kutaisi.py` copies this repo into the kurdiani.ge site, rewriting the
`aseveryn.github.io/kutaisi-land` meta URLs (canonical, og:url, hreflang) to
`kurdiani.ge/kutaisi-project` and injecting the Cloudflare analytics beacon. Then `build.py` publishes.

```
cd ~/projects/kurdiani_ge && python3 sync_kutaisi.py && python3 build.py
```

The URLs written into this repo's HTML remain the github.io ones; the rewrite happens on sync, so
nothing here needs changing when editing the page.

## Editing the page

`index.html` is a self-extracting bundle: an asset manifest and the page template are stored as JSON
on two long lines. The English page is edited directly; the Georgian and Russian editions are
generated from it by a translation script. See the private repo for the toolchain and the notes on
the bundle format.

## Related

Title documents, the registry analysis, the data room and internal material live in the private
repo `aseveryn/kutaisi-land-private`.
