"""Setzt Beispielszenen aus den generierten Assets zusammen (wie die Kamera im Spiel).

Nutzt dasselbe Koordinatensystem und dieselben Layer-Positionen wie ABrawlerStage:
Welt-Z 300 = Oberkante Boden, Figuren-Fuesse bei Z = Tiefe, Kamera-Mitte bei Z = 340.
Ausgabe in voller Aufloesung (1600x900 Units * RES Pixel).
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from common import OUT_DIR, RES  # noqa: E402

SCALE = RES  # Pixel pro Unit in der Vorschau
W, H = 1600, 900
CAM_Z = 340


def load(folder, name):
    img = Image.open(os.path.join(OUT_DIR, "Sprites", folder, name + ".png")).convert("RGBA")
    if SCALE != RES:
        img = img.resize((max(1, img.width * SCALE // RES), max(1, img.height * SCALE // RES)), Image.LANCZOS)
    return img


class Scene:
    def __init__(self, cam_x):
        self.cam_x = cam_x
        self.img = Image.new("RGBA", (W * SCALE, H * SCALE), (10, 8, 20, 255))

    def px(self, x, z):
        return ((x - self.cam_x + W / 2) * SCALE, (H / 2 - (z - CAM_Z)) * SCALE)

    def put_center(self, spr, x, z):
        cx, cy = self.px(x, z)
        self.img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))

    def layer(self, name, base_x, center_z, parallax=1.0):
        x = self.cam_x + (base_x - self.cam_x) * parallax
        self.put_center(load("Backgrounds", name), x, center_z)

    def actor(self, folder, name, x, depth, flip=False, height=0):
        sh = load("Effects", "FX_Shadow")
        self.put_center(sh, x, depth)
        spr = load(folder, name)
        if flip:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        # Frame 320x320, Fuesse bei y=312 -> Mitte 152 Units ueber den Fuessen
        self.put_center(spr, x, depth + height + 152)

    def prop(self, name, x, depth):
        spr = load("Props", name)
        cx, cy = self.px(x, depth)
        self.img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height + 8 * SCALE)))


def compose(cam_x, area, out):
    s = Scene(cam_x)
    if area == "street":
        s.layer("BG_Sky", 2150, 650, 0.15)
        for i, n in enumerate(("BG_Street_00", "BG_Street_01")):
            s.layer(n, 1024 + i * 2048, 580)
        floor = "BG_FloorStreet"
    else:
        s.layer("BG_UBahn_00", 5120, 580)
        s.layer("BG_UBahn_00", 7168, 580)
        floor = "BG_FloorPlatform"
    for i in range(10):
        s.layer(floor, 512 + i * 1024, 90)

    x0 = cam_x - 800
    cast = [
        ("prop", "Prop_TrashCan_00", x0 + 1340, 200),
        ("Brecher", "Brecher_idle_01", x0 + 1250, 160, True),
        ("Kalle", "Kalle_hurt_00", x0 + 930, 90, True),
        ("Kai", "Kai_attack4_01", x0 + 820, 80, False),
        ("Jojo", "Jojo_walk_03", x0 + 470, 40, False),
        ("Ronny", "Ronny_fall_01", x0 + 1140, 30, True, 60),
    ]
    cast.sort(key=lambda e: -e[3])
    for e in cast:
        if e[0] == "prop":
            s.prop(e[1], e[2], e[3])
        else:
            s.actor(e[0], e[1], e[2], e[3], e[4], e[5] if len(e) > 5 else 0)
    s.put_center(load("Effects", "FX_HitBig_01"), x0 + 950, 80 + 150)

    if area == "street":
        s.layer("FG_LampPost", cam_x + 560, CAM_Z, 1.0)
    else:
        s.layer("FG_Pillar", cam_x + 600, CAM_Z, 1.0)

    # HUD-Andeutung
    k = SCALE
    s.img.alpha_composite(load("UI", "Portrait_Kai").resize((96 * k, 96 * k)), (24 * k, 18 * k))
    d = ImageDraw.Draw(s.img)
    d.rectangle([136 * k, 48 * k, 544 * k, 78 * k], fill=(20, 16, 24, 255))
    d.rectangle([140 * k, 52 * k, 460 * k, 74 * k], fill=(250, 200, 50, 255))
    d.rectangle([460 * k, 52 * k, 510 * k, 74 * k], fill=(90, 220, 90, 255))
    s.img.convert("RGB").save(os.path.join(OUT_DIR, out), quality=92)


if __name__ == "__main__":
    compose(1000, "street", "Preview_Scene.png")
    compose(5300, "ubahn", "Preview_UBahn.png")
    compose(2900, "street", "Preview_Street2.png")
