"""Hintergruende fuer Stage 1: Kreuzberg bei Nacht + U-Bahnhof Kottbusser Tor.

Layer (Hoehen in Pixeln = Unreal-Units):
  Sky    2400x700  Parallax 0.15   (Himmel, Fernsehturm, Plattenbauten)
  Street 2048x560  Parallax 1.0    (Fassaden, Laeden)   Unterkante = Welt-Z 300
  UBahn  2048x560  Parallax 1.0    (Bahnsteigwand, Gleis)
  Floor  1024x420  Parallax 1.0    (Gehweg / Bahnsteig) Oberkante = Welt-Z 300
  FG     Laternen / Saeulen, Parallax 1.25, vor den Figuren
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from common import font, mix, shade

K = 2  # Supersampling fuer Hintergruende
LINE = (16, 12, 24, 255)


def _img(w, h, col=(0, 0, 0, 0)):
    im = Image.new("RGBA", (w * K, h * K), col)
    return im, ImageDraw.Draw(im)


def _down(im):
    return im.resize((im.width // K, im.height // K), Image.LANCZOS)


def R(*v):
    return [x * K for x in v]


def gradient(d, x0, y0, x1, y1, c0, c1):
    for y in range(int(y0), int(y1)):
        t = (y - y0) / max(1, (y1 - y0))
        d.line([(x0, y), (x1, y)], fill=mix(c0, c1, t))


def glow_text(im, xy, text, size, col, glow=None, anchor="mm", kind="condensed", stroke=0):
    glow = glow or col
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(layer)
    f = font(size * K, kind)
    gd.text((xy[0] * K, xy[1] * K), text, font=f, fill=glow, anchor=anchor, stroke_width=4 * K, stroke_fill=glow)
    layer = layer.filter(ImageFilter.GaussianBlur(7 * K))
    im.alpha_composite(layer)
    im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    d.text((xy[0] * K, xy[1] * K), text, font=f, fill=mix(col, (255, 255, 255, 255), 0.55), anchor=anchor,
           stroke_width=stroke * K, stroke_fill=col)


def glow_rect(im, box, col, blur=10, strength=2):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle(R(*box), fill=col)
    layer = layer.filter(ImageFilter.GaussianBlur(blur * K))
    for _ in range(strength):
        im.alpha_composite(layer)


# ---------------------------------------------------------------------------
# Himmel
# ---------------------------------------------------------------------------
def sky():
    W, H = 2400, 700
    im, d = _img(W, H)
    gradient(d, 0, 0, W * K, H * K, (14, 12, 38, 255), (96, 50, 96, 255))
    rng = random.Random(2)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.55)
        r = rng.choice([0.8, 1.0, 1.4])
        a = rng.randint(120, 255)
        d.ellipse(R(x - r, y - r, x + r, y + r), fill=(255, 250, 230, a))
    # Mond
    d.ellipse(R(1840, 60, 1930, 150), fill=(250, 240, 210, 255))
    d.ellipse(R(1862, 52, 1950, 140), fill=(24, 18, 46, 255))
    # Fernsehturm
    cx = 700
    base = H
    d.polygon(R(cx - 26, base, cx - 10, 250, cx + 10, 250, cx + 26, base), fill=(32, 28, 52, 255))
    d.ellipse(R(cx - 46, 160, cx + 46, 252), fill=(40, 34, 62, 255))
    d.ellipse(R(cx - 38, 168, cx + 30, 230), fill=(56, 48, 82, 255))
    d.rectangle(R(cx - 48, 214, cx + 48, 222), fill=(28, 24, 46, 255))
    for i in range(10):
        a = i / 10 * math.pi
        x = cx - 44 * math.cos(a)
        d.ellipse(R(x - 2, 216, x + 2, 220), fill=(255, 220, 140, 255))
    d.rectangle(R(cx - 6, 110, cx + 6, 162), fill=(34, 30, 54, 255))
    d.rectangle(R(cx - 3, 30, cx + 3, 112), fill=(40, 36, 60, 255))
    for y in (34, 70, 104):
        d.ellipse(R(cx - 5, y - 5, cx + 5, y + 5), fill=(255, 40, 40, 255))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for y in (34, 70, 104):
        gd.ellipse(R(cx - 14, y - 14, cx + 14, y + 14), fill=(255, 40, 40, 160))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8 * K)))
    # Plattenbauten / Silhouetten
    x = -40
    while x < W:
        w = rng.randint(120, 260)
        h = rng.randint(180, 420)
        col = rng.choice([(34, 28, 56, 255), (40, 32, 62, 255), (30, 26, 50, 255)])
        d.rectangle(R(x, H - h, x + w, H), fill=col)
        for wy in range(H - h + 14, H - 10, 18):
            for wx in range(x + 8, x + w - 8, 14):
                if rng.random() < 0.22:
                    c = rng.choice([(255, 210, 120, 255), (255, 190, 90, 255), (140, 180, 255, 255)])
                    d.rectangle(R(wx, wy, wx + 6, wy + 8), fill=c)
        if rng.random() < 0.3:
            d.rectangle(R(x + w // 2 - 2, H - h - 40, x + w // 2 + 2, H - h), fill=col)
            d.ellipse(R(x + w // 2 - 3, H - h - 44, x + w // 2 + 3, H - h - 38), fill=(255, 60, 60, 255))
        x += w + rng.randint(-30, 40)
    return _down(im)


# ---------------------------------------------------------------------------
# Strassen-Fassaden
# ---------------------------------------------------------------------------
FACADES = [(86, 70, 86, 255), (64, 78, 96, 255), (96, 78, 70, 255), (72, 86, 76, 255), (100, 90, 104, 255)]


def window(d, x, y, w, h, rng, lit_p=0.4):
    frame = (40, 34, 44, 255)
    d.rectangle(R(x - 4, y - 4, x + w + 4, y + h + 4), fill=LINE)
    r = rng.random()
    if r < lit_p:
        col = rng.choice([(255, 206, 120, 255), (255, 186, 96, 255), (250, 226, 160, 255)])
    elif r < lit_p + 0.08:
        col = (110, 150, 255, 255)
    else:
        col = (32, 38, 60, 255)
    d.rectangle(R(x, y, x + w, y + h), fill=col)
    d.line(R(x + w / 2, y, x + w / 2, y + h), fill=frame, width=3 * K)
    d.line(R(x, y + h * 0.35, x + w, y + h * 0.35), fill=frame, width=3 * K)
    if col[0] > 200 and rng.random() < 0.5:
        # Vorhang
        d.polygon(R(x, y, x + w * 0.3, y, x + w * 0.12, y + h), fill=shade(col, 0.8))


def altbau(im, d, x0, x1, top, base, col, rng, floors=4):
    """Berliner Altbau mit Stuck-Gesimsen."""
    d.rectangle(R(x0, top, x1, base), fill=col)
    d.rectangle(R(x0, top, x1, top + 16), fill=shade(col, 1.18))
    d.rectangle(R(x0 - 6, top + 16, x1 + 6, top + 26), fill=shade(col, 0.7))
    d.line(R(x0, top, x0, base), fill=LINE, width=3 * K)
    d.line(R(x1, top, x1, base), fill=LINE, width=3 * K)
    shop_top = base - 170
    fh = (shop_top - top - 40) / floors
    n = max(2, int((x1 - x0) / 110))
    ww = 46
    step = (x1 - x0) / n
    for f in range(floors):
        fy = top + 40 + f * fh
        d.rectangle(R(x0, fy + fh - 10, x1, fy + fh - 4), fill=shade(col, 0.78))
        for i in range(n):
            wx = x0 + step * i + (step - ww) / 2
            window(d, wx, fy + 12, ww, fh - 36, rng)
            d.rectangle(R(wx - 8, fy + 4, wx + ww + 8, fy + 10), fill=shade(col, 1.15))
        if f == 1 and rng.random() < 0.7:
            # Balkon
            bx = x0 + step * rng.randint(0, n - 1) + 6
            d.rectangle(R(bx, fy + fh - 26, bx + step - 12, fy + fh - 18), fill=LINE)
            for k in range(int(bx), int(bx + step - 12), 8):
                d.line(R(k, fy + fh - 52, k, fy + fh - 24), fill=LINE, width=2 * K)
            d.line(R(bx, fy + fh - 52, bx + step - 12, fy + fh - 52), fill=LINE, width=3 * K)
    # Sockel
    d.rectangle(R(x0, shop_top, x1, base), fill=shade(col, 0.62))
    return shop_top


def shopfront(im, d, x0, x1, shop_top, base, name, neon, awning=None, rng=None):
    rng = rng or random.Random(0)
    # Schild
    d.rectangle(R(x0 + 10, shop_top + 8, x1 - 10, shop_top + 54), fill=(24, 20, 30, 255))
    glow_text(im, ((x0 + x1) / 2, shop_top + 31), name, 34, neon)
    # Schaufenster
    wx0, wx1 = x0 + 20, x1 - 90
    d.rectangle(R(wx0 - 4, shop_top + 70, wx1 + 4, base - 16), fill=LINE)
    d.rectangle(R(wx0, shop_top + 74, wx1, base - 20), fill=(250, 214, 150, 255))
    glow_rect(im, (wx0, shop_top + 74, wx1, base - 20), (255, 200, 120, 90), blur=16, strength=1)
    d = ImageDraw.Draw(im)
    # Regale
    for y in range(int(shop_top + 96), int(base - 30), 22):
        d.line(R(wx0, y, wx1, y), fill=(160, 110, 70, 255), width=3 * K)
        for x in range(int(wx0 + 6), int(wx1 - 6), 12):
            c = rng.choice([(220, 60, 60, 255), (60, 140, 220, 255), (240, 200, 60, 255), (70, 170, 80, 255)])
            d.rectangle(R(x, y - 12, x + 7, y - 1), fill=c)
    # Tuer
    d.rectangle(R(x1 - 76, shop_top + 70, x1 - 20, base), fill=LINE)
    d.rectangle(R(x1 - 72, shop_top + 74, x1 - 24, base), fill=(70, 60, 50, 255))
    d.rectangle(R(x1 - 66, shop_top + 82, x1 - 30, base - 70), fill=(250, 214, 150, 255))
    if awning:
        pts = R(x0 + 4, shop_top + 58, x1 - 4, shop_top + 58, x1 + 10, shop_top + 92, x0 - 10, shop_top + 92)
        d.polygon(pts, fill=LINE)
        stripe_w = 24
        for i, x in enumerate(range(int(x0 - 6), int(x1 + 8), stripe_w)):
            c = awning if i % 2 == 0 else (240, 236, 226, 255)
            d.polygon(R(x, shop_top + 62, x + stripe_w, shop_top + 62, x + stripe_w, shop_top + 88, x,
                        shop_top + 88), fill=c)
    return d


def graffiti(im, x, y, text, size, fill, rng, angle=0):
    layer = Image.new("RGBA", (size * K * len(text), size * K * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    f = font(size * K, "condensed")
    ld.text((layer.width / 2, layer.height / 2), text, font=f, fill=fill, anchor="mm", stroke_width=6 * K,
            stroke_fill=(20, 20, 20, 255))
    ld.text((layer.width / 2 - 2 * K, layer.height / 2 - 3 * K), text, font=f, fill=shade(fill, 1.3), anchor="mm")
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(layer, (int(x * K - layer.width / 2), int(y * K - layer.height / 2)))


def tags(d, x0, x1, y0, y1, rng, n=8):
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        c = rng.choice([(240, 240, 240, 255), (30, 30, 30, 255), (220, 60, 160, 255), (60, 200, 230, 255)])
        pts = [(x + i * 6 + rng.uniform(-3, 3), y + rng.uniform(-8, 8)) for i in range(rng.randint(4, 8))]
        d.line([(p[0] * K, p[1] * K) for p in pts], fill=c, width=3 * K, joint="curve")


def posters(d, x0, y0, rng, n=4):
    for i in range(n):
        x = x0 + i * 38 + rng.uniform(-4, 4)
        y = y0 + rng.uniform(-6, 6)
        c = rng.choice([(230, 80, 60, 255), (240, 220, 80, 255), (80, 160, 230, 255), (240, 240, 230, 255)])
        d.rectangle(R(x, y, x + 34, y + 48), fill=c)
        d.rectangle(R(x + 4, y + 6, x + 30, y + 14), fill=shade(c, 0.5))
        d.rectangle(R(x + 4, y + 30, x + 22, y + 34), fill=shade(c, 0.5))


def street_tile(variant):
    W, H = 2048, 560
    base = H
    im, d = _img(W, H)
    rng = random.Random(10 + variant)
    if variant == 0:
        top = altbau(im, d, 0, 520, 40, base, FACADES[0], rng)
        d = shopfront(im, d, 20, 500, top, base, "SPÄTI", (60, 230, 255, 255), awning=(40, 120, 200, 255),
                      rng=rng)
        top = altbau(im, d, 520, 1040, 70, base, FACADES[2], rng)
        d = shopfront(im, d, 540, 1020, top, base, "DÖNER KEBAB", (255, 200, 60, 255),
                      awning=(200, 50, 40, 255), rng=rng)
        # Baulücke mit Brandwand
        d.rectangle(R(1040, 0, 1400, base), fill=(0, 0, 0, 0))
        d.rectangle(R(1400, 20, 1460, base), fill=(110, 84, 74, 255))
        for y in range(30, base, 16):
            d.line(R(1400, y, 1460, y), fill=(90, 66, 58, 255), width=2 * K)
        # Bauzaun
        d.rectangle(R(1040, base - 150, 1400, base), fill=LINE)
        d.rectangle(R(1044, base - 146, 1396, base - 4), fill=(170, 170, 176, 255))
        for x in range(1050, 1400, 40):
            d.line(R(x, base - 146, x, base), fill=(120, 120, 130, 255), width=4 * K)
        graffiti(im, 1220, base - 80, "BERLIN", 54, (255, 90, 170, 255), rng, angle=4)
        d = ImageDraw.Draw(im)
        posters(d, 1060, base - 140, rng, 3)
        top = altbau(im, d, 1460, W, 30, base, FACADES[1], rng, floors=5)
        d.rectangle(R(1480, top + 20, W - 20, base), fill=(40, 34, 44, 255))
        d.rectangle(R(1500, top + 40, W - 40, base - 10), fill=(60, 52, 60, 255))
        # Tor zum Hinterhof
        d.rectangle(R(1560, top + 30, 1720, base), fill=LINE)
        d.rectangle(R(1566, top + 36, 1714, base), fill=(58, 44, 36, 255))
        d.line(R(1640, top + 36, 1640, base), fill=LINE, width=3 * K)
        tags(d, 1480, W - 40, top + 60, base - 20, rng, 14)
        graffiti(im, 1880, top + 90, "KIEZ", 46, (80, 220, 120, 255), rng, angle=-6)
    else:
        top = altbau(im, d, 0, 600, 60, base, FACADES[3], rng)
        d.rectangle(R(20, top + 10, 580, base), fill=(28, 22, 36, 255))
        glow_text(im, (300, top + 44), "CLUB 36", 44, (255, 60, 140, 255))
        d = ImageDraw.Draw(im)
        d.rectangle(R(240, top + 90, 360, base), fill=LINE)
        d.rectangle(R(246, top + 96, 354, base), fill=(90, 20, 60, 255))
        glow_rect(im, (246, top + 96, 354, base), (255, 40, 120, 80), blur=18)
        d = ImageDraw.Draw(im)
        tags(d, 30, 220, top + 90, base - 20, rng, 10)
        tags(d, 380, 570, top + 90, base - 20, rng, 10)
        graffiti(im, 470, top + 120, "SO36", 40, (255, 220, 60, 255), rng, angle=-8)
        d = ImageDraw.Draw(im)
        top = altbau(im, d, 600, 1180, 30, base, FACADES[4], rng)
        d = shopfront(im, d, 620, 1160, top, base, "KIOSK", (120, 255, 120, 255), awning=(40, 150, 70, 255),
                      rng=rng)
        top = altbau(im, d, 1180, 1640, 80, base, FACADES[0], rng)
        d.rectangle(R(1190, top + 10, 1630, base), fill=(52, 46, 58, 255))
        posters(d, 1210, top + 40, rng, 10)
        tags(d, 1200, 1620, top + 100, base - 10, rng, 16)
        # U-Bahn-Eingang
        top = altbau(im, d, 1640, W, 50, base, FACADES[1], rng)
        d.rectangle(R(1700, top + 10, 1990, base), fill=(20, 18, 26, 255))
        for i in range(8):
            y = top + 60 + i * 14
            d.rectangle(R(1720, y, 1970, y + 6), fill=(60, 56, 66, 255))
        d.rectangle(R(1740, top - 90, 1800, top - 30), fill=LINE)
        d.rectangle(R(1744, top - 86, 1796, top - 34), fill=(30, 90, 200, 255))
        glow_text(im, (1770, top - 60), "U", 44, (255, 255, 255, 255), glow=(80, 160, 255, 255), kind="bold")
        d = ImageDraw.Draw(im)
        d.rectangle(R(1810, top - 76, 1990, top - 44), fill=(240, 240, 236, 255))
        d.text(R(1900, top - 60), "Kottbusser Tor", font=font(20 * K), fill=(20, 20, 20, 255), anchor="mm")
        d.rectangle(R(1766, top - 30, 1774, base), fill=LINE)
    return _down(im)


# ---------------------------------------------------------------------------
# U-Bahnhof
# ---------------------------------------------------------------------------
def ubahn_tile():
    W, H = 2048, 560
    im, d = _img(W, H)
    rng = random.Random(33)
    tile = (72, 150, 140, 255)
    gradient(d, 0, 0, W * K, 60 * K, (30, 30, 36, 255), (50, 50, 56, 255))
    d.rectangle(R(0, 60, W, 470), fill=tile)
    for y in range(60, 470, 22):
        d.line(R(0, y, W, y), fill=shade(tile, 0.8), width=2 * K)
    for x in range(0, W, 44):
        d.line(R(x, 60, x, 470), fill=shade(tile, 0.85), width=1 * K)
    d.rectangle(R(0, 60, W, 74), fill=(230, 196, 50, 255))
    d.rectangle(R(0, 450, W, 470), fill=(40, 40, 46, 255))
    # Leuchtstoffroehren
    for x in range(80, W, 340):
        d.rectangle(R(x, 30, x + 180, 40), fill=(250, 250, 240, 255))
        glow_rect(im, (x, 30, x + 180, 40), (250, 250, 220, 120), blur=14)
    d = ImageDraw.Draw(im)
    # Stationsschilder
    for x in (240, 1260):
        d.rectangle(R(x - 6, 150, x + 426, 222), fill=LINE)
        d.rectangle(R(x, 156, x + 420, 216), fill=(248, 248, 244, 255))
        d.text(R(x + 210, 186), "Kottbusser Tor", font=font(40 * K), fill=(20, 20, 20, 255), anchor="mm")
    # Werbeplakate
    for x in (760, 1760):
        d.rectangle(R(x - 6, 120, x + 206, 330), fill=LINE)
        c1 = rng.choice([(220, 60, 60, 255), (60, 110, 220, 255), (240, 190, 40, 255)])
        gradient(d, x * K, 126 * K, (x + 200) * K, 324 * K, c1, shade(c1, 0.5))
        d.text(R(x + 100, 190), rng.choice(["TECHNO", "KIEZ FEST", "CURRY 36"]), font=font(26 * K, "condensed"),
               fill=(255, 255, 255, 255), anchor="mm")
        d.ellipse(R(x + 60, 230, x + 140, 310), fill=shade(c1, 1.4))
    for x in (60, 1100, 1980):
        tags(d, x - 40, x + 60, 280, 430, rng, 8)
    # Gleisbett
    d.rectangle(R(0, 470, W, H), fill=(26, 24, 28, 255))
    for x in range(0, W, 36):
        d.rectangle(R(x, 520, x + 22, 532), fill=(70, 56, 44, 255))
    d.rectangle(R(0, 508, W, 514), fill=(170, 170, 180, 255))
    d.rectangle(R(0, 538, W, 544), fill=(170, 170, 180, 255))
    return _down(im)


# ---------------------------------------------------------------------------
# Boden
# ---------------------------------------------------------------------------
def floor_street():
    W, H = 1024, 420
    im, d = _img(W, H)
    rng = random.Random(5)
    # Gehweg
    d.rectangle(R(0, 0, W, 220), fill=(92, 88, 100, 255))
    # Mosaikpflaster (Kleinpflaster) oben
    for y in range(0, 60, 9):
        for x in range(-(y % 18), W, 10):
            c = rng.randint(78, 104)
            d.rectangle(R(x, y, x + 8, y + 7), fill=(c, c - 4, c + 8, 255))
    # Granitplatten in der Mitte
    y = 64
    for row, hgt in enumerate((70, 70)):
        off = 0 if row == 0 else 60
        for x in range(-off, W, 120):
            c = rng.randint(112, 128)
            d.rectangle(R(x + 2, y + 2, x + 118, y + hgt - 2), fill=(c, c - 2, c + 8, 255))
            if rng.random() < 0.2:
                d.line(R(x + rng.randint(10, 60), y + 4, x + rng.randint(60, 110), y + hgt - 6),
                       fill=(90, 88, 96, 255), width=2 * K)
        y += hgt
    for yy in range(y, 220, 9):
        for x in range(-(yy % 18), W, 10):
            c = rng.randint(76, 100)
            d.rectangle(R(x, yy, x + 8, yy + 7), fill=(c, c - 4, c + 8, 255))
    # Gullideckel
    d.ellipse(R(700, 150, 760, 184), fill=(50, 46, 52, 255))
    for k in range(5):
        d.line(R(708, 156 + k * 6, 752, 156 + k * 6), fill=(80, 76, 84, 255), width=2 * K)
    # Bordstein
    d.rectangle(R(0, 220, W, 236), fill=(150, 146, 156, 255))
    d.rectangle(R(0, 236, W, 244), fill=(70, 66, 76, 255))
    # Asphalt
    d.rectangle(R(0, 244, W, H), fill=(52, 50, 62, 255))
    for _ in range(1600):
        x, yy = rng.uniform(0, W), rng.uniform(244, H)
        c = rng.randint(40, 72)
        d.point((x * K, yy * K), fill=(c, c, c + 8, 255))
    for x in range(40, W, 256):
        d.rectangle(R(x, 360, x + 140, 370), fill=(220, 214, 196, 255))
    # Pfuetze mit Neon-Reflex
    d.ellipse(R(300, 280, 460, 316), fill=(40, 36, 70, 255))
    d.ellipse(R(330, 288, 400, 300), fill=(200, 60, 140, 160))
    return _down(im)


def floor_platform():
    W, H = 1024, 420
    im, d = _img(W, H)
    rng = random.Random(6)
    d.rectangle(R(0, 0, W, 8), fill=(20, 20, 24, 255))
    d.rectangle(R(0, 8, W, 22), fill=(170, 166, 160, 255))
    d.rectangle(R(0, 22, W, 34), fill=(236, 200, 40, 255))
    # Blindenleitstreifen
    d.rectangle(R(0, 40, W, 64), fill=(200, 196, 190, 255))
    for x in range(0, W, 12):
        for y in (44, 52):
            d.ellipse(R(x + 2, y, x + 8, y + 6), fill=(170, 166, 160, 255))
    for yy in range(64, H, 64):
        for x in range(-(yy % 128), W, 128):
            c = rng.randint(118, 138)
            d.rectangle(R(x + 2, yy + 2, x + 126, yy + 62), fill=(c, c - 4, c - 8, 255))
            if rng.random() < 0.25:
                d.ellipse(R(x + rng.randint(10, 90), yy + rng.randint(10, 40), x + rng.randint(95, 120),
                            yy + rng.randint(42, 60)), fill=(c - 14, c - 18, c - 20, 255))
    return _down(im)


# ---------------------------------------------------------------------------
# Vordergrund
# ---------------------------------------------------------------------------
def lamp_post():
    W, H = 160, 900
    im, d = _img(W, H)
    d.rectangle(R(66, 60, 94, H), fill=(26, 30, 38, 255))
    d.rectangle(R(72, 60, 80, H), fill=(44, 50, 62, 255))
    d.rectangle(R(56, H - 120, 104, H), fill=(22, 26, 32, 255))
    d.polygon(R(20, 40, 140, 40, 120, 70, 40, 70), fill=(26, 30, 38, 255))
    d.rectangle(R(40, 68, 120, 76), fill=(255, 230, 170, 255))
    glow_rect(im, (40, 64, 120, 90), (255, 220, 150, 140), blur=20)
    return _down(im)


def pillar():
    W, H = 180, 900
    im, d = _img(W, H)
    d.rectangle(R(30, 0, 150, H), fill=(40, 90, 86, 255))
    d.rectangle(R(40, 0, 70, H), fill=(60, 120, 114, 255))
    d.rectangle(R(30, 300, 150, 330), fill=(230, 196, 50, 255))
    return _down(im)
