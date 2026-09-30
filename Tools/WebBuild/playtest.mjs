// Automatischer Playtest der Browser-Version mit Playwright (headless Chromium).
//
//   npm i playwright          (einmalig, in einem beliebigen Ordner mit NODE_PATH darauf)
//   python -m http.server 8765 --directory web &
//   node Tools/WebBuild/playtest.mjs [--url http://localhost:8765] [--out playtest-out]
//
// Ablauf: 0) Laden im abgeschotteten iframe (wie im Artifact-Viewer)
//         1) Titelmenue + Figurenauswahl + manueller Start per Tastatur (Screenshots)
//         2) Optionsmenue: Musik/Sounds, Tastenbelegung aendern, Leyla spielen, Pause, Speichern
//         3) Bot spielt alle Stages mit Kai und mit Leyla durch (?autoplay&god&speed=8).
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const URL = args.url || 'http://localhost:8765';
const OUT = args.out || 'playtest-out';
const MAX_MIN = Number(args.minutes || 12);
fs.mkdirSync(OUT, { recursive: true });

const exe = process.env.CHROMIUM_PATH || undefined;
const browser = await chromium.launch({ executablePath: exe, args: ['--autoplay-policy=no-user-gesture-required'] });
const errors = [];
let failed = false;
const fail = (m) => { console.error('FEHLER:', m); failed = true; };

async function newPage(query) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(`${URL}/index.html${query}`);
  await page.waitForFunction(() => window.__sob, null, { timeout: 60000 });
  return page;
}
const state = (page) => page.evaluate(() => {
  const g = window.__sob;
  return { flow: g.flow, char: g.player && g.player.sprite, stage: g.stageIndex, x: g.player ? Math.round(g.player.x) : null, hp: g.player ? g.player.health : null,
    enemies: g.aliveEnemies(), enc: g.nextEnc, score: g.score, stats: g.stats, weapon: g.player && g.player.weapon };
});

// --- 0) Abgeschotteter Frame (wie im Artifact-Viewer: iframe sandbox, Origin "null") ---
{
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const frameErrors = [];
  page.on('pageerror', (e) => frameErrors.push(e.message));
  await page.setContent(`<iframe sandbox="allow-scripts" src="${URL}/index.html?mute" style="width:1600px;height:900px;border:0"></iframe>`);
  await page.waitForTimeout(5000);
  const frame = page.frames().find((f) => f !== page.mainFrame());
  const status = frame ? await frame.evaluate(() => { const s = document.getElementById('status'); return s ? s.textContent : null; }) : 'kein Frame';
  console.log('Sandbox-Frame:', status === null ? 'Spiel geladen' : status);
  if (status !== null) fail('Spiel laedt im abgeschotteten Frame nicht: ' + status);
  if (frameErrors.length) fail('Fehler im Sandbox-Frame: ' + frameErrors.join('; '));
  await page.screenshot({ path: path.join(OUT, '00_sandbox.png') });
  await page.close();
}

// --- 1) Manuell: Titel, Start, laufen, schlagen --------------------------------
{
  const page = await newPage('?mute');
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(OUT, '01_title.png') });
  await page.keyboard.press('Enter'); // SPIEL STARTEN
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, '01b_select.png') });
  await page.keyboard.press('Enter'); // Figur bestaetigen (Kai)
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(OUT, '02_intro.png') });
  await page.keyboard.down('KeyD');
  await page.waitForTimeout(2600);
  await page.keyboard.up('KeyD');
  for (let i = 0; i < 12; i++) { await page.keyboard.press('KeyJ'); await page.waitForTimeout(120); }
  await page.keyboard.press('KeyK'); await page.waitForTimeout(150); await page.keyboard.press('KeyJ');
  await page.waitForTimeout(700);
  await page.screenshot({ path: path.join(OUT, '03_fight.png') });
  const s = await state(page);
  console.log('Manuell:', JSON.stringify(s));
  if (s.flow !== 'playing') fail('Nach Start nicht im Spiel: ' + s.flow);
  if (!(s.x > 400)) fail('Spieler hat sich nicht bewegt: x=' + s.x);
  await page.close();
}

