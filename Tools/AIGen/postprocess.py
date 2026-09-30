"""Nachbearbeitung der KI-Bilder: Hintergrund entfernen, auf die Puppet-Silhouette ausrichten, ins Frame-Format bringen."""
import numpy as np
from PIL import Image


def remove_green(img, strength=1.25):
    """Chroma-Key fuer den im Prompt verlangten gruenen Hintergrund (#00ff00), mit Despill."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    other = np.maximum(r, b)
    dominance = g - other * strength
    alpha = np.clip(1.0 - dominance / 60.0, 0.0, 1.0)
    alpha[g < 60] = 1.0
    # Gruenstich an Kanten entfernen
    spill = (g > other) & (alpha < 1.0) | (g > other * 1.1)
    a[..., 1] = np.where(spill, np.minimum(g, other * 1.05), g)
    out = np.dstack([a, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def remove_background(img, method="green"):
    if method == "rembg":
        try:
            from rembg import remove  # type: ignore
        except ImportError as e:
            raise RuntimeError("rembg ist nicht installiert: pip install rembg") from e
        return remove(img.convert("RGBA"))
    if method == "none":
        return img.convert("RGBA")
    return remove_green(img)


def _bbox(alpha, thresh=100):
    m = np.asarray(alpha) > thresh
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def align_to_mask(gen_rgba, mask, max_scale=1.8, min_scale=0.5):
    """Skaliert/verschiebt das KI-Bild, sodass seine Silhouette auf der Puppet-Maske (gleicher Bildraum) steht:
    gleiche Hoehe, gleiche Unterkante (Fuesse), gleiche horizontale Mitte."""
    gb = _bbox(gen_rgba.split()[3])
    mb = _bbox(mask)
    if not gb or not mb:
        return gen_rgba
    gh, mh = gb[3] - gb[1], mb[3] - mb[1]
    s = max(min_scale, min(max_scale, mh / max(1, gh)))
    crop = gen_rgba.crop(gb)
    crop = crop.resize((max(1, round(crop.width * s)), max(1, round(crop.height * s))), Image.LANCZOS)
    out = Image.new("RGBA", gen_rgba.size, (0, 0, 0, 0))
    cx = (mb[0] + mb[2]) / 2
    x = round(cx - crop.width / 2)
    y = mb[3] - crop.height
    out.paste(crop, (x, y), crop)  # paste schneidet ueberstehende Teile automatisch ab
    return out


def to_frame(img_1024, res=2):
    """1024er Arbeitsbild -> Spiel-Frame (320 Units * RES)."""
    size = 320 * res
    return img_1024.resize((size, size), Image.LANCZOS)
