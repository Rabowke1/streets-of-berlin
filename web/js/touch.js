// Touch-Steuerung fuer Handys/Tablets: virtueller Stick links, Aktionsknoepfe rechts.
export function setupTouch(game, root) {
  const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
  if (!coarse && !new URLSearchParams(location.search).has('touch')) return;

  const pad = document.createElement('div');
  pad.className = 'touchpad';
  pad.innerHTML = `
    <div class="stick" aria-label="Laufen"><div class="knob"></div></div>
    <div class="buttons">
      <button type="button" data-a="special" aria-label="Spezial">SPEZ</button>
      <button type="button" data-a="back" aria-label="Rückschlag oder Waffe werfen">WURF</button>
      <button type="button" data-a="jump" aria-label="Sprung">SPRUNG</button>
      <button type="button" data-a="attack" class="big" aria-label="Schlag">SCHLAG</button>
    </div>
    <button type="button" class="start" data-a="start" aria-label="Start oder Pause">START</button>`;
  root.appendChild(pad);

  const stick = pad.querySelector('.stick');
  const knob = pad.querySelector('.knob');
  let stickId = null;
  const setStick = (x, y) => {
    game.virtual = { x, y };
    knob.style.transform = `translate(${x * 34}px, ${-y * 34}px)`;
  };
  const move = (t) => {
    const r = stick.getBoundingClientRect();
    let x = (t.clientX - (r.left + r.width / 2)) / (r.width / 2);
    let y = -(t.clientY - (r.top + r.height / 2)) / (r.height / 2);
    const len = Math.hypot(x, y);
    if (len > 1) { x /= len; y /= len; }
    if (len < 0.2) { x = 0; y = 0; }
    setStick(x, y);
  };
  stick.addEventListener('touchstart', (e) => { e.preventDefault(); const t = e.changedTouches[0]; stickId = t.identifier; move(t); game.initAudio(); }, { passive: false });
  stick.addEventListener('touchmove', (e) => {
    e.preventDefault();
    for (const t of e.changedTouches) if (t.identifier === stickId) move(t);
  }, { passive: false });
  const end = (e) => { for (const t of e.changedTouches) if (t.identifier === stickId) { stickId = null; setStick(0, 0); } };
  stick.addEventListener('touchend', end);
  stick.addEventListener('touchcancel', end);

  for (const b of pad.querySelectorAll('button[data-a]')) {
    b.addEventListener('touchstart', (e) => {
      e.preventDefault();
      game.initAudio();
      game.touchPress(b.dataset.a);
      b.classList.add('down');
    }, { passive: false });
    const up = () => b.classList.remove('down');
    b.addEventListener('touchend', up);
    b.addEventListener('touchcancel', up);
    b.addEventListener('click', () => game.touchPress(b.dataset.a)); // Maus / Tests
  }
}
