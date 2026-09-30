// Spielobjekte: Portierung von ABrawlerEntity/Fighter/Player/Enemy/Prop/Pickup/Effect + Waffen.
import { ANIM, ENEMIES, PLAYER_ATTACKS, W, WEAPONS, atk, weaponAttack } from './data.js';

const rand = (a, b) => a + Math.random() * (b - a);
const sign = (v) => (v > 0 ? 1 : v < 0 ? -1 : 0);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// ---------------------------------------------------------------------------
// Basis
// ---------------------------------------------------------------------------
export class Entity {
  constructor(game) {
    this.game = game;
    this.x = 0; this.depth = 0; this.h = 0;
    this.vx = 0; this.vd = 0; this.vz = 0;
    this.facing = 1;
    this.hitstop = 0;
    this.dead = false;
    this.folder = ''; this.prefix = '';
    this.frames = []; this.animKey = ''; this.animTime = 0; this.fps = 10; this.loop = true; this.frame = 0; this.animDone = false;
    this.shadow = 1; this.blink = 0; this.shake = 0;
    this.front = false; // immer vorne (Effekte)
  }
  play(folder, prefix, fps, loop, restart = false) {
    const key = folder + '/' + prefix;
    this.fps = fps; this.loop = loop;
    if (key === this.animKey && !restart) return;
    this.animKey = key; this.animTime = 0; this.frame = 0; this.animDone = false;
    this.folder = folder;
    this.frames = this.game.assets.frames(folder, prefix);
  }
  setFrame(i) {
    if (!this.frames.length) return;
    this.frame = clamp(i, 0, this.frames.length - 1);
    this.animTime = this.frame / Math.max(this.fps, 0.01);
  }
  get frameName() { return this.frames[this.frame]; }
  updateAnim(dt) {
    const n = this.frames.length;
    if (!n || this.fps <= 0) return;
    this.animTime += dt;
    let f = Math.floor(this.animTime * this.fps);
    if (this.loop) f %= n;
    else if (f >= n) { f = n - 1; this.animDone = true; }
    this.frame = f;
  }
  update(dt) {
    if (this.hitstop > 0) { this.hitstop -= dt; this.shake = this.hitstop; return; }
    this.shake = 0;
    this.tick(dt);
    if (!this.dead) this.updateAnim(dt);
  }
  tick() {}
  isHittable() { return false; }
  receiveHit() { return false; }
  get hurtHalfWidth() { return W.BodyHalfWidth; }
  get hurtHeight() { return W.BodyHeight; }
  destroy() { this.dead = true; }
}

