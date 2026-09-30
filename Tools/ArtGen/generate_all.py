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
import backgrounds2 as bg2  # noqa: E402
import effects as fx  # noqa: E402
from characters import ANIMS_BY_STYLE, make_characters, stance  # noqa: E402
from common import OUT_DIR, RES, ROOT, ensure_dir, save  # noqa: E402
from puppet import render_pose  # noqa: E402

# Frame-Groesse in Welt-Units (Pixel = Units * RES)
FRAME = (320, 320)
FOOT = (160, 312)

# Eigene Grafiken (handgezeichnet oder mit einem Bild-KI-Tool erzeugt) mit gleichem Namen
# in Art/Custom/<Ordner>/<Name>.png ersetzen die generierte Version automatisch.
CUSTOM_DIR = os.path.join(ROOT, "Art", "Custom")

manifest = {"frame_size": list(FRAME), "foot": list(FOOT), "pixels_per_unit": RES, "sprites": [], "sounds": []}
custom_used = []
# Hand-Anker pro Figuren-Frame + Waffen-Griffpunkte (fuer Waffen in der Hand), gelesen von C++ und Web
anchors = {"frames": {}, "weapons": {}}
DATA_DIR = os.path.join(ROOT, "Content", "Data")


def add_sprite(img, folder, name):
    rel = os.path.join("Sprites", folder, name + ".png")
    custom = os.path.join(CUSTOM_DIR, folder, name + ".png")
    if os.path.exists(custom):
        src = Image.open(custom).convert("RGBA")
        if src.size != img.size:
            print("  Hinweis: %s hat %dx%d statt %dx%d – wird skaliert" % (custom, src.width, src.height,
                                                                          img.width, img.height))
            src = src.resize(img.size, Image.LANCZOS)
        img = src
        custom_used.append(rel)
    save(img, rel)
    manifest["sprites"].append({
        "file": rel.replace("\\", "/"),
        "package": "/Game/Sprites/" + folder,
        "name": name,
        "size": [img.width, img.height],
        "ppu": RES,
    })


def portrait(char, style, scale):
    R = RES
    big = render_pose(char, stance(style), size=(420 * R, 900 * R), foot=(210 * R, 880 * R), scale=2.8 * R)
    bbox = big.getbbox()
    top = bbox[1]
    alpha = big.split()[3].crop((0, top, big.width, top + 120 * R))
    hb = alpha.getbbox()
    cx = (hb[0] + hb[2]) // 2 if hb else 210 * R
    crop = big.crop((cx - 80 * R, top - 10 * R, cx + 80 * R, top + 150 * R))
    return crop.resize((128 * RES, 128 * RES), Image.LANCZOS)


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
                img = render_pose(spec["char"], p, (FRAME[0] * RES, FRAME[1] * RES), (FOOT[0] * RES, FOOT[1] * RES),
                                  spec["scale"] * RES)
                frame_name = "%s_%s_%02d" % (name, anim, i)
                add_sprite(img, name, frame_name)
                ax, ay, ang = spec["char"].last_anchor
                sc = spec["scale"]
                anchors["frames"][frame_name] = [round(ax * sc, 1), round(ay * sc, 1), round(ang, 1)]
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


