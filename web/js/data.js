// Spieldaten: Figuren, Angriffe, Gegner, Waffen und Stages.

export const W = {
  DepthMin: 0, DepthMax: 240, FloorTopZ: 300, Gravity: 2600,
  ScreenW: 1600, ScreenH: 900, CameraZ: 340, StageEndX: 8192,
  FrameSize: 320, FootX: 160, FootY: 312, BodyHalfWidth: 26, BodyHeight: 170,
};

// Animationen: [FPS, Loop]
export const ANIM = {
  idle: [7, true], walk: [11, true], hurt: [10, false], grabbed: [5, true], fall: [8, false], down: [1, false],
  getup: [7, false], attack1: [15, false], attack2: [14, false], attack3: [14, false], attack4: [13, false],
  jump: [0, false], jump_kick: [14, false], special: [16, false], back_attack: [14, false], grab: [1, true],
  grab_knee: [14, false], throw: [11, false], pickup: [1, false], victory: [4, true],
  weapon_swing: [13, false], weapon_throw: [12, false],
  whistle: [4, false], point: [3, false], guard: [3, true], shove: [7, false],
};

// Angriffs-Vorlage (entspricht FBrawlerAttack)
export function atk(o) {
  return Object.assign({
    anim: 'attack1', start: 1, end: 1, dmg: 5, rmin: 0, rmax: 90, depth: 26, hmin: 40, hmax: 190,
    type: 'light', kb: 80, launch: 0, stop: 0.07, lunge: 0, behind: false, both: false, multi: false,
    fps: 0, cancel: 2, invuln: false, cost: 0, loop: false, dur: 0, whoosh: true,
  }, o);
}

export const PLAYER_ATTACKS = {
  combo: [
    atk({ anim: 'attack1', dmg: 4, rmax: 98, kb: 30, cancel: 1, stop: 0.06 }),
    atk({ anim: 'attack2', dmg: 5, rmax: 104, kb: 40, lunge: 90, cancel: 1 }),
    atk({ anim: 'attack3', start: 1, end: 2, dmg: 7, rmax: 92, type: 'heavy', kb: 60, stop: 0.09 }),
    atk({ anim: 'attack4', start: 1, end: 2, dmg: 11, rmax: 138, type: 'kd', kb: 360, launch: 540, lunge: 60, stop: 0.12, cancel: 99 }),
  ],
  jumpKick: atk({ anim: 'jump_kick', dmg: 10, rmax: 120, hmin: -40, hmax: 140, type: 'kd', kb: 300, launch: 420, stop: 0.09 }),
  special: atk({ anim: 'special', start: 1, end: 4, dmg: 14, rmax: 130, both: true, depth: 42, type: 'kd', kb: 400, launch: 560, stop: 0.1, invuln: true, cost: 10, cancel: 99 }),
  back: atk({ anim: 'back_attack', dmg: 9, rmax: 105, behind: true, type: 'kd', kb: 300, launch: 420, stop: 0.1, cancel: 99 }),
  knee: atk({ anim: 'grab_knee', dmg: 6, rmax: 90, hmin: 20, stop: 0.08, whoosh: false }),
  kneeFinal: atk({ anim: 'grab_knee', dmg: 10, rmax: 90, hmin: 20, type: 'kd', kb: 320, launch: 520, stop: 0.12, whoosh: false }),
  throw: atk({ anim: 'throw', start: 99, end: 99, dmg: 0, invuln: true }),
};

// Leyla: schneller, weniger Energie, Kicks mit mehr Reichweite
export const LEYLA_ATTACKS = {
  combo: [
    atk({ anim: 'attack1', dmg: 4, rmax: 96, kb: 30, cancel: 1, stop: 0.05, fps: 17 }),
    atk({ anim: 'attack2', dmg: 6, rmax: 124, kb: 50, lunge: 60, cancel: 1, fps: 16 }),
    atk({ anim: 'attack3', start: 1, end: 1, dmg: 7, rmax: 86, hmin: 20, type: 'heavy', kb: 50, stop: 0.09, fps: 15 }),
    atk({ anim: 'attack4', start: 1, end: 2, dmg: 12, rmax: 148, type: 'kd', kb: 380, launch: 520, lunge: 80, stop: 0.12, cancel: 99, fps: 14 }),
  ],
  // Hechtsprung-Kick: schraeg nach unten, reisst Gegner um
  jumpKick: atk({ anim: 'jump_kick', dmg: 11, rmax: 125, hmin: -60, hmax: 130, type: 'kd', kb: 340, launch: 380, stop: 0.09, dive: true }),
  // Helikopter-Kick: trifft mehrfach auf beiden Seiten und jongliert
  special: atk({ anim: 'special', start: 1, end: 4, dmg: 4, rmax: 135, both: true, multi: true, depth: 40, type: 'kd', kb: 180, launch: 420, stop: 0.06, invuln: true, cost: 12, cancel: 99, fps: 14 }),
  back: atk({ anim: 'back_attack', dmg: 10, rmax: 118, behind: true, type: 'kd', kb: 340, launch: 400, stop: 0.1, cancel: 99, fps: 13 }),
  knee: PLAYER_ATTACKS.knee,
  kneeFinal: PLAYER_ATTACKS.kneeFinal,
  throw: PLAYER_ATTACKS.throw,
};

