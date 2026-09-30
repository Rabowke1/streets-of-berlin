"""Baut die Assets fuer die Browser-Version (web/assets) aus Art/Generated.

- packt alle Frames eines Ordners (Figur, Effekte, Props, Waffen, UI) in einen Texturatlas
  (transparente Raender werden abgeschnitten, Offsets gespeichert)
- Hintergruende als einzelne WebP-Dateien
- Sounds werden kopiert (Musik auf 22 kHz reduziert)
- Anker-Daten (Hand/Waffen) werden mitkopiert

Aufruf:  python Tools/WebBuild/build_web.py [--scale 1.0]
Standard-Skalierung: 1 Pixel pro Welt-Unit (die Quell-Grafiken haben RES Pixel pro Unit).
"""
import argparse
import json
import os
import shutil
import wave

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEN = os.path.join(ROOT, "Art", "Generated")
OUT = os.path.join(ROOT, "web", "assets")
ATLAS_W = 2048


def pack(frames):
    """Einfaches Shelf-Packing. frames: list of (name, img). Liefert (atlas, rects)."""
    frames = sorted(frames, key=lambda f: -f[1].height)
    x = y = shelf_h = 0
    rects = {}
    for name, img in frames:
        w, h = img.size
        if x + w > ATLAS_W:
            x = 0
            y += shelf_h + 2
            shelf_h = 0
        rects[name] = (x, y, w, h)
        x += w + 2
        shelf_h = max(shelf_h, h)
    H = y + shelf_h
    atlas = Image.new("RGBA", (ATLAS_W, max(4, H)), (0, 0, 0, 0))
    for name, img in frames:
        rx, ry, _, _ = rects[name]
        atlas.paste(img, (rx, ry))
    return atlas, rects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0, help="Pixel pro Welt-Unit in der Web-Version")
    ap.add_argument("--quality", type=int, default=88)
    args = ap.parse_args()

    manifest = json.load(open(os.path.join(GEN, "manifest.json"), encoding="utf-8"))
    ppu = manifest.get("pixels_per_unit", 1)
    k = args.scale / ppu

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "bg"))
    os.makedirs(os.path.join(OUT, "audio"))

    by_folder = {}
    for s in manifest["sprites"]:
        folder = s["package"].rsplit("/", 1)[-1]
        by_folder.setdefault(folder, []).append(s)

    atlas_index = {"scale": args.scale, "atlases": {}, "backgrounds": {}}
    total = 0
    for folder, sprites in sorted(by_folder.items()):
        if folder == "Backgrounds":
            for s in sprites:
                img = Image.open(os.path.join(GEN, s["file"])).convert("RGBA")
                w, h = max(1, round(img.width * k)), max(1, round(img.height * k))
                img = img.resize((w, h), Image.LANCZOS)
                fn = "bg/%s.webp" % s["name"]
                img.save(os.path.join(OUT, fn), "WEBP", quality=args.quality, method=5)
                atlas_index["backgrounds"][s["name"]] = {"file": fn, "size": [s["size"][0] / ppu, s["size"][1] / ppu]}
                total += os.path.getsize(os.path.join(OUT, fn))
            continue
        frames = []
        meta = {}
        for s in sprites:
            img = Image.open(os.path.join(GEN, s["file"])).convert("RGBA")
            fw, fh = s["size"][0] / ppu, s["size"][1] / ppu  # Welt-Units
            img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
            bbox = img.getbbox() or (0, 0, 1, 1)
            crop = img.crop(bbox)
            frames.append((s["name"], crop))
            meta[s["name"]] = (bbox[0], bbox[1], fw, fh)
        atlas, rects = pack(frames)
        fn = "atlas_%s.webp" % folder
        atlas.save(os.path.join(OUT, fn), "WEBP", quality=args.quality, method=5)
        total += os.path.getsize(os.path.join(OUT, fn))
        entries = {}
        for name, (x, y, w, h) in rects.items():
            ox, oy, fw, fh = meta[name]
            # [atlasX, atlasY, w, h, offX, offY, frameW, frameH]  (Pixel bei 'scale', Frame in Welt-Units)
            entries[name] = [x, y, w, h, ox, oy, fw, fh]
        atlas_index["atlases"][folder] = {"file": fn, "frames": entries}

    # Audio
    atlas_index["sounds"] = {}
    for s in manifest["sounds"]:
        src = os.path.join(GEN, s["file"])
        dst = os.path.join(OUT, "audio", s["name"] + ".wav")
        if s["name"].startswith("MUS_"):
            with wave.open(src, "rb") as w:
                rate, n = w.getframerate(), w.getnframes()
                data = np.frombuffer(w.readframes(n), dtype=np.int16)
            data = data[::2]
            with wave.open(dst, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate // 2)
                w.writeframes(data.tobytes())
        else:
            shutil.copy(src, dst)
        atlas_index["sounds"][s["name"]] = "audio/%s.wav" % s["name"]
        total += os.path.getsize(dst)

    shutil.copy(os.path.join(ROOT, "Content", "Data", "anchors.json"), os.path.join(OUT, "anchors.json"))
    with open(os.path.join(OUT, "atlas.json"), "w", encoding="utf-8") as f:
        json.dump(atlas_index, f, separators=(",", ":"))
    print("web/assets: %d Atlanten, %d Hintergruende, %d Sounds, %.1f MB" % (
        len(atlas_index["atlases"]), len(atlas_index["backgrounds"]), len(atlas_index["sounds"]), total / 1e6))


if __name__ == "__main__":
    main()
