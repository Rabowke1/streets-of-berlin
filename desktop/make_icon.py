"""Erzeugt das App-Icon (icon.png + icon.ico) aus Kais Portrait.

Aufruf:  python desktop/make_icon.py   (benoetigt Pillow; die Dateien liegen fertig im Repo)
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORTRAIT = os.path.join(ROOT, "Art", "Generated", "Sprites", "UI", "Portrait_Kai.png")


def main():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dunkle Kachel mit Neon-Rand (Arcade bei Nacht)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=96, fill=(20, 14, 36, 255), outline=(255, 60, 150, 255), width=20)
    # Portrait nur innerhalb der Kachel zeigen
    face = Image.open(PORTRAIT).convert("RGBA").resize((430, 430), Image.LANCZOS)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    layer.alpha_composite(face, (60, 40))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((28, 28, size - 28, size - 28), radius=78, fill=255)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (size, size), 0), mask))
    img.alpha_composite(layer)
    # gelber Balken unten wie der Energiebalken im HUD
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=96, outline=(255, 60, 150, 255), width=20)
    d.rounded_rectangle((70, 420, size - 70, 452), radius=10, fill=(255, 199, 26, 255), outline=(10, 6, 16, 255), width=6)
    img.save(os.path.join(HERE, "icon.png"))
    img.save(os.path.join(HERE, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("icon.png / icon.ico geschrieben")


if __name__ == "__main__":
    main()