// ---------------------------------------------------------------------------
// Kaempfer
// ---------------------------------------------------------------------------
export class Fighter extends Entity {
  constructor(game) {
    super(game);
    this.team = 'enemy'; this.sprite = ''; this.displayName = '';
    this.maxHealth = 100; this.health = 100; this.walkSpeed = 250; this.depthSpeed = 160;
    this.grabbable = true; this.armor = 0; this.armorHits = 0; this.armorReset = 0;
    this.state = 'idle'; this.stateTime = 0; this.hurtDur = 0.3; this.invuln = 0; this.downDur = 0.9; this.getupInvuln = 0.6;
    this.attack = null; this.connected = false; this.lastActive = -1; this.hitList = new Set();
    this.grabPartner = null; this.grabTimer = 0;
    this.thrown = false; this.bounced = false; this.thrower = null; this.thrownHits = new Set();
    this.clampView = true;
    this.weapon = null; this.weaponDur = 0;
  }
  get alive() { return this.state !== 'dead' && this.health > 0; }
  get downed() { return ['down', 'falling', 'getup', 'dead'].includes(this.state); }
  get free() { return this.state === 'idle' || this.state === 'walk'; }
  get invulnerable() {
    return this.invuln > 0 || (this.state === 'attack' && this.attack && this.attack.invuln && this.frame <= this.attack.end);
  }
  anim(name, restart = false, fpsOverride = 0) {
    const [fps, loop] = ANIM[name] || [10, false];
    this.play(this.sprite, this.sprite + '_' + name, fpsOverride || fps, loop, restart);
  }
  enter(s) {
    const old = this.state;
    this.state = s; this.stateTime = 0;
    switch (s) {
      case 'idle': this.vx = this.vd = 0; this.anim('idle'); break;
      case 'walk': this.anim('walk'); break;
      case 'hurt': this.anim('hurt', true); break;
      case 'grabbed': this.vx = this.vd = 0; this.anim('grabbed', true); break;
      case 'grabbing': this.vx = this.vd = 0; this.grabTimer = 0; this.anim('grab', old !== 'attack'); break;
      case 'falling': this.anim('fall', true); break;
      case 'down': this.vx = this.vd = this.vz = 0; this.h = 0; this.anim('down', true); break;
      case 'getup': this.anim('getup', true); break;
      case 'pickup': this.vx = this.vd = 0; this.anim('pickup', true); break;
      case 'dead': this.vx = this.vd = this.vz = 0; this.anim('down'); break;
      case 'victory': this.vx = this.vd = 0; this.anim('victory', true); break;
      case 'jump': this.anim('jump', true); break;
    }
  }
  tick(dt) {
    this.stateTime += dt;
    this.invuln = Math.max(0, this.invuln - dt);
    this.blink = this.state === 'dead' ? this.stateTime + 0.07 : (this.invuln > 0 && this.team === 'player' ? this.invuln : 0);
    if (this.armorHits > 0) { this.armorReset -= dt; if (this.armorReset <= 0) this.armorHits = 0; }

    switch (this.state) {
      case 'idle': case 'walk':
        this.control(dt);
        if (this.state === 'idle' || this.state === 'walk') this.move(dt);
        break;
      case 'jump':
        this.control(dt);
        if (this.state === 'jump') { this.setFrame(this.vz > 0 ? 0 : 1); this.air(dt); }
        break;
      case 'attack': this.tickAttack(dt); break;
      case 'hurt':
        this.vx += (0 - this.vx) * Math.min(1, dt * 10);
        this.move(dt);
        if (this.stateTime >= this.hurtDur) this.enter('idle');
        break;
      case 'grabbing':
        this.grabTimer += dt;
        this.holdPartner();
        this.control(dt);
        if (this.state === 'grabbing' && (this.grabTimer > 2.2 || !this.grabPartner || this.grabPartner.state !== 'grabbed')) {
          this.releaseGrab(); this.enter('idle');
        }
        break;
      case 'grabbed':
        if (!this.grabPartner || (this.grabPartner.state !== 'grabbing' && this.grabPartner.state !== 'attack')) this.releasedFromGrab();
        break;
      case 'falling':
        this.setFrame(this.vz > 0 ? 0 : 1);
        this.air(dt);
        if (this.thrown) this.thrownCollisions();
        break;
      case 'down':
        if (this.stateTime >= this.downDur) {
          if (this.health <= 0) { this.enter('dead'); this.onDied(); } else this.enter('getup');
        }
        break;
      case 'getup':
        if (this.animDone && this.stateTime > 0.3) { this.invuln = Math.max(this.invuln, this.getupInvuln); this.enter('idle'); }
        break;
      case 'pickup':
        if (this.stateTime > 0.25) this.enter('idle');
        break;
    }
    this.clampPos();
  }
  control() {}
  move(dt) { this.x += this.vx * dt; this.depth += this.vd * dt; }
  clampPos() {
    this.depth = clamp(this.depth, W.DepthMin, W.DepthMax);
    if (this.clampView) this.x = clamp(this.x, this.game.viewMin + 40, this.game.viewMax - 40);
    this.x = clamp(this.x, -400, W.StageEndX + 400);
  }
  air(dt) {
    this.vz -= W.Gravity * dt;
    this.h += this.vz * dt; this.x += this.vx * dt; this.depth += this.vd * dt;
    if (this.h <= 0 && this.vz <= 0) { this.h = 0; this.landed(); this.vz = 0; }
  }
  landed() {
    const g = this.game;
    if (this.state === 'falling') {
      if (!this.bounced && this.vz < -500) {
        this.bounced = true; this.vz = 280; this.vx *= 0.45; this.h = 0.1;
        g.effect('FX_Dust', this.x, this.depth, 0, this.facing, 14);
        g.sfx('SFX_Thud', 0.8); g.shake(4, 0.12);
        if (this.thrown) { this.thrown = false; this.health = Math.max(0, this.health - 12); }
        return;
      }
      this.thrown = false; this.bounced = false;
      this.enter('down');
      if (this.health <= 0) { this.downDur = 1.0; g.sfx('SFX_KO', 0.7, 0.2); }
      return;
    }
    if (this.state === 'attack' || this.state === 'jump') {
      if (this.state === 'attack') {
        this.state = 'idle';
        this.attackFinished();
        if (this.state !== 'idle') return;
      }
      this.vx = this.vd = 0;
      g.effect('FX_Dust', this.x, this.depth, 0, this.facing, 16, 0.6);
      this.enter('idle');
    }
  }

  // --- Angriffe --------------------------------------------------------------
  startAttack(a) {
    this.attack = a; this.connected = false; this.lastActive = -1; this.hitList = new Set();
    const prev = this.state;
    this.state = 'attack'; this.stateTime = 0;
    if (prev !== 'jump' && this.h <= 0) { this.vx = this.vd = 0; }
    const [fps] = ANIM[a.anim] || [10];
    this.play(this.sprite, this.sprite + '_' + a.anim, a.fps || fps, a.loop, true);
    if (a.cost > 0) this.health = Math.max(1, this.health - a.cost);
    if (a.whoosh) this.game.sfx('SFX_Whoosh', 0.45, 0.15);
  }
  tickAttack(dt) {
    const a = this.attack;
    const airborne = this.h > 0 || this.vz > 0;
    if (!airborne) {
      const active = this.frame >= a.start - 1 && this.frame <= a.end;
      this.vx = (active ? a.lunge : 0) * this.facing; this.vd = 0;
      this.move(dt);
    }
    this.attackFrame();
    this.processHits();
    if (airborne) { this.air(dt); return; }
    const done = a.loop ? this.stateTime >= a.dur : (this.animDone && this.stateTime > 0.05);
    if (done) {
      this.state = 'idle';
      this.attackFinished();
      if (this.state === 'idle') this.enter('idle');
    }
  }
  attackFrame() {}
  processHits() {
    const a = this.attack;
    const active = a.loop ? true : (this.frame >= a.start && this.frame <= a.end);
    if (!active) return;
    if (a.multi && this.frame !== this.lastActive) this.hitList = new Set();
    this.lastActive = this.frame;
    for (const t of this.game.entities) {
      if (t === this || t.dead || !t.isHittable(this.team) || this.hitList.has(t)) continue;
      if (t instanceof Fighter && t.state === 'grabbed' && t.grabPartner !== this && this.team !== 'player') continue;
      if (!this.overlaps(t, a)) continue;
      let dir = sign(t.x - this.x); if (!dir) dir = this.facing;
      if (t.receiveHit(this, a, dir)) {
        this.hitList.add(t); this.connected = true; this.hitstop = Math.max(this.hitstop, a.stop);
        this.onAttackHit(t, a);
      }
    }
  }
  overlaps(t, a) {
    const hw = t.hurtHalfWidth;
    const fwd = (t.x - this.x) * this.facing;
    const front = fwd + hw >= a.rmin && fwd - hw <= a.rmax;
    const back = -fwd + hw >= a.rmin && -fwd - hw <= a.rmax;
    const horiz = a.both ? (front || back) : (a.behind ? back : front);
    if (!horiz || Math.abs(t.depth - this.depth) > a.depth) return false;
    const amin = this.h + a.hmin, amax = this.h + a.hmax;
    return !(amax < t.h || amin > t.h + t.hurtHeight);
  }
  onAttackHit() {}
  attackFinished() {}
  onHurt() {}
  onDied() {}

