// Menues: Titel, Figurenauswahl, Optionen, Steuerung (Tastenbelegung) und Pause.
// Bedienbar mit Tastatur, Gamepad, Maus und Touch (Tippen auf Eintraege).
import { PLAYERS, W } from './data.js';
import { ACTIONS, keyName, padName } from './settings.js';

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const pct = (v) => `${Math.round(v * 100)} %`;
const CHARS = Object.keys(PLAYERS);
const STAT_NAMES = [['power', 'KRAFT'], ['speed', 'TEMPO'], ['reach', 'REICHWEITE']];

export class Menu {
  constructor(game) {
    this.game = game;
    this.stack = [];
    this.wait = null; // { action, col } waehrend eine Taste/ein Knopf neu belegt wird
    this.rects = [];
    this.t = 0;
  }
  get active() { return this.stack.length > 0; }
  get top() { return this.stack[this.stack.length - 1]; }
  reset(id) { this.stack = id ? [{ id, sel: 0, col: 0 }] : []; this.wait = null; }
  open(id, players = 1) {
    const sel = id === 'select' ? Math.max(0, CHARS.indexOf(this.game.settings.character)) : 0;
    const top = { id, sel, col: 0 };
    // Zu zweit: jedes Geraet hat seinen eigenen Cursor. 1P = Geraet, das "2 SPIELER" bestaetigt hat.
    if (id === 'select' && players > 1) {
      top.coop = { slots: [{ dev: this.game.lastMenuDev || 'kb', sel, ready: false },
        { dev: null, sel: (sel + 1) % CHARS.length, ready: false }], taken: 0 };
    }
    this.stack.push(top);
    this.beep();
  }
  close() {
    this.wait = null;
    if (this.top && this.top.id === 'pause') { this.game.resume(); return; }
    if (this.stack.length > 1) { this.stack.pop(); this.beep(); }
  }
  beep(v = 0.35) { this.game.sfx('SFX_Pickup', v, 0.02); }

  // --- Eintraege -------------------------------------------------------------------
  items(id) {
    const g = this.game, s = g.settings;
    const toggle = (k) => () => { s[k] = !s[k]; s.save(); g.applyAudio(); };
    const vol = (k) => (d) => { s[k] = clamp(Math.round((s[k] + d * 0.1) * 10) / 10, 0, 1); s.save(); g.applyAudio(); };
    switch (id) {
      case 'main': return [
        { label: '1 SPIELER', act: () => this.open('select', 1) },
        { label: '2 SPIELER', act: () => this.open('select', 2) },
        { label: 'OPTIONEN', act: () => this.open('options') },
        // nur in der Desktop-Version (.exe)
        ...(g.desktop ? [{ label: 'BEENDEN', act: () => g.desktop.quit() }] : []),
      ];
      case 'pause': return [
        { label: 'WEITER', act: () => g.resume() },
        { label: 'OPTIONEN', act: () => this.open('options') },
        { label: 'ZUM TITEL', act: () => g.toTitle() },
      ];
      case 'options': return [
        { label: 'MUSIK', value: () => (s.music ? 'AN' : 'AUS'), act: toggle('music'), adj: toggle('music') },
        { label: 'MUSIK-LAUTSTÄRKE', value: () => pct(s.musicVol), adj: vol('musicVol'), act: () => vol('musicVol')(1), dim: () => !s.music },
        { label: 'SOUNDS', value: () => (s.sfx ? 'AN' : 'AUS'), act: toggle('sfx'), adj: toggle('sfx') },
        { label: 'SOUND-LAUTSTÄRKE', value: () => pct(s.sfxVol), adj: vol('sfxVol'), act: () => vol('sfxVol')(1), dim: () => !s.sfx },
        { label: 'STEUERUNG ANPASSEN', act: () => this.open('controls') },
        ...(g.canFullscreen() ? [{ label: 'VOLLBILD', value: () => (g.isFullscreen() ? 'AN' : 'AUS'), act: () => g.toggleFullscreen(), adj: () => g.toggleFullscreen() }] : []),
        { label: 'ZURÜCK', act: () => this.close() },
      ];
      case 'controls': return [
        ...ACTIONS.map(([a, name]) => ({ label: name, action: a, act: () => { this.wait = { action: a, col: this.top.col }; this.beep(); } })),
        { label: 'STANDARD WIEDERHERSTELLEN', act: () => { s.resetControls(); this.beep(0.6); } },
        { label: 'ZURÜCK', act: () => this.close() },
      ];
      case 'select': return CHARS.map((c) => ({ label: c, act: () => g.beginGame(c) }));
      default: return [];
    }
  }

