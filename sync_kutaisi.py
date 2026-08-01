#!/usr/bin/env python3
"""Sync the Kutaisi land page from ~/projects/kutaisi-land.

The source repo no longer serves anything itself (its GitHub Pages is
disabled); kurdiani.ge/kutaisi-project/ is the only live copy.

The source pages are self-extracting bundles: ~2.6 MB each, everything
base64-inlined, nothing rendered until a JS runtime unpacks it. That is the
right shape for a portable artifact and the wrong one for a hosted page, so
each HTML file is flattened here into plain HTML plus shared assets (see
flatten_kutaisi.py). The bundle stays the editable source; only the published
copy is flattened.

Also on the way in: aseveryn.github.io meta URLs are rewritten to kurdiani.ge
and the Cloudflare beacon is injected. Everything else (og.jpg, briefs/, …) is
copied verbatim.

Run `python3 build.py` afterwards to publish the copy into docs/.
"""
import os
import shutil

from build import CF_BEACON_TOKEN  # single source of truth for the token
from flatten_kutaisi import flatten

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

written = {}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for name in files:
        if name in SKIP:
            continue
        src = os.path.join(root, name)
        rel = os.path.relpath(src, SRC)
        dst = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if name.endswith(".html"):
            # language editions sit one level down and reach up for the assets
            sub = os.path.dirname(rel)
            depth = len(sub.split(os.sep)) if sub else 0
            text, assets = flatten(open(src, encoding="utf-8").read(), "../" * depth)
            text = text.replace("aseveryn.github.io/kutaisi-land",
                                "kurdiani.ge/kutaisi-project")
            assert text.count("</body>") == 1, src
            text = text.replace("</body>", BEACON + "\n</body>")
            open(dst, "w", encoding="utf-8").write(text)
            print(f"flattened  {rel}  ({len(text)//1024} KB)")
            for arel, data in assets.items():          # shared; identical bytes
                if arel in written:
                    continue
                apath = os.path.join(DST, arel)
                os.makedirs(os.path.dirname(apath), exist_ok=True)
                open(apath, "wb").write(data)
                written[arel] = len(data)
        else:
            shutil.copy2(src, dst)
            print(f"copied     {rel}")

total = sum(written.values())
print(f"\nassets: {len(written)} files, {total/1024/1024:.2f} MB "
      f"(fetched on demand; 7 of 8 images lazy-loaded)")
