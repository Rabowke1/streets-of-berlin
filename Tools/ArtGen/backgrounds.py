"""Gemalte Hintergruende fuer Stage 1: Kreuzberg bei Nacht + U-Bahnhof Kottbusser Tor.

Layer (Masse in Welt-Units, Pixel = Units * RES):
  Sky    2400x700  Parallax 0.15   Himmel, Wolken, Fernsehturm, Skyline im Dunst
  Street 2048x560  Parallax 1.0    Altbau-Fassaden, Laeden, Neon, Graffiti   Unterkante = Welt-Z 300
  UBahn  2048x560  Parallax 1.0    Bahnsteigwand, Gleisbett
  Floor  1024x420  Parallax 1.0    Gehweg/Strasse bzw. Bahnsteig            Oberkante = Welt-Z 300
  FG     Laterne / Saeule, Parallax 1.25, vor den Figuren
"""
import math
import random

from bgkit import (LINE, Canvas, bricks, drop_shadow, glow_spot, graffiti_piece, light_cone, neon_sign,
                   poster_wall, tags)
from common import mix, shade

WARM = (255, 196, 120, 255)
NEON_PINK = (255, 60, 150, 255)
NEON_CYAN = (60, 225, 255, 255)
NEON_YELLOW = (255, 210, 70, 255)
NEON_GREEN = (110, 255, 130, 255)


# ---------------------------------------------------------------------------
# Himmel
# ---------------------------------------------------------------------------
def sky():
    W, H = 2400, 700
    c = Canvas(W, H, k=1)
    c.vgrad(0, 0, W, H * 0.62, (10, 10, 34, 255), (58, 32, 92, 255))
    c.vgrad(0, H * 0.62, W, H, (58, 32, 92, 255), (150, 62, 110, 255))
    rng = random.Random(2)
    for _ in range(420):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.5)
        r = rng.choice([0.6, 0.8, 1.0, 1.3])
        c.circle(x, y, r, (255, 250, 235, rng.randint(90, 230)))
    # Mond mit Hof
    glow_spot(c, 1880, 120, 150, (180, 170, 255, 120))
    c.circle(1880, 120, 42, (250, 244, 222, 255))
    c.circle(1868, 110, 8, (228, 220, 200, 255))
    c.circle(1895, 135, 6, (232, 224, 204, 255))
    # Wolken, von unten vom Stadtlicht angeleuchtet
    for i in range(14):
        cx, cy = rng.uniform(-100, W + 100), rng.uniform(120, 360)
        w = rng.uniform(200, 460)

        def cloud(L, cx=cx, cy=cy, w=w, seed=i):
            r2 = random.Random(seed)
            for _ in range(9):
                bx = cx + r2.uniform(-w / 2, w / 2)
                by = cy + r2.uniform(-14, 10)
                br = r2.uniform(24, 60)
                L.ellipse(bx - br * 1.6, by - br * 0.6, bx + br * 1.6, by + br * 0.6, (88, 58, 120, 170))
            L.ellipse(cx - w / 2, cy + 6, cx + w / 2, cy + 26, (210, 110, 140, 90))

        c.light((cx - w, cy - 80, cx + w, cy + 80), cloud, blur=14, mode="over")

    # Stadtglühen am Horizont
    c.light((0, H - 260, W, H), lambda L: L.rect(0, H - 150, W, H, (255, 120, 90, 130)), blur=90)

    # Ferne Skyline (Dunst)
    def skyline(y_base, hmin, hmax, col, win_p, seed, win_col):
        r2 = random.Random(seed)
        x = -40
        while x < W:
            w = r2.randint(90, 240)
            h = r2.randint(hmin, hmax)
            c.rect(x, y_base - h, x + w, y_base, col)
            if r2.random() < 0.35:
                c.rect(x + w * 0.3, y_base - h - 30, x + w * 0.36, y_base - h, col)
                c.circle(x + w * 0.33, y_base - h - 32, 3, (255, 70, 70, 255))
            for wy in range(int(y_base - h + 12), int(y_base - 8), 16):
                for wx in range(int(x + 8), int(x + w - 8), 13):
                    if r2.random() < win_p:
                        c.rect(wx, wy, wx + 6, wy + 8, r2.choice(win_col))
            x += w + r2.randint(-20, 30)

    skyline(H, 160, 330, (52, 38, 84, 255), 0.10, 11, [(255, 200, 150, 200), (170, 190, 255, 180)])
    c.light((0, H - 330, W, H), lambda L: L.rect(0, H - 330, W, H, (130, 70, 130, 90)), blur=40, mode="over")

    # Fernsehturm
    cx = 700
    shaft = (46, 36, 76, 255)
    c.poly([(cx - 30, H), (cx - 12, 262), (cx + 12, 262), (cx + 30, H)], shaft)
    c.poly([(cx - 30, H), (cx - 12, 262), (cx - 4, 262), (cx - 12, H)], (60, 48, 96, 255))
    c.circle(cx, 208, 50, (56, 46, 90, 255))
    c.circle(cx - 14, 194, 34, (84, 70, 124, 255))
    c.circle(cx - 22, 186, 14, (120, 104, 160, 255))
    c.rect(cx - 54, 222, cx + 54, 234, (34, 28, 58, 255))
    for i in range(14):
        x = cx - 50 + i * 7.7
        c.rect(x, 225, x + 4, 231, (255, 214, 150, 255))
    c.light((cx - 60, 220, cx + 60, 236), lambda L: L.rect(cx - 50, 225, cx + 50, 231, (255, 200, 130, 200)), blur=6)
    c.rect(cx - 7, 120, cx + 7, 162, (40, 32, 66, 255))
    c.rect(cx - 3, 20, cx + 3, 122, (52, 44, 80, 255))
    for y in (24, 64, 100, 150):
        glow_spot(c, cx, y, 30, (255, 40, 40, 200))
        c.circle(cx, y, 4, (255, 90, 90, 255))

    skyline(H, 70, 190, (30, 22, 52, 255), 0.18, 12, [(255, 196, 120, 255), (255, 170, 90, 255),
                                                     (150, 180, 255, 255)])
    # Baukran
    c.line([(1320, H - 170), (1320, 250)], (30, 22, 50, 255), 5)
    c.line([(1180, 262), (1520, 262)], (30, 22, 50, 255), 5)
    c.line([(1320, 250), (1210, 262)], (30, 22, 50, 255), 2)
    c.line([(1320, 250), (1480, 262)], (30, 22, 50, 255), 2)
    glow_spot(c, 1520, 262, 24, (255, 50, 50, 200))
    return c.result()


