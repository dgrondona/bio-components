"""The image components.

Text that can live in markdown does, because markdown reflows and can carry a
real link. What stays here is what markdown genuinely cannot express: outlined
typography, a chart, and the two cards whose layout is the point.

Every component renders at an arbitrary width so the README can serve a narrow
build to phones via <picture media="(max-width: 500px)">. That is not a nicety:
GitHub puts max-width:100% on README images, so an 880px card on a 400px screen
scales to ~45% and its 13px body type lands near 6px.
"""

from . import tokens as T
from . import primitives as P

PAD = 32
LABEL = 11
GRID = 8


def _wrap(text, width, weight="regular", size=13):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if P.measure(t, weight, size) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _section(label, x, y, th, width, pad, tick=True):
    """Shared card header: accent tick, tracked micro-label, hairline."""
    out = []
    lx = x
    if tick:
        out.append(P.accent_tick(x, y - 8, th, w=18, h=3))
        lx = x + 26
    out.append(P.label(label, lx, y, th["muted"], size=LABEL, weight=600, spacing="1.3"))
    out.append(P.hline(x, y + 14, width - pad, th["hairline"]))
    return out, y + 14


def _lang_chip(lang, x, y, th, size=11, h=20):
    """Pill with Linguist's real colour for the language."""
    dot = T.LANG_COLORS.get(lang, T.LANG_FALLBACK)
    tw = P.measure(lang, "semibold", size)
    w = tw + 14 + 13
    g = (f'<g><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h}" rx="{h/2}" '
         f'fill="{th["chip_bg"]}" stroke="{th["hairline"]}" stroke-width="1"/>'
         f'<circle cx="{x+11:.2f}" cy="{y+h/2:.2f}" r="4" fill="{dot}"/>'
         + P.label(lang, x + 19, y + h / 2 + size * 0.36, th["muted"],
                   size=size, weight=600) + "</g>")
    return g, w


# ------------------------------------------------------------------ wordmark

def wordmark(data, th, width=880):
    ident = data["identity"]
    narrow = width < 560
    name_size = 27 if narrow else 40
    role_size = 12 if narrow else 14

    b = [P.accent_tick(0, 0, th, w=22 if narrow else 28)]
    name_y = 44 if narrow else 62
    path, _ = P.headline(ident["name"], 0, name_y, th["ink"], weight="bold",
                         size=name_size, tracking=-0.6 if narrow else -1.0)
    b.append(path)

    y = name_y + (19 if narrow else 26)
    for ln in _wrap(f'{ident["role"]} · {ident["affiliation"]}', width, "regular", role_size):
        b.append(P.label(ln, 0, y, th["muted"], size=role_size))
        y += role_size + 5

    rule_y = y + (5 if narrow else 8)
    b.append(P.hline(0, rule_y, width, th["hairline"], cls="rule"))

    fy = rule_y + (19 if narrow else 22)
    track, gap = 1.4, (18 if narrow else 32)
    fsize = 10 if narrow else 11
    x = 0
    for i, f in enumerate(ident["focus"]):
        up = f.upper()
        if i:
            b.append(P.label("/", x - gap / 2 - 3, fy, th["faint"], size=fsize))
        b.append(P.label(up, x, fy, th["muted"], size=fsize, weight=600, spacing=str(track)))
        x += P.measure(up, "semibold", fsize) + track * len(up) + gap

    h = fy + (13 if narrow else 16)
    style = (".rule{stroke-dasharray:%d;stroke-dashoffset:%d;"
             "animation:draw 1.1s cubic-bezier(.22,.7,.28,1) .12s forwards}"
             "@keyframes draw{to{stroke-dashoffset:0}}"
             "@media(prefers-reduced-motion:reduce){.rule{animation:none;stroke-dashoffset:0}}"
             ) % (width, width)
    return P.doc(width, h, "".join(b), th,
                 f'{ident["name"]} — {ident["role"]}, {ident["affiliation"]}',
                 desc="Focus areas: " + ", ".join(ident["focus"]), style=style)


# ------------------------------------------------------------------ worklist

