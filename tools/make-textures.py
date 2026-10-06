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


def blur(a, r):
    """Gaussian blur in the frequency domain: wraps at the edges, so tiles stay seamless."""
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * r) ** 2 * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def light(hgt, depth, sun=(-.55, -.65, .52), gloss=48):
    """Real surface normals from a heightmap -> diffuse + Blinn-Phong specular."""
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * depth
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * depth
    n = np.dstack([-gx, -gy, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array(sun, np.float32); L /= np.linalg.norm(L)
    H = L + np.array([0, 0, 1], np.float32); H /= np.linalg.norm(H)
    diff = np.clip(n @ L, 0, 1)
    spec = np.clip(n @ H, 0, 1) ** gloss
    return diff, spec


def clay(name, stops, glints, w=640, h=640):
    """Moulded, embossed glitter-clay — the picture-frame surface.

    Height = swollen lumps + crusty ridged noise + fine pitting, so the
    relief carries detail at three scales. Crevices are darkened with a
    cavity (ambient-occlusion) pass; ridges catch tight wet highlights."""
    lumps = np.sqrt(noise(w, h, scales=(24, 48, 96, 160), weights=(.4, 1, .9, .5)))
    r = noise(w, h, scales=(8, 16, 32), weights=(.5, 1, .6))
    ridges = (1 - np.abs(r * 2 - 1)) ** 3            # crusty, worm-like folds
    r2 = noise(w, h, scales=(4, 8), weights=(1, .6))
    crumbs = (1 - np.abs(r2 * 2 - 1)) ** 4           # small crumbs and pits
    pits = (rng.random((h, w)) < .004).astype(np.float32)
    pits = blur(pits, 1.2) * 6
    hgt = lumps * 1.6 + ridges * .4 + crumbs * .18 - pits * .25
    hgt = blur(hgt, .7)
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())

    diff, spec = light(hgt, depth=40, gloss=22)
    cavity = np.clip((blur(hgt, 6) - hgt) * 5, 0, 1)   # high where sunk below surroundings
    rim = np.clip((hgt - blur(hgt, 3)) * 9, 0, 1)      # raised edges

    base = ramp(.25 + hgt * .55 + rim * .25, stops[:-1])
    shade_ = (.42 + diff * .78)[..., None]
    img = base * shade_
    img = img * (1 - cavity[..., None] * .75) + rgb(INK) * (cavity[..., None] * .75)
    hi = rgb(stops[-1])
    s = np.clip(spec * 1.9 + rim * diff * .3, 0, .95)[..., None]
    img = img * (1 - s) + hi * s
    # glitter sits on the surface: brighter on lit faces
    img = glitter(img, .02, glints, 1, .55)
    img = glitter(img, .004, glints + [GOLD], 1, 1)
    img = glitter(img, .0008, [GOLD], 2, .9)
    save(img, f"clay-{name}", 84)


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
    clay("gilt", [INK, PLUM, GOLD, GOLD, GOLD], [ROSE, LIME, GOLD])
    carved("bloom", "magenta-cyber-asset.png", [INK, PLUM, ROSE, GOLD])
    carved("dusk", "dark-blue-trash.png", [ABYSS, PLUM, ROSE, LIME])
    stars("abyss", [ABYSS, ABYSS, INK, PLUM])
    stars("ink", [INK, INK, ABYSS, LEAF])
    glitter_field("bloom", [PLUM, ROSE, GOLD])
    glitter_field("venom", [LEAF, LIME, GOLD])