# ---------------------------------------------------------------------------
# Fassaden-Bausteine
# ---------------------------------------------------------------------------
def window(c, x, y, w, h, rng, kind=None, frame=(210, 196, 180, 255), lit_list=None):
    kind = kind or rng.choices(["lit", "dark", "tv", "curtain"], [0.34, 0.4, 0.08, 0.18])[0]
    c.outlined_rect(x - 5, y - 5, x + w + 5, y + h + 5, frame, 1.8)
    # Laibung (Innenschatten)
    c.rect(x, y, x + w, y + h, (26, 22, 34, 255))
    gx0, gy0 = x + 3, y + 3
    if kind != "dark":
        c.emissive_rect(gx0, gy0, x + w - 3, y + h - 3, 225)
    if kind == "lit":
        c.vgrad(gx0, gy0, x + w - 3, y + h - 3, (255, 222, 160, 255), (230, 140, 76, 255))
        # Innenraum-Silhouetten
        r = rng.random()
        if r < 0.3:
            c.circle(x + w * 0.5, y + h * 0.3, w * 0.16, (255, 245, 210, 255))  # Lampe
            c.line([(x + w * 0.5, y + 3), (x + w * 0.5, y + h * 0.2)], (60, 40, 30, 255), 1)
        elif r < 0.55:
            c.ellipse(x + w * 0.52, y + h * 0.52, x + w * 0.9, y + h * 0.9, (60, 90, 50, 255))  # Pflanze
            c.rect(x + w * 0.62, y + h * 0.82, x + w * 0.8, y + h - 3, (120, 60, 40, 255))
        elif r < 0.7:
            c.ellipse(x + w * 0.25, y + h * 0.35, x + w * 0.5, y + h * 0.55, (70, 40, 40, 255))  # Person
            c.rect(x + w * 0.2, y + h * 0.55, x + w * 0.55, y + h - 3, (70, 40, 40, 255))
        c.rect(gx0, gy0, x + w * 0.2, y + h - 3, (200, 80, 70, 200))  # Vorhang
        c.rect(x + w * 0.8, gy0, x + w - 3, y + h - 3, (200, 80, 70, 200))
        if lit_list is not None:
            lit_list.append((x, y, x + w, y + h, WARM))
    elif kind == "tv":
        c.vgrad(gx0, gy0, x + w - 3, y + h - 3, (130, 170, 255, 255), (60, 80, 200, 255))
        if lit_list is not None:
            lit_list.append((x, y, x + w, y + h, (120, 160, 255, 255)))
    elif kind == "curtain":
        c.vgrad(gx0, gy0, x + w - 3, y + h - 3, (250, 190, 150, 255), (200, 120, 110, 255))
        for i in range(5):
            xx = gx0 + (w - 6) * (i + 0.5) / 5
            c.line([(xx, gy0), (xx, y + h - 3)], (180, 100, 100, 255), 1.2)
        if lit_list is not None:
            lit_list.append((x, y, x + w, y + h, (255, 170, 130, 255)))
    else:
        c.vgrad(gx0, gy0, x + w - 3, y + h - 3, (40, 52, 90, 255), (16, 18, 38, 255))
        c.poly([(gx0 + w * 0.15, gy0), (gx0 + w * 0.4, gy0), (gx0, gy0 + h * 0.5), (gx0, gy0 + h * 0.25)],
               (90, 110, 170, 110))
    # Sprossen
    c.rect(x + w / 2 - 1.5, y, x + w / 2 + 1.5, y + h, frame)
    c.rect(x, y + h * 0.34 - 1.5, x + w, y + h * 0.34 + 1.5, frame)
    # Fensterbank + Schmutzfahne
    grime(c, x - 4, y + h + 10, x + w + 4, y + h + 10 + rng.uniform(25, 55), rng.uniform(0.2, 0.4))
    c.outlined_rect(x - 9, y + h + 5, x + w + 9, y + h + 10, shade(frame, 1.08), 1.5)
    drop_shadow(c, x - 9, y + h + 10, x + w + 9, y + h + 10, 10, 0.35)


def grime(c, x0, y0, x1, y1, amount=0.35):
    """Schmutzfahne unter Fensterbaenken / Gesimsen (nach unten auslaufend)."""
    def paint(L):
        steps = 6
        for i in range(steps):
            t0 = i / steps
            L.rect(x0 + (x1 - x0) * 0.1 * t0, y0 + (y1 - y0) * t0, x1 - (x1 - x0) * 0.1 * t0,
                   y0 + (y1 - y0) * (t0 + 1 / steps), (40, 30, 50, int(255 * amount * (1 - t0))))
    c.light((x0, y0, x1, y1), paint, blur=(x1 - x0) * 0.08, mode="shadow")


def stains(c, x0, y0, x1, y1, rng, n=10):
    def paint(L):
        for _ in range(n):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            r = rng.uniform(10, 40)
            L.ellipse(x - r, y - r * 0.7, x + r, y + r * 0.7, (50, 40, 60, rng.randint(30, 80)))
    c.light((x0, y0, x1, y1), paint, blur=10, mode="shadow")


def pediment(c, x, y, w, col, arch=False):
    if arch:
        c.ellipse(x - 12, y - 24, x + w + 12, y + 16, LINE)
        c.ellipse(x - 10, y - 22, x + w + 10, y + 14, col)
        c.rect(x - 12, y - 4, x + w + 12, y + 4, col)
    else:
        c.poly([(x - 14, y + 2), (x + w / 2, y - 20), (x + w + 14, y + 2)], LINE)
        c.poly([(x - 10, y), (x + w / 2, y - 16), (x + w + 10, y)], col)
    c.rect(x - 12, y, x + w + 12, y + 5, shade(col, 0.8))


def balcony(c, x0, x1, y, rng):
    c.outlined_rect(x0, y, x1, y + 9, (120, 112, 120, 255), 1.5)
    drop_shadow(c, x0, y + 9, x1, y + 9, 24, 0.5)
    rail = (28, 26, 34, 255)
    c.line([(x0 + 2, y - 36), (x1 - 2, y - 36)], rail, 2.4)
    x = x0 + 5
    while x < x1 - 3:
        c.line([(x, y - 36), (x, y)], rail, 1.3)
        x += 6
    if rng.random() < 0.7:
        c.outlined_rect(x0 + 8, y - 48, x0 + 48, y - 38, (150, 80, 50, 255), 1.2)
        for i in range(7):
            c.circle(x0 + 12 + i * 5.5, y - 50 - rng.uniform(0, 6), rng.uniform(3, 5),
                     rng.choice([(70, 150, 60, 255), (230, 70, 90, 255), (240, 220, 80, 255)]))


