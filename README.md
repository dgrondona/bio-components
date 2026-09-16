# bio-components

Self-hosted components for a GitHub profile README. Renders SVG cards and markdown blocks from
one set of design tokens, refreshes them daily from the GitHub API, and commits the result — so
the profile updates itself with no third-party stats service in the dependency chain.

```bash
pip install fonttools lxml
python3 render.py --live --check
```

## What it renders

| | Output | Why |
| --- | --- | --- |
| `wordmark` | SVG, 4 variants | Typography is the point; headline glyphs are outlined so they render identically everywhere |
| `sparkline` | SVG, 4 variants | A chart |
| `intro`, `work`, `stack`, `stats` | markdown | Text belongs in markdown, where it reflows on a phone |

Four variants per component is `{light, dark} × {wide, narrow}` — the README switches on both with
`<picture>`.

## The constraints this works around

A GitHub README can only display *images*. The markdown sanitizer strips `<style>`, inline
`style=`, `class` and `id`, so HTML in a README cannot be styled at all. Everything visual is
therefore an SVG, and these are the rules that SVG has to survive:

| Constraint | Consequence |
| --- | --- |
| Inline `<svg>` is stripped from markdown | components must be files referenced by `<img>` |
| `prefers-color-scheme` inside a camo-proxied SVG is unreliable | ship separate light/dark files, switch with `<picture>` |
| camo cannot fetch webfonts | no `@import`/`<link>`; outline headline text at build time |
| `<script>` in SVG never executes | animate with CSS keyframes or SMIL only |
| GitHub sets `max-width:100%` on README images | an 880px card scaled to a 400px phone renders 13px text at ~6px — hence the narrow variants |
| camo caches aggressively | bust with `?v=N` when iterating |

`--check` enforces all of these, plus a geometry pass that measures every `<text>` and `<rect>`
against the `viewBox` using the same font metrics the renderer lays out with. That last one is not
theoretical — it caught a set of date labels sitting 6px below the canvas, clipped away silently.

## Why generate at commit time

The obvious alternative is a hosted endpoint that renders on request, the way
`github-readme-stats` does. It is not actually fresher:

```
$ curl -sI 'https://github-stats-extended.vercel.app/api?username=dgrondona'
cache-control: max-age=255600      # 71 hours
age: 82590                         # the copy served was 23 hours old
x-vercel-cache: HIT
```

A daily commit beats that, costs nothing, needs no hosting account or PAT, and cannot go down —
the canonical `github-readme-stats.vercel.app` instance returns `503 DEPLOYMENT_PAUSED` as of
this writing, which is the failure mode being avoided.

## A note on language stats

`fetch.py` reports the *count* of distinct languages, never a byte-weighted ranking. GitHub's
language API measures bytes committed, which counts vendored dependencies as authored code. On
this account one coursework repo with a committed virtualenv contributes 24.7 MB of Python — 96%
of the entire footprint — which is why the stock top-languages card renders its owner as a 97%
Python developer whose 137-file C# project shows up as 0.7%.

## Layout

```
biocomponents/
  tokens.py       palette, type scale, spacing — the single source of truth
  primitives.py   shared drawing: outlined text, hairlines, chips, card frames
  svg.py          the two image components, width-aware
  markdown.py     the text blocks + marker-based README rewriting
  fetch.py        GitHub API
  fonts/          Inter, outlined at build time — never fetched at view time
render.py         CLI: render / --live / --check / --readme
profile.json      all content and figures; edit this, not the Python
out/              generated — do not edit by hand
```

## Using it from a profile README

Mark the regions to be managed, and point the images at this repo's `out/`:

```html
<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset=".../wordmark-narrow-dark.svg">
  <source media="(max-width: 500px)"                                  srcset=".../wordmark-narrow-light.svg">
  <source media="(prefers-color-scheme: dark)"                        srcset=".../wordmark-wide-dark.svg">
  <img alt="…" src=".../wordmark-wide-light.svg">
</picture>

<!--bio:work-->
<!--/bio:work-->
```

`render.py --readme README.md` rewrites each marked region and leaves everything else alone. Both
the markdown rewrite and the SVG render are idempotent, so the workflow only commits when a figure
actually moves.
