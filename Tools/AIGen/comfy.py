"""Kleiner ComfyUI-API-Client (nur Standardbibliothek).

ComfyUI-Endpunkte: POST /upload/image, POST /prompt, GET /history/<id>, GET /view
"""
import json
import mimetypes
import os
import time
import urllib.parse
import urllib.request
import uuid


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    def __init__(self, server="http://127.0.0.1:8188", timeout=600):
        self.server = server.rstrip("/")
        self.timeout = timeout
        self.client_id = uuid.uuid4().hex

    def _req(self, path, data=None, headers=None, method=None):
        req = urllib.request.Request(self.server + path, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            raise ComfyError("%s %s -> HTTP %s: %s" % (method or "GET", path, e.code, e.read()[:300])) from e
        except urllib.error.URLError as e:
            raise ComfyError("ComfyUI nicht erreichbar unter %s (%s). Laeuft ComfyUI?" % (self.server, e.reason)) from e

    def upload_image(self, path, name=None):
        name = name or os.path.basename(path)
        boundary = uuid.uuid4().hex
        with open(path, "rb") as f:
            payload = f.read()
        ctype = mimetypes.guess_type(path)[0] or "image/png"
        body = (
            ("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
             % (boundary, name, ctype)).encode() + payload +
            ("\r\n--%s\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--%s--\r\n"
             % (boundary, boundary)).encode()
        )
        res = json.loads(self._req("/upload/image", body, {"Content-Type": "multipart/form-data; boundary=" + boundary},
                                   "POST"))
        return res.get("name", name)

    def queue(self, graph):
        body = json.dumps({"prompt": graph, "client_id": self.client_id}).encode()
        res = json.loads(self._req("/prompt", body, {"Content-Type": "application/json"}, "POST"))
        if "prompt_id" not in res:
            raise ComfyError("Unerwartete Antwort auf /prompt: %s" % res)
        return res["prompt_id"]

    def wait(self, prompt_id, poll=1.0):
        t0 = time.time()
        while time.time() - t0 < self.timeout:
            hist = json.loads(self._req("/history/" + prompt_id))
            if prompt_id in hist:
                entry = hist[prompt_id]
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise ComfyError("ComfyUI meldet Fehler: %s" % status.get("messages"))
                images = []
                for out in entry.get("outputs", {}).values():
                    images += out.get("images", [])
                if images:
                    return images
            time.sleep(poll)
        raise ComfyError("Zeitueberschreitung beim Warten auf %s" % prompt_id)

    def download(self, image_info):
        q = urllib.parse.urlencode({"filename": image_info["filename"], "subfolder": image_info.get("subfolder", ""),
                                    "type": image_info.get("type", "output")})
        return self._req("/view?" + q)


def build_graph(opts, pose_name, lineart_name, prompt, negative, seed):
    """Standard-Workflow: SDXL-Checkpoint (+ optional LoRA) + ControlNet OpenPose (+ optional Lineart)."""
    g = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": opts["checkpoint"]}},
    }
    model, clip = ["1", 0], ["1", 1]
    if opts.get("lora"):
        g["20"] = {"class_type": "LoraLoader", "inputs": {"model": model, "clip": clip, "lora_name": opts["lora"],
                                                          "strength_model": opts.get("lora_strength", 0.9),
                                                          "strength_clip": opts.get("lora_strength", 0.9)}}
        model, clip = ["20", 0], ["20", 1]
    g["2"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip}}
    g["3"] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip}}
    g["4"] = {"class_type": "LoadImage", "inputs": {"image": pose_name}}
    g["5"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": opts["controlnet_pose"]}}
    g["6"] = {"class_type": "ControlNetApplyAdvanced", "inputs": {
        "positive": ["2", 0], "negative": ["3", 0], "control_net": ["5", 0], "image": ["4", 0],
        "strength": opts.get("pose_strength", 0.95), "start_percent": 0.0, "end_percent": 0.9}}
    pos, neg = ["6", 0], ["6", 1]
    if opts.get("controlnet_lineart") and lineart_name:
        g["14"] = {"class_type": "LoadImage", "inputs": {"image": lineart_name}}
        g["15"] = {"class_type": "ControlNetLoader", "inputs": {"control_net_name": opts["controlnet_lineart"]}}
        g["16"] = {"class_type": "ControlNetApplyAdvanced", "inputs": {
            "positive": pos, "negative": neg, "control_net": ["15", 0], "image": ["14", 0],
            "strength": opts.get("lineart_strength", 0.45), "start_percent": 0.0, "end_percent": 0.6}}
        pos, neg = ["16", 0], ["16", 1]
    g["7"] = {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}}
    g["8"] = {"class_type": "KSampler", "inputs": {
        "model": model, "positive": pos, "negative": neg, "latent_image": ["7", 0], "seed": seed,
        "steps": opts.get("steps", 28), "cfg": opts.get("cfg", 6.0), "sampler_name": opts.get("sampler", "dpmpp_2m"),
        "scheduler": opts.get("scheduler", "karras"), "denoise": 1.0}}
    g["9"] = {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["1", 2]}}
    g["10"] = {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "streets_of_berlin"}}
    return g


def fill_template(template_text, values):
    """Eigener Workflow (API-Format) mit Platzhaltern __POSE_IMAGE__, __LINEART_IMAGE__, __PROMPT__, __NEGATIVE__, __SEED__."""
    text = template_text
    for k, v in values.items():
        if isinstance(v, (int, float)):
            text = text.replace('"__%s__"' % k, str(v))
        text = text.replace("__%s__" % k, json.dumps(str(v))[1:-1])
    return json.loads(text)
