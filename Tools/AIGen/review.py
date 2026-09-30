"""Kontaktbogen zum Durchsehen: Puppet-Vorlage | Pose | KI-Ergebnis nebeneinander."""
import os

from PIL import Image, ImageDraw

CELL = 256


def contact_sheet(entries, out_path):
    """entries: Liste (frame_name, pfad_prefix) mit *_puppet.png, *_pose.png, *_ai.png"""
    rows = len(entries)
    sheet = Image.new("RGB", (CELL * 3 + 220, CELL * max(1, rows)), (34, 30, 44))
    d = ImageDraw.Draw(sheet)
    for r, (frame, prefix) in enumerate(entries):
        d.text((8, r * CELL + CELL // 2), frame, fill=(240, 240, 240))
        for c, suffix in enumerate(("_puppet.png", "_pose.png", "_ai.png")):
            p = prefix + suffix
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
            bg = Image.new("RGBA", (CELL, CELL), (60, 54, 80, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.convert("RGB"), (220 + c * CELL, r * CELL))
    sheet.save(out_path)
    return out_path
