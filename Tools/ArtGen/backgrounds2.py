"""Hintergruende fuer Stage 2 (East Side Gallery + Club-Hinterhof) und Stage 3 (Baustelle am Alex + Dach).

Gleiche Masse wie Stage 1: Wand-Kacheln 2048x560 (Unterkante = Boden-Oberkante),
Boden-Kacheln 1024x420, Himmel 2400x700, Vordergrund 200x900.
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


# ---------------------------------------------------------------------------
# Himmel-Bausteine
# ---------------------------------------------------------------------------
def _night_sky(c, W, H, seed, top=(10, 10, 34, 255), mid=(54, 30, 92, 255), bottom=(150, 62, 110, 255)):
    c.vgrad(0, 0, W, H * 0.6, top, mid)
    c.vgrad(0, H * 0.6, W, H, mid, bottom)
    rng = random.Random(seed)
    for _ in range(360):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.5)
        c.circle(x, y, rng.choice([0.6, 0.8, 1.1]), (255, 250, 235, rng.randint(80, 220)))
    for i in range(10):
        cx, cy, w = rng.uniform(0, W), rng.uniform(80, 300), rng.uniform(220, 480)

        def cloud(L, cx=cx, cy=cy, w=w, seed=i + seed):
            r2 = random.Random(seed)
            for _ in range(8):
                bx, by, br = cx + r2.uniform(-w / 2, w / 2), cy + r2.uniform(-12, 10), r2.uniform(24, 56)
                L.ellipse(bx - br * 1.6, by - br * 0.6, bx + br * 1.6, by + br * 0.6, (86, 56, 118, 160))
            L.ellipse(cx - w / 2, cy + 6, cx + w / 2, cy + 24, (210, 110, 140, 80))
        c.light((cx - w, cy - 80, cx + w, cy + 80), cloud, blur=14, mode="over")
    c.light((0, H - 260, W, H), lambda L: L.rect(0, H - 150, W, H, (255, 120, 90, 120)), blur=90)


def _skyline(c, W, y_base, hmin, hmax, col, win_p, seed, win_cols):
    r2 = random.Random(seed)
    x = -40
    while x < W:
        w = r2.randint(80, 220)
        h = r2.randint(hmin, hmax)
        c.rect(x, y_base - h, x + w, y_base, col)
        if r2.random() < 0.3:
            c.rect(x + w * 0.4, y_base - h - 26, x + w * 0.45, y_base - h, col)
            c.circle(x + w * 0.425, y_base - h - 28, 3, (255, 70, 70, 255))
        for wy in range(int(y_base - h + 10), int(y_base - 6), 15):
            for wx in range(int(x + 7), int(x + w - 7), 12):
                if r2.random() < win_p:
                    c.rect(wx, wy, wx + 5, wy + 7, r2.choice(win_cols))
        x += w + r2.randint(-20, 30)


def _tv_tower(c, cx, base, scale=1.0):
    """Fernsehturm; base = Fuss, scale 1 = ca. 690 Units hoch."""
    s = scale
    shaft = (46, 36, 76, 255)
    sphere_y = base - 470 * s
    c.poly([(cx - 32 * s, base), (cx - 13 * s, sphere_y + 50 * s), (cx + 13 * s, sphere_y + 50 * s),
            (cx + 32 * s, base)], shaft)
    c.poly([(cx - 32 * s, base), (cx - 13 * s, sphere_y + 50 * s), (cx - 4 * s, sphere_y + 50 * s),
            (cx - 12 * s, base)], (62, 50, 98, 255))
    c.circle(cx, sphere_y, 54 * s, (56, 46, 90, 255))
    c.circle(cx - 15 * s, sphere_y - 14 * s, 36 * s, (84, 70, 124, 255))
    c.circle(cx - 24 * s, sphere_y - 22 * s, 15 * s, (124, 108, 166, 255))
    c.rect(cx - 58 * s, sphere_y + 14 * s, cx + 58 * s, sphere_y + 27 * s, (34, 28, 58, 255))
    for i in range(16):
        x = cx - 54 * s + i * 7.2 * s
        c.rect(x, sphere_y + 17 * s, x + 4 * s, sphere_y + 24 * s, (255, 214, 150, 255))
    c.light((cx - 70 * s, sphere_y, cx + 70 * s, sphere_y + 40 * s),
            lambda L: L.rect(cx - 54 * s, sphere_y + 17 * s, cx + 54 * s, sphere_y + 24 * s, (255, 200, 130, 200)),
            blur=6 * s)
    c.rect(cx - 8 * s, sphere_y - 100 * s, cx + 8 * s, sphere_y - 50 * s, (40, 32, 66, 255))
    c.rect(cx - 3.5 * s, sphere_y - 210 * s, cx + 3.5 * s, sphere_y - 98 * s, (52, 44, 80, 255))
    for y in (sphere_y - 206 * s, sphere_y - 160 * s, sphere_y - 110 * s, sphere_y - 60 * s):
        glow_spot(c, cx, y, 30 * s, (255, 40, 40, 200))
        c.circle(cx, y, 4 * s, (255, 90, 90, 255))


def _crane(c, x, base, h, jib_l, jib_r, col=(34, 26, 54, 255)):
    top = base - h
    for k in range(0, int(h), 24):
        c.line([(x - 8, base - k), (x + 8, base - k - 24)], col, 1.4)
        c.line([(x + 8, base - k), (x - 8, base - k - 24)], col, 1.4)
    c.line([(x - 8, base), (x - 8, top)], col, 2.4)
    c.line([(x + 8, base), (x + 8, top)], col, 2.4)
    c.line([(x - jib_l, top), (x + jib_r, top)], col, 5)
    c.line([(x, top - 36), (x - jib_l * 0.8, top)], col, 1.5)
    c.line([(x, top - 36), (x + jib_r * 0.9, top)], col, 1.5)
    c.rect(x - jib_l, top - 8, x - jib_l + 40, top + 14, col)
    c.line([(x + jib_r * 0.7, top), (x + jib_r * 0.7, top + 120)], (20, 16, 30, 255), 1)
    glow_spot(c, x + jib_r, top, 24, (255, 50, 50, 210))
    glow_spot(c, x, top - 36, 20, (255, 50, 50, 210))


# ---------------------------------------------------------------------------
# Stage 2: East Side Gallery
# ---------------------------------------------------------------------------
def sky_spree():
    W, H = 2400, 700
    c = Canvas(W, H, k=1)
    _night_sky(c, W, H, 21)
    glow_spot(c, 420, 110, 130, (180, 170, 255, 110))
    c.circle(420, 110, 36, (250, 244, 222, 255))
    _skyline(c, W, H, 140, 300, (52, 38, 84, 255), 0.08, 31, [(255, 200, 150, 200), (170, 190, 255, 180)])
    _tv_tower(c, 1700, H, 0.8)
    # Oberbaumbruecke (Backstein, Doppelturm, Boegen)
    brick = (120, 52, 60, 255)
    bx0, bx1, deck = 300, 1300, H - 390
    c.rect(bx0, deck, bx1, deck + 26, brick)
    for i in range(7):
        ax = bx0 + 40 + i * 140
        c.rect(ax, deck + 26, ax + 22, H, brick)
        c.ellipse(ax + 22, deck + 30, ax + 140, deck + 150, (0, 0, 0, 0))
    for tx in (720, 820):
        c.rect(tx, deck - 150, tx + 50, deck + 26, brick)
        c.poly([(tx - 6, deck - 150), (tx + 25, deck - 200), (tx + 56, deck - 150)], (90, 40, 50, 255))
        for k in range(3):
            c.rect(tx + 16, deck - 130 + k * 40, tx + 34, deck - 104 + k * 40, WARM)
    c.rect(bx0, deck - 18, bx1, deck - 12, (80, 40, 50, 255))
    # U-Bahn (U1) auf der Bruecke
    c.outlined_rect(900, deck - 40, 1160, deck - 4, (250, 210, 60, 255), 2)
    for k in range(9):
        c.rect(910 + k * 27, deck - 32, 928 + k * 27, deck - 18, (255, 240, 190, 255))
    glow_spot(c, 1030, deck - 22, 150, (255, 220, 120, 120))
    c.light((0, H - 200, W, H), lambda L: L.rect(0, H - 200, W, H, (120, 60, 130, 90)), blur=30, mode="over")
    return c.result()


def _mural(c, x0, x1, top, bottom, rng):
    """Bunte, eigene Wandbilder (abstrakt, Figuren, Schriftzuege)."""
    kind = rng.choice(["faces", "stripes", "sun", "hearts", "text", "doves"])
    pal = rng.sample([(240, 70, 70, 255), (250, 210, 60, 255), (60, 150, 230, 255), (80, 200, 120, 255),
                      (240, 120, 200, 255), (250, 150, 40, 255), (120, 80, 200, 255), (245, 245, 235, 255)], 5)
    w, h = x1 - x0, bottom - top
    c.rect(x0, top, x1, bottom, pal[0])
    if kind == "faces":
        for i in range(3):
            fx = x0 + w * (0.2 + i * 0.3)
            c.ellipse(fx - 44, top + h * 0.2, fx + 44, top + h * 0.85, pal[1 + i % 3])
            c.ellipse(fx - 20, top + h * 0.4, fx - 6, top + h * 0.5, LINE)
            c.ellipse(fx + 8, top + h * 0.4, fx + 22, top + h * 0.5, LINE)
            c.line([(fx - 18, top + h * 0.68), (fx, top + h * 0.72), (fx + 18, top + h * 0.66)], LINE, 4)
            c.line([(fx, top + h * 0.2), (fx - 40, top + h * 0.05)], pal[4], 8)
    elif kind == "stripes":
        for i in range(12):
            c.poly([(x0 + i * w / 8 - 60, bottom), (x0 + i * w / 8, top), (x0 + i * w / 8 + 30, top),
                    (x0 + i * w / 8 - 30, bottom)], pal[1 + i % 4])
    elif kind == "sun":
        cx, cy = x0 + w / 2, top + h * 0.6
        for i in range(16):
            a0, a1 = i * math.pi / 8, (i + 0.5) * math.pi / 8
            c.poly([(cx, cy), (cx + math.cos(a0) * 600, cy - math.sin(a0) * 600),
                    (cx + math.cos(a1) * 600, cy - math.sin(a1) * 600)], pal[1 + i % 2])
        c.circle(cx, cy, 70, pal[3])
        c.circle(cx, cy, 50, pal[4])
    elif kind == "hearts":
        for i in range(6):
            hx, hy, r = x0 + rng.uniform(40, w - 40), top + rng.uniform(40, h - 40), rng.uniform(22, 40)
            col = pal[1 + i % 4]
            c.circle(hx - r * 0.5, hy, r * 0.6, col)
            c.circle(hx + r * 0.5, hy, r * 0.6, col)
            c.poly([(hx - r * 1.08, hy + r * 0.15), (hx + r * 1.08, hy + r * 0.15), (hx, hy + r * 1.3)], col)
    elif kind == "doves":
        for i in range(4):
            dx, dy = x0 + w * (0.15 + i * 0.24), top + h * (0.3 + 0.2 * (i % 2))
            c.ellipse(dx - 30, dy - 12, dx + 30, dy + 12, pal[4])
            c.poly([(dx - 10, dy), (dx + 10, dy - 40), (dx + 26, dy - 6)], pal[4])
            c.circle(dx + 26, dy - 6, 9, pal[4])
            c.poly([(dx + 33, dy - 7), (dx + 42, dy - 4), (dx + 33, dy - 2)], pal[2])
    else:
        word = rng.choice(["FREIHEIT", "LIEBE", "BERLIN", "FRIEDEN", "KIEZ"])
        c.text(x0 + w / 2 + 6, top + h / 2 + 6, word, h * 0.34, LINE, kind="condensed")
        c.text(x0 + w / 2, top + h / 2, word, h * 0.34, pal[2], kind="condensed", stroke=3, stroke_c=pal[3])


def gallery_tile(variant):
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(200 + variant)
    top, bottom = 190, 540
    x = 0
    seg = 120
    murals = []
    while x < W:
        span = rng.choice([2, 3, 4]) * seg
        murals.append((x, min(W, x + span)))
        x += span
    for i, (a, b) in enumerate(murals):
        if variant == 1 and i == 3:
            continue  # Luecke in der Mauer
        c.rect(a, top, b, bottom, (190, 186, 176, 255))
        _mural(c, a, b, top + 16, bottom - 6, rng)
        c.texture(a, top, b, bottom, amount=14, grain=3, seed=rng.randint(0, 999))
    c.rect(0, 0, W, top - 14, (0, 0, 0, 0))  # Wandbilder oben abschneiden (Himmel bleibt frei)
    # Mauersegmente: Fugen + Rohr oben
    for (a, b) in murals:
        for sx in range(int(a), int(b), seg):
            c.rect(sx, top, sx + 2, bottom, (60, 56, 60, 255))
    for i, (a, b) in enumerate(murals):
        if variant == 1 and i == 3:
            continue
        c.outlined_rect(a, top - 14, b, top + 6, (200, 196, 188, 255), 2)
        c.rect(a, top - 14, b, top - 8, (230, 228, 222, 255))
        tags(c, a + 10, b - 10, bottom - 90, bottom - 20, rng, int((b - a) / 50))
    c.rect(0, bottom, W, H, (58, 60, 50, 255))  # Graskante
    for gx in range(0, W, 5):
        c.line([(gx, H), (gx + rng.uniform(-3, 3), bottom - rng.uniform(0, 14))], (70, 110, 60, 255), 1.2)
    # Laternen der Promenade werfen Licht auf die Mauer
    lamps = [300, 1000, 1700]
    c.grade((60, 64, 150), 0.72, (90, 80, 160), 0.5)
    c.flush()
    for lx in lamps:
        c.light((lx - 300, top - 60, lx + 300, H), lambda L, lx=lx: L.ellipse(lx - 240, top - 40, lx + 240, H + 60,
                                                                            (255, 190, 120, 110)), blur=60)
    return c.result()


def floor_promenade():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(51)
    c.rect(0, 0, W, 150, (70, 68, 74, 255))
    for y in range(0, 150, 50):
        off = 0 if (y // 50) % 2 == 0 else 50
        for x in range(-off, W, 100):
            v = rng.randint(112, 132)
            c.rect(x + 2, y + 2, x + 98, y + 48, (v, v - 2, v + 4, 255))
    c.texture(0, 0, W, 150, amount=10, grain=2, seed=3)
    # Radweg (rot) mit Symbol
    c.rect(0, 150, W, 214, (150, 54, 50, 255))
    c.texture(0, 150, W, 214, amount=12, grain=0.4, seed=4)
    c.rect(0, 150, W, 153, (230, 230, 220, 255))
    c.rect(0, 211, W, 214, (230, 230, 220, 255))
    for bx in (200, 712):
        c.d.ellipse(c.P(bx - 26, 172, bx - 6, 192), outline=(240, 240, 230, 255), width=int(2.5 * c.s))
        c.d.ellipse(c.P(bx + 6, 172, bx + 26, 192), outline=(240, 240, 230, 255), width=int(2.5 * c.s))
        c.line([(bx - 16, 182), (bx - 4, 168), (bx + 10, 168), (bx + 16, 182), (bx, 182), (bx - 4, 168)],
               (240, 240, 230, 255), 2.5)
    c.rect(0, 214, W, 232, (170, 166, 176, 255))
    c.rect(0, 214, W, 217, (214, 210, 220, 255))
    c.rect(0, 232, W, 240, (46, 42, 54, 255))
    c.rect(0, 240, W, H, (60, 58, 72, 255))
    c.texture(0, 240, W, H, amount=10, grain=3, seed=7)
    c.texture(0, 240, W, H, amount=14, grain=0.25, seed=8)
    for x in range(40, W, 256):
        c.rect(x, 360, x + 150, 370, (206, 200, 184, 255))
    c.grade((90, 80, 140), 0.45, (40, 40, 90), 0.62)
    c.flush()
    # Laternenlicht mittig in der Kachel, damit die Kachelkanten nahtlos bleiben
    c.light((200, 0, 824, 240), lambda L: L.ellipse(312, 10, 712, 190, (255, 190, 120, 55)), blur=40)
    return c.result()


# ---------------------------------------------------------------------------
# Stage 2: Club-Hinterhof
# ---------------------------------------------------------------------------
def backyard_tile():
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(77)
    bricks(c, 0, 0, W, H, (130, 70, 58, 255), rng, bw=30, bh=10)
    c.texture(0, 0, W, H, amount=10, grain=4, seed=5)
    # Fenster oben
    for i in range(10):
        wx = 60 + i * 200
        c.outlined_rect(wx, 40, wx + 60, 130, (50, 44, 50, 255), 2)
        lit = rng.random() < 0.5
        c.vgrad(wx + 4, 44, wx + 56, 126, (255, 214, 150, 255) if lit else (40, 50, 80, 255),
                (220, 140, 80, 255) if lit else (16, 18, 36, 255))
        if lit:
            c.emissive_rect(wx + 4, 44, wx + 56, 126, 220)
        c.rect(wx + 29, 40, wx + 31, 130, (50, 44, 50, 255))
    # Container-Bar
    c.outlined_rect(260, 300, 760, H, (40, 110, 120, 255), 3)
    for x in range(270, 760, 18):
        c.rect(x, 304, x + 8, H, (32, 94, 104, 255))
    c.outlined_rect(320, 360, 700, 450, (30, 24, 20, 255), 2)
    c.vgrad(324, 364, 696, 446, (255, 200, 130, 255), (200, 120, 70, 255))
    c.emissive_rect(324, 364, 696, 446, 210)
    for k in range(9):
        c.rect(340 + k * 40, 380, 354 + k * 40, 420, rng.choice([(90, 60, 30, 255), (40, 140, 60, 255),
                                                                  (220, 60, 60, 255)]))
    c.outlined_rect(300, 450, 720, 470, (110, 80, 50, 255), 2)
    neon_sign(c, 510, 330, "BAR", 34, NEON_PINK)
    # Club-Tuer
    c.outlined_rect(1120, 330, 1260, H, (20, 18, 24, 255), 3)
    c.vgrad(1130, 340, 1250, H, (120, 40, 200, 255), (40, 10, 70, 255))
    c.emissive_rect(1130, 340, 1250, H, 200)
    glow_spot(c, 1190, 300, 60, (255, 40, 40, 220))
    c.circle(1190, 300, 8, (255, 90, 90, 255))
    graffiti_piece(c, 1500, 380, "TECHNO", 58, (120, 220, 255, 255), rng=rng, angle=-3)
    graffiti_piece(c, 960, 260, "RAVE", 44, (255, 220, 60, 255), rng=rng, angle=5)
    tags(c, 800, 1100, 350, 520, rng, 20)
    tags(c, 1300, 2000, 440, 540, rng, 24)
    poster_wall(c, 1700, 200, 2000, 330, rng, 2)
    # Fahrradstaender + Muelltonnen
    for i in range(5):
        bx = 1800 + i * 44
        c.d.arc(c.P(bx - 14, 480, bx + 14, 540), 180, 360, fill=(150, 150, 160, 255), width=int(3 * c.s))
    for i in range(3):
        tx = 60 + i * 64
        c.outlined_rect(tx, 470, tx + 54, H, [(60, 120, 60, 255), (60, 60, 150, 255), (40, 40, 44, 255)][i], 2)
    c.grade((60, 50, 120), 0.7, (80, 60, 120), 0.55)
    c.flush()
    # Lichterketten
    for (x0, x1, y, sag) in ((0, 1100, 180, 60), (900, 2048, 200, 70)):
        pts = []
        for i in range(31):
            t = i / 30
            pts.append((x0 + (x1 - x0) * t, y + sag * 4 * t * (1 - t)))
        c.line(pts, (20, 16, 24, 255), 1.2)
        for i, (px, py) in enumerate(pts[1:-1]):
            col = [(255, 220, 120, 255), (255, 120, 160, 255), (120, 220, 255, 255)][i % 3]
            glow_spot(c, px, py + 6, 16, col)
            c.circle(px, py + 6, 3, col)
    return c.result()


def floor_cobble():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(61)
    c.rect(0, 0, W, H, (48, 44, 50, 255))
    y = 0
    row = 0
    while y < H:
        sh = 18 + y * 0.03
        x = -(row % 2) * sh * 0.6
        while x < W:
            sw = sh * rng.uniform(1.0, 1.4)
            v = rng.randint(92, 130)
            col = (v, v - 6, v - 2, 255)
            c.ellipse(x + 1.5, y + 1.5, x + sw - 1.5, y + sh - 1.5, col)
            c.ellipse(x + 3, y + 2.5, x + sw - 5, y + sh * 0.45, shade(col, 1.12))
            x += sw
        y += sh
        row += 1
    for (px, py, pw, col) in ((260, 250, 200, NEON_PINK), (760, 360, 180, (120, 220, 255, 255))):
        c.ellipse(px - pw / 2, py - 18, px + pw / 2, py + 18, (30, 28, 50, 255))
        c.light((px - pw / 2, py - 20, px + pw / 2, py + 20),
                lambda L, px=px, py=py, pw=pw, col=col: L.ellipse(px - pw * 0.3, py - 12, px + pw * 0.1, py + 12,
                                                                  (*col[:3], 150)), blur=7, strength=1.2)
    c.grade((80, 60, 130), 0.5, (40, 36, 80), 0.64)
    c.flush()
    return c.result()


def tree():
    W, H = 260, 900
    c = Canvas(W, H, k=2)
    c.rect(112, 260, 148, H, (30, 24, 26, 255))
    c.rect(118, 260, 128, H, (54, 44, 44, 255))
    c.line([(130, 380), (60, 250)], (30, 24, 26, 255), 10)
    c.line([(130, 330), (210, 220)], (30, 24, 26, 255), 9)
    rng = random.Random(9)
    for _ in range(40):
        x, y, r = rng.uniform(20, 240), rng.uniform(20, 300), rng.uniform(30, 60)
        c.circle(x, y, r, (24, 40, 36, rng.randint(200, 255)))
    for _ in range(20):
        x, y, r = rng.uniform(40, 220), rng.uniform(40, 260), rng.uniform(14, 30)
        c.circle(x, y, r, (40, 70, 56, 255))
    return c.result()


# ---------------------------------------------------------------------------
# Stage 3: Baustelle am Alexanderplatz + Dach
# ---------------------------------------------------------------------------
def sky_alex():
    W, H = 2400, 700
    c = Canvas(W, H, k=1)
    _night_sky(c, W, H, 41, top=(8, 8, 28, 255), mid=(40, 26, 80, 255), bottom=(170, 70, 90, 255))
    _skyline(c, W, H, 150, 320, (50, 36, 80, 255), 0.1, 51, [(255, 200, 150, 200), (170, 190, 255, 180)])
    _tv_tower(c, 1820, H + 120, 1.25)
    _crane(c, 600, H, 520, 260, 180)
    _crane(c, 1850, H, 460, 160, 300)
    _skyline(c, W, H, 60, 160, (28, 20, 48, 255), 0.18, 52, [(255, 196, 120, 255), (150, 180, 255, 255)])
    return c.result()


def sky_rooftop():
    W, H = 2400, 700
    c = Canvas(W, H, k=1)
    _night_sky(c, W, H, 43, top=(8, 8, 28, 255), mid=(44, 28, 86, 255), bottom=(190, 80, 100, 255))
    # Stadt von oben: dichte Lichter am Horizont
    c.vgrad(0, H - 240, W, H, (40, 28, 70, 255), (24, 18, 40, 255))
    rng = random.Random(44)
    for _ in range(2600):
        x, y = rng.uniform(0, W), rng.uniform(H - 230, H)
        c.circle(x, y, rng.uniform(0.6, 1.6), rng.choice([(255, 210, 140, 255), (255, 170, 90, 255),
                                                          (170, 200, 255, 255), (255, 255, 230, 255)]))
    for k in range(6):
        y = H - 200 + k * 34
        c.light((0, y - 10, W, y + 10), lambda L, y=y: L.line([(0, y), (W, y + 20)], (255, 170, 90, 150), 2),
                blur=4)
    c.light((0, H - 260, W, H), lambda L: L.rect(0, H - 240, W, H, (255, 140, 90, 90)), blur=60)
    _tv_tower(c, 1500, H + 420, 1.5)
    return c.result()


def construction_tile(variant):
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(300 + variant)
    # Rohbau mit Geruest im Hintergrund
    shell = (110, 108, 112, 255)
    c.rect(100, 40, 1500, H, shell)
    c.texture(100, 40, 1500, H, amount=14, grain=3, seed=11)
    for fy in range(40, H, 90):
        c.rect(100, fy, 1500, fy + 12, shade(shell, 0.8))
        for wx in range(140, 1480, 110):
            c.rect(wx, fy + 22, wx + 70, fy + 80, (24, 22, 30, 255))
            if rng.random() < 0.12:
                c.rect(wx, fy + 22, wx + 70, fy + 80, (255, 200, 120, 255))
                c.emissive_rect(wx, fy + 22, wx + 70, fy + 80, 200)
    # Geruest
    for gx in range(100, 1520, 100):
        c.rect(gx, 20, gx + 5, H, (180, 180, 190, 255))
    for gy in range(40, H, 90):
        c.rect(90, gy + 60, 1510, gy + 66, (170, 170, 180, 255))
        c.rect(90, gy + 66, 1510, gy + 72, (150, 110, 60, 255))
    c.light((100, 20, 1500, H), lambda L: L.rect(100, 20, 1500, H, (40, 140, 80, 50)), blur=2, mode="over")
    # Baucontainer
    if variant == 0:
        cx0 = 1560
        for k in range(2):
            y = H - 120 - k * 116
            c.outlined_rect(cx0, y, cx0 + 400, y + 112, (220, 220, 214, 255), 3)
            for wx in range(cx0 + 30, cx0 + 380, 110):
                c.outlined_rect(wx, y + 26, wx + 70, y + 76, (40, 50, 70, 255), 2)
                if rng.random() < 0.6:
                    c.vgrad(wx, y + 26, wx + 70, y + 76, (255, 230, 170, 255), (220, 170, 110, 255))
                    c.emissive_rect(wx, y + 26, wx + 70, y + 76, 210)
    else:
        # Dixi-Klos + Betonmischer
        for i, col in enumerate([(40, 120, 200, 255), (40, 120, 200, 255), (60, 170, 80, 255)]):
            dx = 1580 + i * 100
            c.outlined_rect(dx, H - 230, dx + 84, H, col, 3)
            c.rect(dx + 6, H - 222, dx + 78, H - 214, shade(col, 1.3))
            c.rect(dx + 30, H - 180, dx + 54, H - 170, (240, 240, 240, 255))
        c.outlined_rect(1880, H - 140, 2040, H - 40, (240, 150, 30, 255), 3)
        c.circle(1920, H - 30, 26, LINE)
        c.circle(2010, H - 30, 26, LINE)
    # Bauzaun mit Bannern
    fy = H - 190
    c.rect(0, fy, W, H, (0, 0, 0, 0))
    for x in range(0, W, 180):
        c.outlined_rect(x + 4, fy, x + 176, H, (170, 172, 180, 110), 1.5)
        for k in range(int(x + 10), int(x + 176), 14):
            c.line([(k, fy), (k, H)], (150, 152, 160, 200), 1)
        for k in range(int(fy + 10), int(H), 14):
            c.line([(x + 4, k), (x + 176, k)], (150, 152, 160, 200), 1)
    ban = [("HARALD IMMOBILIEN", "Luxus-Lofts ab 2027", (40, 40, 60, 255), (230, 200, 90, 255)),
           ("BAUSTELLE", "Betreten verboten!", (240, 210, 40, 255), (20, 20, 20, 255)),
           ("MIETEN RUNTER!", "", (220, 50, 60, 255), (255, 255, 255, 255))]
    for i, (t1, t2, bg, fg) in enumerate(ban):
        bx = 90 + i * 660 + variant * 120
        c.outlined_rect(bx, fy + 30, bx + 460, fy + 150, bg, 2)
        c.text(bx + 230, fy + 70, t1, 38, fg, kind="bold")
        if t2:
            c.text(bx + 230, fy + 120, t2, 22, fg)
        if i == 2:
            graffiti_piece(c, bx + 380, fy + 150, "NEIN", 30, (255, 255, 255, 255), rng=rng, angle=-10)
    # Flutlicht
    lights = [(420, 30), (1300, 40)]
    for (lx, ly) in lights:
        c.rect(lx - 3, ly, lx + 3, H, (60, 60, 70, 255))
        c.outlined_rect(lx - 26, ly - 16, lx + 26, ly + 8, (40, 40, 48, 255), 2)
        c.rect(lx - 22, ly + 4, lx + 22, ly + 8, (255, 255, 240, 255))
        c.emissive_rect(lx - 22, ly + 4, lx + 22, ly + 8)
    c.grade((60, 70, 140), 0.72, (100, 90, 150), 0.5)
    c.flush()
    for (lx, ly) in lights:
        light_cone(c, lx, ly + 8, 40, 640, 560, (240, 250, 255, 110), 1.0)
        glow_spot(c, lx, ly + 6, 80, (255, 255, 240, 220))
    # Warnleuchten auf dem Zaun
    for x in range(90, W, 360):
        glow_spot(c, x, fy - 6, 24, (255, 170, 30, 220))
        c.circle(x, fy - 6, 5, (255, 200, 80, 255))
    return c.result()


def floor_construction():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(71)
    c.rect(0, 0, W, H, (96, 88, 80, 255))
    c.texture(0, 0, W, H, amount=18, grain=3, seed=1)
    c.texture(0, 0, W, H, amount=22, grain=0.2, seed=2)
    for _ in range(500):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        v = rng.randint(70, 140)
        c.circle(x, y, rng.uniform(0.8, 2.2), (v, v - 6, v - 12, 255))
    for ty in (120, 180):  # Reifenspuren
        for x in range(0, W, 14):
            c.rect(x, ty, x + 8, ty + 12, (70, 64, 58, 255))
    for (px, py, pw, ph) in ((200, 300, 220, 30), (720, 90, 140, 22)):  # Bretter
        c.outlined_rect(px, py, px + pw, py + ph, (170, 130, 80, 255), 1.5)
        c.line([(px + 4, py + ph / 2), (px + pw - 4, py + ph / 2)], (140, 100, 60, 255), 1)
    # Absperrband
    for x in range(0, W, 40):
        c.poly([(x, 380), (x + 20, 380), (x + 30, 392), (x + 10, 392)], (230, 40, 40, 255))
        c.poly([(x + 20, 380), (x + 40, 380), (x + 50, 392), (x + 30, 392)], (245, 245, 240, 255))
    c.ellipse(560, 230, 740, 262, (40, 36, 50, 255))
    c.light((560, 230, 740, 262), lambda L: L.ellipse(600, 236, 660, 256, (240, 250, 255, 150)), blur=6)
    c.grade((90, 90, 150), 0.42, (40, 40, 90), 0.62)
    c.flush()
    c.light((0, 0, W, 300), lambda L: L.ellipse(200, 0, 700, 260, (240, 250, 255, 60)), blur=60)
    return c.result()


def rooftop_tile():
    W, H = 2048, 560
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(90)
    # Bruestung mit Gelaender (Himmel bleibt transparent)
    c.outlined_rect(0, 460, W, H, (120, 118, 124, 255), 2)
    c.texture(0, 460, W, H, amount=12, grain=2, seed=3)
    c.rect(0, 460, W, 466, (170, 168, 174, 255))
    c.line([(0, 400), (W, 400)], (190, 190, 200, 255), 3)
    for x in range(0, W, 60):
        c.line([(x, 400), (x, 460)], (160, 160, 170, 255), 2.4)
    # Lueftung, Wassertank, Antenne, Werbetafel-Geruest
    for ax in (180, 900, 1500):
        c.outlined_rect(ax, 380, ax + 140, 470, (150, 152, 160, 255), 2)
        c.circle(ax + 70, 425, 32, (90, 92, 100, 255))
        for k in range(6):
            c.line([(ax + 70, 425), (ax + 70 + 30 * math.cos(k), 425 + 30 * math.sin(k))], (60, 60, 66, 255), 2)
    c.outlined_rect(560, 250, 720, 400, (110, 90, 80, 255), 3)
    for yy in range(262, 400, 22):
        c.rect(560, yy, 720, yy + 3, (90, 72, 64, 255))
    c.rect(570, 400, 580, 470, (60, 60, 66, 255))
    c.rect(700, 400, 710, 470, (60, 60, 66, 255))
    c.line([(1200, 470), (1200, 120)], (60, 60, 70, 255), 4)
    for k in range(4):
        c.line([(1170 + k * 4, 180 + k * 40), (1230 - k * 4, 180 + k * 40)], (60, 60, 70, 255), 3)
    glow_spot(c, 1200, 118, 30, (255, 40, 40, 220))
    # Leuchtreklame auf dem Dach (von hinten)
    c.rect(1700, 200, 1710, 460, (50, 50, 60, 255))
    c.rect(1990, 200, 2000, 460, (50, 50, 60, 255))
    neon_sign(c, 1850, 190, "HARALD IMMOBILIEN", 30, NEON_YELLOW)
    c.grade((60, 70, 140), 0.6, (90, 80, 150), 0.5)
    c.flush()
    return c.result()


def floor_rooftop():
    W, H = 1024, 420
    c = Canvas(W, H, k=2)
    c.begin_lighting()
    rng = random.Random(81)
    c.rect(0, 0, W, H, (84, 84, 92, 255))
    for y in range(0, H, 64):
        for x in range(0, W, 64):
            v = rng.randint(96, 116)
            c.rect(x + 2, y + 2, x + 62, y + 62, (v, v, v + 8, 255))
    c.texture(0, 0, W, H, amount=10, grain=1.5, seed=4)
    # Lueftungsgitter, Pfuetzen
    for (gx, gy) in ((180, 140), (700, 300)):
        c.outlined_rect(gx, gy, gx + 90, gy + 40, (70, 70, 78, 255), 2)
        for k in range(8):
            c.rect(gx + 6 + k * 10.5, gy + 6, gx + 11 + k * 10.5, gy + 34, (40, 40, 46, 255))
    c.ellipse(420, 220, 620, 256, (44, 44, 60, 255))
    c.light((420, 220, 620, 256), lambda L: L.ellipse(470, 228, 540, 248, (255, 200, 90, 140)), blur=6)
    for x in range(0, W, 12):
        c.rect(x, 0, x + 6, 8, (236, 200, 40, 255))
    c.grade((90, 90, 150), 0.42, (50, 50, 100), 0.6)
    c.flush()
    return c.result()


def scaffold():
    W, H = 200, 900
    c = Canvas(W, H, k=2)
    for x in (40, 150):
        c.rect(x, 0, x + 12, H, (170, 172, 182, 255))
        c.rect(x, 0, x + 4, H, (220, 222, 232, 255))
    for y in range(40, H, 160):
        c.line([(46, y), (156, y + 150)], (150, 152, 162, 255), 5)
        c.rect(30, y, 170, y + 10, (160, 120, 70, 255))
    c.light((0, 0, W, H), lambda L: L.rect(0, 0, W, H, (20, 10, 40, 120)), blur=1, mode="shadow")
    return c.result()