def gen_weapons():
    for name, (w, h, gx, gy) in fx.WEAPONS.items():
        add_sprite(fx.weapon(name), "Weapons", "Weapon_" + name)
        anchors["weapons"][name] = {"size": [w, h], "grip": [gx, gy]}


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
    # Stage 2
    add_sprite(bg2.sky_spree(), "Backgrounds", "BG_SkySpree")
    add_sprite(bg2.gallery_tile(0), "Backgrounds", "BG_Gallery_00")
    add_sprite(bg2.gallery_tile(1), "Backgrounds", "BG_Gallery_01")
    add_sprite(bg2.floor_promenade(), "Backgrounds", "BG_FloorPromenade")
    add_sprite(bg2.backyard_tile(), "Backgrounds", "BG_Backyard_00")
    add_sprite(bg2.floor_cobble(), "Backgrounds", "BG_FloorCobble")
    add_sprite(bg2.tree(), "Backgrounds", "FG_Tree")
    # Stage 3
    add_sprite(bg2.sky_alex(), "Backgrounds", "BG_SkyAlex")
    add_sprite(bg2.construction_tile(0), "Backgrounds", "BG_Construction_00")
    add_sprite(bg2.construction_tile(1), "Backgrounds", "BG_Construction_01")
    add_sprite(bg2.floor_construction(), "Backgrounds", "BG_FloorConstruction")
    add_sprite(bg2.sky_rooftop(), "Backgrounds", "BG_SkyRooftop")
    add_sprite(bg2.rooftop_tile(), "Backgrounds", "BG_Rooftop_00")
    add_sprite(bg2.floor_rooftop(), "Backgrounds", "BG_FloorRooftop")
    add_sprite(bg2.scaffold(), "Backgrounds", "FG_Scaffold")


def gen_audio():
    for name, path in audio.generate(os.path.join(OUT_DIR, "Audio")):
        manifest["sounds"].append({
            "file": os.path.relpath(path, OUT_DIR).replace("\\", "/"),
            "package": "/Game/Audio",
            "name": name,
        })


def main():
    ensure_dir(OUT_DIR)
    steps = [("Figuren", gen_characters), ("Effekte", gen_effects), ("Props", gen_props), ("Waffen", gen_weapons),
             ("UI", gen_ui),
             ("Hintergruende", gen_backgrounds), ("Audio", gen_audio)]
    only = set(sys.argv[1:])
    if only:
        # Teil-Lauf: vorhandenes Manifest/Anker laden und nur die genannten Schritte neu erzeugen
        old = os.path.join(OUT_DIR, "manifest.json")
        if os.path.exists(old):
            prev = json.load(open(old, encoding="utf-8"))
            labels = {"Figuren": "Sprites/", "Effekte": "Sprites/Effects/", "Hintergruende": "Sprites/Backgrounds/"}
            _ = labels
            manifest["sounds"] = [] if "Audio" in only else prev.get("sounds", [])
            keep_folders = {
                "Figuren": None, "Effekte": {"Effects"}, "Props": {"Props"}, "Waffen": {"Weapons"}, "UI": {"UI"},
                "Hintergruende": {"Backgrounds"},
            }
            drop = set()
            for lab in only:
                if keep_folders.get(lab):
                    drop |= keep_folders[lab]
            char_names = set(make_characters().keys())
            for spr in prev.get("sprites", []):
                folder = spr["package"].rsplit("/", 1)[-1]
                if folder in drop or ("Figuren" in only and (folder in char_names or spr["name"].startswith("Portrait_"))):
                    continue
                manifest["sprites"].append(spr)
        oa = os.path.join(DATA_DIR, "anchors.json")
        if os.path.exists(oa):
            prev_a = json.load(open(oa, encoding="utf-8"))
            if "Figuren" not in only:
                anchors["frames"] = prev_a.get("frames", {})
            if "Waffen" not in only:
                anchors["weapons"] = prev_a.get("weapons", {})
        steps = [s_ for s_ in steps if s_[0] in only]
    for label, fn in steps:
        t0 = time.time()
        print("%s ..." % label)
        fn()
        print("  fertig (%.1fs)" % (time.time() - t0))
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    ensure_dir(DATA_DIR)
    with open(os.path.join(DATA_DIR, "anchors.json"), "w", encoding="utf-8") as f:
        json.dump(anchors, f, separators=(",", ":"))
    print("%d Sprites, %d Sounds -> %s" % (len(manifest["sprites"]), len(manifest["sounds"]), OUT_DIR))
    if custom_used:
        print("Eigene Grafiken aus Art/Custom verwendet: %d" % len(custom_used))


if __name__ == "__main__":
    main()