def worklist(data, th, width=880):
    items = data["work"]
    narrow = width < 560
    pad = 20 if narrow else PAD
    name_size = 14 if narrow else 15
    desc_size = 12 if narrow else 13
    lh = 17 if narrow else 18

    head, hy = _section("SELECTED WORK", pad, 30 if narrow else 34, th, width, pad)
    b = list(head)

    # a slightly short measure reads better than full-bleed text
    descw = (width - pad * 2) if narrow else (width - pad * 2 - 96)
    rows, y = [], hy + (16 if narrow else 20)
    for it in items:
        lines = _wrap(it["desc"], descw, "regular", desc_size)
        rows.append((it, lines, y))
        y += (24 if narrow else 26) + (len(lines) * lh) + (20 if narrow else 22)
        if narrow:
            y += 22   # chip sits on its own line
    h = y - (6 if narrow else 4)

    body = [P.frame(width, h, th)] + b
    for i, (it, lines, y) in enumerate(rows):
        if i:
            body.append(P.hline(pad, y - (12 if narrow else 13), width - pad,
                                th["hairline"], opacity="0.5"))
        body.append(P.label(it["name"], pad, y + 12, th["ink"], size=name_size,
                            weight=600, mono=True))
        chip, cw = _lang_chip(it["lang"], pad if narrow else 0, 0, th,
                              size=10 if narrow else 11, h=19 if narrow else 20)
        if narrow:
            cy = y + 22
            chip, _ = _lang_chip(it["lang"], pad, cy, th, size=10, h=19)
            body.append(chip)
            ty = y + 60
        else:
            chip, _ = _lang_chip(it["lang"], width - pad - cw, y - 2, th)
            body.append(chip)
            ty = y + 34
        for j, ln in enumerate(lines):
            body.append(P.label(ln, pad, ty + j * lh, th["muted"], size=desc_size))

    desc = "; ".join(f'{i["name"]} ({i["lang"]}): {i["desc"]}' for i in items)
    return P.doc(width, h, "".join(body), th, "Selected work", desc=desc)


# --------------------------------------------------------------------- stack

def stack(data, th, width=880):
    groups = data["stack"]
    narrow = width < 560
    pad = 20 if narrow else PAD
    head, hy = _section("STACK", pad, 30 if narrow else 34, th, width, pad)

    rows, y = [], hy + (14 if narrow else 16)
    for g in groups:
        rows.append((g, y))
        y += (74 if narrow else 52)
    h = y + (4 if narrow else 8)

    body = [P.frame(width, h, th)] + head
    labelcol = 0 if narrow else 186
    for i, (g, y) in enumerate(rows):
        if i:
            body.append(P.hline(pad, y - (14 if narrow else 10), width - pad,
                                th["hairline"], opacity="0.5"))
        body.append(P.label(g["group"], pad, y + (14 if narrow else 30),
                            th["ink"], size=12 if narrow else 13, weight=600))
        x = pad + labelcol
        cy = y + (26 if narrow else 16)
        for item in g["items"]:
            chip, cw = _lang_chip(item, x, cy, th, size=10 if narrow else 11,
                                  h=19 if narrow else 20)
            body.append(chip)
            x += cw + 7

    desc = "; ".join(f'{g["group"]}: {", ".join(g["items"])}' for g in groups)
    return P.doc(width, h, "".join(body), th, "Technical stack", desc=desc)


# ------------------------------------------------------------------ activity