// --- 2) Optionen, Tastenbelegung, Leyla, Pause ---------------------------------------
{
  const page = await newPage('');
  const key = async (k, n = 1) => { for (let i = 0; i < n; i++) { await page.keyboard.press(k); await page.waitForTimeout(90); } };
  const menu = () => page.evaluate(() => { const g = window.__sob, t = g.menu.top; return { id: t && t.id, sel: t && t.sel, wait: g.menu.wait, s: { music: g.settings.music, sfx: g.settings.sfx, sfxVol: g.settings.sfxVol, attack: g.settings.keys.attack } }; });
  await page.waitForTimeout(500);
  await key('ArrowDown', 2); await key('Enter');
  let m = await menu();
  if (m.id !== 'options') fail('Optionsmenue nicht geoeffnet: ' + JSON.stringify(m));
  await key('Enter');                  // Musik aus
  await key('ArrowDown', 2); await key('Enter'); // Sounds aus
  await key('ArrowDown'); await key('ArrowLeft'); // Sound-Lautstaerke 80 -> 70 %
  await page.screenshot({ path: path.join(OUT, '04_options.png') });
  await key('ArrowDown'); await key('Enter');     // Steuerung
  await key('ArrowDown', 4); await key('Enter');  // Schlag neu belegen
  m = await menu();
  if (!m.wait || m.wait.action !== 'attack') fail('Neubelegen nicht aktiv: ' + JSON.stringify(m));
  await page.screenshot({ path: path.join(OUT, '05_controls_wait.png') });
  await key('KeyU');
  m = await menu();
  console.log('Optionen:', JSON.stringify(m));
  if (m.s.music || m.s.sfx || Math.abs(m.s.sfxVol - 0.7) > 1e-6) fail('Audio-Optionen nicht uebernommen: ' + JSON.stringify(m.s));
  if (m.s.attack[0] !== 'KeyU') fail('Tastenbelegung nicht uebernommen: ' + JSON.stringify(m.s));
  await page.screenshot({ path: path.join(OUT, '06_controls.png') });
  await key('Escape'); await key('Escape');       // zurueck zum Titel
  m = await menu();
  if (m.id !== 'main') fail('Zurueck zum Titel klappt nicht: ' + JSON.stringify(m));
  await key('ArrowUp', 2); await key('Enter'); await key('ArrowRight');
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, '07_select_leyla.png') });
  await key('Enter');
  await page.waitForTimeout(2600);
  await page.keyboard.down('KeyD'); await page.waitForTimeout(1500); await page.keyboard.up('KeyD');
  await page.keyboard.press('KeyJ'); // alte Taste: darf nicht mehr schlagen
  const oldKey = await page.evaluate(() => window.__sob.player.state);
  await page.keyboard.press('KeyU');
  await page.waitForTimeout(30);
  const newKey = await page.evaluate(() => [window.__sob.player.state, window.__sob.player.attack && window.__sob.player.attack.anim]);
  if (oldKey === 'attack') fail('Alte Taste J schlaegt noch');
  if (newKey[0] !== 'attack') fail('Neue Taste U schlaegt nicht: ' + newKey);
  await page.waitForTimeout(600);
  await page.keyboard.press('KeyL');
  await page.waitForTimeout(250);
  const spec = await page.evaluate(() => window.__sob.player.attack && window.__sob.player.attack.anim);
  await page.screenshot({ path: path.join(OUT, '08_leyla_special.png') });
  if (spec !== 'special') fail('Leylas Spezialangriff startet nicht: ' + spec);
  let s = await state(page);
  console.log('Leyla:', JSON.stringify(s));
  if (s.char !== 'Leyla') fail('Falsche Figur: ' + s.char);
  await page.waitForTimeout(800);
  await key('Escape');
  m = await menu();
  await page.screenshot({ path: path.join(OUT, '09_pause.png') });
  if (m.id !== 'pause') fail('Pause-Menue fehlt: ' + JSON.stringify(m));
  await key('Escape');
  if (await page.evaluate(() => window.__sob.paused)) fail('Weiter aus der Pause klappt nicht');
  await page.reload();
  await page.waitForFunction(() => window.__sob, null, { timeout: 60000 });
  const saved = await page.evaluate(() => ({ c: window.__sob.settings.character, a: window.__sob.settings.keys.attack[0], m: window.__sob.settings.music }));
  console.log('Nach Neuladen:', JSON.stringify(saved));
  if (saved.c !== 'Leyla' || saved.a !== 'KeyU' || saved.m !== false) fail('Einstellungen nicht gespeichert: ' + JSON.stringify(saved));
  await page.close();
}