def downpipe(c, x, y0, y1):
    c.rect(x - 3.5, y0, x + 3.5, y1, (60, 62, 72, 255))
    c.rect(x - 1.5, y0, x, y1, (110, 112, 124, 255))
    for y in range(int(y0 + 30), int(y1), 70):
        c.rect(x - 5, y, x + 5, y + 4, (40, 40, 48, 255))


def altbau(c, x0, x1, top, base, col, rng, floors=4, shop_h=170, lit=None):
    """Berliner Altbau mit Stuck, Gesimsen, Balkonen."""
    stucco = shade(col, 1.25)
    # Dach
    c.poly([(x0 - 6, top), (x0 + 30, top - 46), (x1 - 30, top - 46), (x1 + 6, top)], (36, 32, 48, 255))
    for i in range(max(1, int((x1 - x0) / 170))):
        dx = x0 + 60 + i * 170
        if dx + 40 < x1 - 30:
            c.outlined_rect(dx, top - 40, dx + 36, top - 6, (70, 64, 84, 255), 1.5)
            c.rect(dx + 7, top - 32, dx + 29, top - 10, WARM if rng.random() < 0.5 else (30, 36, 60, 255))
    # Wand
    c.rect(x0, top, x1, base, col)
    c.texture(x0, top, x1, base, amount=14, grain=5, seed=rng.randint(0, 9999))
    # Pilaster an den Kanten
    c.rect(x0, top, x0 + 12, base - shop_h, shade(col, 1.08))
    c.rect(x1 - 12, top, x1, base - shop_h, shade(col, 0.9))
    # Hauptgesims
    c.outlined_rect(x0 - 8, top, x1 + 8, top + 16, stucco, 2)
    for x in range(int(x0), int(x1), 14):
        c.rect(x + 2, top + 16, x + 8, top + 24, shade(stucco, 0.9))  # Konsolen
    drop_shadow(c, x0 - 8, top + 16, x1 + 8, top + 16, 26, 0.55)

    shop_top = base - shop_h
    fh = (shop_top - top - 34) / floors
    n = max(2, int((x1 - x0) / 104))
    step = (x1 - x0) / n
    ww = min(52, step * 0.55)
    for f in range(floors):
        fy = top + 34 + f * fh
        wh = fh - 44
        for i in range(n):
            wx = x0 + step * i + (step - ww) / 2
            if f == 0:
                pediment(c, wx, fy + 8, ww, stucco, arch=(i % 2 == 1))
            window(c, wx, fy + 14, ww, wh, rng, lit_list=lit)
        # Stockwerksgesims
        c.outlined_rect(x0, fy + fh - 10, x1, fy + fh - 4, shade(col, 1.12), 1.2)
        drop_shadow(c, x0, fy + fh - 4, x1, fy + fh - 4, 12, 0.35)
        if f in (1, 2) and rng.random() < 0.75:
            bi = rng.randint(0, n - 1)
            balcony(c, x0 + step * bi + 6, x0 + step * (bi + 1) - 6, fy + fh - 12, rng)
    stains(c, x0, top + 30, x1, shop_top, rng, n=int((x1 - x0) / 40))
    # Umgebungsverdeckung an den Hauskanten
    c.light((x0, top, x1, base), lambda L: (L.rect(x0, top, x0 + 14, base, (20, 10, 40, 110)),
                                            L.rect(x1 - 14, top, x1, base, (20, 10, 40, 110))), blur=10,
            mode="shadow")
    downpipe(c, x1 - 22, top + 16, base)
    # Sockelgeschoss
    c.rect(x0, shop_top, x1, base, shade(col, 0.62))
    c.texture(x0, shop_top, x1, base, amount=10, grain=3, seed=rng.randint(0, 9999))
    c.outlined_rect(x0 - 4, shop_top - 8, x1 + 4, shop_top, stucco, 1.5)
    return shop_top


def awning(c, x0, x1, y, col, depth=34):
    c.poly([(x0 - 4, y), (x1 + 4, y), (x1 + 16, y + depth), (x0 - 16, y + depth)], LINE)
    sw = 26
    x = x0 - 12
    i = 0
    while x < x1 + 12:
        cc = col if i % 2 == 0 else (242, 238, 228, 255)
        c.poly([(max(x0, x + 4), y + 3), (min(x1, x + sw + 4), y + 3), (min(x1 + 12, x + sw), y + depth - 3),
                (max(x0 - 12, x), y + depth - 3)], cc)
        c.circle(x + sw / 2, y + depth - 2, sw / 2 - 1, cc)
        x += sw
        i += 1
    c.tint(x0 - 16, y, x1 + 16, y + depth + 14, (255, 255, 255), 0.0, (40, 20, 60), 0.35)
    drop_shadow(c, x0 - 10, y + depth + 8, x1 + 10, y + depth + 8, 30, 0.5)


