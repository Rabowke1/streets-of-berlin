"""2D-Puppet-Renderer im Stil moderner handgezeichneter Brawler.

Eine Figur besteht aus Koerperteilen (Kapseln / Polygone), die ueber
Gelenkwinkel (Pose) positioniert werden. Jedes Teil bekommt eine dicke
Kontur und ein Cel-Shading (harte Schattenkante unten/hinten).

Koordinatensystem des Modells: x = nach vorne (Blickrichtung rechts),
y = nach oben, Boden bei y = 0. Einheiten = finale Pixel.
"""
import math

from PIL import Image, ImageChops, ImageDraw

from common import OUTLINE, SS, add, draw_inflated, mix, mul, norm, rot, shade, sub

OL = 2.6  # Konturbreite in finalen Pixeln
HIGHLIGHT_W = 1.6  # Breite der Glanzkante
RIM_W = 2.4  # Breite des Randlichts
RIM_COLOR = (170, 215, 255, 255)
SHADOW_TINT = (70, 40, 120, 255)  # Schatten leicht violett statt nur dunkler


def dir_from_down(deg):
    """Richtung fuer einen Winkel gemessen von 'gerade nach unten', + = nach vorne."""
    a = math.radians(deg)
    return (math.sin(a), -math.cos(a))


def dir_from_up(deg):
    a = math.radians(deg)
    return (math.sin(a), math.cos(a))


class Shape:
    __slots__ = ("pts", "r", "fill", "dark", "light_shift", "outline", "details")

    def __init__(self, pts, r, fill, dark=None, light_shift=3.5, outline=True):
        self.pts = list(pts)
        self.r = r
        self.fill = fill
        self.dark = dark if dark is not None else mix(shade(fill, 0.64), SHADOW_TINT, 0.22)
        self.light_shift = light_shift
        self.outline = outline
        self.details = []  # (kind, data) Zeichnungen ohne Shading (Augen, Linien)


def limb_shape(p0, p1, w0, wm, w1, fill, **kw):
    d = norm(sub(p1, p0))
    n = (-d[1], d[0])
    k = min(w0, wm, w1) * 0.75
    pm = mul(add(p0, p1), 0.5)
    pts = [
        add(p0, mul(n, w0 - k)),
        add(pm, mul(n, wm - k)),
        add(p1, mul(n, w1 - k)),
        sub(p1, mul(n, w1 - k)),
        sub(pm, mul(n, wm - k)),
        sub(p0, mul(n, w0 - k)),
    ]
    return Shape(pts, k, fill, **kw)


def local_poly(origin, angle_deg, pts, scale=1.0):
    """Transformiert lokale Punkte (x vorne, y oben) um origin mit Drehung."""
    return [add(origin, rot((p[0] * scale, p[1] * scale), angle_deg)) for p in pts]


# ---------------------------------------------------------------------------
# Standard-Pose
# ---------------------------------------------------------------------------
BASE_POSE = {
    "t": 5.0,  # Oberkoerper-Neigung (vorne +)
    "h": 0.0,  # Kopfneigung (hoch +)
    "af": (30.0, 100.0),  # vorderer Arm: Schulter (von unten, vorne +), Ellbogen (+ = beugen)
    "ab": (20.0, 110.0),
    "lf": (18.0, 12.0, 0.0),  # vorderes Bein: Huefte, Knie (+ = beugen), Fusswinkel
    "lb": (-14.0, 14.0, 0.0),
    "rot": 0.0,  # Rotation des ganzen Koerpers (Wurf, Liegen)
    "dx": 0.0,
    "dy": 0.0,
    "face": "normal",
    "hf": "fist",  # Handform vorne: fist/open
    "hb": "fist",
    "ground": True,
}


def pose(**kw):
    p = dict(BASE_POSE)
    p.update(kw)
    return p


def blend(p1, p2, t):
    out = {}
    for k, v in p1.items():
        w = p2.get(k, v)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = v + (w - v) * t
        elif isinstance(v, tuple):
            out[k] = tuple(a + (b - a) * t for a, b in zip(v, w))
        else:
            out[k] = v if t < 0.5 else w
    return out


