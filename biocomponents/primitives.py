"""Shared SVG primitives.

Everything the components draw goes through this module, so the five cards stay
visually consistent by construction rather than by discipline.

Two text strategies, chosen per use:

  outline()  converts glyphs to <path> via fontTools. Used for headline type where
             the exact letterforms are part of the identity. Immune to camo's
             inability to fetch webfonts, at the cost of ~150 bytes/glyph and
             text that is no longer selectable.

  label()    emits a real <text> node using GitHub's own UI font stack. Used for
             everything small. Stays selectable and accessible; renders in
             whatever the viewer already has installed.

measure() estimates rendered width using Inter's metrics as a proxy so label()
text can still be laid out and centred. It is an estimate: the viewer's actual
fallback font may differ slightly, so anything measured this way is centred
rather than edge-aligned, which degrades gracefully when the estimate is off.
"""

import os
from functools import lru_cache

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

from . import tokens as T

_HERE = os.path.dirname(os.path.abspath(__file__))


@lru_cache(maxsize=None)
def _font(weight):
    return TTFont(os.path.join(_HERE, T.FONTS[weight]))


def _ntos(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") or "0"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def measure(text, weight="regular", size=14, tracking=0.0):
    """Advance width of `text`, in px, using Inter metrics."""
    f = _font(weight)
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    scale = size / upem
    w = 0.0
    for ch in text:
        g = cmap.get(ord(ch))
        w += (hmtx[g][0] * scale if g else size * 0.5) + tracking
    return w - tracking if text else 0.0


def outline(text, weight="bold", size=40, tracking=0.0):
    """Return (path_data, advance_width) with baseline at y=0, glyphs above it."""
    f = _font(weight)
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    hmtx = f["hmtx"]
    scale = size / upem
    x, parts = 0.0, []
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            x += size * 0.5 + tracking
            continue
        # round to 2dp: raw pen output carries 8 decimals and triples file size
        pen = SVGPathPen(gs, ntos=_ntos)
        # flip Y: font space is y-up, SVG is y-down
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
        d = pen.getCommands()
        if d:
            parts.append(d)
        x += hmtx[g][0] * scale + tracking
    return " ".join(parts), (x - tracking if text else 0.0)


def headline(text, x, y, fill, weight="bold", size=40, tracking=0.0, cls=""):
    d, w = outline(text, weight, size, tracking)
    c = f' class="{cls}"' if cls else ""
    return (f'<g transform="translate({x:.2f},{y:.2f})"{c}>'
            f'<path d="{d}" fill="{fill}"/></g>'), w


def label(text, x, y, fill, size=None, weight=400, anchor="start",
          mono=False, opacity=None, spacing=None, cls=""):
    size = size or T.SIZE_BODY
    stack = T.MONO_STACK if mono else T.UI_STACK
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family=\'{stack}\' '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}"'
            f'{a}{o}{ls}{c}>{esc(text)}</text>')


def hline(x1, y, x2, stroke, width=1, opacity=None, cls=""):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    c = f' class="{cls}"' if cls else ""
    # +0.5 keeps a 1px stroke on the pixel grid instead of straddling it
    yy = round(y) + 0.5 if width == 1 else y
    return (f'<line x1="{x1:.2f}" y1="{yy}" x2="{x2:.2f}" y2="{yy}" '
            f'stroke="{stroke}" stroke-width="{width}"{o}{c}/>')


def vline(x, y1, y2, stroke, width=1, opacity=None):
    o = f' opacity="{opacity}"' if opacity is not None else ""
    xx = round(x) + 0.5 if width == 1 else x
    return (f'<line x1="{xx}" y1="{y1:.2f}" x2="{xx}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}"{o}/>')


def frame(w, h, th, radius=6):
    """Hairline card border. Inset by .5px so the stroke lands on whole pixels."""
    return (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{radius}" '
            f'fill="none" stroke="{th["hairline"]}" stroke-width="1"/>')


def chip(text, x, y, th, size=11, pad=7, height=20):
    """Pill-shaped tag. Text is centred so an imperfect width estimate degrades
    into uneven padding rather than overflow."""
    w = measure(text, "semibold", size) + pad * 2
    return (f'<g><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{height}" '
            f'rx="{height/2}" fill="{th["chip_bg"]}" stroke="{th["hairline"]}" '
            f'stroke-width="1"/>'
            + label(text, x + w / 2, y + height / 2 + size * 0.36, th["muted"],
                    size=size, weight=600, anchor="middle")
            + "</g>"), w


def accent_tick(x, y, th, w=28, h=3):
    """The one recurring brand mark: a short accent rule."""
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w}" height="{h}" '
            f'rx="{h/2}" fill="{th["accent"]}"/>')


def doc(w, h, body, th, title, desc="", style=""):
    """SVG document wrapper.

    Deliberately contains no <script>, no @import, no <link> and no external
    references -- all four are either stripped or silently fail behind camo.
    """
    s = f"<style>{style}</style>" if style else ""
    d = f'<desc id="d">{esc(desc)}</desc>' if desc else ""
    bg = ("" if th["bg"] == "none"
          else f'<rect width="{w}" height="{h}" fill="{th["bg"]}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t" fill="none">'
        f'<title id="t">{esc(title)}</title>{d}{s}{bg}{body}</svg>'
    )
