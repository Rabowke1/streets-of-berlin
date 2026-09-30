"""Hintergruende fuer Stage 4: Strassenbahn-Nachtfahrt (Haltestelle zwischen Plattenbauten -> Betriebshof).

Gleiche Masse wie die anderen Stages: Wand-Kacheln 2048x560 (Unterkante = Boden-Oberkante),
Boden-Kacheln 1024x420 (Tiefe d liegt bei Bild-y = 300 - d), Himmel 2400x700, Vordergrund 200x900.

Die beiden Gleise liegen genau auf den Spuren, durch die im Bosskampf die Tram faehrt
(TRAM_LANES, gleiche Werte wie in web/js/game.js).
"""
import random

from backgrounds2 import NEON_CYAN, NEON_PINK, NEON_YELLOW, WARM, _night_sky, _skyline, _tv_tower
from bgkit import LINE, Canvas, glow_spot, light_cone, neon_sign, poster_wall, tags
from common import shade

# Gleismitte (Tiefe) der hinteren und vorderen Spur
TRAM_LANES = (170, 70)
TRAM_YELLOW = (246, 200, 40, 255)


def _y(depth):
    return 300 - depth


def sky_tram():
    W, H = 2400, 700
    c = Canvas(W, H, k=2)
    _night_sky(c, W, H, seed=404, mid=(40, 34, 96, 255), bottom=(170, 80, 90, 255))
    _skyline(c, W, H - 40, 120, 320, (30, 26, 58, 255), 0.35, 12,
             [(255, 214, 140, 255), (255, 190, 110, 255), (170, 200, 255, 255)])
    _tv_tower(c, 1700, H - 40, 0.8)
    _skyline(c, W, H, 60, 200, (20, 18, 40, 255), 0.25, 13, [(255, 200, 130, 255), (140, 180, 255, 255)])
    return c.result()


def _catenary(c, W, y, sag=14, masts=()):
    """Oberleitung: Tragseil + Fahrdraht mit Haengern."""
    for x in masts:
        c.rect(x - 7, y - 60, x + 7, 560, (40, 44, 52, 255))
        c.rect(x - 3, y - 60, x + 1, 560, (70, 76, 88, 255))
        c.line([(x, y - 40), (x + 180, y - 6)], (40, 44, 52, 255), 4)
    for seg in range(0, W, 256):
        pts = [(seg + t * 256 / 8, y - sag * 4 * (t / 8) * (1 - t / 8)) for t in range(9)]
        c.line(pts, (24, 24, 30, 255), 2.2)
        for px, py in pts[1:-1:2]:
            c.line([(px, py), (px, y + 12)], (24, 24, 30, 255), 1.0)
    c.line([(0, y + 12), (W, y + 12)], (20, 20, 26, 255), 2.6)


def _plattenbau(c, x0, x1, top, rng):
    """DDR-Plattenbau mit Fensterraster, teils erleuchtet."""
    c.outlined_rect(x0, top, x1, 400, (118, 112, 126, 255), 2)
    for yy in range(int(top) + 22, 390, 44):
        c.rect(x0 + 2, yy - 2, x1 - 2, yy, (96, 90, 104, 255))
        for xx in range(int(x0) + 18, int(x1) - 30, 52):
            lit = rng.random() < 0.38
            col0 = rng.choice([(255, 214, 150, 255), (255, 190, 120, 255), (150, 190, 255, 255)]) if lit else (36, 40, 66, 255)
            c.outlined_rect(xx, yy + 8, xx + 30, yy + 34, col0, 1.5)
            if lit:
                c.emissive_rect(xx + 1, yy + 9, xx + 29, yy + 33, 200)
        # Balkonbruestungen in Farbe
        if rng.random() < 0.5:
            bx = x0 + rng.randint(1, max(1, int((x1 - x0) / 52) - 2)) * 52 + 10
            c.rect(bx, yy + 26, bx + 46, yy + 40, rng.choice([(190, 90, 60, 255), (60, 130, 150, 255), (200, 170, 70, 255)]))