# ---------------------------------------------------------------------------
# Figur
# ---------------------------------------------------------------------------
class Character:
    """Beschreibt Proportionen, Farben und Stil einer Figur."""

    def __init__(self, name, **kw):
        self.name = name
        # Proportionen (finale Pixel)
        self.head_r = 18
        self.neck = 7
        self.torso = 60
        self.chest_w = 50
        self.waist_w = 36
        self.belly = 0.0
        self.upper_arm = 33
        self.forearm = 30
        self.arm_w = (9.5, 10.5, 7.5)
        self.fore_w = (8.0, 8.5, 6.5)
        self.fist_r = 9.5
        self.thigh = 44
        self.shin = 42
        self.thigh_w = (12.5, 12.5, 9.0)
        self.shin_w = (9.0, 9.5, 7.0)
        self.shoe_len = 29
        self.shoe_h = 12
        # Farben
        self.skin = (232, 176, 136, 255)
        self.hair = (40, 30, 26, 255)
        self.top = (200, 50, 40, 255)  # Oberteil
        self.top_inner = None  # sichtbares Shirt bei offener Jacke
        self.sleeve_upper = None  # None = Haut
        self.sleeve_lower = None
        self.pants = (40, 50, 80, 255)
        self.shorts = False
        self.belt = (30, 24, 20, 255)
        self.shoe = (240, 240, 240, 255)
        self.sole = (70, 70, 80, 255)
        self.glove = None
        self.eye = (30, 20, 20, 255)
        # Stil
        self.hair_style = "short"
        self.beard = False
        self.beard_color = None
        self.shades = False
        self.cap_color = (30, 30, 30, 255)
        self.logo = None  # (Text ist zu klein) -> Farbiger Aufdruck
        self.logo_color = None
        self.stripe = None  # Farbe fuer Streifen auf Hose (Trainingshose)
        self.earring = False
        self.__dict__.update(kw)

    # -- Skelett ---------------------------------------------------------
    def skeleton(self, p):
        j = {}
        hip = (0.0, 0.0)
        t = p["t"]
        up = dir_from_up(t)
        fwd = (up[1], -up[0])
        j["hip"] = hip
        j["up"] = up
        j["fwd"] = fwd
        neck = add(hip, mul(up, self.torso))
        j["neck"] = neck
        sh = add(hip, mul(up, self.torso - 9))
        j["sh_f"] = add(sh, mul(fwd, 3.0))
        j["sh_b"] = add(sh, mul(fwd, -3.0))
        j["hip_f"] = add(hip, mul(fwd, 3.0))
        j["hip_b"] = add(hip, mul(fwd, -3.0))
        head_c = add(neck, mul(dir_from_up(t * 0.6 - p["h"] * 0.3), self.neck + self.head_r * 0.85))
        j["head"] = head_c
        j["head_ang"] = -t * 0.5 + p["h"]
        for side, key in (("f", "af"), ("b", "ab")):
            s_ang, e_bend = p[key]
            s = j["sh_" + side]
            elbow = add(s, mul(dir_from_down(s_ang), self.upper_arm))
            fa = s_ang + e_bend
            wrist = add(elbow, mul(dir_from_down(fa), self.forearm))
            j["elbow_" + side] = elbow
            j["wrist_" + side] = wrist
            j["fa_ang_" + side] = fa
        for side, key in (("f", "lf"), ("b", "lb")):
            h_ang, k_bend, f_ang = p[key]
            hp = j["hip_" + side]
            knee = add(hp, mul(dir_from_down(h_ang), self.thigh))
            sa = h_ang - k_bend
            ankle = add(knee, mul(dir_from_down(sa), self.shin))
            j["knee_" + side] = knee
            j["ankle_" + side] = ankle
            j["foot_ang_" + side] = f_ang
            j["shin_ang_" + side] = sa
        return j

    # -- Teile -----------------------------------------------------------
    def _arm(self, j, side, p, dim):
        f = (lambda c: shade(c, 0.8)) if dim else (lambda c: c)
        upper_c = f(self.sleeve_upper or self.skin)
        lower_c = f(self.sleeve_lower or self.skin)
        fist_c = f(self.glove or self.skin)
        s, e, w = j["sh_" + side], j["elbow_" + side], j["wrist_" + side]
        shapes = [
            limb_shape(s, e, *self.arm_w, upper_c),
            limb_shape(e, w, *self.fore_w, lower_c),
        ]
        d = norm(sub(w, e))
        hand = p["hf"] if side == "f" else p["hb"]
        if hand == "open":
            c = add(w, mul(d, self.fist_r * 0.9))
            n = (-d[1], d[0])
            pts = [add(c, mul(d, self.fist_r * 0.8)), add(c, mul(n, self.fist_r * 0.35)),
                   sub(c, mul(d, self.fist_r * 0.5)), sub(c, mul(n, self.fist_r * 0.35))]
            shapes.append(Shape(pts, self.fist_r * 0.45, fist_c, light_shift=2))
        else:
            c = add(w, mul(d, self.fist_r * 0.55))
            fist = Shape([c], self.fist_r, fist_c, light_shift=2.5)
            n = (-d[1], d[0])
            knuckle = add(c, mul(d, self.fist_r * 0.35))
            fist.details.append(("line", [add(knuckle, mul(n, self.fist_r * 0.6)),
                                          sub(knuckle, mul(n, self.fist_r * 0.6))], shade(fist_c, 0.6), 1.0))
            shapes.append(fist)
        # Muskel-/Faltenlinie am Oberarm
        de = norm(sub(e, s))
        ne = (-de[1], de[0])
        mid = mul(add(s, e), 0.5)
        shapes[0].details.append(("line", [add(mid, mul(ne, -2)), add(add(mid, mul(de, 8)), mul(ne, -4))],
                                  shade(upper_c, 0.7), 1.0))
        return shapes

    def _leg(self, j, side, dim):
        f = (lambda c: shade(c, 0.8)) if dim else (lambda c: c)
        hp, k, a = j["hip_" + side], j["knee_" + side], j["ankle_" + side]
        thigh_c = f(self.pants)
        shin_c = f(self.skin if self.shorts else self.pants)
        shapes = [limb_shape(hp, k, *self.thigh_w, thigh_c)]
        if self.stripe is not None:
            pass
        shapes.append(limb_shape(k, a, *self.shin_w, shin_c))
        if self.shorts:
            # Hosenbein-Abschluss am Knie
            shapes[0] = limb_shape(hp, add(k, mul(norm(sub(k, hp)), 4)), *self.thigh_w, thigh_c)
        # Naht / Falten
        seam_c = shade(thigh_c, 0.72)
        dth = norm(sub(k, hp))
        nth = (-dth[1], dth[0])
        shapes[0].details.append(("line", [add(hp, mul(nth, 3)), add(k, mul(nth, 2))], seam_c, 1.0))
        kf = add(k, mul(nth, -self.thigh_w[2] * 0.4))
        shapes[0].details.append(("line", [sub(kf, mul(dth, 7)), add(kf, mul(nth, 4))], seam_c, 1.2))
        if not self.shorts:
            dsh = norm(sub(a, k))
            nsh = (-dsh[1], dsh[0])
            shapes[-1].details.append(("line", [add(k, mul(nsh, 2)), add(a, mul(nsh, 1.5))], seam_c, 1.0))
        if self.stripe is not None:
            s1 = limb_shape(add(hp, (0, 0)), k, 2.0, 2.0, 2.0, f(self.stripe), outline=False, light_shift=0)
            s2 = limb_shape(k, a, 1.8, 1.8, 1.8, f(self.stripe), outline=False, light_shift=0)
            shapes += [s1, s2]
        # Schuh
        fa = j["foot_ang_" + side]
        L, H = self.shoe_len, self.shoe_h
        loc = [(-0.28 * L, 0.45 * H), (0.30 * L, 0.35 * H), (0.78 * L, 0.02 * H),
               (0.86 * L, -0.55 * H), (-0.30 * L, -0.55 * H)]
        pts = local_poly(a, fa, loc)
        shoe = Shape(pts, 3.0, f(self.shoe), light_shift=2.5)
        lace = local_poly(a, fa, [(0.05 * L, 0.30 * H), (0.30 * L, 0.22 * H), (0.12 * L, 0.10 * H),
                                  (0.40 * L, 0.05 * H)])
        shoe.details.append(("line", lace, shade(f(self.shoe), 0.6), 1.0))
        shapes.append(shoe)
        sole = local_poly(a, fa, [(-0.30 * L, -0.42 * H), (0.86 * L, -0.42 * H)])
        shapes.append(Shape(sole, 2.2, f(self.sole), outline=False, light_shift=0))
        return shapes

    def _torso(self, j, p):
        t = p["t"]
        L = self.torso
        cw, ww, bl = self.chest_w / 2.0, self.waist_w / 2.0, self.belly
        r = 5.0
        loc = [
            (-ww + r, 0.0 + r),
            (-ww * 1.02 + r, 0.35 * L),
            (-cw * 0.95 + r, 0.70 * L),
            (-cw * 0.80 + r, L - r),
            (cw * 0.55 - r, L - r),
            (cw + 2 - r, 0.78 * L),
            (cw * 0.95 + bl * 0.4 - r, 0.55 * L),
            (ww + bl - r, 0.28 * L),
            (ww + bl * 0.5 - r, 0.06 * L + r),
        ]
        pts = local_poly(j["hip"], -t, loc)
        torso = Shape(pts, r, self.top, light_shift=5.0)
        fold_c = shade(self.top, 0.68)
        # Stofffalten
        for (a0, a1) in (((-cw * 0.5, 0.30 * L), (-cw * 0.1, 0.42 * L)), ((-cw * 0.6, 0.55 * L), (-cw * 0.2, 0.62 * L)),
                         ((ww * 0.2, 0.18 * L), (ww * 0.7, 0.24 * L))):
            torso.details.append(("line", local_poly(j["hip"], -t, [a0, a1]), fold_c, 1.1))
        shapes = [torso]
        if self.top_inner is not None:
            inner = [
                (cw * 0.35, 0.93 * L), (cw + 1.5, 0.80 * L), (cw * 0.95 + bl * 0.4, 0.55 * L),
                (ww + bl, 0.28 * L), (ww * 0.6, 0.20 * L), (cw * 0.25, 0.55 * L),
            ]
            s = Shape(local_poly(j["hip"], -t, inner), 1.5, self.top_inner, light_shift=4.0, outline=False)
            # Jackenkante + Kragen
            s.details.append(("line", local_poly(j["hip"], -t, [(cw * 0.25, 0.55 * L), (ww * 0.6, 0.20 * L)]),
                              shade(self.top, 0.55), 1.6))
            s.details.append(("line", local_poly(j["hip"], -t, [(cw * 0.35, 0.93 * L), (cw * 0.25, 0.55 * L)]),
                              shade(self.top, 0.55), 1.6))
            shapes.append(s)
            if getattr(self, "tie", None):
                tie = local_poly(j["hip"], -t, [(cw * 0.62, 0.90 * L), (cw * 0.78, 0.86 * L), (cw * 0.74, 0.40 * L),
                                                (cw * 0.62, 0.34 * L), (cw * 0.52, 0.42 * L)])
                shapes.append(Shape(tie, 1.2, self.tie, light_shift=2.0))
            collar = local_poly(j["hip"], -t, [(-cw * 0.55, 0.97 * L), (cw * 0.1, 1.02 * L), (cw * 0.42, 0.88 * L)])
            shapes.append(Shape(collar, 2.4, shade(self.top, 1.1), light_shift=1.5))
        if self.logo_color is not None:
            c = local_poly(j["hip"], -t, [(cw * 0.25, 0.62 * L)])[0]
            shapes.append(Shape([c], 6.5, self.logo_color, outline=False, light_shift=0))
        # Guertel
        belt = local_poly(j["hip"], -t, [(-ww * 0.95, 0.08 * L), (ww + bl * 0.4, 0.08 * L)])
        shapes.append(Shape(belt, 3.4, self.belt, outline=False, light_shift=0))
        return shapes

    def _pelvis(self, j):
        c = add(j["hip"], mul(j["up"], 3))
        return Shape([add(c, mul(j["fwd"], -4)), add(c, mul(j["fwd"], 4))], self.waist_w * 0.42, self.pants,
                     light_shift=3)

    def _neck(self, j):
        return limb_shape(j["neck"], j["head"], 6.0, 6.0, 6.0, shade(self.skin, 0.85), light_shift=2)

    def _head(self, j, p):
        R = self.head_r
        c = j["head"]
        a = j["head_ang"]
        loc = [
            (-0.86, 0.05), (-0.66, 0.66), (0.0, 0.88), (0.64, 0.56), (0.80, 0.22),
            (1.02, -0.02), (0.84, -0.18), (0.86, -0.38), (0.72, -0.66), (0.42, -0.84),
            (-0.10, -0.70), (-0.52, -0.40),
        ]
        pts = local_poly(c, a, [(x * R, y * R) for x, y in loc])
        head = Shape(pts, R * 0.14, self.skin, light_shift=3.5)
        shapes = [head]
        # Ohr
        ear = local_poly(c, a, [(-0.18 * R, -0.02 * R)])
        shapes.append(Shape(ear, R * 0.2, shade(self.skin, 0.93), light_shift=1.5))
        if self.earring:
            shapes.append(Shape(local_poly(c, a, [(-0.2 * R, -0.28 * R)]), 1.8, (240, 210, 80, 255),
                                outline=False, light_shift=0))
        if self.beard:
            bc = self.beard_color or self.hair
            bl = [(-0.30, -0.18), (0.10, -0.40), (0.62, -0.46), (0.86, -0.40), (0.80, -0.70),
                  (0.42, -0.94), (-0.08, -0.78), (-0.36, -0.46)]
            shapes.append(Shape(local_poly(c, a, [(x * R, y * R) for x, y in bl]), 2.0, bc, light_shift=2.5))
        # Gesicht (Details)
        face = p["face"]
        eye = local_poly(c, a, [(0.52 * R, 0.14 * R)])[0]
        brow0 = local_poly(c, a, [(0.30 * R, 0.36 * R)])[0]
        brow1 = local_poly(c, a, [(0.80 * R, 0.30 * R if face != "angry" else 0.20 * R)])[0]
        m0 = local_poly(c, a, [(0.62 * R, -0.46 * R)])[0]
        m1 = local_poly(c, a, [(0.86 * R, -0.44 * R)])[0]
        det = head.details
        if self.shades:
            g = local_poly(c, a, [(0.30 * R, 0.24 * R), (0.92 * R, 0.24 * R), (0.88 * R, 0.02 * R),
                                  (0.36 * R, 0.02 * R)])
            det.append(("poly", g, (18, 18, 24, 255)))
            det.append(("line", [local_poly(c, a, [(0.45 * R, 0.19 * R)])[0],
                                 local_poly(c, a, [(0.70 * R, 0.19 * R)])[0]], (120, 140, 170, 255), 1.2))
        elif face in ("hurt", "ko"):
            e0 = local_poly(c, a, [(0.40 * R, 0.18 * R)])[0]
            e1 = local_poly(c, a, [(0.66 * R, 0.10 * R)])[0]
            det.append(("line", [e0, e1], OUTLINE, 2.2))
            if face == "ko":
                e2 = local_poly(c, a, [(0.40 * R, 0.06 * R)])[0]
                e3 = local_poly(c, a, [(0.66 * R, 0.20 * R)])[0]
                det.append(("line", [e2, e3], OUTLINE, 2.2))
        else:
            det.append(("ellipse", eye, (3.3, 3.8), (250, 250, 245, 255)))
            det.append(("ellipse", add(eye, rot((1.3, 0.0), a)), (1.8, 2.6), self.eye))
        if not self.shades:
            det.append(("line", [brow0, brow1], shade(self.hair, 0.7), 3.0))
        if face in ("hurt", "shout", "ko"):
            mo = local_poly(c, a, [(0.74 * R, -0.46 * R)])[0]
            det.append(("ellipse", mo, (3.2, 3.6), (90, 20, 30, 255)))
        else:
            det.append(("line", [m0, m1], shade(self.skin, 0.45), 1.8))
        # Nasenschatten
        n0 = local_poly(c, a, [(0.86 * R, -0.12 * R)])[0]
        n1 = local_poly(c, a, [(0.96 * R, -0.04 * R)])[0]
        det.append(("line", [n0, n1], shade(self.skin, 0.6), 1.5))
        shapes += self._hair(c, a, R)
        return shapes

    def _hair(self, c, a, R):
        st = self.hair_style
        H = self.hair
        out = []

        def P(lst, r=2.0, col=H, ls=3.0):
            out.append(Shape(local_poly(c, a, [(x * R, y * R) for x, y in lst]), r, col, light_shift=ls))

        if st == "short":
            P([(-0.94, -0.10), (-1.00, 0.40), (-0.78, 0.86), (-0.50, 1.02), (-0.30, 1.22), (-0.05, 1.04),
               (0.18, 1.20), (0.36, 0.98), (0.64, 1.02), (0.70, 0.78), (0.88, 0.62), (0.58, 0.52),
               (0.30, 0.60), (0.10, 0.46), (-0.20, 0.44), (-0.34, 0.16), (-0.56, -0.08)])
        elif st == "mohawk":
            P([(-0.80, 0.62), (-1.02, 1.30), (-0.62, 0.98), (-0.56, 1.62), (-0.24, 1.08), (-0.06, 1.78),
               (0.16, 1.06), (0.42, 1.56), (0.46, 0.92), (0.70, 1.18), (0.62, 0.64), (0.10, 0.80),
               (-0.40, 0.76)], r=1.8)
        elif st == "cap":
            cc = self.cap_color
            P([(-0.92, 0.28), (-0.76, 0.84), (-0.30, 1.06), (0.30, 1.02), (0.70, 0.70), (0.78, 0.38),
               (-0.10, 0.36)], r=2.4, col=cc)
            # Schirm nach hinten
            P([(-0.70, 0.40), (-1.52, 0.30), (-1.54, 0.18), (-0.80, 0.20)], r=1.6, col=shade(cc, 0.8))
            P([(0.66, 0.40), (0.90, 0.36)], r=1.2, col=H)
        elif st == "bald":
            pass
        elif st == "long":
            P([(-0.90, -0.60), (-1.10, 0.20), (-0.86, 0.84), (-0.30, 1.08), (0.30, 1.04), (0.74, 0.76),
               (0.86, 0.44), (0.40, 0.56), (0.00, 0.52), (-0.30, 0.20), (-0.44, -0.30), (-0.70, -0.90)])
        elif st == "ponytail":
            P([(-0.92, -0.05), (-0.98, 0.45), (-0.70, 0.90), (-0.20, 1.06), (0.36, 1.00), (0.74, 0.70),
               (0.84, 0.40), (0.46, 0.50), (0.10, 0.44), (-0.30, 0.30), (-0.52, 0.02)])
            # Zopf
            P([(-0.70, 0.70), (-1.30, 0.62), (-1.62, 0.10), (-1.58, -0.50), (-1.40, -0.60), (-1.30, 0.00),
               (-1.02, 0.36), (-0.74, 0.40)], r=2.0)
            P([(-0.78, 0.66), (-0.86, 0.50)], r=2.6, col=(200, 50, 80, 255))  # Haargummi
        elif st == "slick":
            P([(-0.92, 0.00), (-0.94, 0.52), (-0.60, 0.94), (0.00, 1.06), (0.56, 0.92), (0.82, 0.62),
               (0.60, 0.56), (0.20, 0.72), (-0.30, 0.60), (-0.56, 0.24), (-0.60, -0.02)], r=1.6, ls=2.2)
            out.append(Shape(local_poly(c, a, [(-0.40 * R, 0.84 * R), (0.30 * R, 0.90 * R)]), 1.4,
                             shade(H, 1.6), outline=False, light_shift=0))
        elif st == "buzz":
            P([(-0.88, 0.00), (-0.82, 0.60), (-0.40, 0.92), (0.20, 0.94), (0.62, 0.66), (0.70, 0.48),
               (0.20, 0.60), (-0.30, 0.40), (-0.50, 0.00)], r=1.4, ls=2.0)
        if st == "bald":
            # Glanzpunkt
            out.append(Shape(local_poly(c, a, [(-0.10 * R, 0.62 * R), (0.20 * R, 0.66 * R)]), 2.2,
                             shade(self.skin, 1.35), outline=False, light_shift=0))
        return out

    # -- Zusammenbau -----------------------------------------------------
    def build(self, p):
        j = self.skeleton(p)
        layers = []
        layers += self._arm(j, "b", p, True)
        layers += self._leg(j, "b", True)
        layers.append(self._neck(j))
        layers.append(self._pelvis(j))
        layers += self._torso(j, p)
        layers += self._leg(j, "f", False)
        layers += self._head(j, p)
        layers += self._arm(j, "f", p, False)
        # Gelenkpunkte fuer die KI-Pipeline (OpenPose-Export)
        R = self.head_r
        ha = j["head_ang"]
        joints = {k: j[k] for k in ("neck", "head", "sh_f", "sh_b", "elbow_f", "elbow_b", "wrist_f", "wrist_b",
                                    "hip_f", "hip_b", "knee_f", "knee_b", "ankle_f", "ankle_b")}
        joints["nose"] = add(j["head"], rot((0.95 * R, -0.05 * R), ha))
        joints["eye"] = add(j["head"], rot((0.52 * R, 0.14 * R), ha))
        joints["ear"] = add(j["head"], rot((-0.18 * R, 0.0), ha))
        # Hand-Anker (vordere Faust) fuer Waffen: Punkt + Richtung des Unterarms
        d = norm(sub(j["wrist_f"], j["elbow_f"]))
        hand = add(j["wrist_f"], mul(d, self.fist_r * 0.55))
        tip = add(hand, d)
        # globale Transformation (Rotation, Grounding)
        rr = p["rot"]
        if rr:
            pivot = add(j["hip"], mul(j["up"], self.torso * 0.4))
            for s in layers:
                s.pts = [add(pivot, rot(sub(q, pivot), rr)) for q in s.pts]
                s.details = [_rot_detail(d, pivot, rr) for d in s.details]
            hand = add(pivot, rot(sub(hand, pivot), rr))
            tip = add(pivot, rot(sub(tip, pivot), rr))
            joints = {k: add(pivot, rot(sub(v, pivot), rr)) for k, v in joints.items()}
        if p["ground"]:
            low = min(q[1] - s.r for s in layers for q in s.pts)
            off = (p["dx"], -low + p["dy"])
        else:
            off = (p["dx"], p["dy"])
        for s in layers:
            s.pts = [add(q, off) for q in s.pts]
            s.details = [_off_detail(d, off) for d in s.details]
        hand = add(hand, off)
        tip = add(tip, off)
        self.last_joints = {k: add(v, off) for k, v in joints.items()}
        # (x, y) in Modell-Einheiten ueber dem Fusspunkt, Winkel in Grad (0 = nach vorne, + = nach oben)
        self.last_anchor = (hand[0], hand[1], math.degrees(math.atan2(tip[1] - hand[1], tip[0] - hand[0])))
        return layers


