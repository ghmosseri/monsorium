#!/usr/bin/env python3
"""Write the vector UI pieces in assets/ui/.

    python3 tools/make-ui.py

Nav buttons come in pairs: <name>-mask.svg (solid silhouette, used as a CSS
mask over an ovilats texture) and <name>-line.svg (the inked outline and
ornament drawn on top). Bottles are full illustrations. Palette colours only.
"""
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "assets" / "ui"
INK, GOLD, PLUM, LEAF, LIME, ROSE, ABYSS = (
    "#180724", "#FFD06B", "#942C5B", "#62BA52", "#87E627", "#E69393", "#0B0236")


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">{body}</svg>\n')


def scallop(cx, cy, rx, ry, n, bulge=1.18):
    """A closed path of n outward arcs around an ellipse: a puffy shell edge."""
    import math
    pts = [(cx + rx * math.cos(2 * math.pi * i / n - math.pi / 2),
            cy + ry * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        r = math.dist((x0, y0), (x1, y1)) / 2 * bulge
        d += f" A{r:.1f} {r:.1f} 0 0 1 {x1:.1f} {y1:.1f}"
    return d + " Z"


# ---------------------------------------------------------------- buttons
# Each: (viewBox w, h, silhouette path, extra ornament drawn on the line layer)
BUTTONS = {
    # Home — a puffy scalloped shell-cartouche
    "home": (200, 92, scallop(100, 46, 88, 34, 14),
             f'<path d="{scallop(100, 46, 70, 22, 14, 1.1)}" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-dasharray="2 5" stroke-linecap="round"/>'),
    # The Heretic — an ogee plaque with a little finial, pointed like a lancet arch
    "heretic": (270, 92,
                "M34 12 H118 C126 12 128 4 135 1 C142 4 144 12 152 12 H236 "
                "C252 12 260 32 268 46 C260 60 252 80 236 80 H152 C144 80 142 88 135 91 "
                "C128 88 126 80 118 80 H34 C18 80 10 60 2 46 C10 32 18 12 34 12 Z",
                f'<path d="M30 22 H240 M30 70 H240" stroke="{GOLD}" stroke-width="1.4" stroke-dasharray="1 6" stroke-linecap="round"/>'
                f'<circle cx="135" cy="7" r="2.6" fill="{GOLD}"/><circle cx="135" cy="85" r="2.6" fill="{GOLD}"/>'),
    # The Alleyway — an admission ticket with rounded notches
    "alleyway": (270, 92,
                 "M16 4 H254 A12 12 0 0 0 266 16 V33 A13 13 0 0 0 266 59 V76 "
                 "A12 12 0 0 0 254 88 H16 A12 12 0 0 0 4 76 V59 A13 13 0 0 0 4 33 "
                 "V16 A12 12 0 0 0 16 4 Z",
                 f'<path d="M214 14 V78" stroke="{INK}" stroke-width="2" stroke-dasharray="3 5" stroke-linecap="round"/>'
                 f'<path d="M232 34 l4 8 9 1 -7 6 2 9 -8 -5 -8 5 2 -9 -7 -6 9 -1z" fill="{PLUM}"/>'),
    # Bottles at Sea — a bottle lying on its side, corked
    "bottles": (290, 92,
                "M44 10 H172 C198 10 208 30 226 33 H250 C254 33 256 30 260 30 H276 "
                "C283 30 286 37 286 46 C286 55 283 62 276 62 H260 C256 62 254 59 250 59 "
                "H226 C208 62 198 82 172 82 H44 C20 82 4 66 4 46 C4 26 20 10 44 10 Z",
                f'<path d="M258 30 V62" stroke="{INK}" stroke-width="2.4"/>'
                f'<path d="M262 30 H276 C283 30 286 37 286 46 C286 55 283 62 276 62 H262 Z" fill="{PLUM}"/>'
                f'<path d="M30 26 C22 34 20 52 28 64" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>'),
    # Conches — a conch: spire whorls on the left, tapering to the canal
    "conches": (240, 92,
                "M8 48 C5 38 13 31 22 33 C22 22 33 16 41 22 C45 12 59 9 66 17 "
                "C74 5 95 5 103 14 C124 4 164 9 194 27 C210 35 226 42 234 48 "
                "C226 53 210 58 194 66 C164 84 112 88 82 82 C62 80 46 74 35 66 "
                "C23 68 10 60 8 48 Z",
                f'<path d="M24 46 C26 38 36 36 40 42 C44 48 36 54 30 50" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
                f'<path d="M112 20 C104 40 104 60 114 80 M140 18 C132 40 132 62 142 80 M168 22 C162 40 162 60 170 74" '
                f'fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="1 5"/>'),
}


def write_buttons():
    for name, (w, h, d, extra) in BUTTONS.items():
        (UI / f"btn-{name}-mask.svg").write_text(svg(w, h, f'<path d="{d}" fill="#000"/>'))
        line = (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linejoin="round" '
                f'transform="translate({w * .02:.1f} {h * .03:.1f}) scale(.96 .94)"/>' + extra)
        (UI / f"btn-{name}-line.svg").write_text(svg(w, h, line))


# ---------------------------------------------------------------- bottles
# Silhouettes share a neck (x 104..136) so the cork and lip line up.
BOTTLES = {
    # round-bellied flask
    "rose": ("M104 62 V146 C104 166 92 176 78 184 C36 206 12 246 12 292 "
             "C12 356 60 404 120 404 C180 404 228 356 228 292 C228 246 204 206 162 184 "
             "C148 176 136 166 136 146 V62 Z", (ROSE, PLUM), LIME, 258),
    # tall, square-shouldered
    "lime": ("M106 62 V128 C106 168 72 176 66 212 C62 236 62 250 62 270 V382 "
             "C62 398 74 408 90 408 H150 C166 408 178 398 178 382 V270 C178 250 178 236 174 212 "
             "C168 176 134 168 134 128 V62 Z", (LIME, LEAF), ROSE, 282),
    # apothecary teardrop
    "dusk": ("M106 62 V118 C106 140 98 150 86 166 C50 214 30 262 30 312 "
             "C30 370 70 408 120 408 C170 408 210 370 210 312 C210 262 190 214 154 166 "
             "C142 150 134 140 134 118 V62 Z", (ROSE, ABYSS), GOLD, 300),
}


def bottle_svg(key, d, glass, liquid, level):
    g0, g1 = glass
    wave = (f"M0 {level} C40 {level - 14} 80 {level + 14} 120 {level} "
            f"C160 {level - 14} 200 {level + 14} 240 {level} V440 H0 Z")
    body = f"""
<defs>
  <linearGradient id="g-{key}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{g0}" stop-opacity=".78"/>
    <stop offset="1" stop-color="{g1}" stop-opacity=".92"/>
  </linearGradient>
  <linearGradient id="l-{key}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{liquid}" stop-opacity=".85"/>
    <stop offset="1" stop-color="{g1}" stop-opacity=".95"/>
  </linearGradient>
  <clipPath id="c-{key}"><path d="{d}"/></clipPath>
</defs>
<path d="{d}" fill="url(#g-{key})"/>
<g clip-path="url(#c-{key})">
  <path d="{wave}" fill="url(#l-{key})"/>
  <path d="M0 {level} C40 {level - 14} 80 {level + 14} 120 {level} C160 {level - 14} 200 {level + 14} 240 {level}"
        fill="none" stroke="{GOLD}" stroke-width="3" stroke-opacity=".7"/>
  <g transform="rotate(-14 120 250)">
    <rect x="84" y="150" width="72" height="190" rx="14" fill="{GOLD}"/>
    <path d="M96 182 H144 M96 202 H140 M96 222 H146 M96 242 H132 M96 262 H142 M96 282 H128"
          stroke="{PLUM}" stroke-width="3" stroke-linecap="round"/>
    <ellipse cx="120" cy="150" rx="36" ry="9" fill="{ROSE}"/>
    <ellipse cx="120" cy="340" rx="36" ry="9" fill="{ROSE}"/>
  </g>
</g>
<path d="{d}" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
<path d="M58 250 C50 290 56 336 80 368" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linecap="round" stroke-opacity=".75" clip-path="url(#c-{key})"/>
<path d="M122 90 V130" stroke="{GOLD}" stroke-width="5" stroke-linecap="round" stroke-opacity=".75"/>
<rect x="94" y="48" width="52" height="18" rx="9" fill="{g0}" stroke="{INK}" stroke-width="5"/>
<path d="M104 8 H136 C142 8 146 12 146 18 V44 C146 48 142 52 136 52 H104 C98 52 94 48 94 44 V18 C94 12 98 8 104 8 Z"
      fill="{PLUM}" stroke="{INK}" stroke-width="5"/>
<path d="M104 18 H136 M104 28 H136 M104 38 H136" stroke="{ROSE}" stroke-width="2.4" stroke-linecap="round"/>
<path d="M100 78 C120 86 140 74 150 84 C158 92 150 104 160 112" fill="none" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
"""
    return svg(240, 440, body)


def write_bottles():
    for key, (d, glass, liquid, level) in BOTTLES.items():
        (UI / f"bottle-{key}.svg").write_text(bottle_svg(key, d, glass, liquid, level))


def write_misc():
    star = "M50 0 C54 34 66 46 100 50 C66 54 54 66 50 100 C46 66 34 54 0 50 C34 46 46 34 50 0 Z"
    (UI / "sparkle.svg").write_text(svg(100, 100, f'<path d="{star}" fill="#000"/>'))


# ---------------------------------------------------------------- frame contour
# "Eurotrash" rococo frame outline, as mask pieces the CSS lays around a box:
# four solid scrolled corners, bead-moulded edge runs between them, and a shell crest
# at the top and bottom centre. All drawn in the top-left orientation and
# mirrored. The frame body is inset 22% of the corner size; corners, crests
# and the bead rows stand proud of it.
CORNER = ("M100 22 H80 C80 10 70 4 60 6 C50 8 50 20 42 20 C36 20 36 4 22 2 "
          "C8 0 0 8 2 22 C4 36 20 36 20 42 C20 50 8 50 6 60 C4 70 10 80 22 80 V100 H100 Z")
MIRROR = {"tl": "", "tr": "translate(100 0) scale(-1 1)",
          "bl": "translate(0 100) scale(1 -1)", "br": "translate(100 100) scale(-1 -1)"}


def scallops(n, length=200, depth=24):
    """A bead moulding: a row of small rounded beads standing on the edge (base at y=depth)."""
    w = length / n
    d = f"M0 {depth}"
    for i in range(n):
        x0, x1 = i * w, (i + 1) * w
        d += f" C{x0 + w * .05:.1f} 12 {x1 - w * .05:.1f} 12 {x1:.1f} {depth}"
    return d + " Z"


CREST = ("M0 50 C30 50 40 34 56 30 C62 14 70 4 80 2 C90 4 98 14 104 30 "
         "C120 34 130 50 160 50 V54 H0 Z")


def write_frame_contour():
    for k, t in MIRROR.items():
        (UI / f"frame-corner-{k}.svg").write_text(
            svg(100, 100, f'<path d="{CORNER}" fill="#000" fill-rule="evenodd" transform="{t}"/>'))
    edge = scallops(16)
    (UI / "frame-edge-top.svg").write_text(svg(200, 24, f'<path d="{edge}" fill="#000"/>').replace(
        "<svg ", '<svg preserveAspectRatio="none" '))
    (UI / "frame-edge-bottom.svg").write_text(svg(200, 24, f'<path d="{edge}" fill="#000" transform="translate(0 24) scale(1 -1)"/>').replace(
        "<svg ", '<svg preserveAspectRatio="none" '))
    (UI / "frame-edge-left.svg").write_text(svg(24, 200, f'<path d="{edge}" fill="#000" transform="matrix(0 1 1 0 0 0)"/>').replace(
        "<svg ", '<svg preserveAspectRatio="none" '))
    (UI / "frame-edge-right.svg").write_text(svg(24, 200, f'<path d="{edge}" fill="#000" transform="matrix(0 1 -1 0 24 0)"/>').replace(
        "<svg ", '<svg preserveAspectRatio="none" '))
    (UI / "frame-crest-top.svg").write_text(svg(160, 54, f'<path d="{CREST}" fill="#000" fill-rule="evenodd"/>'))
    (UI / "frame-crest-bottom.svg").write_text(svg(160, 54, f'<path d="{CREST}" fill="#000" fill-rule="evenodd" transform="translate(0 54) scale(1 -1)"/>'))


# ---------------------------------------------------------------- carousel arrows
# A nouveau arrow cartouche pointing right: a swelling teardrop body with a
# whiplash tail curl and a lancet point. The "prev" button is the same art
# mirrored in CSS. Mask + inked line layer, like the nav buttons.
ARROW = ("M10 40 C10 24 22 14 38 16 C50 17 58 10 68 6 C74 4 78 8 82 12 "
         "L118 40 L82 68 C78 72 74 76 68 74 C58 70 50 63 38 64 C22 66 10 56 10 40 Z")


def write_arrows():
    (UI / "arrow-mask.svg").write_text(svg(128, 80, f'<path d="{ARROW}" fill="#000"/>'))
    line = (f'<path d="{ARROW}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="{ARROW}" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linejoin="round" transform="translate(5 3) scale(.92 .92)"/>'
            # whiplash tail curl
            f'<path d="M24 40 C24 32 32 28 38 32 C43 35 41 43 35 43 C31 43 30 39 33 37" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
            # shaft and barb
            f'<path d="M48 40 H98 M88 31 L100 40 L88 49" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M48 40 H98 M88 31 L100 40 L88 49" fill="none" stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="66" cy="18" r="2.6" fill="{GOLD}"/><circle cx="66" cy="62" r="2.6" fill="{GOLD}"/>')
    (UI / "arrow-line.svg").write_text(svg(128, 80, line))


if __name__ == "__main__":
    UI.mkdir(parents=True, exist_ok=True)
    write_buttons()
    write_bottles()
    write_misc()
    write_frame_contour()
    write_arrows()
    for p in sorted(UI.iterdir()):
        print(p.name)
