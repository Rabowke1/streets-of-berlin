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


HOLD = {"Pipe": 80, "Bat": 80, "Golf": 80, "Knife": 70, "Bottle": 80}


def with_weapon(frame_img, frame_name, weapon):
    """Zeichnet eine Waffe am Hand-Anker (wie Spiel/Engine)."""
    import json
    anchors = json.load(open(os.path.join(os.path.dirname(OUT_DIR), "..", "Content", "Data", "anchors.json")))
    if frame_name not in anchors["frames"]:
        return frame_img
    ax, ay, ang = anchors["frames"][frame_name]
    gx, gy = anchors["weapons"][weapon]["grip"]
    w = load("Weapons", "Weapon_" + weapon)
    big = Image.new("RGBA", (w.width * 3, w.width * 3), (0, 0, 0, 0))
    cx = cy = big.width // 2
    big.alpha_composite(w, (int(cx - gx * SCALE), int(cy - gy * SCALE)))
    rot = big.rotate(ang + HOLD[weapon], resample=Image.BICUBIC)
    out = frame_img.copy()
    hx, hy = (160 + ax) * SCALE, (312 - ay) * SCALE
    out.alpha_composite(rot, (int(hx - cx), int(hy - cy)))
    return out


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

    def actor(self, folder, name, x, depth, flip=False, height=0, weapon=None):
        sh = load("Effects", "FX_Shadow")
        self.put_center(sh, x, depth)
        spr = load(folder, name)
        if weapon:
            spr = with_weapon(spr, name, weapon)
        if flip:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        # Frame 320x320, Fuesse bei y=312 -> Mitte 152 Units ueber den Fuessen
        self.put_center(spr, x, depth + height + 152)

    def prop(self, name, x, depth):
        spr = load("Props", name)
        cx, cy = self.px(x, depth)
        self.img.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height + 8 * SCALE)))


AREAS = {
    "street": dict(sky="BG_Sky", walls=["BG_Street_00", "BG_Street_01"], floor="BG_FloorStreet", fg="FG_LampPost"),
    "ubahn": dict(sky=None, walls=["BG_UBahn_00"] * 5, floor="BG_FloorPlatform", fg="FG_Pillar"),
    "gallery": dict(sky="BG_SkySpree", walls=["BG_Gallery_00", "BG_Gallery_01"], floor="BG_FloorPromenade", fg="FG_Tree"),
    "construction": dict(sky="BG_SkyAlex", walls=["BG_Construction_00", "BG_Construction_01"],
                         floor="BG_FloorConstruction", fg="FG_Scaffold"),
    "rooftop": dict(sky="BG_SkyRooftop", walls=["BG_Rooftop_00"] * 5, floor="BG_FloorRooftop", fg=None),
}

DEFAULT_CAST = [
    ("prop", "Prop_TrashCan_00", 540, 200),
    ("Brecher", "Brecher_idle_01", 450, 160, True),
    ("Kalle", "Kalle_hurt_00", 130, 90, True),
    ("Kai", "Kai_attack4_01", 20, 80, False),
    ("Jojo", "Jojo_walk_03", -330, 40, False),
    ("Ronny", "Ronny_fall_01", 340, 30, True, 60),
]


def compose(cam_x, area, out, cast=None, spark=(150, 230)):
    a = AREAS[area]
    s = Scene(cam_x)
    if a["sky"]:
        s.layer(a["sky"], 2150, 650, 0.15)
    for i, n in enumerate(a["walls"]):
        s.layer(n, 1024 + i * 2048, 580)
    for i in range(10):
        s.layer(a["floor"], 512 + i * 1024, 90)
    cast = sorted(cast or DEFAULT_CAST, key=lambda e: -e[3])
    for e in cast:
        if e[0] == "prop":
            s.prop(e[1], cam_x + e[2], e[3])
        else:
            s.actor(e[0], e[1], cam_x + e[2], e[3], e[4], e[5] if len(e) > 5 else 0, e[6] if len(e) > 6 else None)
    if spark:
        s.put_center(load("Effects", "FX_HitBig_01"), cam_x + spark[0], spark[1])
    if a["fg"]:
        s.layer(a["fg"], cam_x + 560, CAM_Z, 1.0)

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
    compose(1500, "gallery", "Preview_Gallery.png", [
        ("Zoe", "Zoe_attack2_02", 170, 90, True), ("Kai", "Kai_hurt_00", 20, 80, False),
        ("Micha", "Micha_weapon_swing_00", -260, 150, False, 0, "Knife"), ("Nina", "Nina_idle_00", 480, 180, True)], spark=(60, 250))
    compose(2500, "construction", "Preview_Construction.png", [
        ("Harald", "Harald_weapon_swing_01", 190, 100, True, 0, "Golf"), ("Kai", "Kai_weapon_swing_02", -60, 110, False, 0, "Pipe"),
        ("Brecher", "Brecher_attack1_00", -420, 190, False), ("Zoe", "Zoe_fall_01", 420, 40, True, 70)], spark=(120, 270))