  // --- Treffer ------------------------------------------------------------------
  isHittable(team) {
    if (team === this.team || !this.alive || this.invulnerable) return false;
    if (['down', 'getup', 'dead'].includes(this.state)) return false;
    if (this.state === 'falling') return !this.thrown;
    return true;
  }
  get hurtHeight() { return this.state === 'falling' ? 90 : W.BodyHeight; }
  receiveHit(att, a, dir) {
    if (!att || !this.isHittable(att.team)) return false;
    const g = this.game;
    this.health = Math.max(0, this.health - a.dmg);
    const heavyFx = a.type !== 'light' || this.health <= 0;
    const fxH = clamp(att.h + (a.hmin + a.hmax) * 0.5 - this.h, 40, 170) + this.h;
    g.effect(heavyFx ? 'FX_HitBig' : 'FX_HitSpark', this.x - dir * 18, this.depth, fxH, dir, 22);
    g.sfx(heavyFx ? 'SFX_HitHeavy' : 'SFX_HitLight', heavyFx ? 1 : 0.8, 0.12);
    if (heavyFx) g.shake(6, 0.15);
    g.onDamage(att, this, a.dmg);
    this.hitstop = Math.max(this.hitstop, a.stop * 1.15);
    this.onHurt(att, a.dmg);
    const grabbedByAtt = this.state === 'grabbed' && this.grabPartner === att;
    if (this.state === 'grabbing' || (this.state === 'attack' && this.grabPartner)) this.releaseGrab();

    if (this.health <= 0) { this.knockdown(dir, Math.max(a.kb, 260), Math.max(a.launch, 620)); return true; }
    if (a.type === 'kd' || this.state === 'falling') {
      const launch = this.state === 'falling' ? Math.max(a.launch * 0.6, 420) : a.launch;
      this.knockdown(dir, Math.max(a.kb, 160), Math.max(launch, 380));
      return true;
    }
    if (grabbedByAtt) { this.anim('grabbed', true); return true; }
    if (this.armor > 0 && this.armorHits < this.armor && this.state !== 'hurt') {
      this.armorHits++; this.armorReset = 1.5; return true;
    }
    this.armorHits = 0;
    if (this.state === 'grabbed') this.releasedFromGrab();
    this.facing = -dir;
    this.hurtDur = a.type === 'heavy' ? 0.5 : 0.34;
    this.enter('hurt');
    this.vx = dir * a.kb; this.vd = 0;
    if (this.h > 0) this.knockdown(dir, 160, 300);
    return true;
  }
  knockdown(dir, speed, launch) {
    if (this.state === 'grabbing' || this.grabPartner) this.releaseGrab();
    this.grabPartner = null;
    this.dropWeapon();
    this.facing = -dir;
    this.vx = dir * speed; this.vd = 0; this.vz = launch; this.h = Math.max(this.h, 1);
    this.bounced = false; this.downDur = 0.9;
    this.enter('falling');
  }

  // --- Griffe -------------------------------------------------------------------
  startGrab(t) { this.grabPartner = t; t.grabbedBy(this); this.enter('grabbing'); this.holdPartner(); }
  releaseGrab() {
    const p = this.grabPartner; this.grabPartner = null;
    if (p && p.state === 'grabbed') p.releasedFromGrab();
  }
  grabbedBy(g) { this.grabPartner = g; this.facing = -g.facing; this.enter('grabbed'); }
  releasedFromGrab() {
    this.grabPartner = null;
    if (this.state === 'grabbed') { this.invuln = Math.max(this.invuln, 0.3); this.enter('idle'); }
  }
  holdPartner() {
    const p = this.grabPartner;
    if (p) { p.x = this.x + this.facing * 52; p.depth = this.depth - 0.5; p.h = 0; p.facing = -this.facing; }
  }
  getThrown(thrower, dir) {
    this.grabPartner = null; this.thrower = thrower; this.thrownHits = new Set();
    this.health = Math.max(0, this.health - 10);
    this.knockdown(dir, 520, 560);
    this.thrown = true;
    this.game.onDamage(thrower, this, 10);
  }
  thrownCollisions() {
    for (const o of this.game.fighters()) {
      if (o === this || o.team !== this.team || !o.alive || o.downed || this.thrownHits.has(o)) continue;
      if (Math.abs(o.x - this.x) < 60 && Math.abs(o.depth - this.depth) < 30 && this.h < 160) {
        this.thrownHits.add(o);
        const src = this.thrower || this;
        if (o.team !== src.team) o.receiveHit(src, atk({ dmg: 12, type: 'kd', kb: 300, launch: 500, hmin: 0, hmax: 150, stop: 0.08 }), sign(this.vx) || 1);
      }
    }
  }

