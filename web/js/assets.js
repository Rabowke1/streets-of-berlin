// Laedt Texturatlanten, Hintergruende, Anker-Daten und Sounds (erzeugt von Tools/WebBuild/build_web.py).
export class Assets {
  constructor(base = 'assets/') {
    this.base = base;
    this.index = null; this.anchors = null;
    this.images = {}; this.bg = {}; this.sounds = {};
    this.frameCache = {};
    this.ctx = null;
  }
  async load(onProgress) {
    // Im Buendel (bundle.js) sind die Daten eingebettet: kein fetch() noetig (wichtig in abgeschotteten Frames)
    const embedded = window.__SOB_DATA || {};
    this.index = embedded['atlas.json'] || await (await fetch(this.base + 'atlas.json')).json();
    this.anchors = embedded['anchors.json'] || await (await fetch(this.base + 'anchors.json')).json();
    const jobs = [];
    for (const [folder, a] of Object.entries(this.index.atlases)) jobs.push(['atlas', folder, a.file]);
    for (const [name, b] of Object.entries(this.index.backgrounds)) jobs.push(['bg', name, b.file]);
    let done = 0;
    await Promise.all(jobs.map(([kind, key, file]) => new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => { (kind === 'atlas' ? this.images : this.bg)[key] = img; done++; onProgress && onProgress(done / jobs.length); resolve(); };
      img.onerror = () => reject(new Error('Bild fehlt: ' + file));
      img.src = this.base + file;
    })));
    // Frame-Lookup: name -> [folder, entry]
    this.lookup = {};
    for (const [folder, a] of Object.entries(this.index.atlases)) {
      for (const [name, e] of Object.entries(a.frames)) this.lookup[name] = [folder, e];
    }
  }
  async loadSounds(actx) {
    this.ctx = actx;
    this.soundEls = {};
    // In abgeschotteten Frames (Origin "null") scheitert fetch() ohne CORS-Header -> direkt <audio> nutzen
    const opaque = (self.origin || location.origin) === 'null';
    await Promise.all(Object.entries(this.index.sounds).map(async ([name, file]) => {
      try {
        if (opaque) throw new Error('opaque origin');
        const buf = await (await fetch(this.base + file)).arrayBuffer();
        this.sounds[name] = await actx.decodeAudioData(buf);
      } catch (e) {
        // Rueckfall ohne fetch (z.B. im Artifact-Viewer): <audio>-Elemente brauchen keine CORS-Header
        const el = new Audio(this.base + file);
        el.preload = 'auto';
        this.soundEls[name] = el;
      }
    }));
  }
  /** Alle Frame-Namen <prefix>_00, _01, ... eines Ordners */
  frames(folder, prefix) {
    const key = folder + '/' + prefix;
    if (this.frameCache[key]) return this.frameCache[key];
    const out = [];
    for (let i = 0; i < 64; i++) {
      const n = prefix + '_' + String(i).padStart(2, '0');
      if (!this.lookup[n]) break;
      out.push(n);
    }
    this.frameCache[key] = out;
    return out;
  }
  has(name) { return !!this.lookup[name]; }
  /**
   * Zeichnet einen Frame. (px, py) = Bildschirmpunkt des Ankers; ax/ay = Ankerpunkt im Frame (Welt-Units, y von oben).
   */
  draw(ctx, name, px, py, ax, ay, flip = false, scale = 1, alpha = 1) {
    const hit = this.lookup[name];
    if (!hit) return;
    const [folder, [x, y, w, h, ox, oy]] = hit;
    const img = this.images[folder];
    const s = this.index.scale;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(px, py);
    if (flip) ctx.scale(-scale, scale); else if (scale !== 1) ctx.scale(scale, scale);
    ctx.drawImage(img, x, y, w, h, ox / s - ax, oy / s - ay, w / s, h / s);
    ctx.restore();
  }
  frameSize(name) {
    const hit = this.lookup[name];
    return hit ? [hit[1][6], hit[1][7]] : [0, 0];
  }
  /** Unterste sichtbare Zeile des Frames (Welt-Units) – fuer Props/Pickups, die auf dem Boden stehen */
  frameBottom(name) {
    const hit = this.lookup[name];
    if (!hit) return 0;
    const [, [, , , h, , oy]] = hit;
    return (oy + h) / this.index.scale;
  }
}
