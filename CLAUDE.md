# kurdiani.ge — static portfolio site

Portfolio site for **Kurdiani Architects** (architect Paata Kurdiani),
hosted on GitHub Pages at `kurdiani.ge`. Dark-theme portfolio: a Work grid
of project covers, one page per project, and an About page. Contact details
sit in a site-wide footer; Call / WhatsApp / Messenger buttons in the header.

## Repo layout

```
content/
  projects/<slug>/
    project.md      # frontmatter: title, title_ka, title_ru, year, order, layout
    cover.jpg       # cover image for the Work grid (shown cropped to 202:158)
    images/NN.jpg   # project photos, displayed in filename order
    videos/NN.mp4   # optional videos
  about/
    about.<lang>.html   # About page copy, one file per language
    portrait.jpg        # studio portrait
  footer.<lang>.html    # footer contact block, one file per language
  kutaisi-project/  # self-contained Kutaisi land-sale page (built in the
                    # separate ~/projects/kutaisi-land repo, URLs rewritten),
                    # copied verbatim to docs/kutaisi-project/; its language
                    # folders are /, ge/, ru/ — hence KUTAISI_PATHS in build.py.
                    # The brass "Kutaisi Project" header pill links to it.
assets/             # css / js / fonts, copied verbatim into the build
build.py            # static site generator (Python 3 + Pillow), writes docs/
docs/               # GENERATED output, served by GitHub Pages — do not edit by hand
```

## Languages

Three: **Georgian (`ka`) is the default and is served at `/`**, Russian at
`/ru/`, English at `/en/`. Add one by extending `LANGS` and `STRINGS` in
build.py plus the matching `content/**/*.<lang>.html` files.

Anything untranslated **falls back to English** — a project with no
`title_ka` shows its English title rather than breaking the build. UI
strings live in `STRINGS` in build.py; page copy lives in the per-language
content files.

The Georgian and Russian text was drafted during the build and has not yet
been reviewed by a native speaker — if the user reports awkward wording,
edit the content files rather than assuming the build is wrong.

Fonts: Montserrat and Roboto Slab cover Latin and Cyrillic as separate
subsets loaded per `unicode-range`. Neither covers Georgian, so Noto Sans
Georgian and Noto Serif Georgian sit next in the `:root` stacks and the
browser picks them per glyph. Preserve that ordering.

## How to add a new project (the common request)

1. The user drops photos into `content/projects/<new-slug>/images/`
   (or gives files to copy there). Name them `01.jpg`, `02.jpg`, … in the
   order they should appear; rename/renumber if needed.
2. Create `content/projects/<new-slug>/project.md`:

   ```
   ---
   title: Villa in Example, Tbilisi, Georgia.
   year: 2026
   order: 0
   ---
   Optional description text shown under the title.
   ```

   `order: 0` puts the newest project first in the grid (lower = earlier;
   existing projects are numbered 1–32). Renumber if the user wants a
   specific position.
3. Cover: copy the best image to `content/projects/<new-slug>/cover.jpg`
   (it is displayed center-cropped to 202:158; pre-crop with Pillow if the
   user wants specific framing).
4. `layout:` is only needed when mixing module types, tokens in display
   order: `grid:1-8` (justified grid of images 1..8), `full:9` (image 9
   full-width), `video:1` (videos/01.mp4 centered). Omit for a plain grid
   of all images.
5. Build: `python3 build.py` (incremental; `--clean` for full rebuild).
6. Preview: `cd docs && python3 -m http.server 8765`, check
   `http://localhost:8765/<new-slug>/` and the home grid.
7. Deploy: commit `content/` + `docs/` and push to `main`. GitHub Pages
   serves `docs/` on the main branch — live within a couple of minutes.

## Design fidelity notes (do not "improve" without being asked)

- Measurements are deliberate and exact, matching the site's established
  design: 1600px container, #222 bg, #eee/#888 text,
  4-column flush cover grid (breakpoints 932/540px → 2/1 columns),
  hover overlay black@0.5 with slab-serif title 30px + year 13px,
  project H1 60/70 with 20px bottom padding, justified image grid with
  8px gutters (item padding 4px, container margin -4px, modules padding
  0 16px).
- Project grid items use **percentage base widths + flex-grow ∝ aspect
  ratio** so row grouping stays identical at every viewport width —
  do not switch to px bases.
- Fonts: Montserrat (sans 400/600/700) and Roboto Slab 700 (titles),
  self-hosted woff2 in `assets/fonts/`.
- Copy fixes applied and approved: brand spelled "kurdiani architects"
  (previously "architechts"), phone (+995) 599 50 59 71 (previously
  (+599) 995…). Keep these.
- The Contact page title is offset left-margin 49% with no top padding —
  intentional, keep it.

## Images

`build.py` generates 600/1200/native(≤1920) JPEG derivatives per image and
640/1280 cover crops into `docs/img/<slug>/`. Masters in `content/` are
kept ≤1920px. Derivatives regenerate only when the master is newer — safe
to run the build repeatedly.

## Hosting / DNS

GitHub Pages serves `docs/` from `main` with `docs/CNAME` = kurdiani.ge.

DNS chain: **registrator.ge** (registrar; NS changes there require a
verification code sent to Paata's phone and email) → **Cloudflare** free
zone → **GitHub Pages** apex A records 185.199.108–111.153 plus a `www`
CNAME to `aseveryn.github.io`. All Cloudflare records must stay **DNS only
/ gray cloud** — proxying them blocks GitHub's TLS certificate issuance.

The same GitHub account also serves ksk.ge from a separate repo; Pages
routes by hostname, so the domains do not interact.
