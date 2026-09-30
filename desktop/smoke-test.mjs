// Automatischer Test der Desktop-Version (Electron) mit Playwright.
//
//   npm test                                   -> testet desktop/ (vorher "npm run stage")
//   node smoke-test.mjs --exe dist/StreetsOfBerlin-linux-x64/StreetsOfBerlin   -> testet ein gepacktes Build
//   --full                                     -> zusaetzlich Bot-Durchlauf aller Stages
//
// Prueft: Laden ueber app://, Titelmenue mit "BEENDEN", Start per Tastatur, Vollbild-Umschaltung,
// Spielen, optional kompletter Durchlauf bis zum Abspann.
import { _electron as electron } from 'playwright-core';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const exeIdx = args.indexOf('--exe');
const exe = exeIdx >= 0 ? path.resolve(args[exeIdx + 1]) : null;
const full = args.includes('--full');
const extra = process.platform === 'linux' && !process.env.DISPLAY ? ['--ozone-platform=headless'] : [];

let failed = false;
const fail = (m) => { console.error('FEHLER:', m); failed = true; };

async function launch(query) {
  const opts = exe
    ? { executablePath: exe, args: [...extra, `--sob-query=${query}`] }
    : { args: [HERE, ...extra, `--sob-query=${query}`] };
  const app = await electron.launch(opts);
  const page = await app.firstWindow();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.waitForFunction(() => window.__sob, null, { timeout: 60000 });
  return { app, page, errors };
}
const state = (page) => page.evaluate(() => {
  const g = window.__sob;
  return { flow: g.flow, char: g.player && g.player.sprite, stage: g.stageIndex, x: g.player ? Math.round(g.player.x) : null, fs: g.fullscreen };
});

// --- 1) Start, Menue, Spielen ---------------------------------------------------------
{
  const { app, page, errors } = await launch('?mute');
  const info = await page.evaluate(() => ({
    desktop: !!window.sobDesktop,
    origin: location.origin,
    main: window.__sob.menu.items('main').map((i) => i.label),
    options: window.__sob.menu.items('options').map((i) => i.label),
    atlases: Object.keys(window.__sob.assets.images).length,
  }));
  console.log('Start:', JSON.stringify(info));
  if (!info.desktop) fail('window.sobDesktop fehlt');
  if (!info.main.includes('BEENDEN')) fail('BEENDEN fehlt im Titelmenue');
  if (!info.options.includes('VOLLBILD')) fail('VOLLBILD fehlt in den Optionen');
  if (info.atlases < 10) fail('Grafiken nicht geladen');

  await page.evaluate(() => window.__sob.toggleFullscreen());
  await page.waitForTimeout(1200);
  const fsOn = await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows()[0].isFullScreen());
  const fsGame = (await state(page)).fs;
  await page.evaluate(() => window.__sob.toggleFullscreen());
  await page.waitForTimeout(1200);
  console.log('Vollbild:', fsOn, fsGame);
  // ohne Fenstermanager (reiner Headless-Modus) gibt es kein Vollbild – dann nur mit Xvfb/Desktop pruefbar
  if (extra.length) console.log('Vollbild-Pruefung uebersprungen (headless)');
  else if (!fsOn || !fsGame) fail('Vollbild laesst sich nicht einschalten');

  await page.keyboard.press('Enter');
  await page.waitForTimeout(300);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2600);
  await page.keyboard.down('KeyD'); await page.waitForTimeout(1500); await page.keyboard.up('KeyD');
  for (let i = 0; i < 6; i++) { await page.keyboard.press('KeyJ'); await page.waitForTimeout(120); }
  const s = await state(page);
  console.log('Spiel:', JSON.stringify(s));
  if (s.flow !== 'playing') fail('Nicht im Spiel: ' + s.flow);
  if (!(s.x > 400)) fail('Spieler bewegt sich nicht');
  await page.screenshot({ path: path.join(HERE, 'dist', 'smoke.png') }).catch(() => {});
  if (errors.length) fail('JS-Fehler: ' + errors.slice(0, 5).join('; '));
  await app.close();
}

// --- 2) Optional: Bot spielt alles durch -------------------------------------------------
if (full) {
  const { app, page, errors } = await launch('?autoplay&god&mute&speed=8&char=leyla');
  const t0 = Date.now();
  let s;
  while (Date.now() - t0 < 10 * 60000) {
    await page.waitForTimeout(5000);
    s = await state(page);
    console.log(`t=${Math.round((Date.now() - t0) / 1000)}s`, JSON.stringify(s));
    if (s.flow === 'ending') break;
  }
  if (!s || s.flow !== 'ending') fail('Abspann nicht erreicht');
  if (errors.length) fail('JS-Fehler: ' + errors.slice(0, 5).join('; '));
  await app.close();
}

console.log(failed ? 'DESKTOP-TEST FEHLGESCHLAGEN' : 'DESKTOP-TEST OK');
process.exit(failed ? 1 : 0);