  // --- Eingabe ------------------------------------------------------------------------
  /** p: Set mit 'up','down','left','right','ok','back','start' */
  input(p, byDev) {
    const top = this.top; if (!top || this.wait) return;
    if (top.coop) { this.coopInput(top, byDev || new Map()); return; }
    const items = this.items(top.id);
    const horiz = top.id === 'select';
    const prev = horiz ? 'left' : 'up', next = horiz ? 'right' : 'down';
    if (p.has(prev)) { top.sel = (top.sel + items.length - 1) % items.length; this.beep(0.2); }
    if (p.has(next)) { top.sel = (top.sel + 1) % items.length; this.beep(0.2); }
    const it = items[top.sel];
    if (!horiz && (p.has('left') || p.has('right'))) {
      const d = p.has('left') ? -1 : 1;
      if (top.id === 'controls' && it.action) { top.col = clamp(top.col + d, 0, 2); this.beep(0.2); }
      else if (it.adj) { it.adj(d); this.beep(0.3); }
    }
    if (p.has('ok') || (p.has('start') && top.id !== 'pause')) { it.act(); return; }
    if (p.has('back') || (p.has('start') && top.id === 'pause')) this.close();
  }
  /** Figurenauswahl zu zweit: Eingaben je Geraet */
  coopInput(top, byDev) {
    const { slots } = top.coop;
    for (const [dev, set] of byDev) {
      const ok = set.has('ok') || set.has('start');
      let idx = slots.findIndex((sl) => sl.dev === dev);
      if (idx < 0) {
        // Zweites Geraet meldet sich an
        if (ok && slots[1].dev === null) { slots[1].dev = dev; this.beep(0.6); }
        continue;
      }
      const sl = slots[idx], other = slots[1 - idx];
      if (!sl.ready && (set.has('left') || set.has('right'))) {
        sl.sel = (sl.sel + (set.has('right') ? 1 : CHARS.length - 1)) % CHARS.length; this.beep(0.2);
      }
      if (ok && !sl.ready) {
        if (other.ready && other.sel === sl.sel) { top.coop.taken = 1.2; this.game.sfx('SFX_Thud', 0.6, 0); }
        else { sl.ready = true; this.beep(0.6); }
      } else if (set.has('back')) {
        if (sl.ready) sl.ready = false;
        else if (idx === 0) { this.close(); return; }
        else sl.dev = null;
        this.beep(0.2);
      }
    }
    if (slots.every((sl) => sl.dev && sl.ready)) this.game.beginGame(slots.map((sl) => CHARS[sl.sel]), slots.map((sl) => sl.dev));
  }
  /** Tastendruck waehrend des Neubelegens. true = verbraucht. */
  captureKey(code) {
    const w = this.wait; if (!w) return false;
    if (code === 'Escape') { this.wait = null; return true; }
    if (w.col === 2) return true; // wartet auf Gamepad-Knopf
    if (code === 'Backspace' || code === 'Delete') this.game.settings.clearKey(w.action, w.col);
    else this.game.settings.bindKey(w.action, w.col, code);
    this.wait = null; this.beep(0.6);
    return true;
  }
  capturePad(button) {
    const w = this.wait; if (!w || w.col !== 2) return false;
    this.game.settings.bindPad(w.action, button);
    this.wait = null; this.beep(0.6);
    return true;
  }
  hit(x, y) { return this.rects.find((r) => x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h); }
  hover(x, y) {
    const r = this.hit(x, y), top = this.top;
    if (!r || !top || this.wait) return;
    top.sel = r.i; if (r.col !== undefined) top.col = r.col;
  }
  click(x, y) {
    const top = this.top; if (!top) return;
    if (this.wait) { this.wait = null; return; } // Tippen bricht Neubelegen ab
    const r = this.hit(x, y); if (!r) return;
    if (top.coop) {
      // Maus/Touch steuert Spieler 1
      const sl = top.coop.slots[0];
      if (sl.sel === r.i && !sl.ready) this.coopInput(top, new Map([[sl.dev, new Set(['ok'])]]));
      else if (!sl.ready) { sl.sel = r.i; this.beep(0.2); }
      return;
    }
    top.sel = r.i; if (r.col !== undefined) top.col = r.col;
    const it = this.items(top.id)[r.i];
    if (r.dir && it.adj) { it.adj(r.dir); this.beep(0.3); } else it.act();
  }

