# kurdiani.ge — static portfolio site

Static rebuild of the former Adobe Portfolio site for **Kurdiani Architects**
(architect Paata Kurdiani). Free hosting on GitHub Pages, custom domain
`kurdiani.ge`. The site is a dark-theme portfolio: a Work grid of project
covers, one page per project, and a Contact page.

## Repo layout

```
content/
  projects/<slug>/
    project.md      # frontmatter: title, year, order, layout (optional); body = description
    cover.jpg       # cover image for the Work grid (shown cropped to 202:158)
    images/NN.jpg   # project photos, displayed in filename order
    videos/NN.mp4   # optional videos
  contact.html      # contact page body fragment
assets/             # css / js / fonts, copied verbatim into the build
build.py            # static site generator (Python 3 + Pillow), writes docs/
scrape.py           # one-time scraper that archived the old Adobe Portfolio site
docs/               # GENERATED output, served by GitHub Pages — do not edit by hand
```

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

- Measurements were taken from the original Adobe Portfolio "geometric"
  theme and are exact: 1600px container, #222 bg, #eee/#888 text,
  4-column flush cover grid (breakpoints 932/540px → 2/1 columns),
  hover overlay black@0.5 with slab-serif title 30px + year 13px,
  project H1 60/70 with 20px bottom padding, justified image grid with
  8px gutters (item padding 4px, container margin -4px, modules padding
  0 16px).
- Project grid items use **percentage base widths + flex-grow ∝ aspect
  ratio** so row grouping stays identical at every viewport width
  (that's how the original behaves — do not switch to px bases).
- Fonts: originals are obfuscated Typekit faces; free stand-ins are
  Montserrat (sans 400/600/700) and Roboto Slab 700 (titles), self-hosted
  woff2 in `assets/fonts/`.
- Intentional fixes vs the original (user-approved): brand spelled
  "kurdiani architects" (site had "architechts"), phone corrected to
  (+995) 599 50 59 71 (site had (+599) 995…).
- The Contact page title is offset left-margin 49% with no top padding —
  a quirk of the original, kept deliberately.

## Images

`build.py` generates 600/1200/native(≤1920) JPEG derivatives per image and
640/1280 cover crops into `docs/img/<slug>/`. Masters in `content/` are
kept ≤1920px (that's what Adobe served). Derivatives regenerate only when
the master is newer — safe to run the build repeatedly.

## Hosting / DNS

GitHub Pages serves `docs/` from `main` with `docs/CNAME` = kurdiani.ge.
DNS cutover (user does at their registrar): apex A records
185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 and
`www` CNAME to `<github-user>.github.io`, then enforce HTTPS in repo
Settings → Pages.
The Adobe Portfolio subscription ($17/month) can be cancelled once the
domain points at GitHub Pages and looks right.