  // --- Waffen -------------------------------------------------------------------
  takeWeapon(name, dur) {
    this.weapon = name; this.weaponDur = dur ?? WEAPONS[name].dur;
  }
  dropWeapon(pop = true) {
    if (!this.weapon) return;
    const item = new WeaponItem(this.game, this.weapon, this.weaponDur);
    item.x = this.x; item.depth = this.depth; item.h = Math.max(this.h, 40);
    if (pop) { item.vz = 420; item.vx = -this.facing * 120; }
    this.game.add(item);
    this.weapon = null;
  }
  useWeaponHit() {
    if (!this.weapon) return;
    this.weaponDur -= 1;
    if (this.weaponDur <= 0) {
      this.game.effect('FX_HitSpark', this.x + this.facing * 80, this.depth, 110, this.facing, 20);
      this.game.sfx('SFX_Break', 0.6, 0.1);
      this.weapon = null;
    }
  }
  throwWeapon() {
    if (!this.weapon) return;
    const p = new Projectile(this.game, this.weapon, this, WEAPONS[this.weapon].throwDmg);
    p.x = this.x + this.facing * 50; p.depth = this.depth; p.h = 120; p.facing = this.facing; p.vx = this.facing * 900;
    p.durLeft = this.weaponDur;
    this.game.add(p);
    this.weapon = null;
    this.game.sfx('SFX_Whoosh', 0.8, 0.1);
  }
}

