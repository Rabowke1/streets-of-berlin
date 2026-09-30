"""Gemeinsame Hilfsfunktionen fuer den prozeduralen Art-Generator.

Alle Grafiken werden mit Supersampling (SS) gerendert und danach
heruntergerechnet, damit die Kanten weich wie handgezeichnet wirken.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

SS = 3  # Supersampling-Faktor
# Ausgabe-Aufloesung: Pixel pro Unreal-Unit. 2 = scharf bis 4K (Sprites bekommen PixelsPerUnrealUnit=2).
RES = int(os.environ.get("SOB_RES", "2"))
OUTLINE = (22, 16, 28, 255)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "Art", "Generated")

_FONT_CANDIDATES = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "condensed": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialnb.ttf",
    ],
}


def font(size, kind="bold"):
    for path in _FONT_CANDIDATES.get(kind, []) + _FONT_CANDIDATES["bold"]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def shade(color, f):
    """Farbe abdunkeln (f<1) oder aufhellen (f>1)."""
    r, g, b = color[:3]
    a = color[3] if len(color) > 3 else 255
    if f <= 1.0:
        return (int(r * f), int(g * f), int(b * f), a)
    k = f - 1.0
    return (int(r + (255 - r) * k), int(g + (255 - g) * k), int(b + (255 - b) * k), a)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def rgba(c):
    return c if len(c) == 4 else (c[0], c[1], c[2], 255)


def rot(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def norm(v):
    l = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / l, v[1] / l)


def lerp(a, b, t):
    return a + (b - a) * t


def downsample(img, factor=SS):
    w, h = img.size
    return img.resize((w // factor, h // factor), Image.LANCZOS)


def draw_inflated(draw, pts, r, fill):
    """Zeichnet ein Polygon (oder Kapsel/Kreis), das um r aufgeblaeht ist."""
    r = max(r, 0.5)
    if len(pts) >= 3:
        draw.polygon(pts, fill=fill)
    n = len(pts)
    if n >= 2:
        segs = [(pts[i], pts[(i + 1) % n]) for i in range(n if n >= 3 else 1)]
        for a, b in segs:
            draw.line([a, b], fill=fill, width=max(1, int(round(2 * r))))
    for p in pts:
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def star_points(cx, cy, r_out, r_in, n, rot_deg=0.0, jitter=0.0, rng=None):
    rng = rng or random.Random(0)
    pts = []
    for i in range(n * 2):
        ang = math.radians(rot_deg + i * 180.0 / n)
        rr = r_out if i % 2 == 0 else r_in
        rr *= 1.0 + (rng.uniform(-jitter, jitter) if jitter else 0.0)
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    return pts


def save(img, *parts):
    path = os.path.join(OUT_DIR, *parts)
    ensure_dir(os.path.dirname(path))
    img.save(path, optimize=True)
    return path