def shop_interior(c, x0, y0, x1, y1, kind, rng):
    c.emissive_rect(x0, y0, x1, y1, 215)
    c.vgrad(x0, y0, x1, y1, (236, 186, 128, 255), (170, 110, 70, 255))
    if kind == "spaeti":
        # Kuehlschraenke
        fx = x0 + 10
        while fx + 70 < x1 - 10:
            c.outlined_rect(fx, y0 + 8, fx + 66, y1, (170, 214, 240, 255), 1.5)
            for sy in range(int(y0 + 22), int(y1 - 6), 20):
                for bx in range(int(fx + 5), int(fx + 60), 8):
                    col = rng.choice([(90, 60, 30, 255), (40, 140, 60, 255), (220, 60, 60, 255),
                                      (250, 200, 60, 255), (60, 110, 220, 255)])
                    c.rect(bx, sy - 14, bx + 5, sy, col)
                    c.rect(bx + 1, sy - 17, bx + 4, sy - 14, shade(col, 0.7))
                c.rect(fx + 2, sy, fx + 64, sy + 2, (170, 190, 210, 255))
            fx += 76
        c.light((x0, y0, x1, y1), lambda L: L.rect(x0 + 10, y0 + 8, x1 - 10, y1, (120, 200, 255, 70)), blur=16)
    elif kind == "doener":
        c.rect(x0, y0 + (y1 - y0) * 0.62, x1, y1, (150, 150, 160, 255))  # Theke
        c.rect(x0, y0 + (y1 - y0) * 0.62, x1, y0 + (y1 - y0) * 0.62 + 4, (220, 220, 230, 255))
        for sx in (x0 + 60, x0 + 150):
            c.poly([(sx - 22, y0 + 18), (sx + 22, y0 + 18), (sx + 14, y0 + (y1 - y0) * 0.6),
                    (sx - 14, y0 + (y1 - y0) * 0.6)], (150, 80, 40, 255))
            for k in range(6):
                yy = y0 + 24 + k * ((y1 - y0) * 0.55 / 6)
                c.line([(sx - 18 + k * 0.6, yy), (sx + 18 - k * 0.6, yy + 3)], (190, 110, 60, 255), 1.5)
            c.rect(sx - 1.5, y0 + 6, sx + 1.5, y0 + (y1 - y0) * 0.62, (200, 200, 210, 255))
            c.light((sx - 30, y0, sx + 30, y1), lambda L, sx=sx: L.rect(sx - 26, y0 + 10, sx + 26, y1 - 30,
                                                                        (255, 110, 30, 110)), blur=10)
        mx = x0 + 210
        c.outlined_rect(mx, y0 + 10, min(x1 - 10, mx + 150), y0 + 60, (30, 30, 36, 255), 1.5)
        for k in range(4):
            c.rect(mx + 8, y0 + 18 + k * 10, mx + 90, y0 + 22 + k * 10, (250, 230, 120, 255))
            c.rect(mx + 110, y0 + 18 + k * 10, mx + 135, y0 + 22 + k * 10, (255, 120, 90, 255))
    else:  # kiosk
        for sy in range(int(y0 + 16), int(y1 - 4), 26):
            c.rect(x0 + 6, sy + 18, x1 - 6, sy + 21, (130, 90, 60, 255))
            bx = x0 + 10
            while bx < x1 - 24:
                w = rng.uniform(14, 22)
                c.rect(bx, sy, bx + w, sy + 18, rng.choice([(230, 70, 60, 255), (60, 120, 220, 255),
                                                           (250, 220, 70, 255), (240, 240, 235, 255)]))
                bx += w + 3
    # Spiegelung auf dem Glas
    c.light((x0, y0, x1, y1), lambda L: L.poly([(x0 + 20, y0), (x0 + 70, y0), (x0 + 10, y1), (x0 - 40, y1)],
                                                (255, 255, 255, 60)), blur=2)


def shopfront(c, x0, x1, shop_top, base, name, neon, awn, kind, rng, lit=None):
    c.outlined_rect(x0 + 6, shop_top + 4, x1 - 6, base, (34, 30, 40, 255), 2)
    neon_sign(c, (x0 + x1) / 2, shop_top + 30, name, 36, neon)
    wx0, wx1 = x0 + 18, x1 - 96
    wy0, wy1 = shop_top + 96, base - 14
    c.outlined_rect(wx0 - 4, wy0 - 4, wx1 + 4, wy1 + 4, (70, 64, 76, 255), 2)
    shop_interior(c, wx0, wy0, wx1, wy1, kind, rng)
    c.rect(wx0 - 4, wy1, wx1 + 4, wy1 + 6, (90, 86, 96, 255))
    # Tuer
    dx0, dx1 = x1 - 84, x1 - 22
    c.outlined_rect(dx0, shop_top + 90, dx1, base, (74, 60, 50, 255), 2)
    c.vgrad(dx0 + 7, shop_top + 98, dx1 - 7, base - 60, (240, 196, 140, 255), (180, 120, 80, 255))
    c.emissive_rect(dx0 + 7, shop_top + 98, dx1 - 7, base - 60, 215)
    c.rect(dx1 - 14, base - 60, dx1 - 9, base - 48, (220, 200, 120, 255))
    neon_sign(c, (dx0 + dx1) / 2, shop_top + 110, "OFFEN", 10, (255, 70, 70, 255), board=False, kind="bold")
    if awn:
        awning(c, x0 + 8, x1 - 8, shop_top + 58, awn)
    if lit is not None:
        lit.append((wx0, wy0, wx1, wy1, WARM))
        lit.append((dx0, shop_top + 98, dx1, base, WARM))


def bottle_crates(c, x, base, rng, n=3):
    for i in range(n):
        col = rng.choice([(60, 130, 70, 255), (200, 60, 50, 255), (240, 190, 50, 255)])
        y = base - 26 * (i + 1)
        c.outlined_rect(x, y, x + 50, y + 24, col, 1.5)
        for k in range(5):
            c.rect(x + 4 + k * 9, y - 8, x + 9 + k * 9, y + 2, (70, 50, 30, 255))
        c.rect(x + 4, y + 8, x + 46, y + 11, shade(col, 0.7))


def bike(c, x, base, col=(220, 60, 60, 255)):
    for wx in (x, x + 62):
        c.d.ellipse(c.P(wx - 20, base - 42, wx + 20, base - 2), outline=LINE, width=int(4 * c.s))
        for a in range(0, 180, 30):
            dx, dy = math.cos(math.radians(a)) * 17, math.sin(math.radians(a)) * 17
            c.line([(wx - dx, base - 22 - dy), (wx + dx, base - 22 + dy)], (150, 150, 160, 255), 0.6)
    c.line([(x, base - 22), (x + 24, base - 52), (x + 52, base - 52), (x + 62, base - 22)], col, 3.2)
    c.line([(x + 24, base - 52), (x + 30, base - 22), (x, base - 22)], col, 3.2)
    c.line([(x + 30, base - 22), (x + 52, base - 52)], col, 3.2)
    c.line([(x + 24, base - 52), (x + 20, base - 60)], LINE, 3)
    c.line([(x + 12, base - 62), (x + 26, base - 62)], LINE, 4)
    c.line([(x + 52, base - 52), (x + 56, base - 66), (x + 64, base - 66)], LINE, 3)


def trash_bags(c, x, base, rng):
    for i in range(3):
        bx = x + i * 26 + rng.uniform(-4, 4)
        r = rng.uniform(18, 24)
        c.circle(bx, base - r + 2, r + 2, LINE)
        c.circle(bx, base - r + 2, r, (34, 34, 42, 255))
        c.circle(bx - r * 0.35, base - r * 1.4, r * 0.3, (80, 84, 100, 255))


