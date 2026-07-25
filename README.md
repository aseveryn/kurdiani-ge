# kurdiani.ge

Portfolio of **Kurdiani Architects** — the practice of architect Paata
Kurdiani in Tbilisi, Georgia. Thirty-two projects spanning residential,
hotel, restaurant, public and interior work.

Live at **[kurdiani.ge](https://kurdiani.ge)**.

## How it works

A small Python script turns the `content/` folder into a finished static
site in `docs/`, which GitHub Pages serves. No framework, no JavaScript
dependencies, nothing to pay for — Pillow is the only requirement.

```
content/projects/<slug>/
  project.md      title, year, display order, optional description
  cover.jpg       image used in the work grid
  images/         project photographs, shown in filename order
  videos/         optional video
```

Each project gets its own page with a justified image grid and a lightbox;
the home page is the grid of covers.

## Working on the site

```sh
python3 build.py                          # regenerate docs/ (incremental)
cd docs && python3 -m http.server 8765    # preview at localhost:8765
```

Adding a project means creating one folder under `content/projects/`,
running the build, and pushing — Pages redeploys on its own. Image
derivatives are generated automatically and only rebuilt when a source
image changes.

`CLAUDE.md` documents the content model, the layout options for mixing
grids, full-width images and video, and the design constraints to preserve.