// --- 3) Zu zweit: Tastatur (1P) + Gamepad (2P, simuliert) --------------------------------
{
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  // Gamepad-Attrappe: window.__pad steuert Knoepfe und Stick
  await page.addInitScript(() => {
    window.__pad = { buttons: new Array(17).fill(false), axes: [0, 0] };
    navigator.getGamepads = () => [{ connected: true, index: 0, id: 'Test-Pad', axes: window.__pad.axes,
      buttons: window.__pad.buttons.map((p) => ({ pressed: p, value: p ? 1 : 0 })) }];
  });
  await page.goto(`${URL}/index.html?mute`);
  await page.waitForFunction(() => window.__sob, null, { timeout: 60000 });
  const padTap = async (i) => {
    await page.evaluate((b) => { window.__pad.buttons[b] = true; }, i); await page.waitForTimeout(120);
    await page.evaluate((b) => { window.__pad.buttons[b] = false; }, i); await page.waitForTimeout(120);
  };
  await page.waitForTimeout(400);
  await page.keyboard.press('ArrowDown'); await page.waitForTimeout(100);
  await page.keyboard.press('Enter'); await page.waitForTimeout(300);   // 2 SPIELER (1P = Tastatur)
  await padTap(0);                                                        // Gamepad meldet sich als 2P an
  const joined = await page.evaluate(() => window.__sob.menu.top.coop.slots.map((s) => s.dev));
  await page.screenshot({ path: path.join(OUT, '10_coop_select.png') });
  await page.keyboard.press('Enter'); await page.waitForTimeout(150);    // 1P bereit
  await padTap(0);                                                        // 2P bereit -> Start
  await page.waitForTimeout(2600);
  const coop = await page.evaluate(() => window.__sob.players.map((p) => ({ c: p.sprite, dev: p.device, x: Math.round(p.x) })));
  console.log('Koop-Start:', JSON.stringify(joined), JSON.stringify(coop));
  if (joined[0] !== 'kb' || joined[1] !== 'pad0') fail('Geraete-Zuordnung falsch: ' + JSON.stringify(joined));
  if (coop.length !== 2 || coop[0].dev !== 'kb' || coop[1].dev !== 'pad0' || coop[0].c === coop[1].c) fail('Koop-Start falsch: ' + JSON.stringify(coop));
  // Stick nach rechts bewegt nur 2P, Taste D nur 1P
  await page.evaluate(() => { window.__pad.axes = [1, 0]; }); await page.waitForTimeout(900);
  await page.evaluate(() => { window.__pad.axes = [0, 0]; });
  const afterPad = await page.evaluate(() => window.__sob.players.map((p) => Math.round(p.x)));
  await page.keyboard.down('KeyD'); await page.waitForTimeout(700); await page.keyboard.up('KeyD');
  const afterKb = await page.evaluate(() => window.__sob.players.map((p) => Math.round(p.x)));
  console.log('Koop-Bewegung:', JSON.stringify({ start: coop.map((p) => p.x), afterPad, afterKb }));
  if (!(afterPad[1] > coop[1].x + 100) || Math.abs(afterPad[0] - coop[0].x) > 5) fail('Gamepad steuert nicht nur 2P');
  if (!(afterKb[0] > afterPad[0] + 80) || Math.abs(afterKb[1] - afterPad[1]) > 5) fail('Tastatur steuert nicht nur 1P');
  await page.screenshot({ path: path.join(OUT, '11_coop_game.png') });
  await page.close();
}

// --- 4) Bots spielen alle Stages: Kai, Leyla und zu zweit ---------------------------------
const BOSS_EVENTS = ['boss Klaus', 'train', 'boss down Klaus', 'boss Tuer', 'spot', 'bass drop', 'boss down Tuer', 'boss Harald', 'crane', 'boss down Harald', 'boss Alex', 'tram', 'zap', 'bellwave', 'boss down Alex'];
for (const who of ['kai', 'leyla', 'duo']) {
  const query = who === 'duo' ? '?autoplay&god&mute&speed=8&players=2' : `?autoplay&god&mute&speed=8&char=${who}`;
  const page = await newPage(query);
  const t0 = Date.now();
  let lastStage = -1, shots = 0, lastX = -1, stuck = 0;
  while (Date.now() - t0 < MAX_MIN * 60000) {
    await page.waitForTimeout(3000);
    const s = await state(page);
    if (s.stage !== lastStage || shots < 3 * (s.stage + 1)) {
      await page.screenshot({ path: path.join(OUT, `bot_${who}_s${s.stage + 1}_${String(shots).padStart(2, '0')}.png`) });
      shots++;
      lastStage = s.stage;
    }
    console.log(`t=${Math.round((Date.now() - t0) / 1000)}s`, JSON.stringify(s));
    if (s.flow === 'ending') { console.log('Alle Stages geschafft.'); break; }
    if (s.flow === 'playing' && s.x === lastX && s.enemies === 0) stuck++; else stuck = 0;
    lastX = s.x;
    if (stuck > 10) { fail('Bot steckt fest: ' + JSON.stringify(s)); break; }
  }
  const s = await state(page);
  if (s.flow !== 'ending') fail(`Ende nicht erreicht (${who}): ` + JSON.stringify(s));
  if (who !== 'duo' && s.char && s.char.toLowerCase() !== who) fail(`Bot spielt falsche Figur: ${s.char}`);
  if (who === 'duo' && (await page.evaluate(() => window.__sob.players.length)) !== 2) fail('Duo-Lauf ohne 2 Spieler');
  await page.screenshot({ path: path.join(OUT, `zz_end_${who}.png`) });
  const log = await page.evaluate(() => window.__sob.fullLog.join('\n'));
  const missing = BOSS_EVENTS.filter((ev) => !log.includes('] ' + ev));
  console.log(`Boss-Mechaniken (${who}):`, missing.length ? 'FEHLEN ' + missing.join(', ') : 'alle ausgeloest');
  if (missing.length) fail(`Boss-Ereignisse fehlen (${who}): ${missing.join(', ')}`);
  fs.writeFileSync(path.join(OUT, `game-log-${who}.txt`), log);
  await page.close();
}

await browser.close();
if (errors.length) { console.error(errors.slice(0, 20).join('\n')); fail(`${errors.length} JS-Fehler`); }
console.log(failed ? 'PLAYTEST FEHLGESCHLAGEN' : 'PLAYTEST OK');
process.exit(failed ? 1 : 0);
