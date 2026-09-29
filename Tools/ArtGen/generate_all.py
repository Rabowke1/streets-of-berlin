"""Erzeugt alle Grafiken und Sounds fuer Streets of Berlin.

Aufruf:  python Tools/ArtGen/generate_all.py   (benoetigt Pillow + numpy)

Ergebnis:
  Art/Generated/...           PNG/WAV-Dateien
  Art/Generated/manifest.json Liste aller Assets inkl. Ziel-Pfad in Unreal
                              (wird von Tools/Unreal/import_assets.py gelesen)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image  # noqa: E402

import audio  # noqa: E402
import backgrounds as bg  # noqa: E402
import effects as fx  # noqa: E402
from characters import ANIMS_BY_STYLE, make_characters, stance  # noqa: E402
from common import OUT_DIR, ensure_dir, save  # noqa: E402
from puppet import render_pose  # noqa: E402

FRAME = (320, 320)
FOOT = (160, 312)

manifest = {"frame_size": list(FRAME), "foot": list(FOOT), "sprites": [], "sounds": []}


def add_sprite(img, folder, name):
    rel = os.path.join("Sprites", folder, name + ".png")
    save(img, rel)
    manifest["sprites"].append({
        "file": rel.replace("\\", "/"),
        "package": "/Game/Sprites/" + folder,
        "name": name,
        "size": [img.width, img.height],
    })


def portrait(char, style, scale):
    big = render_pose(char, stance(style), size=(420, 900), foot=(210, 880), scale=2.8)
    bbox = big.getbbox()
    top = bbox[1]
    alpha = big.split()[3].crop((0, top, big.width, top + 120))
    hb = alpha.getbbox()
    cx = (hb[0] + hb[2]) // 2 if hb else 210
    crop = big.crop((cx - 80, top - 10, cx + 80, top + 150))
    return crop.resize((128, 128), Image.LANCZOS)


def gen_characters(only=None):
    chars = make_characters()
    for name, spec in chars.items():
        if only and name not in only:
            continue
        t0 = time.time()
        anims = ANIMS_BY_STYLE[spec["style"]]()
        count = 0
        for anim, frames in anims.items():
            for i, p in enumerate(frames):
                img = render_pose(spec["char"], p, FRAME, FOOT, spec["scale"])
                add_sprite(img, name, "%s_%s_%02d" % (name, anim, i))
                count += 1
        add_sprite(portrait(spec["char"], spec["style"], spec["scale"]), "UI", "Portrait_" + name)
        print("  %-8s %3d Frames  (%.1fs)" % (name, count, time.time() - t0))


def gen_effects():
    for i, im in enumerate(fx.hit_spark()):
        add_sprite(im, "Effects", "FX_HitSpark_%02d" % i)
    for i, im in enumerate(fx.hit_spark(frames=5, size=192, big=True, seed=5)):
        add_sprite(im, "Effects", "FX_HitBig_%02d" % i)
    for i, im in enumerate(fx.dust()):
        add_sprite(im, "Effects", "FX_Dust_%02d" % i)
    for i, im in enumerate(fx.special_ring()):
        add_sprite(im, "Effects", "FX_SpecialRing_%02d" % i)
    add_sprite(fx.shadow(), "Effects", "FX_Shadow")


def gen_props():
    add_sprite(fx.trash_can(False), "Props", "Prop_TrashCan_00")
    add_sprite(fx.trash_can(True), "Props", "Prop_TrashCan_01")
    add_sprite(fx.crate(False), "Props", "Prop_Crate_00")
    add_sprite(fx.crate(True), "Props", "Prop_Crate_01")
    add_sprite(fx.doener(), "Props", "Pickup_Doener")
    add_sprite(fx.currywurst(), "Props", "Pickup_Currywurst")
    add_sprite(fx.money(), "Props", "Pickup_Money")


def gen_ui():
    add_sprite(fx.go_arrow(), "UI", "UI_Go")
    add_sprite(fx.title_logo(), "UI", "UI_Logo")


def gen_backgrounds():
    add_sprite(bg.sky(), "Backgrounds", "BG_Sky")
    add_sprite(bg.street_tile(0), "Backgrounds", "BG_Street_00")
    add_sprite(bg.street_tile(1), "Backgrounds", "BG_Street_01")
    add_sprite(bg.ubahn_tile(), "Backgrounds", "BG_UBahn_00")
    add_sprite(bg.floor_street(), "Backgrounds", "BG_FloorStreet")
    add_sprite(bg.floor_platform(), "Backgrounds", "BG_FloorPlatform")
    add_sprite(bg.lamp_post(), "Backgrounds", "FG_LampPost")
    add_sprite(bg.pillar(), "Backgrounds", "FG_Pillar")


def gen_audio():
    for name, path in audio.generate(os.path.join(OUT_DIR, "Audio")):
        manifest["sounds"].append({
            "file": os.path.relpath(path, OUT_DIR).replace("\\", "/"),
            "package": "/Game/Audio",
            "name": name,
        })


def main():
    ensure_dir(OUT_DIR)
    steps = [("Figuren", gen_characters), ("Effekte", gen_effects), ("Props", gen_props), ("UI", gen_ui),
             ("Hintergruende", gen_backgrounds), ("Audio", gen_audio)]
    for label, fn in steps:
        t0 = time.time()
        print("%s ..." % label)
        fn()
        print("  fertig (%.1fs)" % (time.time() - t0))
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print("%d Sprites, %d Sounds -> %s" % (len(manifest["sprites"]), len(manifest["sounds"]), OUT_DIR))


if __name__ == "__main__":
    main()
