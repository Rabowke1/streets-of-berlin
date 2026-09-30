// Spielablauf, Stages, Kamera, HUD, Eingabe und Audio (Portierung von ABrawlerGameMode/HUD/Stage/Controller).
import { ENEMIES, PLAYERS, STAGES, W, WEAPONS, atk } from './data.js';
import { Effect, Enemy, FallingBeam, Fighter, GolfBall, Pickup, Player, Prop, WeaponItem, Projectile } from './entities.js';
import { Menu } from './menu.js';
import { Settings } from './settings.js';

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const rand = (a, b) => a + Math.random() * (b - a);
const MAX_ATTACKERS = 2;

export class Game {
  constructor(canvas, assets, opts = {}) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d'); this.assets = assets;
    this.opts = opts;
    this.entities = []; this.players = [];
    // Spieler-Aufstellung fuer das naechste Spiel: [{ char, device }] (device: 'all' | 'kb' | 'padN')
    this.party = [];
    this.flow = 'title'; this.flowTime = 0; this.paused = false;
    this.stageIndex = 0; this.stage = null;
    this.camX = 800; this.lockX = -1; this.shakeT = 0; this.shakeA = 0; this.timeScale = 1; this.slowT = 0;
    this.combo = 0; this.comboT = 0; this.goT = 0; this.respawnT = -1;
    this.lastHit = null; this.lastHitT = 0;
    this.tokens = new Set();
    this.nextEnc = 0; this.activeEnc = -1; this.nextGroup = 0; this.groupT = 0; this.bossActive = false;
    this.keys = new Set(); this.pressed = new Set(); this.menuKeys = new Set();
    // Eingaben je Geraet ('kb' = Tastatur + Touch, 'pad0'..'pad3'): Aktionen und Menue-Impulse dieses Frames
    this.devPressed = new Map(); this.devMenu = new Map(); this.pads = {}; this.lastMenuDev = 'kb';
    // Boss-Mechaniken der Stage und Einblendungen
    this.train = null; this.spot = null; this.popups = []; this.bossIntro = null; this.flash = 0;
    this.virtual = { x: 0, y: 0 }; this.virtualPrev = { x: 0, y: 0 };
    this.settings = new Settings();
    if (opts.character && PLAYERS[opts.character]) this.settings.character = opts.character;
    this.menu = new Menu(this); this.menu.reset('main');
    this.setupFullscreen();
    this.lastRender = performance.now();
    this.audio = null; this.music = null; this.musicGain = null;
    this.stats = { hits: 0, kills: 0, stagesCleared: 0, deaths: 0, frames: 0 };
    this.log = []; this.fullLog = [];
    this.bindInput();
  }

  // --- Hilfen ------------------------------------------------------------------
  /** Spieler 1 (fuer Einzelspieler-Code und Tests) */
  get player() { return this.players[0] || null; }
  /** Spieler, die noch im Spiel sind (nicht endgueltig raus) */
  activePlayers() { return this.players.filter((p) => !p.out); }
  get score() { return this.players.reduce((a, p) => a + p.score, 0); }
  addScore(who, n) {
    const pl = who instanceof Player ? who : this.players[0];
    if (pl) pl.score = Math.max(0, pl.score + n);
  }
  popup(text, x, depth, h, color = '#fff') { this.popups.push({ text, x, depth, h, color, t: 0 }); }
  get viewMin() { return this.camX - W.ScreenW / 2; }
  get viewMax() { return this.camX + W.ScreenW / 2; }
  add(e) { this.entities.push(e); return e; }
  *fighters() { for (const e of this.entities) if (e instanceof Fighter && !e.dead) yield e; }
  enemies() { return this.entities.filter((e) => e instanceof Enemy && !e.dead); }
  aliveEnemies() { return this.enemies().filter((e) => e.alive).length; }
  note(msg) {
    const line = `[${this.stats.frames}] ${msg}`;
    this.log.push(line); if (this.log.length > 400) this.log.shift();
    this.fullLog.push(line); if (this.fullLog.length > 5000) this.fullLog.shift();
  }

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
  /** Figurenauswahl bestaetigt: neues Spiel. chars/devices je Spieler (1 oder 2 Eintraege). */
  beginGame(chars, devices) {
    chars = (Array.isArray(chars) ? chars : [chars]).map((c) => (PLAYERS[c] ? c : 'Kai'));
    devices = devices || (chars.length > 1 ? ['kb', 'pad0'] : ['all']);
    this.settings.character = chars[0];
    this.settings.save();
    this.menu.reset();
    this.initAudio();
    this.party = chars.map((c, i) => ({ char: c, device: devices[i] || 'all' }));
    this.players = [];
    this.note('party ' + this.party.map((p) => p.char + '@' + p.device).join(', '));
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
  toTitle() { this.paused = false; this.menu.reset('main'); this.stopMusic(); this.entities = []; this.players = []; this.train = null; this.spot = null; this.bossIntro = null; this.camX = 800; this.lockX = -1; this.stageIndex = 0; this.stage = null; this.setFlow('title'); }
  nextStage() {
    if (this.stageIndex + 1 >= STAGES.length) { this.setFlow('ending'); return; }
    this.startStage(this.stageIndex + 1, true);
  }
  startStage(i, keepPlayer = false) {
    const prev = keepPlayer ? this.players : [];
    this.stageIndex = i; this.stage = STAGES[i];
    this.entities = []; this.tokens.clear();
    this.camX = 800; this.lockX = -1; this.nextEnc = 0; this.activeEnc = -1; this.bossActive = false; this.goT = 0;
    this.lastHit = null; this.combo = 0; this.timeScale = 1;
    this.train = null; this.spot = null; this.popups = []; this.bossIntro = null;
    for (const [type, x, d, drop] of this.stage.props) { const p = new Prop(this, type, drop); p.x = x; p.depth = d; this.add(p); }
    for (const [type, x, d] of this.stage.weapons) { const w = new WeaponItem(this, type); w.x = x; w.depth = d; this.add(w); }
    this.players = this.party.map((m, idx) => {
      const pl = new Player(this, m.char);
      pl.index = idx; pl.device = m.device;
      pl.x = 260 - idx * 70; pl.depth = 110 + idx * 70;
      const old = prev[idx];
      if (old) { pl.score = old.score; pl.lives = old.out ? 0 : old.lives; pl.out = old.out; }
      if (!pl.out) this.add(pl);
      return pl;
    });
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
      // Menue-Impulse je Geraet (fuer die Figurenauswahl zu zweit)
      const byDev = new Map();
      for (const [dev, set] of this.devMenu) byDev.set(dev, new Set(set));
      for (const [dev, set] of this.devPressed) {
        const m = byDev.get(dev) || new Set();
        for (const a of ['up', 'down', 'left', 'right', 'start']) if (set.has(a)) m.add(a);
        if (set.has('attack')) m.add('ok');
        if (set.has('back')) m.add('back');
        byDev.set(dev, m);
      }
      for (const [dev, m] of byDev) if (m.has('ok') || m.has('start')) this.lastMenuDev = dev;
      this.menu.input(p, byDev);
      this.clearInput();
      if (this.opts.autoplay && this.flow === 'title' && this.menu.t > 1) {
        const first = this.opts.character || this.settings.character;
        const other = Object.keys(PLAYERS).find((c) => c !== first);
        this.beginGame(this.opts.players > 1 ? [first, other] : [first]);
      }
      if (this.flow === 'title' || this.paused) return;
    }
    this.menuKeys.clear(); this.devMenu.clear();
    if (this.pressed.has('start')) this.onStart();
    if (this.opts.autoplay && this.flow === 'clear' && this.flowTime > 2) this.onStart();
    if (this.paused) { this.clearInput(); return; }
    this.stats.frames++;
    if (this.slowT > 0) { this.slowT -= dtReal; if (this.slowT <= 0) this.timeScale = 1; }
    const dt = dtReal * this.timeScale;
    this.flowTime += dt;

    for (const pl of this.players) if (!pl.out) this.applyInput(pl);

    this.comboT = Math.max(0, this.comboT - dt); if (this.comboT <= 0) this.combo = 0;
    this.lastHitT = Math.max(0, this.lastHitT - dt);
    this.goT = Math.max(0, this.goT - dt);
    for (const t of [...this.tokens]) if (t.dead || !t.alive || t.downed) this.tokens.delete(t);

    if (this.flow === 'intro' && this.flowTime > 2.2) this.setFlow('playing');
    if (this.flow === 'playing') this.updateEncounters(dt);
    if (this.flow === 'clear' && this.opts.autoplay && this.flowTime > 3) this.nextStage();

    for (const pl of this.players) {
      if (pl.respawnT > 0) {
        pl.respawnT -= dt;
        if (pl.respawnT <= 0) { pl.x = this.camX - 250 + pl.index * 90; pl.depth = 120 + pl.index * 50; pl.dropIn(); }
      }
    }
    this.updateHazards(dt);

    for (const e of this.entities.slice()) if (!e.dead) e.update(dt);
    this.entities = this.entities.filter((e) => !e.dead);
    this.updateCamera(dt);
    this.clearInput();
  }
  clearInput() { this.pressed.clear(); this.menuKeys.clear(); this.devPressed.clear(); this.devMenu.clear(); }
  devAdd(map, dev, a) { let s = map.get(dev); if (!s) map.set(dev, (s = new Set())); s.add(a); }

  // --- Boss-Mechaniken der Stage (U-Bahn, Spotlight) sowie Einblendungen -----------
  /** Kontrolleur Klaus: Warnung, dann faehrt ein Zug durch die hintere Spur */
  startTrain() {
    this.train = { phase: 'warn', t: 0, x: 0, hit: new Set() };
    this.sfx('SFX_Go', 0.8, 0); this.note('train');
  }
  get trainZone() { return W.DepthMax - 75; }
  /** Die Tuer: Spotlight verfolgt einen Spieler, dann Bass-Drop */
  startSpot(target) {
    this.spot = { target, x: target.x, depth: target.depth, t: 0 };
    this.note('spot');
  }
  updateHazards(dt) {
    this.flash = Math.max(0, this.flash - dt * 2.5);
    for (const p of this.popups) p.t += dt;
    this.popups = this.popups.filter((p) => p.t < 1.3);
    if (this.bossIntro) { this.bossIntro.t += dt; if (this.bossIntro.t > 3.2) this.bossIntro = null; }
    const tr = this.train;
    if (tr) {
      tr.t += dt;
      if (tr.phase === 'warn' && tr.t > 2.2) { tr.phase = 'pass'; tr.x = this.viewMin - 60; this.sfx('SFX_Whoosh', 1, 0); this.shake(5, 1.0); }
      if (tr.phase === 'pass') {
        tr.x += 2800 * dt;
        const a = { ...atk({ dmg: 20, type: 'kd', kb: 520, launch: 480, stop: 0.1 }) };
        for (const f of this.fighters()) {
          if (f.boss || tr.hit.has(f) || !f.alive || f.h > 140 || f.depth < this.trainZone) continue;
          if (f.x < tr.x && f.x > tr.x - 1600) {
            tr.hit.add(f);
            const fake = { team: 'hazard', x: f.x - 50, h: 0, facing: 1 };
            if (f.receiveHit(fake, f.team === 'enemy' ? { ...a, dmg: 35 } : a, 1)) this.popup('AUTSCH!', f.x, f.depth, 220, '#ffd24a');
          }
        }
        if (tr.x - 1600 > this.viewMax + 100) this.train = null;
      }
    }
    const sp = this.spot;
    if (sp) {
      sp.t += dt;
      const tg = sp.target;
      if (sp.t < 2.4 && tg && !tg.dead) {
        const k = Math.min(1, dt * 2.6);
        sp.x += (tg.x - sp.x) * k; sp.depth += (tg.depth - sp.depth) * k;
      }
      if (sp.t >= 3.0) {
        this.spot = null; this.flash = 1; this.shake(12, 0.4);
        this.sfx('SFX_Special', 1, 0); this.sfx('SFX_HitHeavy', 1, 0);
        this.effect('FX_SpecialRing', sp.x, sp.depth, 10, 1, 14, 1.4);
        const a = atk({ dmg: 22, type: 'kd', kb: 380, launch: 560, stop: 0.12 });
        for (const f of this.fighters()) {
          if (f.boss || !f.alive) continue;
          const nx = (f.x - sp.x) / 150, nd = (f.depth - sp.depth) / 48;
          if (nx * nx + nd * nd <= 1) f.receiveHit({ team: 'hazard', x: sp.x, h: 0, facing: 1 }, a, Math.sign(f.x - sp.x) || 1);
        }
        this.note('bass drop');
      }
    }
  }

  updateCamera(dt) {
    let target = this.camX;
    if (this.lockX >= 0) target = this.lockX;
    else if (this.flow !== 'title' && this.activePlayers().length) {
      const xs = this.activePlayers().map((p) => p.x);
      target = Math.max(this.camX, Math.max(...xs) + 120);
      // Zu zweit: niemand darf links aus dem Bild fallen
      target = Math.min(target, Math.min(...xs) + W.ScreenW / 2 - 90);
      target = Math.max(target, this.camX);
      const enc = this.stage && this.stage.encounters[this.nextEnc];
      if (enc) target = Math.min(target, enc.lock);
    }
    target = clamp(target, W.ScreenW / 2, W.StageEndX - W.ScreenW / 2);
    this.camX += (target - this.camX) * Math.min(1, dt * 5);
    if (this.shakeT > 0) this.shakeT -= dt;
  }

  updateEncounters(dt) {
    const act = this.activePlayers(); if (!act.length || !this.stage) return;
    const leadX = Math.max(...act.map((p) => p.x));
    const encs = this.stage.encounters;
    if (this.activeEnc < 0) {
      if (this.nextEnc < encs.length && leadX >= encs[this.nextEnc].t) {
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
        for (const p of this.activePlayers()) if (p.alive) p.celebrate();
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
    // Zu zweit halten Gegner mehr aus
    if (this.activePlayers().length > 1) e.maxHealth = e.health = Math.round(e.maxHealth * (e.boss ? 1.5 : 1.3));
    this.add(e);
    if (e.boss) { this.bossIntro = { e, t: 0 }; this.note('boss ' + type); this.sfx('SFX_Go', 1, 0); }
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
      this.addScore(att, Math.round(dmg * 10) + this.combo * 5);
      victim.lastAttacker = att;
      this.lastHit = victim; this.lastHitT = 3;
      if (victim.boss && victim.health <= 0) { this.slowMo(0.25, 1.4); this.sfx('SFX_KO', 1, 0); }
    } else if (victim && victim.team === 'player') { this.combo = 0; this.comboT = 0; }
  }
  onEnemyKilled(e) {
    this.stats.kills++;
    this.addScore(e.lastAttacker, e.profile.score);
    if (e.boss) {
      this.note('boss down ' + e.type);
      this.train = null; this.spot = null;
      const enc = this.stage && this.stage.encounters[this.activeEnc];
      if (enc) this.nextGroup = enc.g.length; // nach dem Boss keine weiteren Wellen
    }
    this.tokens.delete(e);
    if (e.boss) {
      for (const o of this.enemies()) if (o !== e && o.alive) { o.health = 0; o.knockdown(o.x > e.x ? 1 : -1, 250, 500); }
    }
  }
  onPlayerDied(pl) {
    this.stats.deaths++;
    if (this.opts.god) { pl.respawnT = 0.5; return; }
    pl.lives--;
    if (pl.lives > 0) { pl.respawnT = 1.0; return; }
    pl.out = true; pl.destroy();
    this.note(`P${pl.index + 1} raus`);
    if (!this.activePlayers().length) { this.stopMusic(); this.setFlow('gameover'); }
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
        if (action) { this.pressed.add(action); this.devAdd(this.devPressed, 'kb', action); }
        if (MENU[ev.code]) { this.menuKeys.add(MENU[ev.code]); this.devAdd(this.devMenu, 'kb', MENU[ev.code]); }
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
  /** Touch-Knopf (touch.js): zaehlt als Tastatur-Spieler */
  touchPress(a) { this.pressed.add(a); this.devAdd(this.devPressed, 'kb', a); }
  /** Alle angeschlossenen Gamepads einzeln abfragen (pad0..pad3) */
  pollGamepad() {
    const list = navigator.getGamepads ? [...navigator.getGamepads()] : [];
    const seen = new Set();
    list.forEach((p, idx) => {
      if (!p || !p.connected) return;
      const dev = 'pad' + idx; seen.add(dev);
      const st = this.pads[dev] || (this.pads[dev] = { prev: [], dir: { x: 0, y: 0 }, x: 0, y: 0 });
      const btn = (i) => !!(p.buttons[i] && p.buttons[i].pressed);
      const edge = (i) => btn(i) && !st.prev[i];
      if (this.menu.wait && this.menu.wait.col !== 2) {
        if (edge(1)) this.menu.wait = null; // B bricht das Neubelegen einer Taste ab
      } else if (this.menu.wait && this.menu.wait.col === 2) {
        const i = p.buttons.findIndex((b, j) => b.pressed && !st.prev[j]);
        if (i >= 0) this.menu.capturePad(i);
      } else {
        const map = this.settings.pad;
        for (const a of ['attack', 'jump', 'special', 'back', 'start']) {
          if (edge(map[a])) { this.pressed.add(a); this.devAdd(this.devPressed, dev, a); }
        }
        // Menues: A bestaetigt, B zurueck (Standard-Konvention, unabhaengig von der Belegung)
        if (edge(0)) { this.menuKeys.add('ok'); this.devAdd(this.devMenu, dev, 'ok'); }
        if (edge(1)) { this.menuKeys.add('back'); this.devAdd(this.devMenu, dev, 'back'); }
      }
      st.prev = p.buttons.map((b) => b.pressed);
      let x = p.axes[0] || 0, y = -(p.axes[1] || 0);
      if (Math.hypot(x, y) < 0.25) { x = 0; y = 0; }
      const m = this.settings.pad;
      if (btn(m.left)) x = -1; if (btn(m.right)) x = 1; if (btn(m.up)) y = 1; if (btn(m.down)) y = -1;
      st.x = x; st.y = y;
      this.dirEdges(st.dir, x, y, dev); st.dir = { x, y };
    });
    for (const dev of Object.keys(this.pads)) if (!seen.has(dev)) delete this.pads[dev];
  }
  /** Richtungs-"Tastendruecke" fuer Menues aus Stick/Steuerkreuz */
  dirEdges(prev, x, y, dev = 'kb') {
    const d = (v) => (v > 0.6 ? 1 : v < -0.6 ? -1 : 0);
    const add = (a) => { this.menuKeys.add(a); this.devAdd(this.devMenu, dev, a); };
    if (d(x) !== d(prev.x) && d(x)) add(d(x) > 0 ? 'right' : 'left');
    if (d(y) !== d(prev.y) && d(y)) add(d(y) > 0 ? 'up' : 'down');
  }
  virtualEdges() { this.dirEdges(this.virtualPrev, this.virtual.x, this.virtual.y, 'kb'); this.virtualPrev = { ...this.virtual }; }
  /** Geraete eines Spielers: allein spielt man mit allem, zu zweit hat jeder sein Geraet */
  devicesOf(pl) { return pl.device === 'all' ? ['kb', ...Object.keys(this.pads)] : [pl.device]; }
  applyInput(pl) {
    if (this.opts.autoplay) { this.botControl(pl); return; }
    let x = 0, y = 0;
    const devs = this.devicesOf(pl);
    for (const dev of devs) {
      if (dev === 'kb') {
        const k = (a) => this.settings.isDown(a, this.keys);
        x += (k('right') ? 1 : 0) - (k('left') ? 1 : 0) + this.virtual.x;
        y += (k('up') ? 1 : 0) - (k('down') ? 1 : 0) + this.virtual.y;
      } else if (this.pads[dev]) { x += this.pads[dev].x; y += this.pads[dev].y; }
    }
    pl.move2 = { x: clamp(x, -1, 1), y: clamp(y, -1, 1) };
    for (const dev of devs) {
      const set = this.devPressed.get(dev);
      if (set) for (const a of ['attack', 'jump', 'special', 'back']) if (set.has(a)) pl.press(a);
    }
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
    // Boss-Gefahren ausweichen: Zugspur, Spotlight, Traeger-Schatten
    if (this.train && pl.depth > this.trainZone - 25) { pl.move2 = { x: 0, y: -1 }; return; }
    if (this.spot && this.spot.t > 1.6 && Math.hypot((pl.x - this.spot.x) / 150, (pl.depth - this.spot.depth) / 48) < 1.4) {
      pl.move2 = { x: Math.sign(pl.x - this.spot.x) || 1, y: Math.sign(pl.depth - this.spot.depth) || 1 }; return;
    }
    const beam = this.entities.find((b) => b instanceof FallingBeam && !b.landed && Math.abs(b.x - pl.x) < 150 && Math.abs(b.depth - pl.depth) < 40);
    if (beam) { pl.move2 = { x: Math.sign(pl.x - beam.x) || 1, y: 0 }; return; }
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
    this.drawPopups();
    ctx.restore();
    if (this.flash > 0) { ctx.fillStyle = `rgba(255,120,220,${this.flash * 0.45})`; ctx.fillRect(0, 0, W.ScreenW, W.ScreenH); }
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
    this.drawHazards(list);
    list.sort((a, b) => (a.front - b.front) || (b.depth - a.depth) || (a.h - b.h));
    for (const e of list) {
      if (e.blink > 0 && (e.blink % 0.12) < 0.06) continue;
      if (e instanceof GolfBall) {
        ctx.beginPath(); ctx.arc(this.sx(e.x), this.sy(e.depth + e.h), 10, 0, Math.PI * 2);
        ctx.fillStyle = '#fbfbf4'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#0a0610'; ctx.stroke();
        continue;
      }
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
  /** Boden-Markierungen und Zug (liegen unter den Figuren) */
  drawHazards(list) {
    const ctx = this.ctx, A = this.assets;
    const now = performance.now() / 1000;
    const floorEllipse = (x, depth, rx, rd, fill) => {
      ctx.beginPath(); ctx.ellipse(this.sx(x), this.sy(depth), rx, rd, 0, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill();
    };
    // Stahltraeger: wachsender Warnschatten
    for (const b of list) {
      if (!(b instanceof FallingBeam) || b.landed) continue;
      const k = b.warn;
      floorEllipse(b.x, b.depth, 40 + 90 * k, 10 + 18 * k, `rgba(10,0,0,${0.25 + 0.45 * k})`);
      ctx.lineWidth = 3; ctx.strokeStyle = `rgba(255,60,60,${0.4 + 0.5 * Math.abs(Math.sin(now * 12))})`; ctx.stroke();
    }
    // U-Bahn: Warnstreifen, dann der Zug in der hinteren Spur
    const tr = this.train;
    if (tr) {
      const y0 = this.sy(W.DepthMax + 12), y1 = this.sy(this.trainZone);
      if (tr.phase === 'warn') {
        ctx.fillStyle = `rgba(255,40,40,${0.18 + 0.2 * Math.abs(Math.sin(now * 9))})`;
        ctx.fillRect(0, y0, W.ScreenW, y1 - y0);
      } else if (this.bgImg('FX_Train')) {
        const [w, h] = this.bgSize('FX_Train');
        ctx.drawImage(this.bgImg('FX_Train'), this.sx(tr.x) - w, y1 - h + 10, w, h);
      }
    }
    // Spotlight der Tuer: Lichtkegel von oben + Kreis am Boden
    const sp = this.spot;
    if (sp) {
      const lock = sp.t > 2.4;
      const a = lock ? 0.45 + 0.35 * Math.abs(Math.sin(now * 20)) : 0.35;
      const x = this.sx(sp.x), y = this.sy(sp.depth);
      const g = ctx.createLinearGradient(0, 0, 0, y);
      g.addColorStop(0, 'rgba(255,120,220,0)'); g.addColorStop(1, `rgba(255,120,220,${a * 0.5})`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(x - 30, 0); ctx.lineTo(x + 30, 0); ctx.lineTo(x + 150, y); ctx.lineTo(x - 150, y); ctx.closePath(); ctx.fill();
      floorEllipse(sp.x, sp.depth, 150, 48, `rgba(255,150,230,${a})`);
      ctx.lineWidth = 4; ctx.strokeStyle = lock ? '#ffffff' : '#ff60c0'; ctx.stroke();
    }
  }
  /** Texte ueber den Figuren (WUT!, GEBLOCKT, Strafe …) */
  drawPopups() {
    for (const p of this.popups) {
      const k = p.t / 1.3;
      this.ctx.globalAlpha = clamp(1.6 - k * 1.6, 0, 1);
      this.text(p.text, this.sx(p.x), this.sy(p.depth + p.h) - k * 50, 28, p.color, 'center');
      this.ctx.globalAlpha = 1;
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
  /** Energie-Panel. slot: 0/1 = Spieler links, 'enemy' = Gegner rechts */
  panel(f, slot, rec) {
    const ctx = this.ctx, A = this.assets;
    const right = slot === 'enemy', coop = this.players.length > 1;
    const P = 96, BW = coop ? 330 : 400;
    const px = right ? 1600 - 24 - P : 24 + (slot || 0) * (P + BW + 60);
    ctx.fillStyle = '#0a0610'; ctx.fillRect(px - 4, 14, P + 8, P + 8);
    ctx.fillStyle = right ? '#591a26' : (slot === 1 ? '#2e1a55' : '#1a3366'); ctx.fillRect(px, 18, P, P);
    const pn = 'Portrait_' + f.sprite;
    if (A.has(pn)) { const [fw] = A.frameSize(pn); A.draw(ctx, pn, px, 18, 0, 0, false, P / fw); }
    const bx = right ? px - 16 - BW : px + P + 16;
    const label = !right && coop ? `${slot + 1}P ${f.displayName}` : f.displayName;
    this.text(label, right ? bx + BW : bx, 16, 26, '#fff', right ? 'right' : 'left');
    this.bar(bx, 52, BW, 22, f.health / f.maxHealth, rec / f.maxHealth, right ? '#f23333' : '#ffc71a', right);
    if (!right) {
      this.text('x' + Math.max(0, f.lives - 1), px + 6, 120, 26, '#ffc71a');
      this.text(String(f.score).padStart(7, '0'), bx, 84, 26, '#fff');
      if (f.weapon) {
        const w = WEAPONS[f.weapon];
        this.text(`${w.name} ${f.weaponDur > 50 ? '' : '×' + f.weaponDur}`, bx + 150, 88, 20, '#9fe8ff');
      }
      if (f.out) { ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(px - 4, 14, P + BW + 30, P + 8); this.text('K.O.', bx + BW / 2, 44, 40, '#ff4080', 'center'); }
    }
  }
  /** Grosse Boss-Leiste unten (wie in SoR4) */
  bossBar(b) {
    const ctx = this.ctx, BW = 900, x = 800 - BW / 2, y = 830;
    this.text(b.displayName, x, y - 40, 30, '#ffc71a');
    if (b.enraged) this.text('WUT', x + BW, y - 38, 26, '#ff4060', 'right');
    this.bar(x, y, BW, 24, b.health / b.maxHealth, 0, '#f23333', false);
    ctx.fillStyle = 'rgba(10,6,16,0.7)';
    for (let i = 1; i < 10; i++) ctx.fillRect(x + (BW * i) / 10 - 1, y, 2, 24);
  }
  /** Boss-Auftritt: Name, Spruch und Tipps in einem schraegen Band */
  drawBossIntro(bi) {
    const ctx = this.ctx, A = this.assets, e = bi.e, p = e.profile;
    const t = bi.t, inK = clamp(t / 0.35, 0, 1), outK = clamp((3.2 - t) / 0.4, 0, 1), k = Math.min(inK, outK);
    ctx.save();
    ctx.globalAlpha = k;
    ctx.translate((1 - inK) * -400, 0);
    ctx.fillStyle = 'rgba(8,4,16,0.82)';
    ctx.beginPath(); ctx.moveTo(0, 300); ctx.lineTo(1600, 250); ctx.lineTo(1600, 560); ctx.lineTo(0, 610); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ff3c96'; ctx.fillRect(0, 296, 1600, 6);
    const pn = 'Portrait_' + e.sprite;
    if (A.has(pn)) { const [fw] = A.frameSize(pn); A.draw(ctx, pn, 170, 290, 0, 0, false, 300 / fw); }
    this.text('ENDGEGNER', 520, 300, 28, '#ff60c0');
    this.text(p.name, 520, 340, 72, '#ffc71a');
    if (p.title) this.text(`„${p.title}“`, 520, 430, 34, '#fff');
    (p.tips || []).forEach((tip, i) => this.text('▸ ' + tip, 520, 485 + i * 30, 22, '#cfc6e0'));
    ctx.restore();
  }
  drawHUD() {
    const ctx = this.ctx, A = this.assets;
    const blink = (performance.now() % 800) < 500;
    if (this.flow === 'title') {
      ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(0, 0, 1600, 900);
      if (A.has('UI_Logo') && this.menu.top && this.menu.top.id === 'main') A.draw(ctx, 'UI_Logo', 800, 90, 550, 0);
      return;
    }
    this.players.forEach((pl, i) => this.panel(pl, i, pl.recoverable));
    const e = this.lastHit;
    if (e && !e.dead && !e.boss && this.lastHitT > 0) this.panel(e, 'enemy', 0);
    const boss = this.enemies().find((b) => b.boss && b.alive && !b.entering);
    if (boss) this.bossBar(boss);
    if (this.bossIntro) this.drawBossIntro(this.bossIntro);
    if (this.train && this.train.phase === 'warn' && blink) this.text('ZURÜCKBLEIBEN, BITTE!', 800, 180, 48, '#ffd24a', 'center');
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
      if (this.players.length > 1) this.text(this.players.map((p, i) => `${i + 1}P ${p.score}`).join('   ·   '), 800, 460, 26, '#cfc6e0', 'center');
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
      if (this.players.length > 1) this.text(this.players.map((p, i) => `${i + 1}P ${p.score}`).join('   ·   '), 800, 490, 26, '#cfc6e0', 'center');
      if (this.flowTime > 1.5 && blink) this.text('ENTER: TITEL', 800, 540, 30, '#fff', 'center');
    }
  }
}

const ENEMY_FROM_RIGHT = new Set(['Rolf', 'Sven', 'Harald', 'Klaus', 'Tuer']);