// ---------------------------------------------------------------------------
// Spieler
// ---------------------------------------------------------------------------
export class Player extends Fighter {
  constructor(game) {
    super(game);
    this.team = 'player'; this.sprite = 'Kai'; this.displayName = 'KAI';
    this.maxHealth = this.health = 120; this.walkSpeed = 280; this.depthSpeed = 180; this.getupInvuln = 1.2;
    this.move2 = { x: 0, y: 0 }; this.buf = { attack: 0, jump: 0, special: 0, back: 0 };
    this.comboStep = 0; this.inCombo = false; this.fromGrab = false; this.throwReleased = false; this.jumpAtkUsed = false;
    this.knees = 0; this.grabCd = 0; this.walkInto = 0; this.recoverable = 0;
    this.enter('idle');
  }
  press(k) { this.buf[k] = 0.18; }
  tick(dt) {
    for (const k in this.buf) this.buf[k] = Math.max(0, this.buf[k] - dt);
    this.grabCd = Math.max(0, this.grabCd - dt);
    const P = PLAYER_ATTACKS;
    if (this.state === 'attack' && this.h <= 0) {
      if (this.buf.special > 0 && this.connected && this.attack.anim !== 'special' && this.health > P.special.cost + 1) {
        this.buf.special = 0; this.startSpecial();
      } else if (this.inCombo && this.buf.attack > 0 && this.connected && this.comboStep < 3 &&
                 this.frame >= this.attack.cancel && this.frame > this.attack.end - 1 && this.stateTime > 0.08) {
        this.buf.attack = 0; this.startCombo(this.comboStep + 1);
      }
    }
    if (this.state === 'attack' && this.attack.anim === 'throw' && !this.throwReleased) {
      const p = this.grabPartner;
      if (p) {
        p.x = this.x + this.facing * (this.frame >= 1 ? 10 : 40);
        p.h = this.frame >= 1 ? 90 : 20;
        if (this.frame >= 2) {
          this.throwReleased = true; this.grabPartner = null;
          p.h = 60; p.x = this.x + this.facing * 30;
          p.getThrown(this, this.facing);
          this.game.sfx('SFX_Whoosh', 0.8, 0.1);
        }
      }
    }
    super.tick(dt);
  }
  attackFrame() {
    if (this.attack.anim === 'weapon_throw' && this.frame >= 1 && this.weapon) this.throwWeapon();
  }
  control(dt) {
    if (this.state === 'idle' || this.state === 'walk') this.ground(dt);
    else if (this.state === 'jump') {
      if (this.buf.attack > 0 && !this.jumpAtkUsed) {
        this.buf.attack = 0; this.jumpAtkUsed = true; this.inCombo = false; this.startAttack(PLAYER_ATTACKS.jumpKick);
      }
    } else if (this.state === 'grabbing') this.grabControl();
  }
  ground(dt) {
    const m = this.move2;
    if (this.buf.jump > 0) {
      this.buf.jump = 0; this.jumpAtkUsed = false;
      this.vz = 860; this.vx = m.x * this.walkSpeed * 1.05; this.vd = m.y * this.depthSpeed * 0.6;
      if (Math.abs(m.x) > 0.2) this.facing = sign(m.x);
      this.h = 0.1; this.enter('jump'); return;
    }
    if (this.buf.special > 0) {
      this.buf.special = 0;
      if (this.health > PLAYER_ATTACKS.special.cost + 1) { this.startSpecial(); return; }
    }
    if (this.buf.back > 0) {
      this.buf.back = 0; this.inCombo = false;
      if (this.weapon) { this.startAttack(atk({ anim: 'weapon_throw', start: 99, end: 99, dmg: 0, fps: 12, whoosh: false })); return; }
      this.startAttack(PLAYER_ATTACKS.back); return;
    }
    if (this.buf.attack > 0) {
      this.buf.attack = 0;
      if (this.tryPickup()) return;
      if (this.weapon) { this.inCombo = false; this.startAttack(weaponAttack(this.weapon)); return; }
      this.startCombo(0); return;
    }
    this.vx = m.x * this.walkSpeed; this.vd = m.y * this.depthSpeed;
    if (Math.abs(m.x) > 0.2) this.facing = sign(m.x);
    const moving = m.x * m.x + m.y * m.y > 0.04;
    if (moving && this.state !== 'walk') { this.enter('walk'); this.vx = m.x * this.walkSpeed; this.vd = m.y * this.depthSpeed; }
    else if (!moving && this.state !== 'idle') this.enter('idle');
    if (moving && Math.abs(m.x) > 0.5 && !this.weapon) {
      this.walkInto += dt;
      if (this.walkInto > 0.12 && this.tryGrab()) this.walkInto = 0;
    } else this.walkInto = 0;
  }
  grabControl() {
    const p = this.grabPartner; if (!p) return;
    if (this.buf.jump > 0) { this.buf.jump = 0; this.releaseGrab(); this.grabCd = 0.6; this.enter('idle'); return; }
    if (this.buf.attack > 0) {
      this.buf.attack = 0; this.inCombo = false; this.fromGrab = true;
      const away = Math.abs(this.move2.x) > 0.5 && sign(this.move2.x) !== this.facing;
      if (away) {
        this.facing = -this.facing; p.x = this.x + this.facing * 40; p.facing = -this.facing;
        this.throwReleased = false; this.startAttack(PLAYER_ATTACKS.throw);
      } else {
        this.knees++; this.startAttack(this.knees >= 3 ? PLAYER_ATTACKS.kneeFinal : PLAYER_ATTACKS.knee);
      }
    }
  }
  startCombo(step) {
    this.comboStep = step; this.inCombo = true; this.fromGrab = false;
    if (Math.abs(this.move2.x) > 0.2) this.facing = sign(this.move2.x);
    this.startAttack(PLAYER_ATTACKS.combo[step]);
  }
  startSpecial() {
    this.inCombo = false; this.fromGrab = false; this.releaseGrab();
    this.recoverable = Math.min(this.recoverable + PLAYER_ATTACKS.special.cost, this.maxHealth);
    this.startAttack(PLAYER_ATTACKS.special);
    this.game.sfx('SFX_Special', 0.9, 0.05);
    this.game.effect('FX_SpecialRing', this.x, this.depth, 20, this.facing, 12);
  }
  tryPickup() {
    let best = null, bd = 1e9;
    for (const e of this.game.entities) {
      if (!(e instanceof Pickup || e instanceof WeaponItem) || !e.canCollect()) continue;
      const d = Math.abs(e.x - this.x);
      if (d < 64 && Math.abs(e.depth - this.depth) < 28 && d < bd) { best = e; bd = d; }
    }
    if (!best) return false;
    if (best instanceof WeaponItem) {
      if (this.weapon) this.dropWeapon(false);
      best.collect(this);
    } else best.collect(this);
    this.enter('pickup');
    return true;
  }
  tryGrab() {
    if (this.grabCd > 0) return false;
    for (const e of this.game.fighters()) {
      if (e.team !== 'enemy' || !e.grabbable || !e.alive) continue;
      if (!['idle', 'walk', 'hurt'].includes(e.state)) continue;
      const fwd = (e.x - this.x) * this.facing;
      if (fwd > 15 && fwd < 66 && Math.abs(e.depth - this.depth) < 16 && e.h <= 0) { this.knees = 0; this.startGrab(e); return true; }
    }
    return false;
  }
  onAttackHit(t, a) {
    if (this.recoverable > 0 && t instanceof Fighter) {
      const r = Math.min(this.recoverable, a.dmg * 0.6);
      this.recoverable -= r; this.health = Math.min(this.maxHealth, this.health + r);
    }
    if (a.weapon && t instanceof Fighter) this.useWeaponHit();
  }
  attackFinished() {
    if (this.fromGrab) {
      this.fromGrab = false;
      const p = this.grabPartner;
      if (p && p.state === 'grabbed' && this.attack.anim !== 'throw') { this.state = 'grabbing'; this.stateTime = 0; this.anim('grab', true); return; }
      this.grabPartner = null; this.grabCd = 0.5;
    }
    if (this.attack.anim !== 'attack1' || !this.connected) this.comboStep = 0;
  }
  onHurt() { this.recoverable = 0; this.comboStep = 0; this.inCombo = false; this.fromGrab = false; }
  landed() { this.jumpAtkUsed = false; super.landed(); }
  onDied() { this.game.onPlayerDied(); }
  celebrate() { this.releaseGrab(); this.enter('victory'); }
  dropIn() {
    this.health = this.maxHealth; this.recoverable = 0; this.h = 600; this.vz = -200; this.vx = 0; this.jumpAtkUsed = true;
    this.invuln = 2.5; this.weapon = null; this.enter('jump');
    for (const e of this.game.fighters()) {
      if (e.team === 'enemy' && e.alive && !e.downed && Math.abs(e.x - this.x) < 350) e.knockdown(sign(e.x - this.x + 0.01), 300, 450);
    }
  }
}

