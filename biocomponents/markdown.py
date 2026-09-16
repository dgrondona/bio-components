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


def work(data):
    out = []
    for w in data["work"]:
        out.append(f'**[{w["name"]}]({w["url"]})** · `{w["lang"]}`  \n{w["desc"]}')
    return "\n\n".join(out)


def stack(data):
    rows = ["| | |", "|---|---|"]
    for g in data["stack"]:
        rows.append(f'| **{g["group"]}** | {" · ".join(g["items"])} |')
    return "\n".join(rows)


def stats(data):
    s = data["stats"]
    head = (f'**{s["contributions_total"]:,}** contributions · '
            f'**{s["repositories"]}** repositories · '
            f'**{s["languages"]}** languages · '
            f'active since **{s["since"]}**')
    years = " · ".join(f'{y} — **{v}**' for y, v in sorted(s["by_year"].items()))
    return f'{head}\n\n<sub>{years}</sub>'


BLOCKS = {"intro": intro, "work": work, "stack": stack, "stats": stats}


def render_all(doc, data):
    for name, fn in BLOCKS.items():
        doc = replace_block(doc, name, fn(data))
    return doc
