"""Design tokens: the single source of truth for every generated component.

Palette deliberately borrows GitHub's own surface/border/text tokens so the cards
read as native page furniture rather than pasted-on images. Card backgrounds stay
transparent for the same reason -- they inherit whatever canvas GitHub paints.

Accent is derived from the red in the previous profile banner (#ff0000), retuned
per theme: pure red fails contrast on GitHub's dark canvas and reads harsh at
display sizes, so each theme gets a tuned variant that still reads as "that red".
"""

THEMES = {
    "light": {
        "bg":        "none",
        "hairline":  "#d1d9e0",
        "ink":       "#1f2328",
        "muted":     "#59636e",
        "faint":     "#818b98",
        "accent":    "#C9252D",
        "accent_dim": "#C9252D22",
        "chip_bg":   "#f6f8fa",
    },
    "dark": {
        "bg":        "none",
        "hairline":  "#3d444d",
        "ink":       "#f0f6fc",
        "muted":     "#9198a1",
        "faint":     "#656c76",
        "accent":    "#FF5A63",
        "accent_dim": "#FF5A6322",
        "chip_bg":   "#151b23",
    },
}

# GitHub's own UI font stack. Must stay a stack of locally-available families:
# camo cannot fetch webfonts, so anything referenced here must already be on the
# viewer's machine or it silently falls back.
UI_STACK = ('-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,'
            '"Apple Color Emoji","Segoe UI Emoji",sans-serif')
MONO_STACK = ('ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
              '"Liberation Mono",monospace')

# Type scale
SIZE_DISPLAY = 40
SIZE_TITLE   = 20
SIZE_BODY    = 14
SIZE_LABEL   = 12
SIZE_MICRO   = 10

# 8px grid
GRID = 8

# Canonical full-bleed width. GitHub renders README images up to ~890px in the
# content column; 880 keeps a hair of margin at max width.
WIDTH = 880

FONTS = {
    "regular":  "fonts/Inter-Regular.ttf",
    "semibold": "fonts/Inter-SemiBold.ttf",
    "bold":     "fonts/Inter-Bold.ttf",
}


# Linguist's own language colours. Using the real ones means a reader who knows
# GitHub recognises a language before reading its label -- colour doing work
# rather than decoration.
LANG_COLORS = {
    "JavaScript": "#f1e05a", "Python": "#3572A5", "C++": "#f34b7d",
    "C": "#555555", "C#": "#178600", "Assembly": "#6E4C13",
    "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051",
    "TypeScript": "#3178c6", "TeX": "#3D6117", "Java": "#b07219",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516",
}
LANG_FALLBACK = "#8b949e"