// ---------------------------------------------------------------------------
// Gegner
// ---------------------------------------------------------------------------
export class Enemy extends Fighter {
  constructor(game, type) {
    super(game);
    const p = ENEMIES[type];
    this.type = type; this.profile = p;
    this.sprite = p.sprite || type; this.displayName = p.name; this.style = p.style;
    this.maxHealth = this.health = p.hp; this.walkSpeed = p.speed; this.depthSpeed = p.speed * 0.65;
    this.grabbable = p.grab !== false; this.armor = p.armor || 0; this.cdBase = p.cd || 1.4;
    this.boss = !!p.boss; this.shadow = p.shadow || 1;
    this.getupInvuln = 0.4;
    this.entering = false; this.think = 0; this.cd = rand(0.4, 1.4); this.side = 1; this.dOff = 0; this.wait = rand(200, 300);
    this.token = false; this.enraged = false; this.summoned = 0; this.throwCd = rand(2, 4);
    if (p.weapon) this.takeWeapon(p.weapon, 999);
    this.enter('idle');
  }
  setEntering(v) { this.entering = v; this.clampView = !v; }
  melee(strong) {
    const s = this.style, dmgK = this.enraged ? 1.3 : 1;
    if (this.weapon) {
      const a = weaponAttack(this.weapon);
      a.dmg = Math.round(a.dmg * (this.boss ? 1.2 : 0.8) * dmgK); a.fps = Math.max(8, a.fps - 3);
      return a;
    }
    if (s === 'heavy') return atk({ anim: 'attack1', start: 2, end: 2, dmg: (this.boss ? 16 : 13) * dmgK, rmax: 118, type: 'kd', kb: 330, launch: 500, stop: 0.12, fps: this.boss ? (this.enraged ? 11 : 9) : 7.5, depth: 30 });
    if (s === 'kicker') {
      if (strong) return atk({ anim: 'attack2', start: 1, end: 2, dmg: 10, rmax: 130, type: 'kd', kb: 300, launch: 460, lunge: 260, fps: 11, stop: 0.1 });
      return atk({ anim: 'attack1', start: 1, end: 1, dmg: 6, rmax: 118, kb: 60, fps: 11, hmin: 20 });
    }
    if (s === 'suit') {
      if (strong) return atk({ anim: 'attack4', start: 1, end: 2, dmg: 14 * dmgK, rmax: 138, type: 'kd', kb: 380, launch: 540, lunge: 60, fps: 12, stop: 0.12 });
      return atk({ anim: 'attack3', start: 1, end: 2, dmg: 9 * dmgK, rmax: 95, type: 'heavy', kb: 70, fps: 13 });
    }
    if (s === 'punk' && strong) return atk({ anim: 'attack2', start: 2, end: 2, dmg: 9, rmax: 104, type: 'kd', kb: 260, launch: 420, stop: 0.1, fps: 9, lunge: 80 });
    return atk({ anim: 'attack1', dmg: 5, rmax: 92, kb: 40, fps: 9 });
  }
  rush() {
    if (this.style === 'skater') return atk({ anim: 'attack2', start: 1, end: 2, dmg: 9, rmax: 110, hmin: 0, hmax: 90, type: 'kd', kb: 280, launch: 380, lunge: 640, fps: 7 });
    if (this.style === 'kicker') return atk({ anim: 'attack2', start: 1, end: 2, dmg: 11, rmax: 130, type: 'kd', kb: 320, launch: 480, lunge: 520, fps: 9 });
    if (this.style === 'suit') return atk({ anim: 'jump_kick', start: 1, end: 1, dmg: 14, rmax: 120, hmin: -40, hmax: 150, type: 'kd', kb: 340, launch: 480, stop: 0.1, jump: true });
    return atk({ anim: 'attack2', start: 0, end: 3, loop: true, dur: this.boss ? 1.3 : 1.0, dmg: this.boss ? 18 : 14, rmax: 80, type: 'kd', kb: 420, launch: 540, lunge: this.boss ? (this.enraged ? 700 : 600) : 520, fps: 12, depth: 32, stop: 0.12 });
  }
  begin(a) {
    this.startAttack(a);
    if (a.jump) { this.vz = 780; this.h = 0.1; this.vx = this.facing * 520; }
  }
  tick(dt) {
    this.cd -= dt; this.throwCd -= dt;
    super.tick(dt);
    if (this.state === 'dead' && this.stateTime > 1.2) this.destroy();
  }
  attackFrame() {
    if (this.attack.anim === 'weapon_throw' && this.frame >= 1 && this.weapon) this.throwWeapon();
  }
  control(dt) {
    const g = this.game, pl = g.player;
    const walk = (vx, vd) => {
      this.vx = vx; this.vd = vd;
      const moving = Math.abs(vx) > 5 || Math.abs(vd) > 5;
      if (moving && this.state !== 'walk') { this.enter('walk'); this.vx = vx; this.vd = vd; }
      else if (!moving && this.state !== 'idle') this.enter('idle');
    };
    if (this.entering) {
      const inside = this.x > g.viewMin + 60 && this.x < g.viewMax - 60;
      if (inside) this.setEntering(false);
      else { this.facing = sign(g.camX - this.x) || 1; walk(this.facing * this.walkSpeed, 0); return; }
    }
    if (!pl || !pl.alive || pl.state === 'victory') { if (this.token) { g.releaseToken(this); this.token = false; } walk(0, 0); return; }
    const dx = pl.x - this.x, dd = pl.depth - this.depth;
    if (Math.abs(dx) > 8) this.facing = sign(dx);
    if (!this.enraged && this.boss && this.health < this.maxHealth * 0.5) {
      this.enraged = true; this.walkSpeed *= 1.3; this.depthSpeed *= 1.3; this.cdBase *= 0.7;
    }
    // Boss ruft Verstaerkung
    if (this.profile.summon && this.summoned < 2 && this.health < this.maxHealth * (this.summoned === 0 ? 0.66 : 0.33)) {
      this.summoned++;
      g.sfx('SFX_Go', 0.6);
      for (const t of this.profile.summon) g.spawnEnemy(t, this.summoned % 2 ? g.viewMin - 80 : g.viewMax + 80, rand(30, 210));
    }
    this.think -= dt;
    if (this.think <= 0) {
      this.think = rand(0.35, 0.9);
      this.side = this.x < pl.x ? -1 : 1;
      if (Math.random() < 0.12) this.side = -this.side;
      this.dOff = rand(-1, 1);
    }
    if (this.cd <= 0) this.token = g.requestToken(this);
    const attackable = !pl.downed && pl.state !== 'grabbed';
    const ready = this.token && this.cd <= 0 && attackable;
    const adx = Math.abs(dx), add = Math.abs(dd);

    if (ready && add < 12) {
      if (this.weapon === 'Knife' && !this.boss && adx > 250 && adx < 520 && this.throwCd <= 0 && Math.random() < 1.5 * dt) {
        this.throwCd = 6; this.begin(atk({ anim: 'weapon_throw', start: 99, end: 99, dmg: 0, fps: 9, whoosh: false })); return;
      }
      const rushChance = { skater: 2.5, kicker: 1.4, heavy: this.boss ? 2.5 : 1.2, suit: 1.6 }[this.style] || 0;
      const [rmin, rmax] = { skater: [170, 360], kicker: [180, 320], heavy: [220, 560], suit: [200, 380] }[this.style] || [9999, 0];
      if (rushChance && adx > rmin && adx < rmax && Math.random() < rushChance * dt) { this.begin(this.rush()); return; }
    }
    const meleeRange = this.weapon ? WEAPONS[this.weapon].reach * 0.8 : ({ heavy: 105, kicker: 105, suit: 100 }[this.style] || 82);
    if (ready && adx < meleeRange && adx > 24 && add < 12) {
      const strong = (this.style === 'punk' && Math.random() < 0.35) || (this.style === 'kicker' && Math.random() < 0.3) || (this.style === 'suit' && Math.random() < 0.35);
      this.begin(this.melee(strong)); return;
    }
    let tx, td;
    if (ready) { tx = pl.x + this.side * meleeRange * 0.75; td = pl.depth; }
    else { tx = pl.x + this.side * this.wait; td = pl.depth + this.dOff * 60; }
    td = clamp(td, W.DepthMin, W.DepthMax);
    let mx = tx - this.x, md = td - this.depth;
    for (const o of g.fighters()) {
      if (o === this || o.team !== 'enemy' || !o.alive) continue;
      const ox = this.x - o.x, od = this.depth - o.depth;
      if (Math.abs(ox) < 60 && Math.abs(od) < 24) { md += (od >= 0 ? 1 : -1) * 40; mx += (ox >= 0 ? 1 : -1) * 30; }
    }
    const vx = Math.abs(mx) > 12 ? clamp(mx * 4, -this.walkSpeed, this.walkSpeed) : 0;
    const vd = Math.abs(md) > 6 ? clamp(md * 4, -this.depthSpeed, this.depthSpeed) : 0;
    walk(vx, vd);
    if (Math.abs(dx) > 8) this.facing = sign(dx);
  }
  attackFinished() {
    this.cd = this.cdBase * rand(0.8, 1.35);
    if (this.token) { this.game.releaseToken(this); this.token = false; }
  }
  onHurt() {
    this.cd = Math.max(this.cd, 0.5); this.entering = false; this.clampView = true;
    if (this.token) { this.game.releaseToken(this); this.token = false; }
  }
  onDied() {
    if (this.token) { this.game.releaseToken(this); this.token = false; }
    this.game.onEnemyKilled(this);
  }
  knockdown(dir, speed, launch) {
    // Gegner-Waffen haben begrenzte Haltbarkeit, sobald sie fallen gelassen werden
    if (this.weapon && this.weaponDur > 50) this.weaponDur = WEAPONS[this.weapon].dur;
    super.knockdown(dir, speed, launch);
  }
}