def _tram_stop(c, x, rng):
    """Haltestelle mit Wartehaeuschen, Haltestellenschild und Fahrgastanzeiger."""
    c.outlined_rect(x, 380, x + 300, 396, (70, 76, 90, 255), 2)                 # Dach
    for px in (x + 10, x + 290):
        c.rect(px - 4, 396, px + 4, 560, (70, 76, 90, 255))
    c.rect(x + 14, 400, x + 286, 520, (120, 170, 200, 70))                       # Glas
    c.outlined_rect(x + 40, 410, x + 140, 490, (40, 40, 44, 255), 2)             # Werbevitrine
    c.vgrad(x + 44, 414, x + 136, 486, (255, 120, 170, 255), (120, 40, 140, 255))
    c.emissive_rect(x + 44, 414, x + 136, 486, 200)
    c.text(x + 90, 450, "KIEZ", 22, (255, 255, 255, 255))
    # Fahrgastanzeiger (LED)
    c.outlined_rect(x + 160, 404, x + 280, 440, (20, 20, 22, 255), 2)
    c.text(x + 220, 414, "M10  Hbf", 13, (255, 170, 40, 255), kind="condensed")
    c.text(x + 220, 430, "2 min", 13, (255, 170, 40, 255), kind="condensed")
    c.emissive_rect(x + 162, 406, x + 278, 438, 170)
    # Haltestellenschild (gruener Kreis mit gelbem H)
    c.rect(x + 330, 330, x + 336, 560, (80, 86, 96, 255))
    c.circle(x + 333, 318, 26, LINE)
    c.circle(x + 333, 318, 23, (40, 150, 70, 255))
    c.text(x + 333, 318, "H", 30, (250, 214, 40, 255), kind="bold")
    c.outlined_rect(x + 290, 346, x + 376, 368, (250, 250, 246, 255), 1.5)
    c.text(x + 333, 357, "Warschauer Str.", 9, (30, 30, 40, 255), kind="condensed")


def tramstop_tile(variant):
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(91 + variant)
    c.rect(0, 0, W, H, (0, 0, 0, 0))
    _plattenbau(c, 0, 900, 60 + variant * 30, rng)
    _plattenbau(c, 980, 2048, 90 - variant * 20, rng)
    # Erdgeschoss: Spaeti, Imbiss, Rolllaeden
    c.rect(0, 400, W, H, (70, 64, 76, 255))
    c.texture(0, 400, W, H, amount=8, grain=4, seed=variant)
    shops = [("SPÄTKAUF", NEON_CYAN), ("CURRY", NEON_YELLOW)] if variant == 0 else [("PHO", NEON_PINK), ("BAR", NEON_CYAN)]
    for i, (name, col) in enumerate(shops):
        sx = 80 + i * 1020
        c.outlined_rect(sx, 440, sx + 360, H, (40, 36, 44, 255), 2)
        c.vgrad(sx + 6, 446, sx + 354, H, (255, 214, 150, 255), (200, 120, 70, 255))
        c.emissive_rect(sx + 6, 446, sx + 354, H, 200)
        neon_sign(c, sx + 180, 420, name, 30, col)
    for i in range(3):
        rx = 520 + i * 130
        c.outlined_rect(rx, 450, rx + 110, H, (110, 110, 118, 255), 2)
        for yy in range(456, H, 8):
            c.rect(rx + 3, yy, rx + 107, yy + 2, (90, 90, 98, 255))
    tags(c, 520, 900, 450, 540, rng, 18)
    poster_wall(c, 930, 440, 1090, 540, rng, 2)
    _tram_stop(c, 1560 if variant == 0 else 1520, rng)
    c.grade((60, 50, 130), 0.6, (70, 50, 110), 0.5)
    c.flush()
    _catenary(c, W, 250, masts=(200, 1224) if variant == 0 else (700, 1724))
    glow_spot(c, 400, 240, 70, WARM)
    glow_spot(c, 1500, 240, 70, WARM)
    return c.result()


def _rails(c, W, depth, rng, groove=(36, 34, 40, 255)):
    y = _y(depth)
    for off in (-14, 14):
        yy = y + off
        c.rect(0, yy - 3, W, yy + 3, groove)
        c.rect(0, yy - 3, W, yy - 1, (180, 180, 190, 255))       # blanke Schienenkante
    c.light((0, y - 30, W, y + 30), lambda L: L.rect(0, y - 16, W, y - 12, (200, 200, 255, 60)), blur=4, strength=0.6)


