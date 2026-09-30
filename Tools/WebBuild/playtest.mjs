// Automatischer Playtest der Browser-Version mit Playwright (headless Chromium).
//
//   npm i playwright          (einmalig, in einem beliebigen Ordner mit NODE_PATH darauf)
//   python -m http.server 8765 --directory web &
//   node Tools/WebBuild/playtest.mjs [--url http://localhost:8765] [--out playtest-out]
//
// Ablauf: 1) Titelbild + manueller Start per Tastatur (Screenshots)
//         2) Bot spielt alle 3 Stages durch (?autoplay&god&speed=8) und prueft Fortschritt/Fehler.
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
  return { flow: g.flow, stage: g.stageIndex, x: g.player ? Math.round(g.player.x) : null, hp: g.player ? g.player.health : null,
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
  await page.keyboard.press('Enter');
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

// --- 2) Bot spielt alle Stages ---------------------------------------------------
{
  const page = await newPage('?autoplay&god&mute&speed=8');
  const t0 = Date.now();
  let lastStage = -1, shots = 0, lastX = -1, stuck = 0;
  while (Date.now() - t0 < MAX_MIN * 60000) {
    await page.waitForTimeout(3000);
    const s = await state(page);
    if (s.stage !== lastStage || shots < 3 * (s.stage + 1)) {
      await page.screenshot({ path: path.join(OUT, `bot_s${s.stage + 1}_${String(shots).padStart(2, '0')}.png`) });
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
  if (s.flow !== 'ending') fail('Ende nicht erreicht: ' + JSON.stringify(s));
  await page.screenshot({ path: path.join(OUT, 'zz_end.png') });
  const log = await page.evaluate(() => window.__sob.log.join('\n'));
  fs.writeFileSync(path.join(OUT, 'game-log.txt'), log);
  await page.close();
}

await browser.close();
if (errors.length) { console.error(errors.slice(0, 20).join('\n')); fail(`${errors.length} JS-Fehler`); }
console.log(failed ? 'PLAYTEST FEHLGESCHLAGEN' : 'PLAYTEST OK');
process.exit(failed ? 1 : 0);
