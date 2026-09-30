// Einstieg: Assets laden, Spiel starten, feste 60-Hz-Spiellogik.
import { Assets } from './assets.js';
import { Game } from './game.js';
import { setupTouch } from './touch.js';

const params = new URLSearchParams(location.search);
const opts = {
  autoplay: params.has('autoplay'),
  god: params.has('god'),
  mute: params.has('mute'),
  speed: Math.max(1, Math.min(16, Number(params.get('speed')) || 1)),
  stage: Math.max(0, Math.min(3, (Number(params.get('stage')) || 1) - 1)),
  // ?players=2: zu zweit (mit ?autoplay spielen zwei Bots)
  players: Math.max(1, Math.min(2, Number(params.get('players')) || 1)),
  // ?char=leyla waehlt die Figur vor (fuer Tests / Direktlinks)
  character: params.has('char') ? params.get('char').charAt(0).toUpperCase() + params.get('char').slice(1).toLowerCase() : null,
};

const canvas = document.getElementById('game');
const status = document.getElementById('status');

// Fehler sichtbar machen statt stumm haengenzubleiben
function showError(msg) {
  if (status && status.isConnected) status.textContent = 'Fehler: ' + msg;
  else console.error(msg);
}
window.addEventListener('error', (e) => showError(e.message || String(e.error)));
window.addEventListener('unhandledrejection', (e) => showError((e.reason && e.reason.message) || String(e.reason)));

function fit() {
  const host = document.getElementById('stage') || document.body;
  const s = Math.min(host.clientWidth / 1600, host.clientHeight / 900);
  canvas.style.width = `${Math.floor(1600 * s)}px`;
  canvas.style.height = `${Math.floor(900 * s)}px`;
}
window.addEventListener('resize', fit);
fit();

async function boot() {
  const assets = new Assets('assets/');
  try {
    await assets.load((p) => { status.textContent = `Lade Grafiken … ${Math.round(p * 100)} %`; });
  } catch (e) {
    status.textContent = 'Fehler beim Laden: ' + e.message;
    throw e;
  }
  status.remove();
  const game = new Game(canvas, assets, opts);
  window.__sob = game; // fuer Tests / Debugging
  setupTouch(game, document.getElementById('stage') || document.body);
  const STEP = 1 / 60;
  let acc = 0, last = performance.now();
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    acc += dt * opts.speed;
    let n = 0;
    while (acc >= STEP && n < 20 * opts.speed) { game.update(STEP); acc -= STEP; n++; }
    game.render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
boot();