// ---------------------------------------------------------------------------
// Gegenstaende
// ---------------------------------------------------------------------------
export class Prop extends Entity {
  constructor(game, type, drop) {
    super(game);
    this.type = type; this.drop = drop; this.hits = 2; this.broken = false; this.brokenTime = 0; this.shadow = 0.95;
    this.play('Props', 'Prop_' + type, 0, false, true); this.setFrame(0);
    this.foot = 'bottom';
  }
  isHittable(team) { return !this.broken && team === 'player'; }
  get hurtHalfWidth() { return 38; }
  get hurtHeight() { return 120; }
  receiveHit(att, a, dir) {
    if (this.broken) return false;
    const g = this.game;
    this.hits--; this.hitstop = 0.06;
    g.effect('FX_HitSpark', this.x - dir * 20, this.depth, 70, dir, 22);
    if (this.hits > 0 && a.type === 'light') { g.sfx('SFX_HitLight', 0.7); return true; }
    this.broken = true; this.setFrame(1);
    g.sfx('SFX_Break', 0.9); g.score += 50; g.effect('FX_Dust', this.x, this.depth, 0, dir, 14);
    if (this.drop) {
      const it = this.drop in WEAPONS ? new WeaponItem(g, this.drop) : new Pickup(g, this.drop);
      it.x = this.x; it.depth = this.depth - 2; it.h = 1; it.vz = 520; it.vx = dir * 110;
      g.add(it);
    }
    return true;
  }
  tick(dt) {
    if (this.broken) {
      this.brokenTime += dt; this.blink = this.brokenTime > 1.2 ? this.brokenTime : 0;
      if (this.brokenTime > 2.2) this.destroy();
    }
  }
}

