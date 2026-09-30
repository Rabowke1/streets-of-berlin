// Spielablauf, Stages, Kamera, HUD, Eingabe und Audio (Portierung von ABrawlerGameMode/HUD/Stage/Controller).
import { PLAYERS, STAGES, W, WEAPONS } from './data.js';
import { Effect, Enemy, Fighter, Pickup, Player, Prop, WeaponItem, Projectile } from './entities.js';
import { Menu } from './menu.js';
import { Settings } from './settings.js';

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const rand = (a, b) => a + Math.random() * (b - a);
const MAX_ATTACKERS = 2;

export class Game {
  constructor(canvas, assets, opts = {}) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d'); this.assets = assets;
    this.opts = opts;
    this.entities = []; this.player = null;
    this.flow = 'title'; this.flowTime = 0; this.paused = false;
    this.stageIndex = 0; this.stage = null;
    this.camX = 800; this.lockX = -1; this.shakeT = 0; this.shakeA = 0; this.timeScale = 1; this.slowT = 0;
    this.score = 0; this.lives = 3; this.combo = 0; this.comboT = 0; this.goT = 0; this.respawnT = -1;
    this.lastHit = null; this.lastHitT = 0;
    this.tokens = new Set();
    this.nextEnc = 0; this.activeEnc = -1; this.nextGroup = 0; this.groupT = 0; this.bossActive = false;
    this.keys = new Set(); this.pressed = new Set(); this.menuKeys = new Set(); this.padPrev = []; this.padDir = { x: 0, y: 0 };
    this.virtual = { x: 0, y: 0 }; this.virtualPrev = { x: 0, y: 0 };
    this.settings = new Settings();
    if (opts.character && PLAYERS[opts.character]) this.settings.character = opts.character;
    this.menu = new Menu(this); this.menu.reset('main');
    this.setupFullscreen();
    this.lastRender = performance.now();
    this.audio = null; this.music = null; this.musicGain = null;
    this.stats = { hits: 0, kills: 0, stagesCleared: 0, deaths: 0, frames: 0 };
    this.log = [];
    this.bindInput();
  }

  // --- Hilfen ------------------------------------------------------------------
  get viewMin() { return this.camX - W.ScreenW / 2; }
  get viewMax() { return this.camX + W.ScreenW / 2; }
  add(e) { this.entities.push(e); return e; }
  *fighters() { for (const e of this.entities) if (e instanceof Fighter && !e.dead) yield e; }
  enemies() { return this.entities.filter((e) => e instanceof Enemy && !e.dead); }
  aliveEnemies() { return this.enemies().filter((e) => e.alive).length; }
  note(msg) { this.log.push(`[${this.stats.frames}] ${msg}`); if (this.log.length > 400) this.log.shift(); }

  effect(prefix, x, depth, h, facing = 1, fps = 18, scale = 1) {
    const e = new Effect(this, prefix, fps, scale, prefix.startsWith('FX_Hit'));
    e.x = x; e.depth = depth; e.h = h; e.facing = facing;
    if (!e.dead) this.add(e);
  }
  sfx(name, vol = 1, pitchVar = 0.08) {
    if (!this.audio || this.opts.mute || !this.settings.sfx) return;
    vol *= this.settings.sfxVol;
    const el = this.assets.soundEls && this.assets.soundEls[name];
    if (el && !this.assets.sounds[name]) {
      const c = el.cloneNode();
      c.volume = Math.min(1, vol * 0.8);
      c.play().catch(() => {});
      return;
    }
    if (!this.assets.sounds[name]) return;
    const src = this.audio.createBufferSource();
    src.buffer = this.assets.sounds[name];
    src.playbackRate.value = 1 + rand(-pitchVar, pitchVar);
    const g = this.audio.createGain(); g.gain.value = vol * 0.8;
    src.connect(g).connect(this.audio.destination);
    src.start();
  }
  shake(a, t) { this.shakeA = Math.max(this.shakeT > 0 ? this.shakeA : 0, a); this.shakeT = Math.max(this.shakeT, t); }
  slowMo(scale, seconds) { this.timeScale = scale; this.slowT = seconds; }

  async initAudio() {
    if (this.audio || this.opts.mute) return;
    try {
      this.audio = new (window.AudioContext || window.webkitAudioContext)();
      await this.assets.loadSounds(this.audio);
      // Sounds laden asynchron: Musik nachholen, falls die Stage schon laeuft
      if (this.stage && !this.music && ['intro', 'playing'].includes(this.flow)) this.playMusic();
    } catch (e) { console.warn('Audio nicht verfuegbar', e); }
  }
  playMusic() {
    if (!this.audio || this.music || !this.settings.music) return;
    const el = this.assets.soundEls && this.assets.soundEls.MUS_Stage1;
    if (el && !this.assets.sounds.MUS_Stage1) {
      el.loop = true; el.volume = this.musicVolume(); el.currentTime = 0;
      el.play().catch(() => {});
      this.music = { stop: () => el.pause(), el };
      return;
    }
    if (!this.assets.sounds.MUS_Stage1) return;
    this.music = this.audio.createBufferSource();
    this.music.buffer = this.assets.sounds.MUS_Stage1; this.music.loop = true;
    this.musicGain = this.audio.createGain(); this.musicGain.gain.value = this.musicVolume();
    this.music.connect(this.musicGain).connect(this.audio.destination);
    this.music.start();
  }
  // --- Vollbild / Desktop-Version --------------------------------------------------
  /** In der .exe (Electron) stellt preload.js window.sobDesktop bereit */
  get desktop() { return window.sobDesktop || null; }
  setupFullscreen() {
    this.fullscreen = false;
    if (this.desktop) {
      this.desktop.onFullscreen((on) => { this.fullscreen = on; this.settings.fullscreen = on; this.settings.save(); });
      if (this.settings.fullscreen) this.desktop.setFullscreen(true);
    } else {
      document.addEventListener('fullscreenchange', () => { this.fullscreen = !!document.fullscreenElement; });
    }
  }
  canFullscreen() { return !!this.desktop || !!document.fullscreenEnabled; }
  isFullscreen() { return this.fullscreen; }
  toggleFullscreen() {
    if (this.desktop) { this.desktop.toggleFullscreen(); return; }
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else document.documentElement.requestFullscreen().catch(() => {});
  }
  musicVolume() { return 0.45 * this.settings.musicVol * 1.4; }
  /** Nach Aenderungen im Optionsmenue: Musik an/aus, Lautstaerke */
  applyAudio() {
    if (!this.settings.music) { this.stopMusic(); return; }
    if (this.music) {
      if (this.music.el) this.music.el.volume = Math.min(1, this.musicVolume());
      else if (this.musicGain) this.musicGain.gain.value = this.musicVolume();
    } else if (this.stage && ['intro', 'playing', 'clear'].includes(this.flow)) this.playMusic();
  }
  stopMusic() { if (this.music) { try { this.music.stop(); } catch (e) { /* schon gestoppt */ } this.music = null; } }

  // --- Ablauf ------------------------------------------------------------------
  setFlow(f) { this.flow = f; this.flowTime = 0; this.note('flow ' + f); }
  /** Figurenauswahl bestaetigt: neues Spiel */
  beginGame(character) {
    this.settings.character = PLAYERS[character] ? character : 'Kai';
    this.settings.save();
    this.menu.reset();
    this.initAudio(); this.score = 0; this.lives = 3;
    this.startStage(this.opts.stage || 0);
  }
  pause() { this.paused = true; this.menu.reset('pause'); this.sfx('SFX_Pickup', 0.3, 0); }
  resume() { this.paused = false; this.menu.reset(); }
  onStart() {
    if (this.flow === 'title') return; // Titel wird ueber das Menue bedient
    else if (this.flow === 'clear' && this.flowTime > 1.5) this.nextStage();
    else if ((this.flow === 'gameover' || this.flow === 'ending') && this.flowTime > 1.5) this.toTitle();
    else if ((this.flow === 'playing' || this.flow === 'intro') && !this.paused) this.pause();
  }
  toTitle() { this.paused = false; this.menu.reset('main'); this.stopMusic(); this.entities = []; this.player = null; this.camX = 800; this.lockX = -1; this.stageIndex = 0; this.stage = null; this.setFlow('title'); }
  nextStage() {
    if (this.stageIndex + 1 >= STAGES.length) { this.setFlow('ending'); return; }
    this.startStage(this.stageIndex + 1, true);
  }
  startStage(i, keepPlayer = false) {
    const hpCarry = keepPlayer && this.player ? this.player : null;
    this.stageIndex = i; this.stage = STAGES[i];
    this.entities = []; this.tokens.clear();
    this.camX = 800; this.lockX = -1; this.nextEnc = 0; this.activeEnc = -1; this.bossActive = false; this.goT = 0;
    this.lastHit = null; this.combo = 0; this.respawnT = -1; this.timeScale = 1;
    for (const [type, x, d, drop] of this.stage.props) { const p = new Prop(this, type, drop); p.x = x; p.depth = d; this.add(p); }
    for (const [type, x, d] of this.stage.weapons) { const w = new WeaponItem(this, type); w.x = x; w.depth = d; this.add(w); }
    const pl = new Player(this, this.settings.character); pl.x = 260; pl.depth = 110;
    if (hpCarry) pl.health = pl.maxHealth;
    this.player = this.add(pl);
    this.playMusic();
    this.setFlow('intro');
  }

  // --- Update ------------------------------------------------------------------
  update(dtReal) {
    this.pollGamepad();
    this.virtualEdges();
    if (this.menu.active) {
      const p = new Set(this.menuKeys);
      for (const a of ['up', 'down', 'left', 'right', 'start']) if (this.pressed.has(a)) p.add(a);
      if (this.pressed.has('attack')) p.add('ok');
      if (this.pressed.has('back')) p.add('back');
      this.menu.input(p);
      this.menuKeys.clear(); this.pressed.clear();
      if (this.opts.autoplay && this.flow === 'title' && this.menu.t > 1) this.beginGame(this.settings.character);
      if (this.flow === 'title' || this.paused) return;
    }
    this.menuKeys.clear();
    if (this.pressed.has('start')) this.onStart();
    if (this.opts.autoplay && this.flow === 'clear' && this.flowTime > 2) this.onStart();
    if (this.paused) { this.pressed.clear(); return; }
    this.stats.frames++;
    if (this.slowT > 0) { this.slowT -= dtReal; if (this.slowT <= 0) this.timeScale = 1; }
    const dt = dtReal * this.timeScale;
    this.flowTime += dt;

    if (this.player) this.applyInput();

    this.comboT = Math.max(0, this.comboT - dt); if (this.comboT <= 0) this.combo = 0;
    this.lastHitT = Math.max(0, this.lastHitT - dt);
    this.goT = Math.max(0, this.goT - dt);
    for (const t of [...this.tokens]) if (t.dead || !t.alive || t.downed) this.tokens.delete(t);

    if (this.flow === 'intro' && this.flowTime > 2.2) this.setFlow('playing');
    if (this.flow === 'playing') this.updateEncounters(dt);
    if (this.flow === 'clear' && this.opts.autoplay && this.flowTime > 3) this.nextStage();

    if (this.respawnT > 0) {
      this.respawnT -= dt;
      if (this.respawnT <= 0 && this.player) { this.player.x = this.camX - 250; this.player.depth = 120; this.player.dropIn(); }
    }

    for (const e of this.entities.slice()) if (!e.dead) e.update(dt);
    this.entities = this.entities.filter((e) => !e.dead);
    this.updateCamera(dt);
    this.pressed.clear();
  }

  updateCamera(dt) {
    let target = this.camX;
    if (this.lockX >= 0) target = this.lockX;
    else if (this.player && this.flow !== 'title') {
      target = Math.max(this.camX, this.player.x + 120);
      const enc = this.stage && this.stage.encounters[this.nextEnc];
      if (enc) target = Math.min(target, enc.lock);
    }
    target = clamp(target, W.ScreenW / 2, W.StageEndX - W.ScreenW / 2);
    this.camX += (target - this.camX) * Math.min(1, dt * 5);
    if (this.shakeT > 0) this.shakeT -= dt;
  }

  updateEncounters(dt) {
    const pl = this.player; if (!pl || !this.stage) return;
    const encs = this.stage.encounters;
    if (this.activeEnc < 0) {
      if (this.nextEnc < encs.length && pl.x >= encs[this.nextEnc].t) {
        this.activeEnc = this.nextEnc++;
        const e = encs[this.activeEnc];
        this.lockX = e.lock; this.goT = 0; this.bossActive = !!e.boss; this.nextGroup = 0; this.groupT = 0;
        this.note(`encounter ${this.activeEnc}`);
        this.spawnGroup(e.g[0]); this.nextGroup = 1;
      }
      return;
    }
    const e = encs[this.activeEnc];
    this.groupT += dt;
    const alive = this.aliveEnemies();
    if (this.nextGroup < e.g.length) {
      const grp = e.g[this.nextGroup];
      if (Math.abs(this.camX - this.lockX) < 40 && (alive <= grp.alive || this.groupT >= (grp.delay || 12))) {
        this.spawnGroup(grp); this.nextGroup++; this.groupT = 0;
      }
      return;
    }
    if (alive === 0 && this.groupT > 0.5) {
      this.activeEnc = -1; this.lockX = -1;
      if (e.boss) {
        this.bossActive = false;
        if (pl.alive) pl.celebrate();
        this.stats.stagesCleared++;
        this.note(`stage ${this.stageIndex + 1} clear`);
        this.setFlow('clear');
      } else { this.goT = 3.5; this.sfx('SFX_Go', 0.8, 0); }
    }
  }
  spawnGroup(grp) {
    grp.e.forEach((type, i) => {
      const right = i % 2 === 0 || ENEMY_FROM_RIGHT.has(type);
      const x = right ? this.viewMax + 80 + i * 40 : this.viewMin - 80 - i * 40;
      this.spawnEnemy(type, x, rand(W.DepthMin + 20, W.DepthMax - 20));
    });
  }
  spawnEnemy(type, x, depth) {
    const e = new Enemy(this, type);
    e.x = x; e.depth = depth; e.facing = x > this.camX ? -1 : 1; e.setEntering(true);
    this.add(e);
    if (e.boss) { this.lastHit = e; this.lastHitT = 4; }
    return e;
  }
  requestToken(e) {
    if (this.tokens.has(e)) return true;
    if (this.tokens.size < MAX_ATTACKERS) { this.tokens.add(e); return true; }
    return false;
  }
  releaseToken(e) { this.tokens.delete(e); }

  onDamage(att, victim, dmg) {
    this.stats.hits++;
    if (att && att.team === 'player') {
      this.combo = this.comboT > 0 ? this.combo + 1 : 1; this.comboT = 1.4;
      this.score += Math.round(dmg * 10) + this.combo * 5;
      this.lastHit = victim; this.lastHitT = 3;
      if (victim.boss && victim.health <= 0) { this.slowMo(0.25, 1.4); this.sfx('SFX_KO', 1, 0); }
    } else if (victim && victim.team === 'player') { this.combo = 0; this.comboT = 0; }
  }
  onEnemyKilled(e) {
    this.stats.kills++;
    this.score += e.profile.score;
    this.tokens.delete(e);
    if (e.boss) {
      for (const o of this.enemies()) if (o !== e && o.alive) { o.health = 0; o.knockdown(o.x > e.x ? 1 : -1, 250, 500); }
    }
  }
  onPlayerDied() {
    this.stats.deaths++;
    if (this.opts.god) { this.respawnT = 0.5; return; }
    this.lives--;
    if (this.lives > 0) this.respawnT = 1.0;
    else { this.stopMusic(); this.setFlow('gameover'); }
  }

  // --- Eingabe -----------------------------------------------------------------
  bindInput() {
    const MENU = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', Enter: 'ok', NumpadEnter: 'ok', Space: 'ok', Escape: 'back', Backspace: 'back' };
    window.addEventListener('keydown', (ev) => {
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'Backspace', 'Tab'].includes(ev.code)) ev.preventDefault();
      this.initAudio();
      if (this.menu.wait) { if (!ev.repeat) this.menu.captureKey(ev.code); return; }
      const action = this.settings.keyToAction[ev.code];
      if (!this.keys.has(ev.code)) {
        if (action) this.pressed.add(action);
        if (MENU[ev.code]) this.menuKeys.add(MENU[ev.code]);
        // Esc pausiert immer, auch wenn Start umbelegt wurde
        if (ev.code === 'Escape' && !this.menu.active && ['playing', 'intro'].includes(this.flow)) this.pressed.add('start');
      }
      this.keys.add(ev.code);
    });
    window.addEventListener('keyup', (ev) => this.keys.delete(ev.code));
    window.addEventListener('blur', () => { this.keys.clear(); if (['playing', 'intro'].includes(this.flow) && !this.paused && !this.opts.autoplay) this.pause(); });
    // Maus / Touch fuer Menues
    const pos = (ev) => {
      const r = this.canvas.getBoundingClientRect();
      return [(ev.clientX - r.left) * W.ScreenW / r.width, (ev.clientY - r.top) * W.ScreenH / r.height];
    };
    this.canvas.addEventListener('pointerdown', (ev) => {
      this.initAudio();
      if (!this.menu.active) {
        if (['clear', 'gameover', 'ending'].includes(this.flow)) this.pressed.add('start');
        return;
      }
      ev.preventDefault();
      this.menu.click(...pos(ev));
    });
    this.canvas.addEventListener('pointermove', (ev) => { if (this.menu.active && ev.pointerType === 'mouse') this.menu.hover(...pos(ev)); });
  }
  pollGamepad() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    const p = pads && [...pads].find((x) => x);
    this.pad = null;
    if (!p) return;
    const btn = (i) => !!(p.buttons[i] && p.buttons[i].pressed);
    const edge = (i) => btn(i) && !this.padPrev[i];
    if (this.menu.wait && this.menu.wait.col !== 2) {
      if (edge(1)) this.menu.wait = null; // B bricht das Neubelegen einer Taste ab
    } else if (this.menu.wait && this.menu.wait.col === 2) {
      const i = p.buttons.findIndex((b, j) => b.pressed && !this.padPrev[j]);
      if (i >= 0) this.menu.capturePad(i);
    } else {
      const map = this.settings.pad;
      for (const a of ['attack', 'jump', 'special', 'back', 'start']) if (edge(map[a])) this.pressed.add(a);
      // Menues: A bestaetigt, B zurueck (Standard-Konvention, unabhaengig von der Belegung)
      if (edge(0)) this.menuKeys.add('ok');
      if (edge(1)) this.menuKeys.add('back');
    }
    this.padPrev = p.buttons.map((b) => b.pressed);
    let x = p.axes[0] || 0, y = -(p.axes[1] || 0);
    if (Math.hypot(x, y) < 0.25) { x = 0; y = 0; }
    const m = this.settings.pad;
    if (btn(m.left)) x = -1; if (btn(m.right)) x = 1; if (btn(m.up)) y = 1; if (btn(m.down)) y = -1;
    this.pad = { x, y };
    this.dirEdges(this.padDir, x, y); this.padDir = { x, y };
  }
  /** Richtungs-"Tastendruecke" fuer Menues aus Stick/Steuerkreuz */
  dirEdges(prev, x, y) {
    const d = (v) => (v > 0.6 ? 1 : v < -0.6 ? -1 : 0);
    if (d(x) !== d(prev.x) && d(x)) this.menuKeys.add(d(x) > 0 ? 'right' : 'left');
    if (d(y) !== d(prev.y) && d(y)) this.menuKeys.add(d(y) > 0 ? 'up' : 'down');
  }
  virtualEdges() { this.dirEdges(this.virtualPrev, this.virtual.x, this.virtual.y); this.virtualPrev = { ...this.virtual }; }
  applyInput() {
    const pl = this.player;
    if (this.opts.autoplay) { this.botControl(pl); return; }
    const k = (a) => this.settings.isDown(a, this.keys);
    let x = (k('right') ? 1 : 0) - (k('left') ? 1 : 0);
    let y = (k('up') ? 1 : 0) - (k('down') ? 1 : 0);
    if (this.pad) { x = clamp(x + this.pad.x, -1, 1); y = clamp(y + this.pad.y, -1, 1); }
    x = clamp(x + this.virtual.x, -1, 1); y = clamp(y + this.virtual.y, -1, 1);
    pl.move2 = { x, y };
    for (const a of ['attack', 'jump', 'special', 'back']) if (this.pressed.has(a)) pl.press(a);
  }

  /** Einfacher Bot fuer automatische Tests (?autoplay=1) */
  botControl(pl) {
    pl.move2 = { x: 0, y: 0 };
    if (this.flow !== 'playing' && this.flow !== 'intro') return;
    const foes = this.enemies().filter((e) => e.alive && !e.downed && !e.entering && e.x > this.viewMin && e.x < this.viewMax);
    const items = this.entities.filter((e) => (e instanceof Pickup && pl.health < pl.maxHealth * 0.6) ||
      (e instanceof WeaponItem && !pl.weapon)).filter((e) => e.canCollect() && e.x > this.viewMin + 40 && e.x < this.viewMax - 40);
    const props = this.entities.filter((e) => e instanceof Prop && !e.broken && e.x > this.viewMin && e.x < this.viewMax);
    let target = null, mode = 'fight';
    if (foes.length) target = foes.reduce((a, b) => (Math.abs(a.x - pl.x) + Math.abs(a.depth - pl.depth) * 2 < Math.abs(b.x - pl.x) + Math.abs(b.depth - pl.depth) * 2 ? a : b));
    if ((!target || (items.length && Math.abs(items[0].x - pl.x) < 200)) && items.length) { target = items[0]; mode = 'item'; }
    if (!target && props.length) { target = props[0]; mode = 'prop'; }
    if (!target) { pl.move2 = { x: 1, y: (110 - pl.depth) / 100 }; return; }
    const near = foes.filter((e) => Math.abs(e.x - pl.x) < 130 && Math.abs(e.depth - pl.depth) < 30).length;
    if (near >= 2 && pl.health > 30 && Math.random() < 0.05) { pl.press('special'); return; }
    const side = mode === 'fight' ? (pl.x < target.x ? -1 : 1) : 0;
    const want = mode === 'item' ? 0 : (pl.weapon ? 95 : 70);
    const tx = target.x + side * want;
    const dx = tx - pl.x, dd = target.depth - pl.depth;
    pl.move2 = { x: Math.abs(dx) > 10 ? Math.sign(dx) : 0, y: Math.abs(dd) > 6 ? clamp(dd / 30, -1, 1) : 0 };
    if (mode === 'item' && Math.abs(target.x - pl.x) < 40 && Math.abs(dd) < 20) { pl.move2 = { x: 0, y: 0 }; pl.press('attack'); return; }
    const inRange = Math.abs(target.x - pl.x) < want + 40 && Math.abs(dd) < 12;
    if (inRange) {
      pl.facing = Math.sign(target.x - pl.x) || pl.facing;
      pl.move2 = { x: 0, y: 0 };
      if (Math.random() < 0.5) pl.press('attack');
      if (mode === 'fight' && Math.random() < 0.01) pl.press('jump');
    }
  }

  // --- Rendering -----------------------------------------------------------------
  sx(x) { return x - this.camX + W.ScreenW / 2; }
  sy(z) { return W.ScreenH / 2 - (z - W.CameraZ); }

  render() {
    const ctx = this.ctx;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#0a0814'; ctx.fillRect(0, 0, W.ScreenW, W.ScreenH);
    let ox = 0, oy = 0;
    if (this.shakeT > 0) { ox = rand(-this.shakeA, this.shakeA); oy = rand(-this.shakeA, this.shakeA) * 0.6; }
    ctx.save(); ctx.translate(ox, oy);
    const st = this.stage || STAGES[0];
    this.drawBackground(st);
    this.drawEntities();
    this.drawForeground(st);
    ctx.restore();
    this.drawHUD();
    const now = performance.now();
    this.menu.render(Math.min(0.1, (now - this.lastRender) / 1000));
    this.lastRender = now;
  }
  bgImg(name) { return this.assets.bg[name]; }
  bgSize(name) { return this.assets.index.backgrounds[name].size; }
  drawBg(name, cx, cz) {
    const img = this.bgImg(name); if (!img) return;
    const [w, h] = this.bgSize(name);
    const x = this.sx(cx) - w / 2, y = this.sy(cz) - h / 2;
    if (x > W.ScreenW || x + w < 0) return;
    this.ctx.drawImage(img, x, y, w, h);
  }
  drawBackground(st) {
    const ctx = this.ctx;
    for (const a of st.areas) {
      if (a.x1 < this.viewMin || a.x0 > this.viewMax) continue;
      ctx.save();
      ctx.beginPath(); ctx.rect(this.sx(a.x0), -100, a.x1 - a.x0, W.ScreenH + 200); ctx.clip();
      if (a.sky) {
        const lo = Math.max(a.x0 + 800, 800), hi = Math.min(a.x1 - 800, W.StageEndX - 800);
        const base = (lo + hi) / 2;
        this.drawBg(a.sky, this.camX + (base - this.camX) * 0.15, W.FloorTopZ + 350);
      }
      a.walls.forEach((n, i) => this.drawBg(n, a.x0 + 1024 + i * 2048, W.FloorTopZ + 280));
      for (let x = a.x0; x < a.x1; x += 1024) this.drawBg(a.floor, x + 512, W.FloorTopZ - 210);
      ctx.restore();
    }
  }
  drawForeground(st) {
    for (const a of st.areas) {
      if (!a.fg) continue;
      const [name, xs] = a.fg;
      for (const bx of xs) this.drawBg(name, this.camX + (bx - this.camX) * 1.25, W.CameraZ);
    }
  }
  drawEntities() {
    const A = this.assets, ctx = this.ctx;
    const list = this.entities.filter((e) => !e.dead);
    // Schatten
    for (const e of list) {
      if (!e.shadow) continue;
      const fade = clamp(1 - e.h / 400, 0.35, 1);
      A.draw(ctx, 'FX_Shadow', this.sx(e.x), this.sy(e.depth), 55, 15, false, e.shadow * fade, 1);
    }
    list.sort((a, b) => (a.front - b.front) || (b.depth - a.depth) || (a.h - b.h));
    for (const e of list) {
      if (e.blink > 0 && (e.blink % 0.12) < 0.06) continue;
      const name = e.frameName; if (!name) continue;
      const px = this.sx(e.x) + (e.shake > 0 ? rand(-4, 4) : 0);
      const py = this.sy(e.depth + e.h);
      const [fw, fh] = A.frameSize(name);
      if (e instanceof Fighter) {
        A.draw(ctx, name, px, py, W.FootX, W.FootY, e.facing < 0);
        if (e.weapon) this.drawHeldWeapon(e, name, px, py);
      } else if (e instanceof Projectile) {
        const w = A.anchors.weapons[e.type];
        ctx.save(); ctx.translate(px, py); if (e.facing < 0) ctx.scale(-1, 1); ctx.rotate(e.spin);
        A.draw(ctx, name, 0, 0, w.size[0] / 2, w.size[1] / 2);
        ctx.restore();
      } else if (e instanceof Effect) {
        const ay = e.foot === 'dust' ? fh / 2 + 30 : fh / 2;
        A.draw(ctx, name, px, py, fw / 2, ay, e.facing < 0, e.scale || 1);
      } else {
        A.draw(ctx, name, px, py, fw / 2, A.frameBottom(name) - 6, false);
      }
    }
  }
  drawHeldWeapon(f, frameName, px, py) {
    const A = this.assets, anc = A.anchors.frames[frameName], w = A.anchors.weapons[f.weapon];
    if (!anc || !w) return;
    const [ax, ay, ang] = anc;
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(px, py);
    if (f.facing < 0) ctx.scale(-1, 1);
    ctx.translate(ax, -ay);
    ctx.rotate(-(ang + WEAPONS[f.weapon].hold) * Math.PI / 180);
    A.draw(ctx, 'Weapon_' + f.weapon, 0, 0, w.grip[0], w.grip[1]);
    ctx.restore();
  }

  // --- HUD --------------------------------------------------------------------------
  text(s, x, y, size, color, align = 'left') {
    const ctx = this.ctx;
    ctx.font = `900 ${size}px "Arial Black", "Helvetica Neue", Arial, sans-serif`;
    ctx.textAlign = align; ctx.textBaseline = 'top';
    ctx.lineWidth = Math.max(3, size * 0.16); ctx.strokeStyle = '#0a0610'; ctx.lineJoin = 'round';
    ctx.strokeText(s, x, y); ctx.fillStyle = color; ctx.fillText(s, x, y);
  }
  bar(x, y, w, h, v, rec, color, rtl) {
    const ctx = this.ctx;
    ctx.fillStyle = '#0a0610'; ctx.fillRect(x - 4, y - 4, w + 8, h + 8);
    ctx.fillStyle = '#2e1f29'; ctx.fillRect(x, y, w, h);
    v = clamp(v, 0, 1); const r = clamp(v + rec, 0, 1);
    ctx.fillStyle = '#4de65a'; ctx.fillRect(rtl ? x + w * (1 - r) : x, y, w * r, h);
    ctx.fillStyle = color; ctx.fillRect(rtl ? x + w * (1 - v) : x, y, w * v, h);
    ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(x, y + 2, w, 3);
  }
  panel(f, right, rec) {
    const ctx = this.ctx, A = this.assets;
    const P = 96, BW = 400, px = right ? 1600 - 24 - P : 24;
    ctx.fillStyle = '#0a0610'; ctx.fillRect(px - 4, 14, P + 8, P + 8);
    ctx.fillStyle = right ? '#591a26' : '#1a3366'; ctx.fillRect(px, 18, P, P);
    const pn = 'Portrait_' + f.sprite;
    if (A.has(pn)) { const [fw] = A.frameSize(pn); A.draw(ctx, pn, px, 18, 0, 0, false, P / fw); }
    const bx = right ? px - 16 - BW : px + P + 16;
    this.text(f.displayName, right ? bx + BW : bx, 16, 26, '#fff', right ? 'right' : 'left');
    this.bar(bx, 52, BW, 22, f.health / f.maxHealth, rec / f.maxHealth, right ? '#f23333' : '#ffc71a', right);
    if (f.weapon && !right) {
      const w = WEAPONS[f.weapon];
      this.text(`${w.name} ${f.weaponDur > 50 ? '' : '×' + f.weaponDur}`, bx + BW + 16, 50, 20, '#9fe8ff');
    }
  }
  drawHUD() {
    const ctx = this.ctx, A = this.assets;
    const blink = (performance.now() % 800) < 500;
    if (this.flow === 'title') {
      ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, 1600, 900);
      if (A.has('UI_Logo') && this.menu.top && this.menu.top.id === 'main') A.draw(ctx, 'UI_Logo', 800, 90, 550, 0);
      return;
    }
    if (this.player) {
      this.panel(this.player, false, this.player.recoverable);
      this.text('x' + Math.max(0, this.lives - 1), 30, 120, 26, '#ffc71a');
      this.text(String(this.score).padStart(7, '0'), 136, 84, 26, '#fff');
    }
    const e = this.lastHit;
    if (e && !e.dead && (this.lastHitT > 0 || (this.bossActive && e.boss))) this.panel(e, true, 0);
    if (this.combo >= 2 && this.comboT > 0) {
      const pop = 1 + clamp(this.comboT - 1.2, 0, 0.2) * 2;
      this.text(String(this.combo), 40, 170, 64 * pop, '#ffc71a');
      this.text('HITS', 40, 245, 26, '#fff');
    }
    if (this.goT > 0 && blink && A.has('UI_Go')) A.draw(ctx, 'UI_Go', 1360, 360, 0, 0);
    const st = this.stage;
    const dim = (a) => { ctx.fillStyle = `rgba(0,0,0,${a})`; ctx.fillRect(0, 0, 1600, 900); };
    if (this.flow === 'intro' && st) {
      this.text(st.name, 800, 320, 56, '#ffc71a', 'center');
      this.text(st.title, 800, 400, 40, '#fff', 'center');
    } else if (this.flow === 'clear') {
      dim(clamp(this.flowTime * 0.3, 0, 0.5));
      this.text(`${st.name} CLEAR!`, 800, 290, 72, '#ffc71a', 'center');
      this.text(`PUNKTE: ${this.score}`, 800, 410, 40, '#fff', 'center');
      if (this.flowTime > 1.5 && blink) this.text(this.stageIndex + 1 < STAGES.length ? 'ENTER: WEITER' : 'ENTER', 800, 510, 30, '#fff', 'center');
    } else if (this.flow === 'gameover') {
      dim(clamp(this.flowTime * 0.4, 0, 0.65));
      this.text('GAME OVER', 800, 320, 80, '#ff4080', 'center');
      if (this.flowTime > 1.5 && blink) this.text('ENTER / START: NOCHMAL', 800, 470, 30, '#fff', 'center');
    } else if (this.flow === 'ending') {
      dim(0.7);
      this.text('BERLIN IST GERETTET!', 800, 260, 64, '#ffc71a', 'center');
      this.text('Harald Immobilien ist pleite – die Mieten bleiben bezahlbar.', 800, 360, 30, '#fff', 'center');
      this.text(`ENDPUNKTE: ${this.score}`, 800, 440, 40, '#fff', 'center');
      if (this.flowTime > 1.5 && blink) this.text('ENTER: TITEL', 800, 540, 30, '#fff', 'center');
    }
  }
}

const ENEMY_FROM_RIGHT = new Set(['Rolf', 'Sven', 'Harald']);