def activity(data, th, width=880):
    """Figures, year trajectory and the weekly chart in one frame.

    These were three separate blocks; as one card the numbers give the chart a
    scale to be read against, and the page gains a resting point instead of a
    run of same-sized boxes.
    """
    s = data["stats"]
    narrow = width < 560
    pad = 20 if narrow else PAD
    head, hy = _section("ACTIVITY", pad, 30 if narrow else 34, th, width, pad)
    b = list(head)
    if not narrow:
        b.append(P.label(f'updated {s["generated"]}', width - pad, 34, th["faint"],
                         size=LABEL, anchor="end"))

    cells = [(f'{s["contributions_total"]:,}', "contributions"),
             (f'{s["repositories"]}', "repositories"),
             (f'{s["languages"]}', "languages"),
             (f'{s["since"]}', "active since")]

    if narrow:
        cw = (width - pad * 2) / 2
        for i, (val, lab) in enumerate(cells):
            cx = pad + (i % 2) * cw
            cy = hy + 42 + (i // 2) * 52
            p, _ = P.headline(val, cx, cy, th["ink"], weight="semibold", size=23, tracking=-0.5)
            b.append(p)
            b.append(P.label(lab, cx, cy + 15, th["muted"], size=11))
        y = hy + 42 + 2 * 52 - 4
    else:
        cw = (width - pad * 2) / 4
        for i, (val, lab) in enumerate(cells):
            cx = pad + i * cw
            p, _ = P.headline(val, cx, hy + 50, th["ink"], weight="semibold",
                              size=32, tracking=-0.8)
            b.append(p)
            b.append(P.label(lab, cx, hy + 70, th["muted"], size=12))
            if i:
                b.append(P.vline(cx - 22, hy + 20, hy + 76, th["hairline"], opacity="0.55"))
        y = hy + 76

    # year trajectory
    b.append(P.hline(pad, y + 12, width - pad, th["hairline"], opacity="0.6"))
    years = sorted(s["by_year"].items())
    peak = max(v for _, v in years) or 1
    gapw = 14 if narrow else 22
    bw = (width - pad * 2 - gapw * (len(years) - 1)) / len(years)
    bx, by = pad, y + (42 if narrow else 46)
    for yr, val in years:
        b.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="6" rx="3" '
                 f'fill="{th["hairline"]}" opacity="0.55"/>')
        b.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw*(val/peak):.1f}" height="6" '
                 f'rx="3" fill="{th["accent"]}"/>')
        b.append(P.label(yr, bx, by - 7, th["muted"], size=10 if narrow else 11, weight=600))
        b.append(P.label(str(val), bx + bw, by - 7, th["ink"], size=10 if narrow else 11,
                         weight=600, anchor="end"))
        bx += bw + gapw

    # weekly chart
    series = s.get("weekly", [])
    if narrow:
        series = series[-26:]
    ctop = by + (26 if narrow else 30)
    plot_h = 26 if narrow else 32
    base = ctop + plot_h
    weeks = len(series)
    b.append(P.label(f"LAST {weeks} WEEKS", pad, ctop - 10, th["faint"],
                     size=10, weight=600, spacing="1.2"))
    if not narrow:
        b.append(P.label(f'{sum(1 for v in series if v)} active',
                         width - pad, ctop - 10, th["faint"], size=10, anchor="end"))
    if series:
        pk = max(series) or 1
        gp = 2 if narrow else 3
        bwid = (width - pad * 2 - gp * (weeks - 1)) / weeks
        for i, v in enumerate(series):
            x = pad + i * (bwid + gp)
            if v:
                bh = max(3.0, plot_h * (v / pk))
                b.append(f'<rect x="{x:.2f}" y="{base-bh:.2f}" width="{bwid:.2f}" '
                         f'height="{bh:.2f}" rx="1.5" fill="{th["accent"]}" '
                         f'opacity="{0.4 + 0.6*(v/pk):.2f}"/>')
            else:
                b.append(f'<rect x="{x:.2f}" y="{base-3:.2f}" width="{bwid:.2f}" '
                         f'height="3" rx="1.5" fill="{th["hairline"]}" opacity="0.7"/>')
    h = base + (16 if narrow else 18)
    years_txt = ", ".join(f"{y} {v}" for y, v in years)
    return P.doc(width, h, "".join(b), th, "GitHub activity",
                 desc=(f'{s["contributions_total"]} contributions across {s["repositories"]} '
                       f'repositories in {s["languages"]} languages since {s["since"]}. '
                       f'By year: {years_txt}.'))


COMPONENTS = {"wordmark": wordmark, "worklist": worklist,
              "stack": stack, "activity": activity}
VARIANTS = {"wide": T.WIDTH, "narrow": 400}