def cables(c, x0, x1, y, sag, rng):
    pts = []
    for i in range(21):
        t = i / 20
        pts.append((x0 + (x1 - x0) * t, y + sag * 4 * t * (1 - t)))
    c.line(pts, (18, 16, 24, 255), 1.4)


def wall_lamp(c, x, y):
    c.rect(x - 2, y - 4, x + 20, y, LINE)
    c.poly([(x + 10, y), (x + 30, y), (x + 26, y + 10), (x + 14, y + 10)], (40, 40, 48, 255))
    c.rect(x + 14, y + 10, x + 26, y + 13, (255, 236, 190, 255))
    c.emissive_rect(x + 14, y + 10, x + 26, y + 13)
    light_cone(c, x + 20, y + 12, 18, 260, 420, (255, 190, 120, 150), 1.0)
    glow_spot(c, x + 20, y + 12, 60, (255, 220, 160, 240))


def litfass(c, x, base, rng):
    """Litfasssaeule mit Plakaten."""
    r = 46
    top = base - 250
    c.rect(x - r - 3, top - 3, x + r + 3, base, LINE)
    c.hgrad(x - r, top, x + r, base, (200, 190, 170, 255), (110, 100, 96, 255))
    y = top + 6
    while y < base - 40:
        h = rng.uniform(40, 64)
        col = rng.choice([(230, 70, 60, 255), (245, 215, 70, 255), (70, 150, 230, 255), (240, 240, 232, 255),
                          (90, 200, 140, 255)])
        c.hgrad(x - r, y, x + r, y + h - 4, col, shade(col, 0.55))
        c.text(x - 6, y + h / 2, rng.choice(["KONZERT", "THEATER", "FILM", "RAVE"]), 11, shade(col, 0.35))
        y += h
    c.rect(x - r, base - 34, x + r, base, (60, 70, 60, 255))
    c.poly([(x - r - 8, top), (x - r + 6, top - 26), (x + r - 6, top - 26), (x + r + 8, top)], LINE)
    c.poly([(x - r - 5, top - 2), (x - r + 8, top - 23), (x + r - 8, top - 23), (x + r + 5, top - 2)],
           (56, 90, 70, 255))
    c.circle(x, top - 30, 8, (56, 90, 70, 255))


def facade_light(c, x0, x1, lit):
    """Nacht-Lichtstimmung wie in SoR4:
    1. alle Oberflaechen (nicht die Lichtquellen) nachtblau abdunkeln, oben staerker als unten
    2. warmes Streulicht vom Gehweg/den Laeden nach oben
    3. aufgeschobene Lichter (Neon, Lampen) + Fensterlicht auftragen
    """
    c.grade((60, 64, 150), 0.78, (110, 90, 170), 0.5)
    c.tint(x0, 360, x1, 560, (255, 255, 255), 0.0, (255, 130, 90), 0.10, mode="add")
    c.flush()

    def window_glow(L):
        for (a, b, cc, d, col) in lit:
            if d <= 480:
                L.rect(a - 3, b - 3, cc + 3, d + 3, (*col[:3], 120))
    if lit:
        c.light((x0, 0, x1, 560), window_glow, blur=12, strength=0.9)

    def shop_spill(L):
        for (a, b, cc, d, col) in lit:
            if d > 480:  # Ladenfenster: Licht faellt nach oben an die Fassade
                L.ellipse(a - 40, b - 160, cc + 40, d + 60, (255, 170, 100, 90))
    c.light((x0, 0, x1, 560), shop_spill, blur=50, strength=1.0)


# ---------------------------------------------------------------------------
# Strassen-Kacheln
# ---------------------------------------------------------------------------
FACADES = [(150, 116, 110, 255), (104, 124, 150, 255), (170, 146, 110, 255), (112, 138, 118, 255),
           (160, 136, 160, 255), (190, 170, 140, 255)]