// Spielbare Figuren (Werte fuer die Figurenauswahl: 1..5)
export const PLAYERS = {
  Kai: {
    sprite: 'Kai', name: 'KAI', hp: 120, walk: 280, depth: 180, jump: 860, attacks: PLAYER_ATTACKS,
    stats: { power: 4, speed: 3, reach: 3 },
    desc: ['Ausgewogener Straßenkämpfer', 'Combo: Jab · Gerade · Uppercut · Kick', 'Spezial: Wirbelwind (trifft rundum)', 'Sprung + Schlag: Flugkick'],
  },
  Leyla: {
    sprite: 'Leyla', name: 'LEYLA', hp: 100, walk: 330, depth: 205, jump: 920, attacks: LEYLA_ATTACKS,
    stats: { power: 3, speed: 5, reach: 4 },
    desc: ['Schnelle Kickboxerin aus Neukölln', 'Combo: Jab · Front-Kick · Knie · Dreh-Roundhouse', 'Spezial: Helikopter-Kick (Mehrfachtreffer)', 'Sprung + Schlag: Hechtsprung-Kick'],
  },
};

// Waffen: Schaden, Reichweite, Haltbarkeit (Treffer), Wurfschaden, Haltewinkel relativ zum Unterarm
export const WEAPONS = {
  Pipe:   { name: 'ROHR', dmg: 12, reach: 140, dur: 8, type: 'heavy', throwDmg: 14, hold: 80, fps: 13 },
  Bat:    { name: 'SCHLÄGER', dmg: 14, reach: 150, dur: 6, type: 'kd', throwDmg: 14, hold: 80, fps: 12 },
  Knife:  { name: 'MESSER', dmg: 9, reach: 112, dur: 12, type: 'light', throwDmg: 18, hold: 70, fps: 17 },
  Bottle: { name: 'FLASCHE', dmg: 16, reach: 110, dur: 1, type: 'kd', throwDmg: 12, hold: 80, fps: 13 },
  Golf:   { name: 'GOLFSCHLÄGER', dmg: 13, reach: 160, dur: 10, type: 'kd', throwDmg: 14, hold: 80, fps: 12 },
};

export function weaponAttack(wname) {
  const w = WEAPONS[wname];
  return atk({
    anim: 'weapon_swing', start: 2, end: 2, dmg: w.dmg, rmax: w.reach, type: w.type,
    kb: w.type === 'kd' ? 340 : 90, launch: w.type === 'kd' ? 500 : 0, stop: 0.11, fps: w.fps, cancel: 99, weapon: wname,
  });
}