def _map_pts(pts, fn):
    return [fn(q) for q in pts]


def _rot_detail(d, pivot, deg):
    f = lambda q: add(pivot, rot(sub(q, pivot), deg))
    return _xform_detail(d, f)


def _off_detail(d, off):
    return _xform_detail(d, lambda q: add(q, off))


def _xform_detail(d, f):
    kind = d[0]
    if kind == "ellipse":
        return (kind, f(d[1]), d[2], d[3])
    if kind == "line":
        return (kind, _map_pts(d[1], f), d[2], d[3])
    if kind == "poly":
        return (kind, _map_pts(d[1], f), d[2])
    return d


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_shapes(shapes, size, foot, scale=1.0):
    """Rendert eine Liste von Shapes in ein RGBA-Bild (finale Groesse)."""
    W, H = size[0] * SS, size[1] * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fx, fy = foot
    k = SS * scale

    def tr(q):
        return (fx * SS + q[0] * k, fy * SS - q[1] * k)

    for s in shapes:
        pts = [tr(q) for q in s.pts]
        r = s.r * k
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        pad = int(r + OL * k + s.light_shift * k + 4)
        x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
        x1, y1 = min(W, int(max(xs)) + pad), min(H, int(max(ys)) + pad)
        if x1 <= x0 or y1 <= y0:
            continue
        lp = [(q[0] - x0, q[1] - y0) for q in pts]
        bw, bh = x1 - x0, y1 - y0
        if s.outline:
            m = Image.new("L", (bw, bh), 0)
            draw_inflated(ImageDraw.Draw(m), lp, r + OL * k, 255)
            img.paste(Image.new("RGBA", (bw, bh), OUTLINE), (x0, y0, x1, y1), m)
        m = Image.new("L", (bw, bh), 0)
        draw_inflated(ImageDraw.Draw(m), lp, r, 255)
        if s.light_shift > 0:
            img.paste(Image.new("RGBA", (bw, bh), s.dark), (x0, y0, x1, y1), m)
            ls = s.light_shift * k
            sh = [(q[0] + ls * 0.35, q[1] - ls) for q in lp]
            m2 = Image.new("L", (bw, bh), 0)
            draw_inflated(ImageDraw.Draw(m2), sh, r, 255)
            lit = ImageChops.darker(m, m2)
            img.paste(Image.new("RGBA", (bw, bh), s.fill), (x0, y0, x1, y1), lit)
            # Glanzkante oben (warmes Licht von oben)
            hl = HIGHLIGHT_W * k
            m3 = Image.new("L", (bw, bh), 0)
            draw_inflated(ImageDraw.Draw(m3), [(q[0], q[1] + hl) for q in lp], r, 255)
            top_band = ImageChops.subtract(lit, m3).point(lambda v: v * 0.55)
            img.paste(Image.new("RGBA", (bw, bh), shade(s.fill, 1.22)), (x0, y0, x1, y1), top_band)
            # Randlicht hinten (kuehles Neon-Gegenlicht wie in naechtlichen SoR4-Stages)
            rw = RIM_W * k
            m4 = Image.new("L", (bw, bh), 0)
            draw_inflated(ImageDraw.Draw(m4), [(q[0] + rw, q[1] + rw * 0.4) for q in lp], r, 255)
            rim = ImageChops.subtract(m, m4).point(lambda v: v * 0.8)
            img.paste(Image.new("RGBA", (bw, bh), mix(s.fill, RIM_COLOR, 0.55)), (x0, y0, x1, y1), rim)
        else:
            img.paste(Image.new("RGBA", (bw, bh), s.fill), (x0, y0, x1, y1), m)
        if s.details:
            d = ImageDraw.Draw(img)
            for det in s.details:
                kind = det[0]
                if kind == "ellipse":
                    c = tr(det[1])
                    rx, ry = det[2][0] * k * 0.5 * 2, det[2][1] * k * 0.5 * 2
                    d.ellipse([c[0] - rx / 2, c[1] - ry / 2, c[0] + rx / 2, c[1] + ry / 2], fill=det[3])
                elif kind == "line":
                    lpts = [tr(q) for q in det[1]]
                    wdt = int(det[3] * k)
                    d.line(lpts, fill=det[2], width=wdt)
                    for q in lpts:
                        d.ellipse([q[0] - wdt / 2, q[1] - wdt / 2, q[0] + wdt / 2, q[1] + wdt / 2], fill=det[2])
                elif kind == "poly":
                    d.polygon([tr(q) for q in det[1]], fill=det[2])
    return img


def render_pose(char, p, size=(320, 320), foot=(160, 312), scale=1.0):
    from common import downsample
    shapes = char.build(p)
    return downsample(render_shapes(shapes, size, foot, scale))
