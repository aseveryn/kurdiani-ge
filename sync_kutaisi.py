#!/usr/bin/env python3
"""Sync the Kutaisi land page from ~/projects/kutaisi-land.

The source repo no longer serves anything itself (its GitHub Pages is
disabled); kurdiani.ge/kutaisi-project/ is the only live copy. The source
pages carry aseveryn.github.io meta URLs and no analytics, so every HTML
file gets its URLs rewritten and the Cloudflare beacon injected on the way
in. Everything else (og.jpg, briefs/, …) is copied verbatim.

Run `python3 build.py` afterwards to publish the copy into docs/.
"""
import os
import shutil

from build import CF_BEACON_TOKEN  # single source of truth for the token

SRC = os.path.expanduser("~/projects/kutaisi-land")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "content", "kutaisi-project")
SKIP = {".git", ".gitignore", ".DS_Store"}

BEACON = ("<!-- Cloudflare Web Analytics --><script type='module' "
          "src='https://static.cloudflareinsights.com/beacon.min.js' "
          f"data-cf-beacon='{{\"token\": \"{CF_BEACON_TOKEN}\"}}'>"
          "</script><!-- End Cloudflare Web Analytics -->")

if os.path.isdir(DST):
    shutil.rmtree(DST)

for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for name in files:
        if name in SKIP:
            continue
        src = os.path.join(root, name)
        dst = os.path.join(DST, os.path.relpath(src, SRC))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if name.endswith(".html"):
            text = open(src, encoding="utf-8").read()
            text = text.replace("aseveryn.github.io/kutaisi-land",
                                "kurdiani.ge/kutaisi-project")
            assert text.count("</body>") == 1, src
            text = text.replace("</body>", BEACON + "\n</body>")
            open(dst, "w", encoding="utf-8").write(text)
            print(f"rewritten  {os.path.relpath(dst, DST)}")
        else:
            shutil.copy2(src, dst)
            print(f"copied     {os.path.relpath(dst, DST)}")
