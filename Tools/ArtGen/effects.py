"""Effekte, Props, Pickups und UI-Grafiken."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from common import OUTLINE, RES, draw_inflated, downsample, font, shade, star_points
from common import SS as _BASE_SS

# Intern wird mit Supersampling * Ausgabe-Aufloesung gezeichnet; downsample() teilt nur durch das
# Supersampling -> Ergebnis hat (Welt-Groesse * RES) Pixel.
SS = _BASE_SS * RES


def _canvas(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


# ---------------------------------------------------------------------------
# Effekte
# ---------------------------------------------------------------------------
def hit_spark(frames=4, size=128, big=False, seed=1):
    rng = random.Random(seed)
    out = []
    core = (255, 255, 235, 255)
    mid = (255, 220, 70, 255) if not big else (255, 150, 40, 255)
    edge = (255, 120, 30, 255) if not big else (230, 40, 40, 255)
    for i in range(frames):
        img, d = _canvas(size, size)
        c = size * SS / 2
        t = (i + 1) / frames
        grow = 0.45 + 0.55 * math.sin(min(1.0, t * 1.3) * math.pi / 2)
        fade = 1.0 if i < frames - 1 else 0.55
        R = size * SS * 0.48 * grow
        n = 9 if big else 7
        rr = rng.uniform(0, 30)
        for col, k, ki in ((edge, 1.0, 0.36), (mid, 0.78, 0.30), (core, 0.5, 0.22)):
            pts = star_points(c, c, R * k, R * ki, n, rot_deg=rr, jitter=0.18, rng=rng)
            col = (col[0], col[1], col[2], int(255 * fade))
            d.polygon(pts, fill=col)
        if i >= frames - 2:
            # Loch in der Mitte -> Ring zerfaellt
            hole = R * (0.25 if i == frames - 2 else 0.5)
            d.ellipse([c - hole, c - hole, c + hole, c + hole], fill=(0, 0, 0, 0))
        # Speed lines
        for _ in range(6 if big else 4):
            a = rng.uniform(0, 2 * math.pi)
            r0, r1 = R * 0.7, R * (1.05 + 0.15 * t)
            d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * r1, c + math.sin(a) * r1)],
                   fill=(255, 255, 255, int(220 * fade)), width=int(3 * SS))
        out.append(downsample(img))
    return out


def dust(frames=4, w=160, h=80, seed=3):
    rng = random.Random(seed)
    puffs = [(rng.uniform(-0.35, 0.35), rng.uniform(0.0, 0.25), rng.uniform(0.10, 0.2)) for _ in range(7)]
    out = []
    for i in range(frames):
        img, d = _canvas(w, h)
        t = (i + 1) / frames
        alpha = int(220 * (1.0 - t * 0.75))
        for px, py, pr in puffs:
            x = (0.5 + px * (0.6 + t)) * w * SS
            y = (0.85 - py - t * 0.25) * h * SS
            r = pr * w * SS * (0.6 + t * 0.8)
            d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=(205, 196, 186, alpha))
            d.ellipse([x - r * 0.6, y - r * 0.7, x + r * 0.4, y + r * 0.1], fill=(235, 230, 222, alpha))
        out.append(downsample(img))
    return out


def shadow(w=110, h=30):
    w, h = w * RES, h * RES
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2 * RES, 2 * RES, w - 2 * RES, h - 2 * RES], fill=(0, 0, 0, 120))
    return img.filter(ImageFilter.GaussianBlur(2 * RES))


def special_ring(frames=4, size=256):
    out = []
    for i in range(frames):
        img, d = _canvas(size, size)
        c = size * SS / 2
        t = (i + 1) / frames
        R = size * SS * 0.46 * (0.4 + 0.6 * t)
        a = int(230 * (1.0 - t * 0.7))
        w = int(SS * (16 - 10 * t))
        d.ellipse([c - R, c - R * 0.45, c + R, c + R * 0.45], outline=(120, 220, 255, a), width=w)
        d.ellipse([c - R * 0.9, c - R * 0.4, c + R * 0.9, c + R * 0.4], outline=(255, 255, 255, a), width=max(2, w // 3))
        out.append(downsample(img))
    return out


# ---------------------------------------------------------------------------
# Props (zerstoerbar)
# ---------------------------------------------------------------------------
def _outlined(d, pts, r, fill):
    draw_inflated(d, pts, r + 2.6 * SS, OUTLINE)
    draw_inflated(d, pts, r, fill)


def trash_can(broken=False):
    """Berliner Muelltonne (grau mit oranger Kante)."""
    W, H = 110, 140
    img, d = _canvas(W, H)
    S = SS
    body = (96, 104, 112, 255)
    orange = (236, 110, 30, 255)
    if not broken:
        pts = [(18 * S, 40 * S), (92 * S, 40 * S), (86 * S, 132 * S), (24 * S, 132 * S)]
        _outlined(d, pts, 4 * S, body)
        for x in (34, 55, 76):
            d.line([(x * S, 50 * S), ((x + (55 - x) * 0.08) * S, 124 * S)], fill=shade(body, 0.75), width=5 * S)
        d.polygon([(64 * S, 44 * S), (88 * S, 44 * S), (84 * S, 128 * S), (72 * S, 128 * S)], fill=shade(body, 0.8))
        lid = [(12 * S, 30 * S), (98 * S, 30 * S), (96 * S, 44 * S), (14 * S, 44 * S)]
        _outlined(d, lid, 3 * S, orange)
        d.line([(20 * S, 34 * S), (70 * S, 34 * S)], fill=shade(orange, 1.35), width=3 * S)
        _outlined(d, [(46 * S, 22 * S), (64 * S, 22 * S)], 4 * S, shade(orange, 0.8))
    else:
        pts = [(10 * S, 80 * S), (78 * S, 66 * S), (96 * S, 128 * S), (22 * S, 134 * S)]
        _outlined(d, pts, 4 * S, shade(body, 0.9))
        d.polygon([(26 * S, 86 * S), (60 * S, 100 * S), (40 * S, 124 * S)], fill=shade(body, 0.6))
        lid = [(62 * S, 120 * S), (104 * S, 108 * S), (106 * S, 118 * S), (64 * S, 132 * S)]
        _outlined(d, lid, 3 * S, orange)
        rng = random.Random(4)
        for _ in range(7):
            x, y = rng.uniform(10, 100) * S, rng.uniform(118, 134) * S
            _outlined(d, [(x, y)], rng.uniform(3, 6) * S,
                      rng.choice([(220, 220, 210, 255), (120, 170, 80, 255), (200, 160, 90, 255)]))
    return downsample(img)


def crate(broken=False):
    W, H = 120, 120
    img, d = _canvas(W, H)
    S = SS
    wood = (178, 124, 70, 255)
    if not broken:
        _outlined(d, [(12 * S, 20 * S), (108 * S, 20 * S), (108 * S, 112 * S), (12 * S, 112 * S)], 3 * S, wood)
        for y in (44, 68, 92):
            d.line([(14 * S, y * S), (106 * S, y * S)], fill=shade(wood, 0.6), width=3 * S)
        d.line([(16 * S, 24 * S), (104 * S, 108 * S)], fill=shade(wood, 0.75), width=9 * S)
        d.line([(16 * S, 24 * S), (104 * S, 108 * S)], fill=shade(wood, 1.15), width=5 * S)
        f = font(15 * S)
        d.text((60 * S, 64 * S), "OBST", font=f, fill=(90, 40, 20, 230), anchor="mm")
    else:
        rng = random.Random(8)
        for i in range(6):
            x = rng.uniform(15, 95) * S
            y = rng.uniform(92, 110) * S
            a = rng.uniform(-0.5, 0.5)
            L = rng.uniform(30, 55) * S
            p0 = (x - math.cos(a) * L / 2, y - math.sin(a) * L / 2)
            p1 = (x + math.cos(a) * L / 2, y + math.sin(a) * L / 2)
            _outlined(d, [p0, p1], 4 * S, shade(wood, rng.uniform(0.8, 1.1)))
    return downsample(img)


# ---------------------------------------------------------------------------
# Pickups
# ---------------------------------------------------------------------------
def doener():
    W, H = 80, 60
    img, d = _canvas(W, H)
    S = SS
    bread = (226, 176, 104, 255)
    _outlined(d, [(8 * S, 34 * S), (72 * S, 26 * S), (70 * S, 46 * S), (12 * S, 52 * S)], 7 * S, bread)
    # Fuellung
    d.ellipse([16 * S, 18 * S, 34 * S, 32 * S], fill=(110, 190, 70, 255))
    d.ellipse([30 * S, 16 * S, 50 * S, 30 * S], fill=(160, 90, 60, 255))
    d.ellipse([46 * S, 14 * S, 64 * S, 28 * S], fill=(220, 60, 50, 255))
    d.ellipse([56 * S, 16 * S, 70 * S, 28 * S], fill=(246, 246, 236, 255))
    d.line([(14 * S, 44 * S), (66 * S, 38 * S)], fill=shade(bread, 0.75), width=3 * S)
    return downsample(img)


def currywurst():
    W, H = 80, 50
    img, d = _canvas(W, H)
    S = SS
    _outlined(d, [(6 * S, 30 * S), (74 * S, 30 * S), (66 * S, 42 * S), (14 * S, 42 * S)], 3 * S,
              (240, 240, 236, 255))
    for x in (16, 30, 44, 58):
        _outlined(d, [(x * S, 26 * S), ((x + 8) * S, 22 * S)], 6 * S, (170, 80, 50, 255))
    d.line([(10 * S, 22 * S), (70 * S, 18 * S)], fill=(200, 40, 30, 255), width=4 * S)
    for x in (20, 36, 52):
        d.ellipse([x * S, 14 * S, (x + 4) * S, 18 * S], fill=(240, 180, 40, 255))
    return downsample(img)


def money():
    W, H = 60, 44
    img, d = _canvas(W, H)
    S = SS
    for i in range(3):
        y = (28 - i * 6) * S
        _outlined(d, [(8 * S, y), (52 * S, y - 2 * S), (52 * S, y + 8 * S), (8 * S, y + 10 * S)], 2 * S,
                  (110, 180, 110, 255))
    d.ellipse([24 * S, 13 * S, 36 * S, 22 * S], fill=(70, 130, 70, 255))
    return downsample(img)


def pipe():
    W, H = 110, 30
    img, d = _canvas(W, H)
    S = SS
    _outlined(d, [(10 * S, 16 * S), (100 * S, 14 * S)], 5 * S, (150, 150, 160, 255))
    d.line([(14 * S, 13 * S), (96 * S, 11 * S)], fill=(220, 220, 230, 255), width=2 * S)
    return downsample(img)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def go_arrow():
    W, H = 200, 110
    img, d = _canvas(W, H)
    S = SS
    f = font(46 * S)
    d.text((70 * S, 55 * S), "GO", font=f, fill=(255, 220, 60, 255), anchor="mm", stroke_width=5 * S,
           stroke_fill=OUTLINE)
    pts = [(128 * S, 30 * S), (190 * S, 55 * S), (128 * S, 80 * S)]
    _outlined(d, pts, 3 * S, (255, 220, 60, 255))
    return downsample(img)


def title_logo():
    W, H = 1100, 300
    img = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f1 = font(150, "condensed")
    f2 = font(90, "condensed")
    d.text((W, 190), "STREETS OF", font=f2, fill=(255, 255, 255, 255), anchor="mm", stroke_width=12,
           stroke_fill=OUTLINE)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((W, 380), "BERLIN", font=font(230, "condensed"), fill=(255, 40, 80, 255), anchor="mm",
            stroke_width=24, stroke_fill=(255, 40, 80, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img = Image.alpha_composite(glow, img)
    d = ImageDraw.Draw(img)
    d.text((W, 380), "BERLIN", font=font(230, "condensed"), fill=(255, 210, 60, 255), anchor="mm",
           stroke_width=14, stroke_fill=OUTLINE)
    d.line([(W - 420, 520), (W + 420, 520)], fill=(255, 40, 80, 255), width=10)
    _ = f1
    return img.resize((W * RES, H * RES), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Waffen (waagerecht, Griff links). WEAPONS[name] = (Breite, Hoehe, Griff-x, Griff-y) in Welt-Units
# ---------------------------------------------------------------------------
WEAPONS = {
    "Pipe": (120, 28, 14, 14),
    "Bat": (130, 32, 14, 16),
    "Knife": (64, 24, 10, 13),
    "Bottle": (70, 30, 12, 15),
    "Golf": (140, 40, 12, 12),
}


def weapon(name):
    W, H, gx, gy = WEAPONS[name]
    img, d = _canvas(W, H)
    S = SS
    if name == "Pipe":
        _outlined(d, [(8 * S, 14 * S), (112 * S, 13 * S)], 5 * S, (140, 144, 156, 255))
        d.line([(12 * S, 11 * S), (108 * S, 10 * S)], fill=(225, 228, 238, 255), width=2 * S)
        _outlined(d, [(104 * S, 13 * S)], 7 * S, (110, 114, 126, 255))
    elif name == "Bat":
        _outlined(d, [(8 * S, 16 * S), (40 * S, 16 * S), (122 * S, 14 * S), (122 * S, 19 * S), (40 * S, 17 * S)],
                  4 * S, (196, 150, 96, 255))
        _outlined(d, [(10 * S, 16 * S), (30 * S, 16 * S)], 5 * S, (50, 40, 36, 255))  # Griffband
        d.line([(44 * S, 13 * S), (118 * S, 11 * S)], fill=(236, 200, 150, 255), width=3 * S)
    elif name == "Knife":
        _outlined(d, [(6 * S, 13 * S), (24 * S, 13 * S)], 5 * S, (40, 36, 40, 255))
        _outlined(d, [(26 * S, 8 * S), (58 * S, 12 * S), (26 * S, 17 * S)], 1.5 * S, (210, 214, 224, 255))
        d.line([(28 * S, 10 * S), (54 * S, 12 * S)], fill=(255, 255, 255, 255), width=1 * S)
    elif name == "Bottle":
        _outlined(d, [(8 * S, 15 * S), (26 * S, 15 * S)], 3.5 * S, (60, 130, 60, 255))
        _outlined(d, [(28 * S, 8 * S), (62 * S, 8 * S), (62 * S, 22 * S), (28 * S, 22 * S)], 4 * S,
                  (60, 140, 64, 255))
        d.rectangle([34 * S, 10 * S, 52 * S, 20 * S], fill=(240, 220, 150, 255))
        d.line([(30 * S, 9 * S), (58 * S, 9 * S)], fill=(170, 230, 160, 255), width=2 * S)
    elif name == "Golf":
        _outlined(d, [(6 * S, 12 * S), (128 * S, 16 * S)], 2.5 * S, (170, 174, 186, 255))
        _outlined(d, [(6 * S, 12 * S), (30 * S, 13 * S)], 4 * S, (30, 30, 34, 255))
        _outlined(d, [(124 * S, 12 * S), (134 * S, 30 * S), (122 * S, 34 * S)], 3 * S, (200, 204, 214, 255))
    return downsample(img)
