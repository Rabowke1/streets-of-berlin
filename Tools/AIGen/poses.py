"""Pose-Export fuer die KI-Pipeline.

Rendert fuer jeden Figuren-Frame (aus Tools/ArtGen) drei Steuerbilder in 1024x1024:
  *_pose.png     OpenPose-Skelett (COCO-18, Standardfarben) fuer ControlNet OpenPose
  *_lineart.png  Konturen der Puppet-Figur (weiss auf schwarz) fuer ControlNet Lineart/Canny
  *_mask.png     Silhouette (weiss) – dient spaeter zum Ausrichten des KI-Bildes

Frame-Raum: 320x320 Welt-Units, Fuesse bei (160, 312)  ->  1024 px: Faktor 3.2
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Tools", "ArtGen"))

from characters import ANIMS_BY_STYLE, make_characters  # noqa: E402
from puppet import render_pose  # noqa: E402

SIZE = 1024
FRAME = 320
FOOT = (160, 312)
K = SIZE / FRAME

# COCO-18: Index -> Gelenk. Figur schaut nach rechts: die dem Betrachter zugewandte Seite ist links.
KEYPOINTS = ["nose", "neck", "sh_b", "elbow_b", "wrist_b", "sh_f", "elbow_f", "wrist_f",
             "hip_b", "knee_b", "ankle_b", "hip_f", "knee_f", "ankle_f", None, "eye", None, "ear"]
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
         (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
          (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
          (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


def to_px(p, scale):
    return ((FOOT[0] + p[0] * scale) * K, (FOOT[1] - p[1] * scale) * K)


def openpose_image(joints, scale):
    img = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    pts = [to_px(joints[k], scale) if k else None for k in KEYPOINTS]
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    stick = 4 * K / 3.2 * 2.5
    for i, (a, b) in enumerate(LIMBS):
        if pts[a] is None or pts[b] is None:
            continue
        (x0, y0), (x1, y1) = pts[a], pts[b]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        length = math.hypot(x1 - x0, y1 - y0) / 2
        ang = math.atan2(y1 - y0, x1 - x0)
        poly = []
        for t in range(0, 360, 20):
            r = math.radians(t)
            ex, ey = math.cos(r) * length, math.sin(r) * stick
            poly.append((mx + ex * math.cos(ang) - ey * math.sin(ang), my + ex * math.sin(ang) + ey * math.cos(ang)))
        ld.polygon(poly, fill=COLORS[i % 18] + (153,))
    img.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(img)
    for i, p in enumerate(pts):
        if p is not None:
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=COLORS[i])
    return img


def lineart_and_mask(render):
    """render: RGBA 1024 Puppet-Bild -> (Lineart, Maske)"""
    rgba = render.convert("RGBA")
    r, g, b, a = rgba.split()
    lum = Image.merge("RGB", (r, g, b)).convert("L")
    # Konturen = dunkle, deckende Pixel
    line = Image.eval(lum, lambda v: 255 if v < 55 else 0)
    line = Image.composite(line, Image.new("L", rgba.size, 0), a.point(lambda v: 255 if v > 128 else 0))
    mask = a.point(lambda v: 255 if v > 100 else 0)
    return Image.merge("RGB", (line, line, line)), mask


def export(char_names=None, anims=None, out_dir=None, limit=None):
    """Exportiert Steuerbilder; liefert Liste von (char, frame_name, pfad_prefix)."""
    out_dir = out_dir or os.path.join(ROOT, "Art", "AIPoses")
    chars = make_characters()
    done = []
    for name, spec in chars.items():
        if char_names and name not in char_names:
            continue
        all_anims = ANIMS_BY_STYLE[spec["style"]]()
        for anim, frames in all_anims.items():
            if anims and anim not in anims:
                continue
            for i, p in enumerate(frames):
                frame = "%s_%s_%02d" % (name, anim, i)
                folder = os.path.join(out_dir, name)
                os.makedirs(folder, exist_ok=True)
                prefix = os.path.join(folder, frame)
                render = render_pose(spec["char"], p, (SIZE, SIZE), (FOOT[0] * K, FOOT[1] * K), spec["scale"] * K)
                openpose_image(spec["char"].last_joints, spec["scale"]).save(prefix + "_pose.png")
                line, mask = lineart_and_mask(render)
                line.save(prefix + "_lineart.png")
                mask.save(prefix + "_mask.png")
                render.save(prefix + "_puppet.png")
                done.append((name, frame, prefix))
                if limit and len(done) >= limit:
                    return done
    return done


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Steuerbilder (OpenPose/Lineart/Maske) fuer die KI-Pipeline exportieren")
    ap.add_argument("--char", action="append", help="Figur (mehrfach moeglich), Standard: alle")
    ap.add_argument("--anim", action="append", help="Animation (mehrfach moeglich), Standard: alle")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = export(args.char, args.anim, args.out)
    print("%d Frames exportiert" % len(res))
