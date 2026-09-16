#!/usr/bin/env python3
"""Render profile components.

    python3 render.py --out out                 render SVGs from profile.json
    python3 render.py --live                    refresh stats from the API first
    python3 render.py --readme ../README.md     also rewrite the markdown blocks
    python3 render.py --check                   validate the rendered SVGs

Emits each SVG component four ways -- {light,dark} x {wide,narrow} -- so the
README can switch on both colour scheme and viewport width with <picture>.
"""

import argparse
import json
import os
import re
import sys

from biocomponents import tokens as T
from biocomponents import primitives as P
from biocomponents import svg, markdown, fetch

HERE = os.path.dirname(os.path.abspath(__file__))


def render(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    written, expected = [], set()
    for name, fn in svg.COMPONENTS.items():
        for variant, width in svg.VARIANTS.items():
            for theme in ("light", "dark"):
                doc = fn(data, T.THEMES[theme], width)
                fname = f"{name}-{variant}-{theme}.svg"
                with open(os.path.join(outdir, fname), "w") as f:
                    f.write(doc)
                expected.add(fname)
                written.append(os.path.join(outdir, fname))

    # Drop output for components that no longer exist. Without this a renamed or
    # merged component leaves its old files behind forever -- they get committed,
    # and any README still pointing at one keeps being served a stale card with
    # no error anywhere.
    for stale in sorted(set(os.listdir(outdir)) - expected):
        if stale.endswith(".svg"):
            os.remove(os.path.join(outdir, stale))
            print(f"  pruned stale {stale}")
    return written


TEXT_RE = re.compile(r'<text\s+x="([\d.-]+)"\s+y="([\d.-]+)"([^>]*)>(.*?)</text>', re.S)


def check(paths):
    from lxml import etree
    bad = []
    for p in paths:
        src, name = open(p).read(), os.path.basename(p)
        for tok in ("<script", "@import", "<link", "<foreignObject"):
            if tok in src:
                bad.append(f"{name}: contains {tok!r} — inert or stripped behind camo")
        for pat in ('href="http', 'src="http', "url(http"):
            if pat in src:
                bad.append(f"{name}: external reference {pat!r} — camo will not fetch it")
        if len(src.encode()) > 200_000:
            bad.append(f"{name}: {len(src)//1024}KB over the 200KB ceiling")
        try:
            etree.fromstring(src.encode())
        except Exception as e:
            bad.append(f"{name}: XML parse error: {e}")

        vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', src)
        if not vb:
            continue
        w, h = float(vb.group(1)), float(vb.group(2))
        for m in TEXT_RE.finditer(src):
            x, y, attrs, txt = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4)
            size = float(re.search(r'font-size="([\d.]+)"', attrs).group(1))
            wt = int(re.search(r'font-weight="(\d+)"', attrs).group(1))
            am = re.search(r'text-anchor="(\w+)"', attrs)
            anchor = am.group(1) if am else "start"
            tw = P.measure(txt, "semibold" if wt >= 600 else "regular", size)
            left = x if anchor == "start" else (x - tw if anchor == "end" else x - tw / 2)
            if left < -0.5 or left + tw > w + 0.5:
                bad.append(f"{name}: text {txt[:32]!r} spans {left:.0f}..{left+tw:.0f} "
                           f"outside 0..{w:.0f}")
            if not 0 <= y <= h:
                bad.append(f"{name}: text {txt[:32]!r} baseline y={y:.0f} outside "
                           f"0..{h:.0f} — it will be clipped")
        for m in re.finditer(r'<rect x="([\d.-]+)" y="([\d.-]+)" '
                             r'width="([\d.]+)" height="([\d.]+)"', src):
            x, y, rw, rh = map(float, m.groups())
            if x < -1 or y < -1 or x + rw > w + 1 or y + rh > h + 1:
                bad.append(f"{name}: rect {x:.0f},{y:.0f} ({rw:.0f}x{rh:.0f}) escapes "
                           f"the {w:.0f}x{h:.0f} canvas")

    for name in svg.COMPONENTS:
        for variant in svg.VARIANTS:
            pair = [os.path.join(os.path.dirname(paths[0]),
                                 f"{name}-{variant}-{t}.svg") for t in ("light", "dark")]
            if not all(os.path.exists(x) for x in pair):
                bad.append(f"{name}-{variant}: missing a light/dark pair")
                continue
            vbs = {re.search(r'viewBox="([^"]+)"', open(x).read()).group(1) for x in pair}
            if len(vbs) > 1:
                bad.append(f"{name}-{variant}: light/dark viewBox mismatch {vbs} "
                           f"— the layout would jump on theme change")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.join(HERE, "profile.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--readme", help="markdown file whose bio: blocks to rewrite")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    with open(a.profile) as f:
        data = json.load(f)

    if a.live:
        data = fetch.refresh(data)
        with open(a.profile, "w") as f:
            json.dump(data, f, indent=2)
        print(f'stats refreshed — {data["stats"]["contributions_total"]:,} contributions, '
              f'{data["stats"]["repositories"]} repos')

    paths = render(data, a.out)
    for p in paths:
        print(f"  {os.path.basename(p):30} {os.path.getsize(p)//1024:>3}KB")

    if a.readme:
        with open(a.readme) as f:
            doc = f.read()
        out = markdown.render_all(doc, data)
        if out != doc:
            with open(a.readme, "w") as f:
                f.write(out)
            print(f"  rewrote markdown blocks in {a.readme}")
        else:
            print(f"  markdown blocks already current in {a.readme}")

    if a.check:
        bad = check(paths)
        if bad:
            print("\nFAILED:")
            for x in bad:
                print("  ✗", x)
            sys.exit(1)
        print(f"\nOK — {len(paths)} files pass all camo constraints")


if __name__ == "__main__":
    main()
