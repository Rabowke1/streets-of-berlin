"""Mal-Werkzeuge fuer die gemalten Hintergruende.

Alle Koordinaten sind Welt-Units (1 Unit = 1 Unreal-Unit). Intern wird mit
RES (Ausgabe-Aufloesung) * K (Supersampling) Pixeln pro Unit gezeichnet.
Licht-Effekte (Glow, Lichtkegel, Schatten) werden in niedriger Aufloesung
gemalt, weichgezeichnet und dann additiv bzw. multiplikativ aufgetragen –
so entsteht der weiche, gemalte Look.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import RES, font, mix, shade

LINE = (18, 14, 26, 255)


class Canvas:
    def __init__(self, w, h, k=2, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.k = k
        self.s = RES * k
        self.img = Image.new("RGBA", (int(w * self.s), int(h * self.s)), bg)
        self.d = ImageDraw.Draw(self.img)
        # Leuchtende Flaechen (werden vom Nacht-Grading ausgenommen)
        self.emit = None
        self.ed = None
        # Aufgeschobene Licht-Effekte (werden nach dem Grading aufgetragen)
        self.deferred = None
        self._flushing = False

    # -- Licht-Pipeline -----------------------------------------------------------
    def begin_lighting(self):
        """Ab jetzt: Licht-Effekte sammeln statt sofort zeichnen, leuchtende Flaechen markieren."""
        self.emit = Image.new("L", self.img.size, 0)
        self.ed = ImageDraw.Draw(self.emit)
        self.deferred = []

    def emissive_rect(self, x0, y0, x1, y1, v=255):
        if self.ed is not None:
            self.ed.rectangle(self.P(x0, y0, x1, y1), fill=v)

    def emissive_circle(self, x, y, r, v=255):
        if self.ed is not None:
            self.ed.ellipse(self.P(x - r, y - r, x + r, y + r), fill=v)

    def later(self, fn):
        if self.deferred is not None and not self._flushing:
            self.deferred.append(fn)
        else:
            fn()

    def grade(self, top_color, top_amount, bottom_color, bottom_amount, y0=0.0, y1=None):
        """Nacht-Grading: multipliziert alle nicht-leuchtenden Flaechen mit einem vertikalen Farbverlauf."""
        y1 = self.h if y1 is None else y1
        box = self._box(0, y0, self.w, y1)
        h = box[3] - box[1]
        t = np.linspace(0, 1, max(1, h), dtype=np.float32)[:, None, None]
        tc = np.array(top_color[:3], np.float32) / 255.0
        bc = np.array(bottom_color[:3], np.float32) / 255.0
        emit = np.asarray(self.emit, np.float32) / 255.0 if self.emit is not None else None

        def fn(a, r0, r1):
            tt = t[r0:r1]
            col = tc * (1 - tt) + bc * tt
            amt = top_amount * (1 - tt) + bottom_amount * tt
            f = 1 - amt + amt * col
            if emit is not None:
                e = emit[box[1] + r0:box[1] + r1, box[0]:box[2], None]
                f = f * (1 - e) + e
            a[..., :3] = a[..., :3] * f

        self._apply(box, fn)

    def flush(self):
        items, self.deferred = self.deferred or [], None
        self._flushing = True
        for it in items:
            if callable(it):
                it()
            else:
                self.light(*it)
        self._flushing = False
        self.emit = None
        self.ed = None

    # -- Grundformen ----------------------------------------------------------
    def P(self, *v):
        return [x * self.s for x in v]

    def pts(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    def refresh(self):
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x0, y0, x1, y1, c):
        if x1 > x0 and y1 > y0:
            self.d.rectangle(self.P(x0, y0, x1 - 1.0 / self.s, y1 - 1.0 / self.s), fill=c)

    def poly(self, pts, c):
        self.d.polygon(self.pts(pts), fill=c)

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse(self.P(x0, y0, x1, y1), fill=c)

    def circle(self, x, y, r, c):
        self.ellipse(x - r, y - r, x + r, y + r, c)

    def line(self, pts, c, w=1.0):
        self.d.line(self.pts(pts), fill=c, width=max(1, int(round(w * self.s))), joint="curve")

    def text(self, x, y, s, size, c, anchor="mm", kind="condensed", stroke=0, stroke_c=None):
        f = font(int(size * self.s), kind)
        self.d.text((x * self.s, y * self.s), s, font=f, fill=c, anchor=anchor,
                    stroke_width=int(stroke * self.s), stroke_fill=stroke_c or c)

    def outlined_rect(self, x0, y0, x1, y1, c, ol=2.0, oc=LINE):
        self.rect(x0 - ol, y0 - ol, x1 + ol, y1 + ol, oc)
        self.rect(x0, y0, x1, y1, c)

    # -- Verlaeufe --------------------------------------------------------------
    def vgrad(self, x0, y0, x1, y1, c0, c1, ease=1.0):
        box = self._box(x0, y0, x1, y1)
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= 0 or h <= 0:
            return
        t = np.linspace(0.0, 1.0, h, dtype=np.float32) ** ease
        c0 = np.array(c0, np.float32)
        c1 = np.array(c1, np.float32)
        col = (c0[None, :] * (1 - t[:, None]) + c1[None, :] * t[:, None]).astype(np.uint8)
        g = Image.fromarray(col.reshape(h, 1, 4), "RGBA").resize((w, h), Image.NEAREST)
        self.img.alpha_composite(g, (box[0], box[1]))

    def hgrad(self, x0, y0, x1, y1, c0, c1):
        box = self._box(x0, y0, x1, y1)
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= 0 or h <= 0:
            return
        t = np.linspace(0.0, 1.0, w, dtype=np.float32)
        c0 = np.array(c0, np.float32)
        c1 = np.array(c1, np.float32)
        col = (c0[None, :] * (1 - t[:, None]) + c1[None, :] * t[:, None]).astype(np.uint8)
        g = Image.fromarray(col.reshape(1, w, 4), "RGBA").resize((w, h), Image.NEAREST)
        self.img.alpha_composite(g, (box[0], box[1]))

    # -- Pixel-Operationen (in Streifen, um Speicher zu sparen) -------------------
    def _box(self, x0, y0, x1, y1):
        W, H = self.img.size
        return (max(0, int(x0 * self.s)), max(0, int(y0 * self.s)),
                min(W, int(math.ceil(x1 * self.s))), min(H, int(math.ceil(y1 * self.s))))

    def _apply(self, box, fn, strip=384):
        x0, y0, x1, y1 = box
        if x1 <= x0 or y1 <= y0:
            return
        for sy in range(y0, y1, strip):
            ey = min(y1, sy + strip)
            reg = self.img.crop((x0, sy, x1, ey))
            a = np.asarray(reg, dtype=np.float32).copy()
            fn(a, sy - y0, ey - y0)
            self.img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), (x0, sy))
        self.refresh()

    def texture(self, x0, y0, x1, y1, amount=10.0, grain=6.0, seed=0, only_opaque=True):
        """Putz-/Material-Rauschen: grobe Flecken + feines Korn."""
        box = self._box(x0, y0, x1, y1)
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= 0 or h <= 0:
            return
        rng = np.random.default_rng(seed)
        cw, ch = max(2, int(w / (grain * 8 * self.s)) + 2), max(2, int(h / (grain * 8 * self.s)) + 2)
        coarse = Image.fromarray((rng.random((ch, cw)) * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
        coarse = np.asarray(coarse, np.float32) / 255.0 - 0.5
        fine_small = Image.fromarray((rng.random((max(2, h // 3), max(2, w // 3))) * 255).astype(np.uint8), "L")
        fine = np.asarray(fine_small.resize((w, h), Image.BILINEAR), np.float32) / 255.0 - 0.5
        noise = coarse * 1.4 + fine * 0.6

        def fn(a, r0, r1):
            n = noise[r0:r1, :, None] * amount
            if only_opaque:
                n = n * (a[..., 3:4] / 255.0)
            a[..., :3] += n

        self._apply(box, fn)

    def tint(self, x0, y0, x1, y1, top_color, top_amount, bottom_color, bottom_amount, mode="multiply"):
        """Vertikaler Licht-/Schatten-Verlauf ueber einen Bereich."""
        box = self._box(x0, y0, x1, y1)
        h = box[3] - box[1]
        if h <= 0:
            return
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        tc = np.array(top_color[:3], np.float32)
        bc = np.array(bottom_color[:3], np.float32)

        def fn(a, r0, r1):
            tt = t[r0:r1]
            col = tc * (1 - tt) + bc * tt
            amt = top_amount * (1 - tt) + bottom_amount * tt
            if mode == "multiply":
                a[..., :3] = a[..., :3] * (1 - amt + amt * col / 255.0)
            else:
                a[..., :3] = a[..., :3] + col * amt

        self._apply(box, fn)

    def light(self, bbox, painter, blur=12.0, mode="add", strength=1.0, scale=0.25):
        """Weiches Licht: painter(L) malt in eine niedrig aufgeloeste Ebene, die weichgezeichnet
        und additiv ('add'), per 'screen' oder abdunkelnd ('shadow') aufgetragen wird."""
        if self.deferred is not None and not self._flushing and mode in ("add", "screen"):
            self.deferred.append((bbox, painter, blur, mode, strength, scale))
            return
        pad = blur * 3
        x0, y0, x1, y1 = bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad
        box = self._box(x0, y0, x1, y1)
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= 0 or h <= 0:
            return
        ls = self.s * scale
        lw, lh = max(1, int(w * scale)), max(1, int(h * scale))
        low = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        L = LightPainter(low, box[0] / self.s, box[1] / self.s, ls)
        painter(L)
        if blur > 0:
            low = low.filter(ImageFilter.GaussianBlur(blur * ls))
        up = np.asarray(low.resize((w, h), Image.BILINEAR), np.float32)

        def fn(a, r0, r1):
            l = up[r0:r1]
            la = l[..., 3:4] / 255.0 * strength
            if mode == "add":
                a[..., :3] += l[..., :3] * la
            elif mode == "screen":
                a[..., :3] = 255 - (255 - a[..., :3]) * (1 - l[..., :3] / 255.0 * la)
            elif mode == "shadow":
                a[..., :3] = a[..., :3] * (1 - la * (1 - l[..., :3] / 255.0))
            elif mode == "over":
                a[..., :3] = a[..., :3] * (1 - la) + l[..., :3] * la
                a[..., 3:4] = np.maximum(a[..., 3:4], la * 255)

        self._apply(box, fn)

    def result(self):
        return self.img.resize((int(self.w * RES), int(self.h * RES)), Image.LANCZOS)


class LightPainter:
    """Zeichnet in eine Licht-Ebene mit Welt-Koordinaten."""

    def __init__(self, img, ox, oy, s):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.ox, self.oy, self.s = ox, oy, s

    def _p(self, x, y):
        return ((x - self.ox) * self.s, (y - self.oy) * self.s)

    def poly(self, pts, c):
        self.d.polygon([self._p(x, y) for x, y in pts], fill=c)

    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle([*self._p(x0, y0), *self._p(x1, y1)], fill=c)

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse([*self._p(x0, y0), *self._p(x1, y1)], fill=c)

    def circle(self, x, y, r, c):
        self.ellipse(x - r, y - r, x + r, y + r, c)

    def line(self, pts, c, w):
        self.d.line([self._p(x, y) for x, y in pts], fill=c, width=max(1, int(w * self.s)), joint="curve")

    def text(self, x, y, s, size, c, anchor="mm", kind="condensed", stroke=0):
        f = font(max(4, int(size * self.s)), kind)
        self.d.text(self._p(x, y), s, font=f, fill=c, anchor=anchor, stroke_width=int(stroke * self.s),
                    stroke_fill=c)


# ---------------------------------------------------------------------------
# Wiederverwendbare Motive
# ---------------------------------------------------------------------------
def neon_sign(c, x, y, text, size, col, board=True, kind="condensed"):
    """Neonschrift mit Glow, weissem Kern und dunklem Schild."""
    f = font(int(size * c.s), kind)
    bw = f.getlength(text) / c.s
    if board:
        c.outlined_rect(x - bw / 2 - 16, y - size * 0.72, x + bw / 2 + 16, y + size * 0.72, (22, 18, 30, 255), 2.5)
        c.line([(x - bw / 2 - 12, y + size * 0.62), (x + bw / 2 + 12, y + size * 0.62)], (44, 38, 56, 255), 2)
    c.light((x - bw / 2 - 30, y - size, x + bw / 2 + 30, y + size),
            lambda L: L.text(x, y, text, size, (*col[:3], 255), kind=kind, stroke=size * 0.12), blur=size * 0.35,
            strength=1.2)
    c.light((x - bw / 2 - 60, y - size * 2, x + bw / 2 + 60, y + size * 2),
            lambda L: L.rect(x - bw / 2, y - size * 0.5, x + bw / 2, y + size * 0.5, (*col[:3], 90)),
            blur=size * 1.2, strength=1.0)

    def crisp():
        c.text(x, y, text, size, (*mix(col, (255, 255, 255, 255), 0.25)[:3], 255), kind=kind, stroke=size * 0.06,
               stroke_c=col)
        c.text(x, y, text, size, (255, 255, 245, 255), kind=kind)
    c.later(crisp)


def glow_spot(c, x, y, r, col, strength=1.0):
    c.light((x - r, y - r, x + r, y + r), lambda L: L.circle(x, y, r * 0.5, col), blur=r * 0.45,
            strength=strength)


def light_cone(c, x, y, w_top, w_bottom, length, col, strength=0.8):
    """Lichtkegel einer Lampe nach unten."""
    def paint(L):
        steps = 8
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            a = int(col[3] * (1 - t0) ** 1.4)
            L.poly([(x - w_top / 2 - (w_bottom - w_top) / 2 * t0, y + length * t0),
                    (x + w_top / 2 + (w_bottom - w_top) / 2 * t0, y + length * t0),
                    (x + w_top / 2 + (w_bottom - w_top) / 2 * t1, y + length * t1),
                    (x - w_top / 2 - (w_bottom - w_top) / 2 * t1, y + length * t1)], (*col[:3], a))
    c.light((x - w_bottom, y, x + w_bottom, y + length), paint, blur=w_top * 0.4, strength=strength)


def drop_shadow(c, x0, y0, x1, y1, depth, amount=0.45):
    """Weicher Schatten unter einer Kante (Gesims, Markise, Balkon)."""
    c.light((x0, y0, x1, y0 + depth),
            lambda L: L.rect(x0, y0, x1, y0 + depth * 0.6, (20, 10, 40, int(255 * amount))),
            blur=depth * 0.35, mode="shadow")


def bricks(c, x0, y0, x1, y1, base, rng, bw=26, bh=9):
    c.rect(x0, y0, x1, y1, shade(base, 0.6))
    row = 0
    y = y0
    while y < y1:
        off = (bw / 2) if row % 2 else 0
        x = x0 - off
        while x < x1:
            v = rng.uniform(0.82, 1.12)
            col = shade(base, v) if v <= 1 else shade(base, 1 + (v - 1))
            c.rect(max(x0, x + 1), y + 1, min(x1, x + bw - 1), min(y1, y + bh - 1), col)
            x += bw
        y += bh
        row += 1


def graffiti_piece(c, x, y, text, size, fill, outline_col=(20, 16, 24, 255), shadow_col=None, angle=0, drips=True,
                   rng=None):
    """Bubble-Graffiti mit 3D-Schatten, Kontur, Highlight und Tropfen."""
    rng = rng or random.Random(1)
    s = c.s
    f = font(int(size * s), "condensed")
    tw = int(f.getlength(text) + size * s * 1.2)
    th = int(size * s * 2.2)
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = tw / 2, th / 2
    shadow_col = shadow_col or shade(fill, 0.35)
    for i in range(int(size * 0.18 * s), 0, -max(1, int(s))):
        ld.text((cx + i, cy + i), text, font=f, fill=shadow_col, anchor="mm", stroke_width=int(size * 0.12 * s),
                stroke_fill=outline_col)
    ld.text((cx, cy), text, font=f, fill=fill, anchor="mm", stroke_width=int(size * 0.12 * s),
            stroke_fill=outline_col)
    ld.text((cx, cy), text, font=f, fill=fill, anchor="mm", stroke_width=int(size * 0.04 * s),
            stroke_fill=shade(fill, 1.35))
    ld.text((cx, cy), text, font=f, fill=fill, anchor="mm")
    # Highlight-Streifen
    hl = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(hl).text((cx, cy - size * 0.18 * s), text, font=f, fill=255, anchor="mm")
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).text((cx, cy), text, font=f, fill=255, anchor="mm")
    hl_only = Image.fromarray(np.minimum(np.asarray(mask), 255 - np.asarray(hl)).astype(np.uint8))
    layer.paste(Image.new("RGBA", (tw, th), shade(fill, 0.75)), (0, 0), hl_only)
    if drips:
        for _ in range(int(len(text) * 1.5)):
            dx = rng.uniform(-tw * 0.35, tw * 0.35)
            L = rng.uniform(0.2, 0.7) * size * s
            ld.line([(cx + dx, cy + size * 0.3 * s), (cx + dx, cy + size * 0.3 * s + L)], fill=fill,
                    width=max(2, int(size * 0.05 * s)))
            ld.ellipse([cx + dx - size * 0.04 * s, cy + size * 0.3 * s + L - size * 0.04 * s,
                        cx + dx + size * 0.04 * s, cy + size * 0.3 * s + L + size * 0.04 * s], fill=fill)
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    c.img.alpha_composite(layer, (int(x * s - layer.width / 2), int(y * s - layer.height / 2)))
    c.refresh()


def tags(c, x0, x1, y0, y1, rng, n=8, cols=None):
    cols = cols or [(235, 235, 235, 255), (26, 26, 30, 255), (230, 60, 150, 255), (70, 200, 235, 255),
                    (250, 210, 60, 255)]
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        col = rng.choice(cols)
        w = rng.uniform(1.5, 3.2)
        pts = [(x, y)]
        for i in range(rng.randint(5, 10)):
            pts.append((pts[-1][0] + rng.uniform(3, 9), y + rng.uniform(-9, 9)))
        c.line(pts, col, w)
        if rng.random() < 0.4:
            c.line([(x, y + 12), (pts[-1][0], y + 13)], col, w * 0.7)


def poster_wall(c, x0, y0, x1, y1, rng, layers=3):
    """Mehrlagige, abgerissene Plakate."""
    palette = [(230, 70, 60, 255), (245, 215, 70, 255), (70, 150, 230, 255), (240, 240, 232, 255),
               (40, 40, 48, 255), (230, 110, 180, 255), (90, 200, 140, 255)]
    for _ in range(layers):
        x = x0
        while x < x1 - 20:
            w = rng.uniform(40, 70)
            h = rng.uniform(60, 90)
            y = rng.uniform(y0, max(y0, y1 - h))
            col = rng.choice(palette)
            ex = min(x1, x + w)
            c.rect(x, y, ex, y + h, col)
            c.rect(x + 5, y + 6, ex - 5, y + 20, shade(col, 0.55))
            c.rect(x + 5, y + 26, ex - 5, y + h * 0.6, mix(col, rng.choice(palette), 0.5))
            c.text((x + ex) / 2, y + h * 0.75, rng.choice(["KIEZ", "RAVE", "LIVE", "SALE", "DEMO", "FEST"]),
                   h * 0.14, shade(col, 0.4))
            if rng.random() < 0.5:
                # abgerissene Ecke
                c.poly([(ex, y + h), (ex - rng.uniform(10, 25), y + h), (ex, y + h - rng.uniform(15, 35))],
                       shade(col, 0.5))
            x += w + rng.uniform(-8, 6)
