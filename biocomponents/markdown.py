"""Markdown blocks for everything that is fundamentally text.

Deliberately avoids wide tables. GitHub gives README images max-width:100% but
gives tables a horizontal scrollbar, and a four-column table is already cramped
at 400px -- so anything that must survive a phone is emitted as bold/plain runs
separated by middots, which reflow like any other paragraph.

Each block is written into the README between HTML-comment markers, so the
workflow can rewrite exactly its own region and leave hand-written prose alone.
"""

import re

START = "<!--bio:{name}-->"
END = "<!--/bio:{name}-->"


def replace_block(doc, name, content):
    """Swap the content between this block's markers, leaving everything else."""
    s, e = START.format(name=name), END.format(name=name)
    pat = re.compile(re.escape(s) + r".*?" + re.escape(e), re.S)
    new = f"{s}\n{content.strip()}\n{e}"
    if not pat.search(doc):
        raise KeyError(f"marker {s} not found in the document")
    return pat.sub(lambda _: new, doc, count=1)


def intro(data):
    return "\n\n".join(data["intro"])


# Only the intro is a managed block. The work card cannot carry links -- a
# camo-proxied SVG never can -- but the right place for navigation is GitHub's
# own pinned-repository row, which sits directly under the README and is
# clickable, described and updated by GitHub itself.
BLOCKS = {"intro": intro}


def render_all(doc, data):
    for name, fn in BLOCKS.items():
        doc = replace_block(doc, name, fn(data))
    return doc
