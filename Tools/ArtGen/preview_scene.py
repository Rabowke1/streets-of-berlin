"""Setzt eine Beispielszene (1600x900) aus den generierten Assets zusammen.

Nutzt dasselbe Koordinatensystem wie das Spiel (siehe BrawlerTypes.h):
Welt-Z 300 = Oberkante Boden, Figuren-Fuesse bei Z = Tiefe.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from common import OUT_DIR  # noqa: E402

W, H = 1600, 900
CAM_Z = 340  # Welt-Z der Bildschirmmitte


def load(folder, name):
    return Image.open(os.path.join(OUT_DIR, "Sprites", folder, name + ".png")).convert("RGBA")


def to_screen(x_world, z_world, cam_x):
    return int(x_world - cam_x + W / 2), int(H / 2 - (z_world - CAM_Z))


def compose(cam_x=900, area="street", out="Preview_Scene.png"):
    img = Image.new("RGBA", (W, H), (10, 8, 20, 255))
    if area == "street":
        sky = load("Backgrounds", "BG_Sky")
        sx, sy = to_screen(cam_x * 0.15 - 200, 300 + sky.height, cam_x)
        img.alpha_composite(sky, (sx - int(cam_x * 0.15) + int(cam_x) - int(cam_x), sy))
        wall = load("Backgrounds", "BG_Street_00")
        floor = load("Backgrounds", "BG_FloorStreet")
    else:
        wall = load("Backgrounds", "BG_UBahn_00")
        floor = load("Backgrounds", "BG_FloorPlatform")
    x, y = to_screen(0, 300 + wall.height, cam_x)
    img.alpha_composite(wall, (x, y))
    for fx in range(0, 3000, floor.width):
        x, y = to_screen(fx, 300, cam_x)
        img.alpha_composite(floor, (x, y))

    def actor(folder, name, wx, depth, flip=False, height=0):
        spr = load(folder, name)
        if flip:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        sh = load("Effects", "FX_Shadow")
        sx, sy = to_screen(wx, depth, cam_x)
        img.alpha_composite(sh, (sx - sh.width // 2, sy - sh.height // 2))
        sx, sy = to_screen(wx, depth + height, cam_x)
        img.alpha_composite(spr, (sx - 160, sy - 312))

    scene = [
        ("Props", "Prop_TrashCan_00", 1340, 200, False, "prop"),
        ("Brecher", "Brecher_idle_01", 1260, 150, True, None),
        ("Kalle", "Kalle_hurt_00", 930, 90, True, None),
        ("Kai", "Kai_attack4_01", 820, 80, False, None),
        ("Jojo", "Jojo_walk_03", 480, 40, False, None),
        ("Ronny", "Ronny_fall_01", 1150, 30, True, None),
    ]
    scene.sort(key=lambda s: -s[3])
    for folder, name, wx, depth, flip, kind in scene:
        if kind == "prop":
            spr = load(folder, name)
            sx, sy = to_screen(wx, depth, cam_x)
            img.alpha_composite(spr, (sx - spr.width // 2, sy - spr.height + 8))
        else:
            actor(folder, name, wx, depth, flip, 60 if "fall" in name else 0)
    spark = load("Effects", "FX_HitBig_01")
    sx, sy = to_screen(960, 80 + 170, cam_x)
    img.alpha_composite(spark, (sx - spark.width // 2, sy - spark.height // 2))
    if area == "street":
        lamp = load("Backgrounds", "FG_LampPost")
        img.alpha_composite(lamp, (1380, 0))
    # HUD-Andeutung
    por = load("UI", "Portrait_Kai")
    img.alpha_composite(por, (24, 20))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.rectangle([160, 40, 560, 66], fill=(20, 16, 24, 255))
    d.rectangle([164, 44, 470, 62], fill=(250, 200, 50, 255))
    d.rectangle([470, 44, 520, 62], fill=(90, 220, 90, 255))
    img.convert("RGB").save(os.path.join(OUT_DIR, out))


if __name__ == "__main__":
    compose()
    compose(cam_x=800, area="ubahn", out="Preview_UBahn.png")
