# kurdiani.ge

Static portfolio site for **Kurdiani Architects** (Paata Kurdiani, Tbilisi,
Georgia). A faithful, dependency-free rebuild of the original Adobe
Portfolio site — hosted for free on GitHub Pages.

- `content/` — all site content (one folder per project + contact page)
- `build.py` — generates the site into `docs/` (Python 3 + Pillow)
- `docs/` — the built site, served by GitHub Pages

```sh
python3 build.py            # build (incremental)
cd docs && python3 -m http.server 8765   # preview at http://localhost:8765
```

See `CLAUDE.md` for the full content model and the add-a-project workflow.
