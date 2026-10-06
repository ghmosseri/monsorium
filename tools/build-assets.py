#!/usr/bin/env python3
"""Build the web assets used by index.html from the raw upload folders.

    python3 tools/build-assets.py

Reads   trashets/  ovilats/  psychetitlefont/  psychesubfont/  psychebodyfont/
Reads   artworks/<section>/*.jpg  — the real pieces
Writes  assets/img/overlays/   corner overlays, gradient-mapped to the palette
        assets/img/textures/   ovilats textures, gradient-mapped (button fills)
        assets/img/art/        artworks and stand-ins (original colours, resized)
        assets/fonts/          woff2 subsets of the watermark-free fonts

Needs Pillow, numpy and fontTools (with brotli for woff2).
Only the seven palette colours are used for every recolouring.
"""
from pathlib import Path

import numpy as np
from PIL import Image
from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

INK, GOLD, PLUM, LEAF, LIME, ROSE, ABYSS = (
    "#180724", "#FFD06B", "#942C5B", "#62BA52", "#87E627", "#E69393", "#0B0236")

# Gradient maps: luminance (dark -> light) runs through these stops.
MAPS = {
    "bloom": [INK, PLUM, ROSE, GOLD],          # warm, for most overlays
    "venom": [ABYSS, LEAF, LIME, GOLD],        # acid, for contrast spots
    "bruise": [ABYSS, PLUM, ROSE, LIME],       # the eye-strainer
    "candy": [PLUM, ROSE, GOLD, LIME],         # light, so ink text sits on it
    "moss": [LEAF, LIME, GOLD, ROSE],          # light, green-led
}


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def gradient_map(img, stops, contrast=1.0):
    """Recolour an RGBA image by mapping its luminance onto palette stops."""
    a = np.asarray(img.convert("RGBA"), dtype=np.float32)
    lum = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114) / 255
    lum = np.clip((lum - .5) * contrast + .5, 0, 1)
    cols = [hex_rgb(s) for s in stops]
    pos = lum * (len(cols) - 1)
    idx = np.clip(pos.astype(int), 0, len(cols) - 2)
    t = (pos - idx)[..., None]
    lo = np.stack(cols)[idx]
    hi = np.stack(cols)[idx + 1]
    rgb = lo + (hi - lo) * t
    out = np.dstack([rgb, a[..., 3:4]]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def key_white(img):
    """Turn a white page into transparency (for the nouveau frame scans)."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    whiteness = a.min(axis=2)               # near-white -> high
    alpha = np.clip((250 - whiteness) / 70, 0, 1) * 255
    return Image.fromarray(np.dstack([a, alpha]).astype(np.uint8), "RGBA")


def fit(img, max_side):
    img = img.copy()
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    return img


def save_webp(img, path, quality=82):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=quality, method=6)
    print(f"  {path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")


def build_overlays():
    print("overlays")
    src = ROOT / "trashets"
    jobs = {
        "red-cyber-asset": ("bloom", "venom"),
        "magenta-cyber-asset": ("venom", "bloom"),
        "dark-blue-trash": ("bloom", "bruise"),
        "magenta_dark-blue_assets-combined": ("bloom", "venom"),
        "mary-hot_pink-overlay": ("bloom", "bruise"),
        "mary-bleeding-overlay": ("bloom", "venom"),
        "tiger-orchid": ("venom", "bloom"),
    }
    for name, maps in jobs.items():
        img = fit(Image.open(src / f"{name}.png"), 900)
        for m in maps:
            save_webp(gradient_map(img, MAPS[m], 1.15), OUT / "img/overlays" / f"{name}--{m}.webp")
    for name in ("blank-nouveau-frame", "black-nouveau-frame-with-pic"):
        img = key_white(fit(Image.open(src / f"{name}.png"), 1000))
        bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        img = img.crop(bbox)
        for m in ("bloom", "venom"):
            save_webp(gradient_map(img, MAPS[m], 1.1), OUT / "img/overlays" / f"{name}--{m}.webp")


def build_textures():
    print("textures")
    jobs = {
        "colordots-overlay": "candy",
        "mintbaroque-overlay": "moss",
        "pinkreptile-overlay": "candy",
        "redtiger-overlay": "candy",
        "starleopard-overlay": "moss",
    }
    for name, m in jobs.items():
        img = fit(Image.open(ROOT / "ovilats" / f"{name}.jpg"), 420)
        save_webp(gradient_map(img, MAPS[m], 1.05).convert("RGB"), OUT / "img/textures" / f"{name}--{m}.webp", 74)


# Stand-ins still holding a slot until the real pieces arrive.
STAND_INS = ["ovilats/redtiger-overlay.jpg", "ovilats/starleopard-overlay.jpg"]


def build_art():
    print("art")
    # Real artworks: artworks/<section>/*.jpg, original colours, never recoloured.
    for p in sorted((ROOT / "artworks").glob("*/*.jpg")):
        save_webp(fit(Image.open(p).convert("RGB"), 1280), OUT / "img/art" / f"{p.stem}.webp", 86)
    for p in STAND_INS:
        save_webp(fit(Image.open(ROOT / p).convert("RGB"), 1200), OUT / "img/art" / f"{Path(p).stem}.webp", 80)


# Watermark-free fonts only. The 177Studio demos (Biological Crossroads,
# Certain Reasons, Maritime Network) and Stinger Wide Trial swap letters,
# digits and punctuation for "TRIAL FONT" stamps, so they are not shipped.
FONTS = {
    "psychetitlefont/Slowji DEMO.ttf": "slowji",
    "psychetitlefont/Slowji 3D DEMO.otf": "slowji-3d",
    "psychesubfont/HempaSans-BlackItalic.ttf": "hempa-sans-black-italic",
    "psychesubfont/HempaSans-Light.ttf": "hempa-sans-light",
    "psychesubfont/CheyenneSans[wght].ttf": "cheyenne-sans-var",
    "psychesubfont/CheyenneSans-Italic[wght].ttf": "cheyenne-sans-var-italic",
    "psychebodyfont/BROKUETSSANSDEMO.otf": "brokuets-sans",
    "psychebodyfont/Optician-Sans.otf": "optician-sans",
}
# Latin, Latin-1, Latin Extended-A and punctuation: enough for the page in
# English and for most machine translations into Latin-script languages.
UNICODES = "U+0000-00FF,U+0100-017F,U+2010-2027,U+2030-205E,U+20AC,U+2122,U+2190-2193,U+2605-2606,U+2736"


def build_fonts(extra=()):
    print("fonts")
    (OUT / "fonts").mkdir(parents=True, exist_ok=True)
    pairs = [(ROOT / k, v) for k, v in FONTS.items()] + list(extra)
    for src, name in pairs:
        dst = OUT / "fonts" / f"{name}.woff2"
        subset.main([str(src), f"--unicodes={UNICODES}", "--flavor=woff2",
                     "--layout-features=*", "--no-hinting", f"--output-file={dst}"])
        print(f"  {dst.relative_to(ROOT)}  {dst.stat().st_size // 1024} KB")


if __name__ == "__main__":
    import sys
    # Optional: extra OFL fonts as path=name pairs, e.g. Shrikhand.ttf=shrikhand
    extra = [(Path(a.split("=")[0]), a.split("=")[1]) for a in sys.argv[1:]]
    build_overlays()
    build_textures()
    build_art()
    build_fonts(extra)
