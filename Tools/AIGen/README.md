# KI-Pipeline für Figuren (ComfyUI)

Erzeugt Figuren-Frames im gezeichneten Comic-Stil mit einem Bildmodell (Stable Diffusion XL, Flux …) und
**exakt den Posen aus dem Spiel**. Die Ergebnisse landen als Overrides in `Art/Custom/` und ersetzen beim nächsten
`generate_all.py` die Puppet-Grafiken. Import nach Unreal und die Browser-Version funktionieren danach unverändert.

```
Puppet-Pose (Tools/ArtGen)  ──►  OpenPose-Skelett + Lineart + Maske   (poses.py)
                                          │
                                          ▼
                         ComfyUI: SDXL + ControlNet (+ LoRA)            (comfy.py)
                                          │
                                          ▼
     Grün freistellen ► auf Puppet-Silhouette ausrichten ► 640×640      (postprocess.py)
                                          │
                                          ▼
                 Art/Custom/<Figur>/<Frame>.png  +  Review-Kontaktbogen (review.py)
```

## Voraussetzungen

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) lokal (NVIDIA-GPU ab ca. 8 GB VRAM für SDXL) oder bei einem
  ComfyUI-Hoster, erreichbar über HTTP (Standard `http://127.0.0.1:8188`).
- Ein **SDXL-Checkpoint** mit Comic-/Anime-Stil (z. B. ein Illustrations-Checkpoint) in `ComfyUI/models/checkpoints`.
- **ControlNet OpenPose für SDXL** in `ComfyUI/models/controlnet`.
- Optional: ControlNet Lineart/Canny (engere Silhouette), eine **Figuren-LoRA** für maximale Einheitlichkeit.
- Python 3 mit Pillow + NumPy (wie für `Tools/ArtGen`), optional `rembg` für besseres Freistellen.

## Schnellstart

```bash
# 1) Nur Steuerbilder + Workflows ansehen (keine GPU nötig)
python Tools/AIGen/generate.py --dry-run --char Kai --anim idle

# 2) Einige Frames generieren
python Tools/AIGen/generate.py --char Kai --anim idle --anim walk \
    --checkpoint MEIN_SDXL_COMIC.safetensors \
    --controlnet-pose controlnet-openpose-sdxl-1.0.safetensors

# 3) Ergebnis prüfen: Art/AIPoses/review.png (Puppet | Pose | KI)
# 4) Übernehmen
python Tools/ArtGen/generate_all.py          # nimmt Art/Custom automatisch
python Tools/WebBuild/build_web.py           # Browser-Version aktualisieren
```

Im Unreal-Editor erkennt das Import-Skript das geänderte Manifest und importiert beim nächsten Start neu.

## Einheitlichkeit über alle Frames

Die größte Schwierigkeit ist, dass eine Figur in allen ~30–70 Frames gleich aussieht. Empfohlenes Vorgehen:

1. **Referenzbogen:** Mit `--anim idle` und verschiedenen `--seed`-Werten Varianten erzeugen, die beste auswählen.
2. **LoRA trainieren:** 15–30 gute Bilder der Figur (Idle, verschiedene Blickwinkel) → kleine Figuren-LoRA
   (z. B. mit kohya_ss). Dann `--lora kai_v1.safetensors --lora-strength 0.9`.
3. **Fester Seed pro Figur** (automatisch aus Figurenname + `--seed`), gleicher Prompt, gleiche Einstellungen.
4. **Lineart-ControlNet** zuschalten (`--controlnet-lineart …`), wenn Proportionen zu stark schwanken.
5. Den Kontaktbogen durchsehen, schlechte Frames löschen (dann bleibt dort die Puppet-Grafik) oder mit anderem Seed
   neu erzeugen: `--char Kai --anim attack4 --seed 99`.

Eigene Workflows (z. B. mit IP-Adapter oder Flux) gehen über `--workflow mein_workflow_api.json`. Der Workflow muss
im API-Format gespeichert sein und darf die Platzhalter `__POSE_IMAGE__`, `__LINEART_IMAGE__`, `__PROMPT__`,
`__NEGATIVE__` und `__SEED__` enthalten.

## Prompts

`prompts.json` enthält den Stil-Prompt (gezeichnete Comic-Optik, dicke Tuschekonturen, Cel-Shading, **grüner
Hintergrund** für das Freistellen) sowie eine Beschreibung jeder Figur und jeder Animation. Die Figuren sind eigene
Designs. Bitte keine Modelle/LoRAs auf Grafiken kommerzieller Spiele trainieren.

## Test ohne GPU

```bash
python -m unittest Tools/AIGen/tests/test_pipeline.py -v
```

Startet einen nachgebildeten ComfyUI-Server und prüft die komplette Kette: Upload, Auftrag, Warten, Download,
Freistellen und Ausrichten. Die generierte Figur muss mit Fußlinie und Höhe auf der Puppet-Silhouette stehen.
