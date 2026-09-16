"""The two components that genuinely earn being images.

Everything else on a profile is text, and text belongs in markdown where it
reflows. These two do not: the wordmark is typography (outlined so it renders
identically everywhere), and the sparkline is a chart.

Each renders at an arbitrary width so the README can serve a narrow variant to
phones via <picture media="(max-width: ...)">. That matters more than it sounds:
GitHub puts max-width:100% on README images, so an 880px card on a 400px screen
is scaled to ~45% and its 13px body text lands at ~6px -- unreadable. A
purpose-built narrow layout is the only real fix.
"""

from . import tokens as T
from . import primitives as P


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


def wordmark(data, th, width=880):
    ident = data["identity"]
    narrow = width < 560
    pad = 0

    name_size = 28 if narrow else 40
    role_size = 12 if narrow else 14
    body = [P.accent_tick(pad, 0, th, w=24 if narrow else 28)]

    name_y = 46 if narrow else 62
    path, _ = P.headline(ident["name"], pad, name_y, th["ink"],
                         weight="bold", size=name_size,
                         tracking=-0.6 if narrow else -1.0)
    body.append(path)

    role = f'{ident["role"]} · {ident["affiliation"]}'
    lines = _wrap(role, width - pad * 2, "regular", role_size)
    y = name_y + (20 if narrow else 26)
    for ln in lines:
        body.append(P.label(ln, pad, y, th["muted"], size=role_size))
        y += role_size + 5

    rule_y = y + (6 if narrow else 8)
    body.append(P.hline(pad, rule_y, width - pad, th["hairline"], cls="rule"))

    # focus areas -- drop to a single joined run when the width can't hold gaps
    fy = rule_y + (20 if narrow else 22)
    track, gap = 1.4, (20 if narrow else 34)
    x = pad
    for i, f in enumerate(ident["focus"]):
        up = f.upper()
        if i:
            body.append(P.label("/", x - gap / 2 - 3, fy, th["faint"], size=10 if narrow else 11))
        body.append(P.label(up, x, fy, th["muted"], size=10 if narrow else 11,
                            weight=600, spacing=str(track)))
        x += P.measure(up, "semibold", 10 if narrow else 11) + track * len(up) + gap

    h = fy + (14 if narrow else 16)
    style = (
        ".rule{stroke-dasharray:%d;stroke-dashoffset:%d;"
        "animation:draw 1.1s cubic-bezier(.22,.7,.28,1) .12s forwards}"
        "@keyframes draw{to{stroke-dashoffset:0}}"
        "@media(prefers-reduced-motion:reduce){.rule{animation:none;stroke-dashoffset:0}}"
    ) % (width, width)

    return P.doc(width, h, "".join(body), th,
                 f'{ident["name"]} — {ident["role"]}, {ident["affiliation"]}',
                 desc="Focus areas: " + ", ".join(ident["focus"]), style=style)


def sparkline(data, th, width=880):
    s = data["stats"]
    narrow = width < 560
    series = s.get("weekly", [])
    # a 53-bar chart at phone width gives sub-pixel bars; show a shorter window
    if narrow:
        series = series[-26:]

    pad = 20 if narrow else 28
    top = 54 if narrow else 62
    plot_h = 28 if narrow else 34
    base = top + plot_h
    h = base + (32 if narrow else 36)

    body = [P.frame(width, h, th)]
    weeks = len(series)
    body.append(P.label(f"ACTIVITY · LAST {weeks} WEEKS", pad, 28 if narrow else 32,
                        th["muted"], size=10 if narrow else 11,
                        weight=600, spacing="1.2"))
    active = sum(1 for v in series if v)
    if not narrow:
        body.append(P.label(f"{active} active weeks", width - pad, 32, th["faint"],
                            size=11, anchor="end"))
    body.append(P.hline(pad, 40 if narrow else 46, width - pad, th["hairline"]))

    if series:
        peak = max(series) or 1
        gap = 2 if narrow else 3
        bw = (width - pad * 2 - gap * (weeks - 1)) / weeks
        for i, v in enumerate(series):
            x = pad + i * (bw + gap)
            if v:
                bh = max(3.0, plot_h * (v / peak))
                body.append(
                    f'<rect x="{x:.2f}" y="{base-bh:.2f}" width="{bw:.2f}" '
                    f'height="{bh:.2f}" rx="1.5" fill="{th["accent"]}" '
                    f'opacity="{0.45 + 0.55*(v/peak):.2f}"/>')
            else:
                body.append(
                    f'<rect x="{x:.2f}" y="{base-3:.2f}" width="{bw:.2f}" '
                    f'height="3" rx="1.5" fill="{th["hairline"]}" opacity="0.7"/>')
        body.append(P.hline(pad, base + 9, width - pad, th["hairline"], opacity="0.5"))
        lab = 10 if not narrow else 9
        body.append(P.label(s.get("weekly_from", ""), pad, base + 22, th["faint"], size=lab))
        body.append(P.label("today", width - pad, base + 22, th["faint"],
                            size=lab, anchor="end"))

    return P.doc(width, h, "".join(body), th, "Weekly contribution activity",
                 desc=f"Relative commit activity over {weeks} weeks; {active} with activity.")


COMPONENTS = {"wordmark": wordmark, "sparkline": sparkline}
VARIANTS = {"wide": T.WIDTH, "narrow": 400}
