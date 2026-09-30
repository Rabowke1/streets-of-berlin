// Einstellungen (Audio, Tastenbelegung, Gamepad, Figur) – im Browser gespeichert, sofern erlaubt.
const STORE_KEY = 'sob.settings.v1';

// Aktionen in der Reihenfolge des Steuerungsmenues
export const ACTIONS = [
  ['left', 'LINKS'], ['right', 'RECHTS'], ['up', 'HOCH'], ['down', 'RUNTER'],
  ['attack', 'SCHLAG / AUFHEBEN'], ['jump', 'SPRUNG'], ['special', 'SPEZIAL'], ['back', 'RÜCKSCHLAG / WERFEN'], ['start', 'START / PAUSE'],
];

export const DEFAULT_KEYS = {
  left: ['KeyA', 'ArrowLeft'], right: ['KeyD', 'ArrowRight'], up: ['KeyW', 'ArrowUp'], down: ['KeyS', 'ArrowDown'],
  attack: ['KeyJ', null], jump: ['KeyK', 'Space'], special: ['KeyL', null], back: ['KeyI', null], start: ['Enter', 'KeyP'],
};
// Standard-Gamepad (Xbox-Layout): A=0 B=1 X=2 Y=3, Start=9, Steuerkreuz 12-15
export const DEFAULT_PAD = { left: 14, right: 15, up: 12, down: 13, attack: 2, jump: 0, special: 3, back: 1, start: 9 };
const PAD_NAMES = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'BACK', 'START', 'L3', 'R3', '↑', '↓', '←', '→', 'HOME'];

export const DEFAULTS = { music: true, musicVol: 0.7, sfx: true, sfxVol: 0.8, character: 'Kai', fullscreen: false };

const clone = (o) => JSON.parse(JSON.stringify(o));

export function keyName(code) {
  if (!code) return '—';
  if (code.startsWith('Key')) return code.slice(3);
  if (code.startsWith('Digit')) return code.slice(5);
  if (code.startsWith('Numpad')) return 'NUM ' + code.slice(6);
  const map = { ArrowLeft: '←', ArrowRight: '→', ArrowUp: '↑', ArrowDown: '↓', Space: 'LEER', Enter: 'ENTER',
    ShiftLeft: 'SHIFT L', ShiftRight: 'SHIFT R', ControlLeft: 'STRG L', ControlRight: 'STRG R', AltLeft: 'ALT', AltRight: 'ALT GR',
    Backspace: '⌫', Tab: 'TAB', Comma: ',', Period: '.', Semicolon: 'Ö', Quote: 'Ä', BracketLeft: 'Ü', Minus: 'ß', Slash: '-' };
  return map[code] || code.toUpperCase();
}
export const padName = (i) => (i === null || i === undefined ? '—' : PAD_NAMES[i] || 'B' + i);

export class Settings {
  constructor() {
    Object.assign(this, clone(DEFAULTS));
    this.keys = clone(DEFAULT_KEYS);
    this.pad = clone(DEFAULT_PAD);
    this.load();
    this.rebuild();
  }
  load() {
    let raw = null;
    try { raw = JSON.parse(localStorage.getItem(STORE_KEY) || 'null'); } catch (e) { raw = null; }
    if (!raw || typeof raw !== 'object') return;
    for (const k of Object.keys(DEFAULTS)) if (typeof raw[k] === typeof DEFAULTS[k]) this[k] = raw[k];
    for (const [a] of ACTIONS) {
      if (raw.keys && Array.isArray(raw.keys[a])) this.keys[a] = [0, 1].map((i) => (typeof raw.keys[a][i] === 'string' ? raw.keys[a][i] : null));
      if (raw.pad && Number.isInteger(raw.pad[a])) this.pad[a] = raw.pad[a];
    }
  }
  save() {
    this.rebuild();
    const data = { keys: this.keys, pad: this.pad };
    for (const k of Object.keys(DEFAULTS)) data[k] = this[k];
    try { localStorage.setItem(STORE_KEY, JSON.stringify(data)); } catch (e) { /* Speicher blockiert: nur fuer diese Sitzung */ }
  }
  resetControls() { this.keys = clone(DEFAULT_KEYS); this.pad = clone(DEFAULT_PAD); this.save(); }
  /** Taste -> Aktionen (eine Taste gehoert genau einer Aktion) */
  rebuild() {
    this.keyToAction = {};
    for (const [a] of ACTIONS) for (const c of this.keys[a]) if (c) this.keyToAction[c] = a;
  }
  /** Taste neu belegen; war sie schon vergeben, bekommt die andere Aktion die alte Taste (Tausch). */
  bindKey(action, slot, code) {
    const old = this.keys[action][slot];
    for (const [a] of ACTIONS) {
      for (let i = 0; i < 2; i++) {
        if (this.keys[a][i] === code && !(a === action && i === slot)) this.keys[a][i] = a === action ? null : old;
      }
    }
    this.keys[action][slot] = code;
    this.save();
  }
  bindPad(action, button) {
    const old = this.pad[action];
    for (const [a] of ACTIONS) if (a !== action && this.pad[a] === button) this.pad[a] = old;
    this.pad[action] = button;
    this.save();
  }
  clearKey(action, slot) { this.keys[action][slot] = null; this.save(); }
  isDown(action, keys) { return this.keys[action].some((c) => c && keys.has(c)); }
}