def street_tile(variant):
    W, H = 2048, 560
    base = H
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(10 + variant)
    lit = []
    if variant == 0:
        top = altbau(c, 0, 540, 60, base, FACADES[0], rng, lit=lit)
        shopfront(c, 10, 530, top, base, "SPÄTI", NEON_CYAN, (40, 110, 200, 255), "spaeti", rng, lit)
        top = altbau(c, 540, 1060, 90, base, FACADES[2], rng, lit=lit)
        shopfront(c, 550, 1050, top, base, "DÖNER KEBAB", NEON_YELLOW, (200, 44, 40, 255), "doener", rng, lit)

        # Baulücke: Brandwand + Bauzaun, Himmel bleibt transparent
        bricks(c, 1400, 10, 1480, base, (150, 96, 76, 255), rng)
        c.rect(1060, 120, 1400, base, (0, 0, 0, 0))
        # Mural an der Brandwand des Nachbarhauses (linke Seite des naechsten Hauses)
        c.rect(1060, 80, 1400, 120, (0, 0, 0, 0))
        # Bauzaun
        fy = base - 170
        c.outlined_rect(1062, fy, 1400, base, (170, 172, 180, 255), 2)
        c.texture(1062, fy, 1400, base, amount=12, seed=5)
        poster_wall(c, 1072, fy + 10, 1390, base - 10, rng, layers=2)
        graffiti_piece(c, 1230, base - 90, "BERLIN", 62, (255, 90, 170, 255), rng=rng, angle=4)
        for x in range(1062, 1400, 56):
            c.rect(x, fy - 12, x + 6, base, (120, 124, 132, 255))
        trash_bags(c, 1300, base, rng)
        bike(c, 1090, base, (60, 180, 220, 255))

        top = altbau(c, 1480, W + 40, 40, base, FACADES[1], rng, floors=5, lit=lit)
        c.rect(1490, top + 8, W, base, (46, 40, 52, 255))
        c.texture(1490, top + 8, W, base, amount=10, seed=8)
        # Hofdurchfahrt
        c.outlined_rect(1560, top + 34, 1740, base, (58, 44, 36, 255), 2.5)
        c.poly([(1566, top + 40), (1734, top + 40), (1650, top + 12)], (58, 44, 36, 255))
        c.rect(1648, top + 40, 1652, base, LINE)
        c.light((1560, top + 34, 1740, base), lambda L: L.rect(1600, base - 60, 1700, base, (255, 180, 100, 90)),
                blur=30)
        tags(c, 1500, W - 40, top + 50, base - 20, rng, 18)
        graffiti_piece(c, 1880, top + 90, "KIEZ", 48, (90, 230, 130, 255), rng=rng, angle=-6)
        bottle_crates(c, 460, base, rng, 3)
        wall_lamp(c, 520, top - 30)
        wall_lamp(c, 1520, top - 20)
        cables(c, 0, 1060, 30, 40, rng)
    else:
        top = altbau(c, -40, 620, 80, base, FACADES[3], rng, lit=lit)
        c.rect(0, top + 8, 610, base, (24, 20, 30, 255))
        c.texture(0, top + 8, 610, base, amount=8, seed=21)
        tags(c, 20, 600, top + 30, base - 20, rng, 30)
        graffiti_piece(c, 150, top + 110, "SO36", 50, (255, 220, 60, 255), rng=rng, angle=-8)
        neon_sign(c, 360, top + 44, "CLUB 36", 44, NEON_PINK)
        c.outlined_rect(300, top + 90, 420, base, (60, 16, 40, 255), 2.5)
        c.light((300, top + 90, 420, base), lambda L: L.rect(310, top + 100, 410, base, (255, 40, 110, 200)), blur=20)
        c.vgrad(310, top + 100, 410, base, (170, 30, 90, 255), (80, 10, 50, 255))
        c.emissive_rect(310, top + 100, 410, base, 200)
        for px in (272, 448):
            c.rect(px - 3, base - 70, px + 3, base, (200, 180, 90, 255))
            c.circle(px, base - 72, 6, (220, 200, 110, 255))
        c.line([(272, base - 62), (360, base - 44), (448, base - 62)], (170, 30, 50, 255), 4)
        glow_spot(c, 360, top + 96, 90, (255, 60, 140, 140))

        top = altbau(c, 620, 1180, 50, base, FACADES[4], rng, lit=lit)
        shopfront(c, 630, 1170, top, base, "KIOSK", NEON_GREEN, (40, 150, 70, 255), "kiosk", rng, lit)

        top = altbau(c, 1180, 1640, 100, base, FACADES[5], rng, lit=lit)
        c.rect(1190, top + 8, 1630, base, (56, 50, 62, 255))
        poster_wall(c, 1300, top + 30, 1620, top + 150, rng, layers=3)
        tags(c, 1200, 1620, top + 110, base - 10, rng, 24)
        graffiti_piece(c, 1470, base - 60, "WILD", 44, (80, 200, 255, 255), rng=rng, angle=3)
        litfass(c, 1236, base, rng)

        # U-Bahn-Eingang
        top = altbau(c, 1640, W + 40, 60, base, FACADES[1], rng, lit=lit)
        c.outlined_rect(1700, top + 12, 2000, base, (22, 20, 28, 255), 2.5)
        for i in range(9):
            y = top + 60 + i * 13
            c.rect(1720, y, 1980, y + 6, (70, 66, 78, 255))
            c.rect(1720, y, 1980, y + 1.5, (120, 116, 128, 255))
        c.light((1700, top + 12, 2000, base), lambda L: L.rect(1720, top + 60, 1980, base, (255, 230, 170, 110)),
                blur=30)
        c.rect(1712, top + 30, 1716, base, (190, 190, 200, 255))
        c.rect(1984, top + 30, 1988, base, (190, 190, 200, 255))
        c.rect(1766, top - 130, 1774, base, LINE)
        c.outlined_rect(1740, top - 110, 1800, top - 50, (30, 90, 200, 255), 2.5)
        c.emissive_rect(1740, top - 110, 1800, top - 50)
        c.emissive_rect(1810, top - 96, 1994, top - 62, 200)
        glow_spot(c, 1770, top - 80, 80, (80, 150, 255, 180))
        c.text(1770, top - 80, "U", 46, (255, 255, 255, 255), kind="bold")
        c.outlined_rect(1810, top - 96, 1994, top - 62, (244, 244, 240, 255), 2)
        c.text(1902, top - 79, "Kottbusser Tor", 21, (20, 20, 20, 255), kind="bold")
        wall_lamp(c, 900, top - 20)
        cables(c, 600, 1700, 40, 50, rng)
    facade_light(c, 0, W, lit)
    return c.result()


