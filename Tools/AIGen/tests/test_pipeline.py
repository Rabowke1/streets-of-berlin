"""Ende-zu-Ende-Test der KI-Pipeline gegen einen nachgebildeten ComfyUI-Server (ohne GPU).

    python -m unittest Tools/AIGen/tests/test_pipeline.py -v

Der Fake-Server implementiert /upload/image, /prompt, /history/<id> und /view. Als "KI-Bild" liefert er eine
bewusst zu kleine und verschobene Figur auf gruenem Grund – die Pipeline muss sie freistellen und exakt auf die
Puppet-Silhouette (Fuesse, Hoehe) ausrichten.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import generate  # noqa: E402


class FakeComfy(BaseHTTPRequestHandler):
    uploads = {}
    history = {}
    prompts = []

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/upload/image":
            name = data.split(b'filename="')[1].split(b'"')[0].decode()
            self.uploads[name] = True
            return self._json({"name": name, "subfolder": "", "type": "input"})
        if self.path == "/prompt":
            graph = json.loads(data)["prompt"]
            FakeComfy.prompts.append(graph)
            pid = uuid.uuid4().hex
            assert graph["4"]["inputs"]["image"] in self.uploads, "Pose-Bild wurde nicht hochgeladen"
            FakeComfy.history[pid] = {"status": {"status_str": "success"},
                                      "outputs": {"10": {"images": [{"filename": pid + ".png", "subfolder": "",
                                                                     "type": "output"}]}}}
            return self._json({"prompt_id": pid, "number": 1})
        self._json({"error": "unbekannt"}, 404)

    def do_GET(self):
        if self.path.startswith("/history/"):
            pid = self.path.split("/")[-1]
            return self._json({pid: FakeComfy.history[pid]} if pid in FakeComfy.history else {})
        if self.path.startswith("/view"):
            # "KI-Bild": gruener Hintergrund, Figur absichtlich zu klein (60 %) und nach oben links verschoben
            img = Image.new("RGB", (1024, 1024), (0, 255, 0))
            d = ImageDraw.Draw(img)
            d.rectangle([300, 200, 420, 560], fill=(200, 60, 40))
            d.ellipse([320, 140, 400, 220], fill=(230, 180, 140))
            buf = io.BytesIO()
            img.save(buf, "PNG")
            body = buf.getvalue()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json({"error": "unbekannt"}, 404)


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeComfy)
        cls.url = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.tmp = tempfile.mkdtemp(prefix="sob_ai_")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_end_to_end(self):
        poses_dir = os.path.join(self.tmp, "poses")
        out_dir = os.path.join(self.tmp, "custom")
        rc = generate.main(["--server", self.url, "--char", "Kai", "--anim", "idle", "--anim", "attack4",
                            "--poses-dir", poses_dir, "--out", out_dir, "--timeout", "20"])
        self.assertEqual(rc, 0)
        files = sorted(os.listdir(os.path.join(out_dir, "Kai")))
        self.assertEqual(len(files), 4 + 5, files)  # idle: 4 Frames, attack4: 5 Frames
        self.assertTrue(os.path.exists(os.path.join(poses_dir, "review.png")))

        # Workflow enthaelt ControlNet + Figuren-Prompt
        g = FakeComfy.prompts[-1]
        self.assertEqual(g["5"]["class_type"], "ControlNetLoader")
        self.assertIn("bomber jacket", g["2"]["inputs"]["text"])
        self.assertIn("high kick", g["2"]["inputs"]["text"])

        for f in files:
            img = Image.open(os.path.join(out_dir, "Kai", f))
            self.assertEqual(img.size, (640, 640))
            a = np.asarray(img.split()[3])
            self.assertEqual(a[0, 0], 0, "Hintergrund muss transparent sein")
            ys, xs = np.nonzero(a > 100)
            # Ausrichtung: Unterkante der KI-Figur = Unterkante der Puppet-Maske
            mask = np.asarray(Image.open(os.path.join(poses_dir, "Kai", f.replace(".png", "_mask.png"))).resize((640, 640)))
            my, mx = np.nonzero(mask > 100)
            self.assertLess(abs(ys.max() - my.max()), 6, f)
            self.assertLess(abs((ys.max() - ys.min()) - (my.max() - my.min())) / (my.max() - my.min()), 0.12, f)

    def test_dry_run_writes_workflows(self):
        poses_dir = os.path.join(self.tmp, "dry")
        rc = generate.main(["--dry-run", "--char", "Zoe", "--anim", "attack2", "--poses-dir", poses_dir])
        self.assertEqual(rc, 0)
        wf = [f for f in os.listdir(os.path.join(poses_dir, "Zoe")) if f.endswith("_workflow.json")]
        self.assertEqual(len(wf), 4)
        pose = Image.open(os.path.join(poses_dir, "Zoe", "Zoe_attack2_01_pose.png"))
        self.assertEqual(pose.size, (1024, 1024))
        self.assertGreater(np.asarray(pose).sum(), 0, "OpenPose-Bild darf nicht leer sein")


if __name__ == "__main__":
    unittest.main()