// Gegner-Profile (entspricht ABrawlerEnemy::GetProfile) – style: punk, skater, heavy, kicker, suit
export const ENEMIES = {
  Kalle:   { name: 'KALLE', style: 'punk', hp: 55, speed: 170, score: 100 },
  Ronny:   { name: 'RONNY', style: 'punk', hp: 70, speed: 185, score: 150, cd: 1.1 },
  Micha:   { name: 'MESSER-MICHA', style: 'punk', hp: 70, speed: 180, score: 250, weapon: 'Knife', cd: 1.2 },
  Jojo:    { name: 'JOJO', style: 'skater', hp: 50, speed: 230, score: 150 },
  Deniz:   { name: 'DENIZ', style: 'skater', hp: 60, speed: 250, score: 200, cd: 1.1 },
  Zoe:     { name: 'ZOE', style: 'kicker', hp: 65, speed: 240, score: 250, cd: 1.0 },
  Nina:    { name: 'NINA', style: 'kicker', hp: 75, speed: 250, score: 300, cd: 0.9 },
  Brecher: { name: 'BRECHER', style: 'heavy', hp: 150, speed: 120, score: 500, grab: false, armor: 2, cd: 1.8, shadow: 1.35 },
  Rolf:    { name: 'SECURITY-ROLF', style: 'heavy', hp: 300, speed: 140, score: 3000, grab: false, armor: 3, cd: 1.3, shadow: 1.4 },
  RolfII:  { sprite: 'Rolf', name: 'ROLF (REVANCHE)', style: 'heavy', hp: 260, speed: 150, score: 2000, grab: false, armor: 3, cd: 1.4, shadow: 1.4 },
  Sven:    { name: 'HOOL-SVEN', style: 'heavy', hp: 320, speed: 150, score: 3000, grab: false, armor: 3, cd: 1.2, weapon: 'Bat', shadow: 1.4 },
  Kontrolli: { name: 'KONTROLLEUR', style: 'punk', hp: 60, speed: 190, score: 150, cd: 1.1 },
  // --- Endgegner mit eigenen Mechaniken (siehe Enemy.bossBrain) -------------------------
  Klaus:   { name: 'KONTROLLEUR KLAUS', title: 'Fahrscheine, bitte!', style: 'heavy', hp: 480, speed: 150, score: 6000, grab: false, armor: 3, cd: 1.3, boss: true, brain: 'klaus', shadow: 1.4,
    tips: ['Sprint: Punktestrafe bei Treffer', 'Pfiff: ruft Kontrolleure', 'U-Bahn fährt ein: hinten weg!'] },
  Tuer:    { name: 'DIE TÜR', title: 'Heute nicht.', style: 'heavy', hp: 520, speed: 130, score: 8000, grab: false, armor: 3, cd: 1.2, boss: true, brain: 'tuer', shadow: 1.45,
    tips: ['Blockt von vorne: von hinten angreifen', 'Spotlight: raus aus dem Licht!', 'Würfe und Spezial durchbrechen die Deckung'] },
  Harald:  { name: 'BAULÖWE HARALD', title: 'Das wird alles Luxus!', style: 'suit', hp: 600, speed: 200, score: 10000, grab: false, armor: 2, cd: 1.0, boss: true, brain: 'harald', weapon: 'Golf', shadow: 1.2, summon: ['Zoe', 'Brecher'],
    tips: ['Kran: Schatten am Boden meiden', 'Golfbälle aus der Distanz', 'Ruft Verstärkung'] },
};