class Item extends Entity {
  constructor(game) { super(game); this.collected = false; this.shadow = 0.5; this.foot = 'bottom'; }
  canCollect() { return !this.collected && this.h <= 0; }
  tick(dt) {
    if (this.h > 0 || this.vz > 0) {
      this.vz -= W.Gravity * dt; this.h += this.vz * dt; this.x += this.vx * dt;
      if (this.h <= 0) { this.h = 0; this.vz = 0; this.vx = 0; }
    }
  }
}

export class Pickup extends Item {
  constructor(game, type) {
    super(game); this.type = type;
    this.frames = ['Pickup_' + type]; this.folder = 'Props'; this.fps = 0;
  }
  collect(pl) {
    if (this.collected) return;
    this.collected = true;
    const g = this.game;
    if (this.type === 'Doener') { pl.health = pl.maxHealth; g.score += 200; }
    else if (this.type === 'Currywurst') { pl.health = Math.min(pl.maxHealth, pl.health + 45); g.score += 100; }
    else if (this.type === 'Money') g.score += 1000;
    g.sfx('SFX_Pickup', 0.9, 0);
    this.destroy();
  }
}

export class WeaponItem extends Item {
  constructor(game, type, dur) {
    super(game); this.type = type; this.dur = dur ?? WEAPONS[type].dur; this.life = 0;
    this.frames = ['Weapon_' + type]; this.folder = 'Weapons'; this.fps = 0; this.shadow = 0.6;
  }
  tick(dt) {
    super.tick(dt);
    this.life += dt;
    if (this.life > 18) { this.blink = this.life; if (this.life > 20) this.destroy(); }
  }
  collect(f) {
    if (this.collected) return;
    this.collected = true; f.takeWeapon(this.type, this.dur);
    this.game.sfx('SFX_Pickup', 0.6, 0.1); this.destroy();
  }
}

export class Projectile extends Entity {
  constructor(game, type, owner, dmg) {
    super(game); this.type = type; this.owner = owner; this.dmg = dmg; this.team = owner.team;
    this.frames = ['Weapon_' + type]; this.folder = 'Weapons'; this.fps = 0; this.shadow = 0.5; this.spin = 0; this.travel = 0;
  }
  tick(dt) {
    this.x += this.vx * dt; this.travel += Math.abs(this.vx * dt);
    this.spin += dt * (this.type === 'Knife' ? 0 : 18);
    const a = atk({ dmg: this.dmg, type: 'kd', kb: 300, launch: 420, rmin: -40, rmax: 40, hmin: -20, hmax: 60, stop: 0.08, depth: 24 });
    for (const t of this.game.entities) {
      if (t === this || t === this.owner || t.dead || !t.isHittable(this.team)) continue;
      const fake = { x: this.x, depth: this.depth, h: this.h, facing: this.facing };
      if (!Fighter.prototype.overlaps.call(fake, t, a)) continue;
      if (t.receiveHit(this.owner, a, this.facing)) { this.land(true); return; }
    }
    if (this.travel > 900 || this.x < this.game.viewMin - 100 || this.x > this.game.viewMax + 100) this.land(false);
  }
  land(hit) {
    this.destroy();
    if (this.type === 'Bottle') {
      this.game.effect('FX_HitSpark', this.x, this.depth, this.h, this.facing, 22);
      this.game.sfx('SFX_Break', 0.8, 0.1);
      return;
    }
    if (this.durLeft !== undefined && this.durLeft <= 1) return;
    const it = new WeaponItem(this.game, this.type, Math.max(1, (this.durLeft ?? WEAPONS[this.type].dur) - 1));
    it.x = this.x; it.depth = this.depth; it.h = this.h; it.vz = hit ? 300 : 0; it.vx = hit ? -this.facing * 120 : this.facing * 60;
    this.game.add(it);
  }
}

export class Effect extends Entity {
  constructor(game, prefix, fps, scale, front) {
    super(game);
    this.shadow = 0; this.scale = scale; this.front = front; this.foot = prefix.includes('Dust') ? 'dust' : 'center';
    this.play('Effects', prefix, fps, false, true);
    if (!this.frames.length) this.dead = true;
  }
  tick() { if (this.animDone) this.destroy(); }
}
