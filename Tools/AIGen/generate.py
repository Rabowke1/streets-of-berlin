"""KI-Frames mit ComfyUI generieren und als Overrides nach Art/Custom schreiben.

Ablauf pro Frame:
  1. Steuerbilder aus dem Puppet-Renderer (OpenPose, Lineart, Maske)       -> poses.py
  2. Upload + Workflow (SDXL + ControlNet OpenPose [+ Lineart] [+ LoRA])     -> comfy.py
  3. Gruenen Hintergrund entfernen, auf Puppet-Silhouette ausrichten,
     ins Spiel-Frame-Format (640x640, Fuesse bei 320/624) bringen          -> postprocess.py
  4. Speichern als Art/Custom/<Figur>/<Frame>.png (+ Review-Kontaktbogen)

Beispiele:
  python Tools/AIGen/generate.py --char Kai --anim idle --anim walk \
      --checkpoint sdxl_comic.safetensors --controlnet-pose controlnet-openpose-sdxl.safetensors
  python Tools/AIGen/generate.py --char Kai --dry-run          # nur Steuerbilder + Workflow-JSON schreiben

Danach: python Tools/ArtGen/generate_all.py  (uebernimmt Art/Custom automatisch) und im Editor neu importieren.
"""
import argparse
import io
import json
import os
import sys
import zlib

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import comfy  # noqa: E402
import poses  # noqa: E402
import postprocess  # noqa: E402

ROOT = poses.ROOT


def frame_prompt(prompts, char, frame):
    anim = frame[len(char) + 1:].rsplit("_", 1)[0]
    parts = [prompts["style"], prompts["characters"].get(char, char)]
    hint = prompts.get("animation_hints", {}).get(anim)
    if hint:
        parts.append(hint)
    return ", ".join(parts)


def seed_for(char, base):
    # Gleicher Seed pro Figur -> einheitlicheres Aussehen ueber alle Frames
    return (zlib.crc32(char.encode()) + base) % (2 ** 32)


def run(args):
    prompts = json.load(open(args.prompts, encoding="utf-8"))
    frames = poses.export(args.char, args.anim, args.poses_dir, args.limit)
    print("%d Frames vorbereitet (Steuerbilder in %s)" % (len(frames), args.poses_dir))
    opts = {
        "checkpoint": args.checkpoint, "controlnet_pose": args.controlnet_pose,
        "controlnet_lineart": args.controlnet_lineart, "lora": args.lora, "lora_strength": args.lora_strength,
        "steps": args.steps, "cfg": args.cfg, "pose_strength": args.pose_strength,
    }
    template = open(args.workflow, encoding="utf-8").read() if args.workflow else None
    client = None if args.dry_run else comfy.ComfyClient(args.server, timeout=args.timeout)
    written = []
    for char, frame, prefix in frames:
        prompt = frame_prompt(prompts, char, frame)
        seed = seed_for(char, args.seed)
        if args.dry_run:
            graph = comfy.build_graph(opts, os.path.basename(prefix + "_pose.png"), os.path.basename(prefix + "_lineart.png"),
                                      prompt, prompts["negative"], seed)
            with open(prefix + "_workflow.json", "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=1)
            continue
        pose_name = client.upload_image(prefix + "_pose.png", "sob_%s_pose.png" % frame)
        line_name = client.upload_image(prefix + "_lineart.png", "sob_%s_lineart.png" % frame) if args.controlnet_lineart or template else None
        if template:
            graph = comfy.fill_template(template, {"POSE_IMAGE": pose_name, "LINEART_IMAGE": line_name or "",
                                                   "PROMPT": prompt, "NEGATIVE": prompts["negative"], "SEED": seed})
        else:
            graph = comfy.build_graph(opts, pose_name, line_name, prompt, prompts["negative"], seed)
        pid = client.queue(graph)
        images = client.wait(pid)
        raw = Image.open(io.BytesIO(client.download(images[0]))).convert("RGB")
        if raw.size != (poses.SIZE, poses.SIZE):
            raw = raw.resize((poses.SIZE, poses.SIZE), Image.LANCZOS)
        raw.save(prefix + "_ai_raw.png")
        cut = postprocess.remove_background(raw, args.matting)
        aligned = postprocess.align_to_mask(cut, Image.open(prefix + "_mask.png"))
        aligned.save(prefix + "_ai.png")
        out = os.path.join(args.out, char, frame + ".png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        postprocess.to_frame(aligned, args.res).save(out)
        written.append((char, frame, prefix, out))
        print("  %s -> %s" % (frame, os.path.relpath(out, ROOT)))
    if written:
        import review
        sheet = review.contact_sheet([(f, p) for _, f, p, _ in written], os.path.join(args.poses_dir, "review.png"))
        print("Review-Kontaktbogen: %s" % sheet)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="http://127.0.0.1:8188", help="ComfyUI-Adresse")
    ap.add_argument("--char", action="append", help="Figur(en), Standard: alle")
    ap.add_argument("--anim", action="append", help="Animation(en), Standard: alle")
    ap.add_argument("--limit", type=int, default=None, help="hoechstens N Frames")
    ap.add_argument("--checkpoint", default="sd_xl_base_1.0.safetensors")
    ap.add_argument("--controlnet-pose", dest="controlnet_pose", default="controlnet-openpose-sdxl-1.0.safetensors")
    ap.add_argument("--controlnet-lineart", dest="controlnet_lineart", default=None,
                    help="optional: zweites ControlNet (Lineart/Canny) fuer engere Silhouetten-Treue")
    ap.add_argument("--lora", default=None, help="optional: Figuren- oder Stil-LoRA")
    ap.add_argument("--lora-strength", dest="lora_strength", type=float, default=0.9)
    ap.add_argument("--pose-strength", dest="pose_strength", type=float, default=0.95)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--cfg", type=float, default=6.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--workflow", default=None, help="eigener ComfyUI-Workflow (API-Format) mit Platzhaltern")
    ap.add_argument("--matting", choices=["green", "rembg", "none"], default="green")
    ap.add_argument("--prompts", default=os.path.join(HERE, "prompts.json"))
    ap.add_argument("--poses-dir", dest="poses_dir", default=os.path.join(ROOT, "Art", "AIPoses"))
    ap.add_argument("--out", default=os.path.join(ROOT, "Art", "Custom"), help="Zielordner (Standard: Art/Custom)")
    ap.add_argument("--res", type=int, default=2, help="Pixel pro Welt-Unit der Ausgabe-Frames (wie SOB_RES)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--dry-run", action="store_true", help="nur Steuerbilder + Workflow-JSON schreiben, nichts generieren")
    args = ap.parse_args(argv)
    try:
        run(args)
    except comfy.ComfyError as e:
        print("FEHLER: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
