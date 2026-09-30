# Eigene Grafiken (Overrides)

Jede PNG-Datei hier ersetzt beim nächsten `python Tools/ArtGen/generate_all.py` die gleichnamige generierte
Grafik – egal ob handgezeichnet, gemalt oder mit einem Bild-KI-Tool erzeugt. Alles andere (Import nach Unreal,
Animation, Kollision) funktioniert unverändert.

```
Art/Custom/<Ordner>/<Name>.png   ->   ersetzt   Art/Generated/Sprites/<Ordner>/<Name>.png
```

Beispiele:

| Datei | Größe (bei RES=2) | Hinweis |
|---|---|---|
| `Backgrounds/BG_Street_00.png` | 4096 × 1120 | Fassaden-Kachel, Unterkante = Gehweg-Oberkante, Himmel transparent lassen |
| `Backgrounds/BG_Street_01.png` | 4096 × 1120 | zweite Straßen-Kachel, rechter Rand mit U-Bahn-Eingang |
| `Backgrounds/BG_UBahn_00.png` | 4096 × 1120 | wird 3× hintereinander gekachelt – links/rechts nahtlos |
| `Backgrounds/BG_Sky.png` | 4800 × 1400 | Himmel, Parallaxe 0.15 |
| `Backgrounds/BG_FloorStreet.png` | 2048 × 840 | Boden-Kachel, horizontal nahtlos |
| `Backgrounds/BG_FloorPlatform.png` | 2048 × 840 | Bahnsteig-Kachel, horizontal nahtlos |
| `Kai/Kai_idle_00.png` | 640 × 640 | Figuren-Frame: Blick nach rechts, Füße mittig bei y = 624, transparenter Hintergrund |
| `UI/Portrait_Kai.png` | 256 × 256 | HUD-Portrait |

Die komplette Liste aller Namen steht in `Art/Generated/manifest.json`. Bilder mit falscher Größe werden
automatisch skaliert (mit Hinweis in der Konsole).

**Tipps für KI-generierte Bilder**

- Figuren brauchen für jede Animation *alle* Frames im gleichen Stil. Das ist mit Bild-KIs schwer konsistent
  hinzubekommen. Hintergründe, Portraits und das Logo eignen sich viel besser.
- Seitliche Ansicht („side view, 2D beat 'em up background, hand-painted, night, Berlin Kreuzberg“).
  Keine Perspektive von oben, der Horizont muss zur Boden-Oberkante passen.
- Keine Screenshots oder Grafiken aus kommerziellen Spielen verwenden (Urheberrecht).
