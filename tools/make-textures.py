#!/usr/bin/env python3
"""Procedural textures in the palette, after the reference boards:
lumpy glitter-clay frames, carved ornament frames, glitter starfields.

    python3 tools/make-textures.py

Writes assets/img/textures/{clay-*,carved-*,stars-*,glitter-*}.webp
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "textures"
rng = np.random.default_rng(7)

INK, GOLD, PLUM, LEAF, LIME, ROSE, ABYSS = (
    "#180724", "#FFD06B", "#942C5B", "#62BA52", "#87E627", "#E69393", "#0B0236")


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def ramp(t, stops):
    cols = np.stack([rgb(s) for s in stops])
    pos = np.clip(t, 0, 1) * (len(cols) - 1)
    i = np.clip(pos.astype(int), 0, len(cols) - 2)
    f = (pos - i)[..., None]
    return cols[i] + (cols[i + 1] - cols[i]) * f


def noise(w, h, scales=(4, 8, 16, 32, 64), weights=(1, .6, .35, .2, .12), seamless=True):
    """Fractal value noise, tileable (wrap-padded before upscaling)."""
    acc = np.zeros((h, w), np.float32)
    for s, wt in zip(scales, weights):
        gw, gh = max(2, w // s), max(2, h // s)
        g = rng.random((gh, gw)).astype(np.float32)
        if seamless:
            g = np.pad(g, 2, mode="wrap")
            img = Image.fromarray((g * 255).astype(np.uint8)).resize(
                ((gw + 4) * s, (gh + 4) * s), Image.BICUBIC)
            arr = np.asarray(img, np.float32)[2 * s:2 * s + h, 2 * s:2 * s + w] / 255
        else:
            arr = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        acc += arr * wt
    acc -= acc.min()
    return acc / acc.max()


def shade(height, strength=6.0, light=(-1, -1.3)):
    gy, gx = np.gradient(height)
    lx, ly = light
    n = -(gx * lx + gy * ly)
    n = n / (n.std() + 1e-6) * strength / 10   # normalise: relief reads the same at any size
    return np.clip(n, -1, 1)


def glitter(img, density, colors, size=1, alpha=1.0):
    h, w, _ = img.shape
    count = int(w * h * density)
    ys, xs = rng.integers(0, h, count), rng.integers(0, w, count)
    cs = np.stack([rgb(c) for c in colors])[rng.integers(0, len(colors), count)]
    for dy in range(size):
        for dx in range(size):
            yy, xx = (ys + dy) % h, (xs + dx) % w
            img[yy, xx] = img[yy, xx] * (1 - alpha) + cs * alpha
    return img


def star_burst(img, x, y, r, color):
    h, w, _ = img.shape
    c = rgb(color)
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    d = np.abs(xx) * np.abs(yy)
    core = np.exp(-(xx ** 2 + yy ** 2) / (2 * (r / 6) ** 2))
    rays = np.exp(-d / (r * .4)) * np.exp(-(np.abs(xx) + np.abs(yy)) / (r * .5))
    a = np.clip(core + rays, 0, 1)[..., None]
    ys = (np.arange(y - r, y + r + 1) % h)[:, None]
    xs = (np.arange(x - r, x + r + 1) % w)[None, :]
    img[ys, xs] = img[ys, xs] * (1 - a) + c * a


def save(arr, name, q=80):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.webp"
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(p, "WEBP", quality=q, method=6)
    print(f"  {p.relative_to(ROOT)}  {p.stat().st_size // 1024} KB")


def clay(name, stops, glints, w=640, h=640):
    """Lumpy, glossy, glittered clay — the moulded picture-frame surface."""
    hgt = noise(w, h, scales=(6, 12, 24, 48, 96), weights=(.08, .25, .9, 1, .6))
    hgt = np.sqrt(hgt)  # rounded, swollen lumps
    hgt = np.asarray(Image.fromarray((hgt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    lit = shade(hgt, 4.5)
    base = ramp(hgt * .8 + .1, stops[:-1])
    hi = rgb(stops[-1])
    # specular: sharp, wet-looking highlights on the lit faces
    spec = np.clip((lit - .55) * 3.2, 0, .9)[..., None]
    dark = np.clip(-lit, 0, 1)[..., None]
    img = base * (1 - .45 * dark) + rgb(INK) * (.45 * dark)
    img = img * (1 - spec) + hi * spec
    img = glitter(img, .012, glints, 1, .9)
    img = glitter(img, .0015, glints, 2, .8)
    save(img, f"clay-{name}")


def carved(name, src, stops, w=640, h=640):
    """Ornament asset pressed into clay: a carved, embossed frame surface."""
    orn = Image.open(ROOT / "trashets" / src).convert("RGBA")
    orn = orn.crop(orn.getchannel("A").getbbox())
    orn.thumbnail((w // 2, h // 3))
    a = Image.new("L", (w, h), 0)
    for row, y in enumerate(range(0, h, orn.height)):   # brick-tiled ornament
        off = (orn.width // 2) * (row % 2)
        for x in range(-off, w, orn.width):
            a.paste(orn.getchannel("A"), (x, y), orn.getchannel("A"))
    relief = np.asarray(a.filter(ImageFilter.GaussianBlur(2.2)), np.float32) / 255
    hgt = relief * .9 + noise(w, h) * .35
    lit = shade(hgt, 5)
    base = ramp(hgt * .75 + .1, stops[:-1])
    spec = np.clip((lit - .5) * 2.6, 0, .85)[..., None]
    dark = np.clip(-lit, 0, 1)[..., None]
    img = base * (1 - .6 * dark) + rgb(INK) * (.6 * dark)
    img = img * (1 - spec) + rgb(stops[-1]) * spec
    img = glitter(img, .006, [GOLD, ROSE], 1, .7)
    save(img, f"carved-{name}")


def stars(name, ground, w=512, h=512):
    """Tileable night-diorama sky: nebula wash, glitter dust, cross stars."""
    n = noise(w, h, scales=(16, 32, 64, 128), weights=(.3, .6, 1, 1))
    img = ramp(n ** 1.8, ground)
    img = glitter(img, .02, [GOLD, ROSE, LIME, ROSE], 1, .55)
    img = glitter(img, .003, [GOLD, ROSE, LIME], 1, 1)
    for _ in range(9):
        star_burst(img, int(rng.integers(0, w)), int(rng.integers(0, h)), int(rng.integers(8, 18)),
                   [GOLD, ROSE, LIME][int(rng.integers(0, 3))])
    save(img, f"stars-{name}")


def glitter_field(name, stops, w=400, h=400):
    """Dense iridescent glitter, the dusted-diorama-floor texture."""
    n = noise(w, h, scales=(8, 16, 32), weights=(.4, .8, 1))
    img = ramp(n, stops)
    img = glitter(img, .25, [GOLD, ROSE, LIME, PLUM, ABYSS], 1, .5)
    img = glitter(img, .02, [GOLD, LIME], 1, 1)
    save(img, f"glitter-{name}", 76)


if __name__ == "__main__":
    print("textures")
    clay("bloom", [INK, PLUM, ROSE, ROSE, GOLD], [GOLD, LIME, ROSE])
    clay("venom", [ABYSS, LEAF, LIME, GOLD, GOLD], [ROSE, GOLD, ROSE])
    clay("bruise", [ABYSS, PLUM, PLUM, ROSE, ROSE], [LIME, GOLD])
    carved("bloom", "magenta-cyber-asset.png", [INK, PLUM, ROSE, GOLD])
    carved("dusk", "dark-blue-trash.png", [ABYSS, PLUM, ROSE, LIME])
    stars("abyss", [ABYSS, ABYSS, INK, PLUM])
    stars("ink", [INK, INK, ABYSS, LEAF])
    glitter_field("bloom", [PLUM, ROSE, GOLD])
    glitter_field("venom", [LEAF, LIME, GOLD])