  // --- Zeichnen ------------------------------------------------------------------------
  render(dt) {
    this.t += dt;
    this.rects = [];
    const top = this.top; if (!top) return;
    const g = this.game, ctx = g.ctx;
    if (top.id !== 'main') { ctx.fillStyle = 'rgba(6,4,12,0.72)'; ctx.fillRect(0, 0, W.ScreenW, W.ScreenH); }
    if (top.id === 'select') this.drawSelect(top);
    else if (top.id === 'controls') this.drawControls(top);
    else this.drawList(top);
  }
  drawList(top) {
    const g = this.game, items = this.items(top.id);
    const main = top.id === 'main', wide = top.id === 'options';
    const title = { pause: 'PAUSE', options: 'OPTIONEN' }[top.id];
    if (title) g.text(title, 800, 150, 64, '#ffc71a', 'center');
    const y0 = main ? 420 : 280, step = main ? 64 : 78, w = wide ? 900 : 560;
    items.forEach((it, i) => {
      const y = y0 + i * step, sel = i === top.sel, x = 800 - w / 2;
      this.rects.push({ x, y: y - 8, w, h: step - 12, i });
      if (sel) this.highlight(x, y - 8, w, step - 12);
      const color = it.dim && it.dim() ? '#8a8398' : (sel ? '#ffc71a' : '#fff');
      if (it.value) {
        g.text(it.label, x + 30, y, 32, color, 'left');
        const vx = x + w - 150;
        g.text('◀', vx - 110, y, 32, sel ? '#ff3c96' : '#8a8398', 'center');
        g.text(it.value(), vx, y, 32, color, 'center');
        g.text('▶', vx + 110, y, 32, sel ? '#ff3c96' : '#8a8398', 'center');
        this.rects.push({ x: vx - 150, y: y - 8, w: 90, h: step - 12, i, dir: -1 });
        this.rects.push({ x: vx + 60, y: y - 8, w: 110, h: step - 12, i, dir: 1 });
      } else g.text(it.label, 800, y, main ? 40 : 34, color, 'center');
    });
    const hint = main ? this.controlsHint() : '↑↓ WÄHLEN   ←→ ÄNDERN   ENTER OK   ESC ZURÜCK';
    g.text(hint, 800, main ? 700 : 830, 22, '#cfc6e0', 'center');
    if (main) g.text('3 Stages: Kreuzberg · East Side Gallery · Baustelle am Alex', 800, 745, 22, '#ffd24a', 'center');
  }
  controlsHint() {
    const s = this.game.settings;
    const k = (a) => s.keys[a].filter(Boolean).map(keyName).join('/') || '—';
    const dirs = ['up', 'left', 'down', 'right'];
    const std = dirs.every((d, i) => s.keys[d][0] === 'Key' + 'WASD'[i] && s.keys[d][1] && s.keys[d][1].startsWith('Arrow'));
    const walk = std ? 'WASD / PFEILE' : dirs.map((d) => keyName(s.keys[d][0] || s.keys[d][1])).join(' ');
    return `Laufen ${walk}   Schlag ${k('attack')}   Sprung ${k('jump')}   Spezial ${k('special')}   Rückschlag ${k('back')}`;
  }
  highlight(x, y, w, h) {
    const ctx = this.game.ctx;
    const pulse = 0.55 + 0.25 * Math.sin(this.t * 6);
    ctx.fillStyle = `rgba(255,60,150,${0.22 * pulse + 0.1})`; ctx.fillRect(x, y, w, h);
    ctx.fillStyle = '#ff3c96'; ctx.fillRect(x, y, 8, h);
  }
  drawControls(top) {
    const g = this.game, ctx = g.ctx, s = g.settings, items = this.items('controls');
    g.text('STEUERUNG', 800, 60, 56, '#ffc71a', 'center');
    const cols = [800, 1040, 1280], colW = 220, x0 = 220, y0 = 190, step = 50;
    g.text('AKTION', x0 + 20, 140, 22, '#cfc6e0');
    ['TASTE 1', 'TASTE 2', 'GAMEPAD'].forEach((t, i) => g.text(t, cols[i], 140, 22, '#cfc6e0', 'center'));
    items.forEach((it, i) => {
      const y = y0 + i * step, sel = i === top.sel;
      if (it.action) {
        if (sel) this.highlight(x0, y - 6, 1180, step - 6);
        g.text(it.label, x0 + 20, y, 26, sel ? '#ffc71a' : '#fff');
        this.rects.push({ x: x0, y: y - 6, w: 440, h: step - 6, i });
        for (let c = 0; c < 3; c++) {
          const waiting = this.wait && this.wait.action === it.action && this.wait.col === c;
          const val = waiting ? (c === 2 ? 'KNOPF …' : 'TASTE …') : (c === 2 ? padName(s.pad[it.action]) : keyName(s.keys[it.action][c]));
          const bx = cols[c] - colW / 2;
          if (sel && top.col === c) { ctx.strokeStyle = waiting ? '#ffc71a' : '#ff3c96'; ctx.lineWidth = 3; ctx.strokeRect(bx, y - 6, colW, step - 6); }
          g.text(val, cols[c], y, 26, waiting ? '#ffc71a' : '#fff', 'center');
          this.rects.push({ x: bx, y: y - 6, w: colW, h: step - 6, i, col: c });
        }
      } else {
        const yy = y + 14;
        if (sel) this.highlight(800 - 300, yy - 6, 600, step - 6);
        g.text(it.label, 800, yy, 28, sel ? '#ffc71a' : '#fff', 'center');
        this.rects.push({ x: 500, y: yy - 6, w: 600, h: step - 6, i });
      }
    });
    const hint = this.wait
      ? (this.wait.col === 2 ? 'GAMEPAD-KNOPF DRÜCKEN   ·   ESC ABBRECHEN' : 'NEUE TASTE DRÜCKEN   ·   ⌫ LEEREN   ·   ESC ABBRECHEN')
      : '↑↓ AKTION   ←→ SPALTE   ENTER NEU BELEGEN   ESC ZURÜCK';
    g.text(hint, 800, 820, 22, this.wait ? '#ffc71a' : '#cfc6e0', 'center');
    g.text('Belegte Tasten werden getauscht. Menüs: Pfeile, Enter und Esc funktionieren immer.', 800, 858, 18, '#8a8398', 'center');
  }
  drawSelect(top) {
    const g = this.game, ctx = g.ctx, A = g.assets;
    g.text('WÄHLE DEINE FIGUR', 800, 60, 56, '#ffc71a', 'center');
    const cw = 440, ch = 470, y = 150;
    const coop = top.coop, slots = coop ? coop.slots : null;
    const devName = (d) => (d === 'kb' ? 'TASTATUR' : d && d.startsWith('pad') ? `GAMEPAD ${Number(d.slice(3)) + 1}` : '');
    if (coop) coop.taken = Math.max(0, coop.taken - 1 / 60);
    CHARS.forEach((id, i) => {
      const def = PLAYERS[id];
      const cursors = coop ? slots.map((sl, k) => (sl.dev && sl.sel === i ? k : -1)).filter((k) => k >= 0) : [];
      const sel = coop ? cursors.length > 0 : i === top.sel;
      const cx = 800 + (i - (CHARS.length - 1) / 2) * 480, x = cx - cw / 2;
      this.rects.push({ x, y, w: cw, h: ch, i });
      ctx.fillStyle = '#0a0610'; ctx.fillRect(x - 5, y - 5, cw + 10, ch + 10);
      const grad = ctx.createLinearGradient(0, y, 0, y + ch);
      grad.addColorStop(0, sel ? (i ? '#4a1f6e' : '#1f3a7a') : '#221a2e'); grad.addColorStop(1, '#120c1c');
      ctx.fillStyle = grad; ctx.fillRect(x, y, cw, ch);
      if (sel) { ctx.strokeStyle = '#ff3c96'; ctx.lineWidth = 5; ctx.strokeRect(x, y, cw, ch); }
      const frames = A.frames(def.sprite, def.sprite + '_idle');
      if (frames.length) {
        const f = frames[Math.floor(this.t * 8) % frames.length];
        A.draw(ctx, f, cx, y + 400, W.FootX, W.FootY, i > 0, 1.35, sel ? 1 : 0.55);
      }
      g.text(def.name, cx, y + 16, 44, sel ? '#ffc71a' : '#bdb4cc', 'center');
      cursors.forEach((k, n) => {
        const sl = slots[k], tx = x + 14 + n * 110;
        ctx.fillStyle = k ? '#8a3cff' : '#2f7bff'; ctx.fillRect(tx, y + 70, 100, 34);
        g.text(`${k + 1}P`, tx + 50, y + 74, 24, '#fff', 'center');
        if (sl.ready) g.text('BEREIT', cx, y + 330, 40, k ? '#c7a0ff' : '#9fd0ff', 'center');
      });
      STAT_NAMES.forEach(([k, n], j) => {
        const sy = y + 412 + j * 18;
        g.text(n, x + 24, sy - 2, 14, '#cfc6e0');
        for (let b = 0; b < 5; b++) {
          ctx.fillStyle = b < def.stats[k] ? (sel ? '#ffc71a' : '#8a7a4a') : '#2e2438';
          ctx.fillRect(x + 170 + b * 48, sy, 42, 12);
        }
      });
    });
    if (coop) {
      slots.forEach((sl, k) => {
        const yy = 660 + k * 50;
        const txt = sl.dev ? `${k + 1}P: ${devName(sl.dev)}  –  ${PLAYERS[CHARS[sl.sel]].name}${sl.ready ? '  ✔' : ''}` : '';
        if (sl.dev) g.text(txt, 800, yy, 30, k ? '#c7a0ff' : '#9fd0ff', 'center');
        else if ((performance.now() % 900) < 600) g.text('2P: START / A AUF EINEM ZWEITEN GERÄT DRÜCKEN', 800, yy, 30, '#fff', 'center');
      });
      if (coop.taken > 0) g.text('SCHON VERGEBEN!', 800, 770, 30, '#ff6080', 'center');
      g.text('JEDER MIT SEINEM GERÄT:  ←→ WÄHLEN   ENTER / A BEREIT   ESC / B ZURÜCK', 800, 838, 22, '#cfc6e0', 'center');
      return;
    }
    const def = PLAYERS[CHARS[top.sel]];
    def.desc.forEach((l, i) => g.text(l, 800, 650 + i * 38, i ? 24 : 28, i ? '#fff' : '#ffc71a', 'center'));
    g.text('←→ WÄHLEN   ENTER LOS!   ESC ZURÜCK', 800, 838, 22, '#cfc6e0', 'center');
  }
}