def floor_tram():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(404)
    c.vgrad(0, 0, W, H, (54, 52, 62, 255), (40, 38, 46, 255))
    c.texture(0, 0, W, H, amount=12, grain=3, seed=2)
    # Gleisbereich mit Kopfsteinpflaster
    for depth in TRAM_LANES:
        y = _y(depth)
        c.rect(0, y - 32, W, y + 32, (70, 66, 74, 255))
        for yy in range(int(y - 30), int(y + 30), 12):
            for xx in range(-(yy % 2) * 8, W, 18):
                v = rng.randint(78, 104)
                c.ellipse(xx + 1, yy + 1, xx + 16, yy + 11, (v, v - 4, v + 4, 255))
        _rails(c, W, depth, rng)
    # Bordstein oben, Markierungen
    c.rect(0, 0, W, 18, (120, 116, 126, 255))
    for x in range(0, W, 128):
        c.rect(x + 20, _y(120) - 3, x + 84, _y(120) + 3, (220, 214, 180, 200))
    # Pfuetzen mit Spiegelung
    for (px, py, pw, col) in ((300, 250, 160, NEON_CYAN), (780, 360, 200, NEON_YELLOW)):
        c.ellipse(px - pw / 2, py - 14, px + pw / 2, py + 14, (28, 26, 44, 255))
        c.light((px - pw / 2, py - 18, px + pw / 2, py + 18),
                lambda L, px=px, py=py, pw=pw, col=col: L.ellipse(px - pw * 0.3, py - 10, px + pw * 0.1, py + 10,
                                                                  (*col[:3], 150)), blur=7, strength=1.2)
    c.grade((80, 60, 130), 0.45, (40, 36, 80), 0.6)
    c.flush()
    return c.result()


def depot_tile():
    """Betriebshof: Backsteinhalle mit offenen Toren, drinnen abgestellte Bahnen."""
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(505)
    c.rect(0, 0, W, H, (96, 56, 48, 255))
    for yy in range(0, H, 14):
        off = (yy // 14 % 2) * 16
        for xx in range(-off, W, 32):
            v = rng.randint(-10, 10)
            c.rect(xx + 1, yy + 1, xx + 31, yy + 13, (116 + v, 64 + v, 52 + v, 255))
    c.texture(0, 0, W, H, amount=10, grain=4, seed=9)
    c.outlined_rect(0, 40, W, 80, (80, 44, 38, 255), 2)
    c.text(1024, 60, "BETRIEBSHOF", 34, (236, 220, 190, 255), kind="bold")
    for i in range(4):
        gx = 60 + i * 500
        # Rundbogentor
        c.outlined_rect(gx, 180, gx + 400, H, (30, 26, 34, 255), 3)
        c.ellipse(gx, 110, gx + 400, 250, (30, 26, 34, 255))
        c.vgrad(gx + 8, 190, gx + 392, H, (60, 56, 80, 255), (24, 22, 36, 255))
        # abgestellte Bahn in der Halle
        if i % 2 == 0:
            c.outlined_rect(gx + 30, 330, gx + 370, 520, shade(TRAM_YELLOW, 0.8), 2)
            for k in range(4):
                wx = gx + 50 + k * 80
                c.outlined_rect(wx, 360, wx + 56, 420, (255, 230, 170, 255), 1.5)
                c.emissive_rect(wx + 2, 362, wx + 54, 418, 150)
        light_cone(c, gx + 200, 200, 40, 300, 330, (255, 220, 160, 90))
        glow_spot(c, gx + 200, 200, 40, WARM)
    c.grade((60, 50, 120), 0.55, (70, 50, 110), 0.5)
    c.flush()
    _catenary(c, W, 290, masts=(30, 1030))
    return c.result()


def floor_depot():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(606)
    c.vgrad(0, 0, W, H, (74, 72, 80, 255), (52, 50, 58, 255))
    c.texture(0, 0, W, H, amount=10, grain=3, seed=4)
    for x in range(0, W, 256):
        c.line([(x, 0), (x + 40, H)], (60, 58, 66, 255), 2)
    for depth in TRAM_LANES:
        _rails(c, W, depth, rng)
    # Warnstreifen am Rand der Gleise
    for depth in TRAM_LANES:
        y = _y(depth) + 36
        for x in range(0, W, 40):
            c.poly([(x, y), (x + 20, y), (x + 30, y + 8), (x + 10, y + 8)], (230, 190, 40, 200))
    c.grade((70, 60, 130), 0.4, (40, 36, 80), 0.55)
    c.flush()
    return c.result()


def mast():
    """Vordergrund: Oberleitungsmast."""
    W, H = 200, 900
    c = Canvas(W, H, k=2)
    c.rect(86, 60, 114, H, (30, 32, 40, 255))
    c.rect(92, 60, 100, H, (60, 64, 76, 255))
    for y in range(120, H, 90):
        c.line([(86, y), (114, y + 40)], (24, 26, 32, 255), 3)
    c.line([(100, 120), (200, 150)], (30, 32, 40, 255), 6)
    c.circle(100, 70, 16, (30, 32, 40, 255))
    return c.result()