// Stages: Bereiche (Kulisse), Kaempfe, Kisten, Waffen am Boden
const G = (e, alive = 0, delay = 0) => ({ e, alive, delay });
export const STAGES = [
  {
    name: 'STAGE 1', title: 'KREUZBERG BEI NACHT',
    areas: [
      { x0: 0, x1: 4096, walls: ['BG_Street_00', 'BG_Street_01'], floor: 'BG_FloorStreet', sky: 'BG_Sky', fg: ['FG_LampPost', [1500, 2900, 3800]] },
      { x0: 4096, x1: 10240, walls: ['BG_UBahn_00', 'BG_UBahn_00', 'BG_UBahn_00'], floor: 'BG_FloorPlatform', sky: null, fg: ['FG_Pillar', [4900, 6100, 7300]] },
    ],
    encounters: [
      { t: 560, lock: 900, g: [G(['Kalle', 'Kalle']), G(['Ronny'], 1, 10), G(['Kalle', 'Jojo'], 1, 12)] },
      { t: 1760, lock: 2100, g: [G(['Jojo', 'Kalle', 'Ronny']), G(['Deniz', 'Kalle'], 1, 12)] },
      { t: 2960, lock: 3300, g: [G(['Brecher']), G(['Ronny', 'Jojo'], 1, 6), G(['Kalle', 'Deniz'], 1, 12)] },
      { t: 4560, lock: 4900, g: [G(['Kalle', 'Ronny', 'Deniz']), G(['Jojo', 'Jojo'], 1, 10), G(['Brecher'], 1, 14)] },
      { t: 5860, lock: 6200, g: [G(['Rolf', 'Kalle']), G(['Deniz', 'Ronny', 'Jojo'], 1, 10), G(['Brecher'], 1, 14)] },
      { t: 7050, lock: 7392, boss: true, g: [G(['Klaus']), G(['Kalle', 'Ronny'], 1, 25)] },
    ],
    props: [['TrashCan', 1050, 222, 'Currywurst'], ['Crate', 1520, 205, 'Money'], ['TrashCan', 2650, 225, 'Doener'],
      ['Crate', 3560, 210, 'Currywurst'], ['TrashCan', 4450, 225, 'Money'], ['Crate', 5600, 200, 'Doener'],
      ['TrashCan', 6700, 222, 'Currywurst'], ['Crate', 6950, 90, 'Doener']],
    weapons: [['Pipe', 1300, 60], ['Bottle', 2500, 150], ['Pipe', 5200, 120]],
  },
  {
    name: 'STAGE 2', title: 'EAST SIDE GALLERY',
    areas: [
      { x0: 0, x1: 4096, walls: ['BG_Gallery_00', 'BG_Gallery_01'], floor: 'BG_FloorPromenade', sky: 'BG_SkySpree', fg: ['FG_Tree', [1300, 2700, 3700]] },
      { x0: 4096, x1: 10240, walls: ['BG_Backyard_00', 'BG_Backyard_00', 'BG_Backyard_00'], floor: 'BG_FloorCobble', sky: 'BG_SkySpree', fg: ['FG_Tree', [5400]] },
    ],
    encounters: [
      { t: 560, lock: 900, g: [G(['Zoe', 'Kalle']), G(['Micha', 'Jojo'], 1, 10)] },
      { t: 1760, lock: 2100, g: [G(['Nina', 'Ronny', 'Deniz']), G(['Micha', 'Zoe'], 1, 12)] },
      { t: 2960, lock: 3300, g: [G(['Brecher', 'Micha']), G(['Zoe', 'Nina'], 1, 8)] },
      { t: 4560, lock: 4900, g: [G(['Kalle', 'Micha', 'Deniz']), G(['Brecher', 'Jojo'], 1, 12)] },
      { t: 5860, lock: 6200, g: [G(['Sven', 'Zoe']), G(['Ronny', 'Deniz', 'Kalle'], 1, 12)] },
      { t: 7050, lock: 7392, boss: true, g: [G(['Tuer']), G(['Micha', 'Nina'], 1, 18), G(['Zoe', 'Ronny'], 1, 28)] },
    ],
    props: [['Crate', 1100, 220, 'Currywurst'], ['TrashCan', 2300, 210, 'Money'], ['Crate', 3600, 215, 'Doener'],
      ['TrashCan', 4700, 225, 'Currywurst'], ['Crate', 5500, 200, 'Money'], ['TrashCan', 6800, 222, 'Doener']],
    weapons: [['Bat', 1000, 80], ['Bottle', 4400, 190], ['Bottle', 6300, 60]],
  },
  {
    name: 'STAGE 3', title: 'BAUSTELLE AM ALEX',
    areas: [
      { x0: 0, x1: 4096, walls: ['BG_Construction_00', 'BG_Construction_01'], floor: 'BG_FloorConstruction', sky: 'BG_SkyAlex', fg: ['FG_Scaffold', [1400, 2800, 3900]] },
      { x0: 4096, x1: 10240, walls: ['BG_Rooftop_00', 'BG_Rooftop_00', 'BG_Rooftop_00'], floor: 'BG_FloorRooftop', sky: 'BG_SkyRooftop', fg: null },
    ],
    encounters: [
      { t: 560, lock: 900, g: [G(['Micha', 'Zoe', 'Kalle']), G(['Deniz', 'Nina'], 1, 10)] },
      { t: 1760, lock: 2100, g: [G(['Brecher', 'Nina']), G(['Micha', 'Micha'], 1, 10), G(['Jojo', 'Zoe'], 1, 14)] },
      { t: 2960, lock: 3300, g: [G(['RolfII']), G(['Ronny', 'Kalle'], 1, 10)] },
      { t: 4560, lock: 4900, g: [G(['Zoe', 'Nina', 'Micha']), G(['Brecher', 'Deniz'], 1, 12)] },
      { t: 5860, lock: 6200, g: [G(['Brecher', 'Brecher']), G(['Nina', 'Micha', 'Zoe'], 1, 12)] },
      { t: 7050, lock: 7392, boss: true, g: [G(['Harald']), G(['Micha', 'Nina'], 0, 18)] },
    ],
    props: [['Crate', 1200, 215, 'Doener'], ['TrashCan', 2500, 220, 'Money'], ['Crate', 3700, 200, 'Currywurst'],
      ['Crate', 4700, 215, 'Money'], ['TrashCan', 5600, 225, 'Doener'], ['Crate', 6900, 100, 'Doener']],
    weapons: [['Pipe', 900, 160], ['Bat', 3100, 60], ['Knife', 5100, 140], ['Pipe', 6600, 200]],
  },
];
