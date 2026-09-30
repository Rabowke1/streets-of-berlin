"""Buendelt web/js/*.js (ES-Module) zu einem klassischen Skript web/js/bundle.js.

Warum: In abgeschotteten Frames (z.B. Artifact-Viewer, iframe sandbox ohne same-origin) duerfen ES-Module
und fetch() nur mit CORS-Headern geladen werden. Ein klassisches <script src> und <img> brauchen das nicht.
Deshalb:
  - jedes Modul wird zu einer Funktion, die ihre Exporte zurueckgibt (keine import/export-Anweisungen mehr)
  - atlas.json und anchors.json werden direkt eingebettet (window.__SOB_DATA), kein fetch() fuer die Daten

Aufruf: python Tools/WebBuild/bundle.py   (wird auch von build_web.py aufgerufen)
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JS = os.path.join(ROOT, "web", "js")
ASSETS = os.path.join(ROOT, "web", "assets")
ENTRY = "main.js"

IMPORT_RE = re.compile(r"^import\s*\{([^}]*)\}\s*from\s*'\./([\w.]+)';\s*$", re.M)
EXPORT_DECL_RE = re.compile(r"^export\s+(class|function|const|let|async function)\s+(\w+)", re.M)


def load_module(name):
    src = open(os.path.join(JS, name), encoding="utf-8").read()
    imports = [(m.group(2), [n.strip() for n in m.group(1).split(",") if n.strip()]) for m in IMPORT_RE.finditer(src)]
    exports = [m.group(2) for m in EXPORT_DECL_RE.finditer(src)]
    body = IMPORT_RE.sub("", src)
    body = re.sub(r"^export\s+(?=(class|function|const|let|async function)\s)", "", body, flags=re.M)
    if re.search(r"^\s*(import|export)\b", body, re.M):
        raise SystemExit("%s: nicht unterstuetzte import/export-Form" % name)
    return imports, exports, body


def order(entry):
    seen, out = set(), []

    def visit(n):
        if n in seen:
            return
        seen.add(n)
        for dep, _ in load_module(n)[0]:
            visit(dep)
        out.append(n)
    visit(entry)
    return out


def build():
    parts = ["// Automatisch erzeugt von Tools/WebBuild/bundle.py – nicht von Hand bearbeiten.",
             "(function () {", "'use strict';"]
    data = {}
    for fn in ("atlas.json", "anchors.json"):
        p = os.path.join(ASSETS, fn)
        if os.path.exists(p):
            data[fn] = json.load(open(p, encoding="utf-8"))
    parts.append("window.__SOB_DATA = %s;" % json.dumps(data, separators=(",", ":")))
    for name in order(ENTRY):
        imports, exports, body = load_module(name)
        var = "__mod_" + re.sub(r"\W", "_", name)
        parts.append("const %s = (function () {" % var)
        for dep, names in imports:
            parts.append("  const { %s } = __mod_%s;" % (", ".join(names), re.sub(r"\W", "_", dep)))
        parts.append(body)
        parts.append("  return { %s };" % ", ".join(exports))
        parts.append("})();")
    parts.append("})();")
    out = os.path.join(JS, "bundle.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    return out


if __name__ == "__main__":
    p = build()
    print("%s (%.0f KB)" % (os.path.relpath(p, ROOT), os.path.getsize(p) / 1024))