# ---------------------------------------------------------------------------
# U-Bahnhof
# ---------------------------------------------------------------------------
def ubahn_tile():
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(33)
    # Decke
    c.vgrad(0, 0, W, 64, (26, 26, 32, 255), (48, 48, 56, 255))
    for x in range(0, W, 128):
        c.rect(x, 0, x + 4, 64, (20, 20, 26, 255))
    # Wand-Fliesen
    tile = (96, 176, 164, 255)
    c.rect(0, 64, W, 470, shade(tile, 0.72))
    ty = 64
    row = 0
    while ty < 450:
        tx = -(row % 2) * 22
        while tx < W:
            v = rng.uniform(0.9, 1.08)
            col = shade(tile, v) if v <= 1 else shade(tile, 1 + (v - 1) * 1.5)
            c.rect(tx + 1.2, ty + 1.2, tx + 42.8, ty + 20.8, col)
            c.rect(tx + 2, ty + 2, tx + 42, ty + 5, shade(col, 1.12))
            tx += 44
        ty += 22
        row += 1
    c.texture(0, 64, W, 470, amount=8, grain=4, seed=3)
    # Schmutz nach unten
    c.tint(0, 300, W, 470, (255, 255, 255), 0.0, (60, 50, 40), 0.45)
    # BVG-Gelb-Band
    c.outlined_rect(0, 76, W, 92, (240, 200, 40, 255), 1.5)
    c.outlined_rect(0, 440, W, 470, (46, 46, 52, 255), 1.5)
    # Leuchtstoffroehren mit Licht auf der Wand
    for x in range(90, W, 340):
        c.outlined_rect(x, 38, x + 190, 50, (250, 252, 240, 255), 2)
        c.emissive_rect(x, 38, x + 190, 50)
        light_cone(c, x + 95, 50, 190, 420, 400, (220, 255, 240, 70), 0.9)
        glow_spot(c, x + 95, 44, 120, (230, 255, 240, 200))
    # Stationsschilder (Leuchtkaesten)
    for x in (230, 1250):
        c.outlined_rect(x, 140, x + 440, 214, (250, 250, 246, 255), 3)
        c.emissive_rect(x, 140, x + 440, 214, 170)
        c.rect(x, 140, x + 440, 148, (30, 90, 200, 255))
        c.text(x + 220, 182, "Kottbusser Tor", 42, (22, 22, 26, 255), kind="bold")
        c.light((x, 140, x + 440, 214), lambda L, x=x: L.rect(x, 140, x + 440, 214, (255, 255, 240, 70)), blur=24)
    # Werbeplakate mit Motiven
    for i, x in enumerate((760, 1750)):
        c.outlined_rect(x - 8, 118, x + 218, 340, (180, 180, 190, 255), 3)
        c1 = [(230, 60, 110, 255), (60, 110, 230, 255)][i]
        c.vgrad(x, 126, x + 210, 332, c1, shade(c1, 0.35))
        c.emissive_rect(x, 126, x + 210, 332, 150)
        c.circle(x + 105, 220, 60, shade(c1, 1.5))
        c.circle(x + 105, 220, 40, (255, 240, 200, 255))
        c.poly([(x, 332), (x + 60, 250), (x + 110, 300), (x + 160, 240), (x + 210, 320), (x + 210, 332)],
               shade(c1, 0.25))
        c.text(x + 105, 150, ["TECHNO NACHT", "CURRY 36"][i], 24, (255, 255, 255, 255), stroke=1.5,
               stroke_c=LINE)
        c.light((x, 126, x + 210, 332), lambda L, x=x: L.poly([(x + 30, 126), (x + 90, 126), (x + 20, 332),
                                                                 (x - 40, 332)], (255, 255, 255, 50)), blur=4)
    # Ausgang-Schild + Uhr
    c.outlined_rect(1000, 110, 1140, 146, (30, 90, 200, 255), 2)
    c.emissive_rect(1000, 110, 1140, 146, 180)
    c.text(1060, 128, "Ausgang", 20, (255, 255, 255, 255), kind="bold")
    c.poly([(1105, 118), (1130, 128), (1105, 138)], (255, 255, 255, 255))
    c.circle(120, 170, 34, LINE)
    c.circle(120, 170, 30, (246, 246, 240, 255))
    c.line([(120, 170), (120, 148)], LINE, 3)
    c.line([(120, 170), (136, 176)], LINE, 3)
    # Baenke
    for x in (620, 1520):
        c.outlined_rect(x, 400, x + 170, 412, (200, 60, 50, 255), 2)
        c.rect(x + 12, 412, x + 20, 440, (60, 60, 70, 255))
        c.rect(x + 150, 412, x + 158, 440, (60, 60, 70, 255))
    for x in (40, 1080, 1980):
        tags(c, x - 40, x + 80, 260, 420, rng, 12)
    graffiti_piece(c, 1130, 380, "U8", 40, (250, 220, 70, 255), rng=rng, angle=-4)
    # Gleisbett
    c.rect(0, 470, W, H, (24, 22, 26, 255))
    c.texture(0, 470, W, H, amount=18, grain=1, seed=9)
    for x in range(0, W, 38):
        c.rect(x, 524, x + 24, 536, (74, 58, 44, 255))
    for y in (508, 540):
        c.rect(0, y, W, y + 6, (120, 120, 130, 255))
        c.rect(0, y, W, y + 1.5, (220, 222, 232, 255))
    c.tint(0, 470, W, H, (0, 0, 0), 0.5, (0, 0, 0), 0.1)
    # Kuehles, schummriges Bahnhofslicht; Roehren/Schilder bleiben hell
    c.grade((40, 50, 90), 0.62, (70, 60, 90), 0.5)
    c.flush()
    for x in (230, 1250, 760, 1750):
        c.light((x - 60, 100, x + 500, 380), lambda L, x=x: L.rect(x, 130, x + 440 if x in (230, 1250) else x + 210,
                                                                   214 if x in (230, 1250) else 332,
                                                                   (255, 255, 240, 60)), blur=30)
    return c.result()


# ---------------------------------------------------------------------------
# Boden
# ---------------------------------------------------------------------------
def floor_street():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(5)
    # Kleinpflaster (Mosaik) an der Hauswand
    c.rect(0, 0, W, 62, (56, 52, 62, 255))
    for y in range(0, 60, 8):
        for x in range(-(y % 16), W, 9):
            v = rng.randint(86, 110)
            c.ellipse(x + 0.8, y + 0.8, x + 8.2, y + 7.4, (v, v - 4, v + 8, 255))
    # Granitplatten (Fugen dunkel)
    c.rect(0, 60, W, 204, (58, 54, 64, 255))
    y = 62
    for row in range(2):
        off = 0 if row == 0 else 64
        for x in range(-off, W, 128):
            v = rng.randint(120, 140)
            col = (v, v - 3, v + 8, 255)
            c.rect(x + 2, y + 2, x + 126, y + 68, col)
            c.rect(x + 2, y + 2, x + 126, y + 4, shade(col, 1.1))
            c.rect(x + 2, y + 64, x + 126, y + 68, shade(col, 0.85))
            if rng.random() < 0.3:
                c.line([(x + rng.uniform(10, 50), y + 4), (x + rng.uniform(60, 110), y + 66)],
                       shade(col, 0.7), 1.0)
        y += 70
    c.texture(0, 62, W, 204, amount=10, grain=2, seed=4)
    c.rect(0, 202, W, 224, (56, 52, 62, 255))
    for yy in range(202, 222, 8):
        for x in range(-(yy % 16), W, 9):
            v = rng.randint(80, 104)
            c.ellipse(x + 0.8, yy + 0.8, x + 8.2, yy + 7.4, (v, v - 4, v + 8, 255))
    # Gullideckel
    c.ellipse(700, 150, 770, 188, LINE)
    c.ellipse(703, 152, 767, 186, (60, 56, 64, 255))
    for k in range(6):
        c.line([(710, 157 + k * 5), (760, 157 + k * 5)], (90, 86, 96, 255), 1.4)
    # Bordstein
    c.rect(0, 222, W, 238, (168, 164, 176, 255))
    c.rect(0, 222, W, 225, (214, 210, 220, 255))
    c.rect(0, 238, W, 246, (46, 42, 54, 255))
    for x in range(0, W, 96):
        c.rect(x, 222, x + 1.5, 238, (120, 116, 128, 255))
    # Asphalt: feines Korn, leichte Flecken
    c.rect(0, 246, W, H, (62, 60, 74, 255))
    c.texture(0, 246, W, H, amount=10, grain=3, seed=7)
    c.texture(0, 246, W, H, amount=14, grain=0.25, seed=8)
    c.vgrad(0, 246, W, 270, (30, 28, 40, 200), (30, 28, 40, 0))  # Rinnstein-Schatten
    for x in range(40, W, 256):
        c.rect(x, 364, x + 150, 374, (206, 200, 184, 255))
        c.texture(x, 364, x + 150, 374, amount=36, grain=0.4, seed=x)
    c.rect(560, 290, 700, 330, (54, 52, 66, 255))  # Flicken
    c.line([(560, 290), (700, 290), (700, 330), (560, 330), (560, 290)], (44, 42, 54, 255), 1.2)
    # Pfuetzen: dunkel-glaenzend mit langgezogenen Neon-Spiegelungen
    for (px, py, pw, col) in ((300, 300, 190, NEON_PINK), (840, 395, 160, NEON_CYAN), (90, 405, 130, WARM),
                              (520, 150, 150, NEON_YELLOW)):
        ph = 16 if py > 240 else 12
        c.ellipse(px - pw / 2, py - ph, px + pw / 2, py + ph, (36, 34, 56, 255))
        c.ellipse(px - pw / 2 + 6, py - ph + 3, px + pw / 2 - 6, py + ph - 3, (28, 26, 46, 255))
        c.emissive_circle(px, py, 0.1)  # (Pfuetze selbst wird normal abgedunkelt)

        def refl(L, px=px, py=py, pw=pw, ph=ph, col=col):
            L.ellipse(px - pw * 0.28, py - ph + 3, px + pw * 0.12, py + ph - 3, (*col[:3], 150))
            L.ellipse(px - pw * 0.1, py - ph * 0.4, px + pw * 0.02, py + ph * 0.4, (255, 255, 255, 120))
        c.light((px - pw / 2, py - ph, px + pw / 2, py + ph), refl, blur=7, strength=1.3)
        c.light((px - pw / 2, py - ph, px + pw / 2, py + ph),
                lambda L, px=px, py=py, pw=pw, ph=ph: L.ellipse(px - pw / 2, py - ph, px + pw / 2, py - ph + 5,
                                                                (220, 220, 255, 60)), blur=2)
    # Nacht-Grading: hinten (an den Laeden) etwas heller, vorne dunkler
    c.grade((90, 80, 140), 0.45, (40, 40, 90), 0.62)
    c.flush()
    c.tint(0, 0, W, 120, (255, 160, 100), 0.10, (255, 160, 100), 0.0, mode="add")
    return c.result()


def floor_platform():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(6)
    c.rect(0, 70, W, H, (70, 68, 72, 255))  # Fugen
    c.rect(0, 0, W, 10, (16, 16, 20, 255))
    c.rect(0, 10, W, 24, (176, 172, 166, 255))
    c.rect(0, 10, W, 13, (220, 216, 210, 255))
    c.rect(0, 24, W, 38, (244, 204, 40, 255))
    c.texture(0, 24, W, 38, amount=18, seed=2)
    c.rect(0, 44, W, 70, (206, 202, 196, 255))
    for x in range(0, W, 12):
        for y in (47, 56):
            c.ellipse(x + 2, y, x + 9, y + 7, (170, 166, 160, 255))
            c.ellipse(x + 2, y, x + 8, y + 3, (230, 228, 222, 255))
    yy = 70
    while yy < H:
        off = rng.choice([0, 32, 64])
        for x in range(-off, W, 128):
            v = rng.randint(124, 144)
            col = (v, v - 4, v - 10, 255)
            c.rect(x + 2, yy + 2, x + 126, yy + 62, col)
            c.rect(x + 2, yy + 2, x + 126, yy + 4, shade(col, 1.1))
            if rng.random() < 0.3:
                cx, cy = x + rng.uniform(20, 100), yy + rng.uniform(15, 45)
                c.ellipse(cx - 18, cy - 7, cx + 18, cy + 7, shade(col, 0.86))  # Kaugummi/Flecken
        yy += 64
    c.texture(0, 70, W, H, amount=6, grain=2, seed=6)
    c.texture(0, 70, W, H, amount=8, grain=0.3, seed=16)
    c.grade((70, 80, 110), 0.5, (40, 44, 80), 0.66)
    c.flush()
    # Licht der Leuchtroehren auf dem Boden (Kachel ist 1024 breit, Roehren alle 340 -> weiche Flecken)
    for x in range(100, W, 340):
        c.light((x - 200, 40, x + 200, 260), lambda L, x=x: L.ellipse(x - 170, 50, x + 170, 200,
                                                                     (200, 240, 230, 60)), blur=50)
    return c.result()


# ---------------------------------------------------------------------------
# Vordergrund
# ---------------------------------------------------------------------------
def lamp_post():
    W, H = 200, 900
    c = Canvas(W, H, k=2)
    c.rect(86, 70, 112, H, (22, 26, 34, 255))
    c.rect(91, 70, 99, H, (58, 66, 82, 255))
    c.rect(78, H - 140, 120, H, (18, 22, 28, 255))
    c.rect(84, H - 140, 92, H, (50, 58, 72, 255))
    c.outlined_rect(66, H - 330, 132, H - 270, (240, 240, 236, 255), 2)  # Strassenschild
    c.rect(66, H - 330, 132, H - 326, (30, 90, 180, 255))
    c.text(99, H - 300, "Oranien-", 11, (20, 20, 20, 255), kind="bold")
    c.text(99, H - 286, "straße", 11, (20, 20, 20, 255), kind="bold")
    c.poly([(26, 46), (174, 46), (150, 80), (50, 80)], (24, 28, 36, 255))
    c.rect(50, 78, 150, 86, (255, 236, 190, 255))
    glow_spot(c, 100, 84, 110, (255, 220, 150, 220))
    return c.result()


def pillar():
    W, H = 200, 900
    c = Canvas(W, H, k=2)
    c.rect(34, 0, 166, H, (40, 90, 86, 255))
    for y in range(0, H, 22):
        c.rect(36, y + 1, 164, y + 21, (64, 128, 120, 255))
        c.rect(36, y + 1, 164, y + 3, (90, 160, 150, 255))
    c.hgrad(34, 0, 166, H, (255, 255, 255, 30), (0, 0, 0, 110))
    c.outlined_rect(34, 300, 166, 330, (240, 200, 40, 255), 1.5)
    c.outlined_rect(58, 360, 142, 400, (250, 250, 246, 255), 2)
    c.text(100, 380, "U8", 22, (30, 90, 200, 255), kind="bold")
    return c.result()
