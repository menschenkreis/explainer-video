/* explainer-video engine
   One deterministic function, render(t), draws the whole video for time t.
   Audio is only the clock source: scrubbing, pausing and frame-exact export all call render(t).
   Markup contract (see references/engine-api.md):
     <section class="scene" data-scene="id" data-part="3.1 Label"> ... </section>
     any element:  data-at="cue[+0.4]"  data-fx="rise|fade|pop|draw|..."  data-dur="0.6"  data-out="cue"
     arrows:       <g class="edge" data-edge="idA>idB" data-at="cue" data-fx="edge"></g>  inside .graph > svg.edges
*/
(() => {
'use strict';
const TM = window.TIMING;
const Q = new URLSearchParams(location.search);
const EXPORT = Q.has('export');
const FADE = 0.5;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const easeOut = x => 1 - Math.pow(1 - x, 3);
const easeIO = x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const NS = 'http://www.w3.org/2000/svg';
const stage = $('#stage'), frame = $('#frame'), capbar = $('#capbar'), audio = $('#narration');
const hasAudio = !!(audio && audio.getAttribute('src') && TM.audio);
if (EXPORT) document.body.classList.add('exporting');

/* ---------- scenes ---------- */
const S = [];
for (const el of $$('.scene')) {
  const id = el.dataset.scene, w = TM.scenes[id];
  if (!w) { console.warn('[engine] scene has no timing:', id); continue; }
  S.push({ el, id, start: w.start, end: w.end, part: el.dataset.part || '', on: null, items: [] });
}
S.sort((a, b) => a.start - b.start);

/* ---------- edges (arrows between nodes, auto-clipped to node borders) ---------- */
function showAllForMeasure(on) { for (const s of S) s.el.style.display = on ? 'block' : 'none'; }
function pointOf(token, graph) {
  token = token.trim();
  if (token.includes(',')) { const [x, y] = token.split(',').map(Number); return { x, y, w: 0, h: 0 }; }
  const [id, side] = token.split('@');
  const n = document.getElementById(id);
  if (!n) { console.warn('[engine] edge: unknown node', id); return { x: 0, y: 0, w: 0, h: 0 }; }
  const r = { x: n.offsetLeft + n.offsetWidth / 2, y: n.offsetTop + n.offsetHeight / 2, w: n.offsetWidth, h: n.offsetHeight };
  if (side === 'top') return { x: r.x, y: n.offsetTop, w: 0, h: 0 };
  if (side === 'bottom') return { x: r.x, y: n.offsetTop + n.offsetHeight, w: 0, h: 0 };
  if (side === 'left') return { x: n.offsetLeft, y: r.y, w: 0, h: 0 };
  if (side === 'right') return { x: n.offsetLeft + n.offsetWidth, y: r.y, w: 0, h: 0 };
  return r;
}
function clipToRect(c, toward, pad) {            // point on c's border in direction of `toward`
  if (!c.w && !c.h) return { x: c.x, y: c.y };
  const dx = toward.x - c.x, dy = toward.y - c.y;
  if (!dx && !dy) return { x: c.x, y: c.y };
  const t = Math.min(dx ? (c.w / 2 + pad) / Math.abs(dx) : 1e9, dy ? (c.h / 2 + pad) / Math.abs(dy) : 1e9);
  return { x: c.x + dx * t, y: c.y + dy * t };
}
function buildEdges() {
  for (const g of $$('[data-edge]')) {
    const [sa, sb] = g.dataset.edge.split('>');
    const graph = g.closest('.graph, .fig');
    const A = pointOf(sa, graph), B = pointOf(sb, graph);
    const curve = parseFloat(g.dataset.curve || 0), pad = parseFloat(g.dataset.pad || 8);
    const mid = { x: (A.x + B.x) / 2, y: (A.y + B.y) / 2 };
    const L = Math.hypot(B.x - A.x, B.y - A.y) || 1;
    const ctrl = { x: mid.x - (B.y - A.y) / L * curve * L, y: mid.y + (B.x - A.x) / L * curve * L };
    const aim1 = curve ? ctrl : B, aim2 = curve ? ctrl : A;
    const p1 = clipToRect(A, aim1, pad), p2 = clipToRect(B, aim2, pad);
    const both = g.dataset.arrow === 'both', none = g.dataset.arrow === 'none';
    const HL = 22;                                                // arrow head length
    const ang2 = Math.atan2(p2.y - (curve ? ctrl.y : p1.y), p2.x - (curve ? ctrl.x : p1.x));
    const ang1 = Math.atan2(p1.y - (curve ? ctrl.y : p2.y), p1.x - (curve ? ctrl.x : p2.x));
    const end = none ? p2 : { x: p2.x - Math.cos(ang2) * (HL - 4), y: p2.y - Math.sin(ang2) * (HL - 4) };
    const start = both ? { x: p1.x - Math.cos(ang1) * (HL - 4), y: p1.y - Math.sin(ang1) * (HL - 4) } : p1;
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('class', 'line'); path.setAttribute('pathLength', '1');
    path.setAttribute('d', curve ? `M${start.x} ${start.y} Q${ctrl.x} ${ctrl.y} ${end.x} ${end.y}` : `M${start.x} ${start.y} L${end.x} ${end.y}`);
    g.appendChild(path);
    const head = (p, a) => {
      const h = document.createElementNS(NS, 'polygon'); h.setAttribute('class', 'head');
      const pts = [[0, 0], [-HL, -9], [-HL, 9]].map(([x, y]) => `${p.x + x * Math.cos(a) - y * Math.sin(a)},${p.y + x * Math.sin(a) + y * Math.cos(a)}`);
      h.setAttribute('points', pts.join(' ')); g.appendChild(h);
    };
    if (!none) head(p2, ang2);
    if (both) head(p1, ang1 + Math.PI);
    if (!g.dataset.fx) g.dataset.fx = 'edge';
    if (!g.dataset.dur) g.dataset.dur = '0.8';
  }
}

/* ---------- cue resolution + items ---------- */
const missing = new Set();
function resolve(spec, sc) {
  const m = /^\s*(@?[\w.]+)\s*(?:([+-])\s*(\d*\.?\d+))?\s*$/.exec(spec);
  if (!m) { console.warn('[engine] bad data-at:', spec); return sc.start; }
  let t, base = m[1];
  if (base === '@start') t = sc.start;
  else if (base === '@end') t = sc.end;
  else {
    const key = base.includes('.') ? base : sc.id + '.' + base;
    t = TM.cues[key];
    if (t === undefined) { missing.add(key); t = sc.start; }
  }
  if (m[2]) t += (m[2] === '-' ? -1 : 1) * parseFloat(m[3]);
  return t;
}
function buildItems() {
  for (const sc of S) {
    for (const el of $$('[data-at]', sc.el)) {
      if (!el.dataset.fx) el.dataset.fx = 'fade';
      const draw = /draw|edge|wipe|grow/.test(el.dataset.fx);
      sc.items.push({
        el, at: resolve(el.dataset.at, sc), dur: parseFloat(el.dataset.dur || 0.6),
        out: el.dataset.out ? resolve(el.dataset.out, sc) : null, outDur: parseFloat(el.dataset.outdur || 0.4),
        ease: draw ? easeIO : easeOut, p: -1, q: -1,
      });
    }
  }
}

/* ---------- rail (part chips) ---------- */
const parts = [...new Set(S.map(s => s.part).filter(Boolean))];
const rail = $('#rail');
parts.forEach(p => { const s = document.createElement('span'); s.textContent = p; s.dataset.p = p; rail.appendChild(s); });

/* ---------- render ---------- */
let cur = 0, capIdx = -1, lastPart = null;
const cap = $('#caption');
function render(tt) {
  cur = clamp(tt, 0, TM.duration);
  stage.style.setProperty('--t', cur.toFixed(3));
  let part = null;
  for (const sc of S) {
    const live = cur >= sc.start - 0.02 && cur < sc.end + 0.02;
    if (live !== sc.on) { sc.el.style.display = live ? 'block' : 'none'; sc.on = live; }
    if (!live) continue;
    part = sc.part || part;
    const fin = clamp((cur - sc.start) / FADE), fout = clamp((sc.end - cur) / FADE);
    sc.el.style.opacity = Math.min(fin, fout);
    sc.el.style.setProperty('--st', (cur - sc.start).toFixed(3));
    for (const it of sc.items) {
      const p = it.ease(clamp((cur - it.at) / it.dur));
      const q = it.out === null ? 0 : easeOut(clamp((cur - it.out) / it.outDur));
      if (p !== it.p) { it.el.style.setProperty('--p', p.toFixed(4)); it.p = p; }
      if (q !== it.q) { it.el.style.setProperty('--q', q.toFixed(4)); it.q = q; }
    }
  }
  if (part !== lastPart) { $$('#rail span').forEach(s => s.classList.toggle('on', s.dataset.p === part)); lastPart = part; }
  // captions
  let idx = -1;
  for (let i = 0; i < TM.captions.length; i++) { const c = TM.captions[i]; if (cur >= c.start && cur < c.end) { idx = i; break; } }
  if (idx !== capIdx) {
    capIdx = idx;
    if (idx < 0) { cap.classList.remove('show'); showTip(); }
    else { cap.textContent = TM.captions[idx].text; cap.classList.add('show'); capbar.classList.remove('tip'); capbar.textContent = TM.captions[idx].text; }
  }
}

/* ---------- fit to window (desktop, phone landscape, phone portrait) + zoom/pan ---------- */
let Z = 1, PX = 0, PY = 0, portrait = false, started = false;
const TIP = (TM.lang || 'en').startsWith('de') ? 'Tipp: Handy quer drehen oder ⛶ für Vollbild · Doppeltippen oder zwei Finger zum Zoomen' : 'Tip: rotate your phone or tap ⛶ for full screen · double-tap or pinch to zoom';
const HINT = (TM.lang || 'en').startsWith('de') ? '↻ Quer drehen für ein grösseres Bild' : '↻ Rotate for a bigger picture';
function showTip() { if (!started && portrait) { capbar.textContent = TIP; capbar.classList.add('tip'); } else if (capIdx < 0) capbar.textContent = ''; }
function fit() {
  const W = innerWidth, H = innerHeight;
  portrait = !EXPORT && W < 820 && H > W * 1.05;
  document.body.classList.toggle('portrait', portrait);
  const fw = W, fh = portrait ? Math.round(W * 9 / 16) : H;
  document.documentElement.style.setProperty('--fh', fh + 'px');
  const u = $('#ui'); if (u && portrait) document.documentElement.style.setProperty('--uih', u.offsetHeight + 'px');
  const s = EXPORT ? 1 : Math.min(fw / 1920, fh / 1080), k = s * Z, w = 1920 * k, h = 1080 * k;
  const mx = Math.max(0, (w - fw) / 2), my = Math.max(0, (h - fh) / 2);
  PX = clamp(PX, -mx, mx); PY = clamp(PY, -my, my);
  stage.style.transform = `translate(${(fw - w) / 2 + PX}px,${(fh - h) / 2 + PY}px) scale(${k})`;
  capbar.dataset.hint = portrait ? HINT : '';
  showTip();
}
function setZoom(z, cx, cy) {                  // cx/cy: point (client px) that should stay under the finger
  const fh = portrait ? Math.round(innerWidth * 9 / 16) : innerHeight, old = Z; Z = clamp(z, 1, 3);
  if (Z === 1) { PX = PY = 0; }
  else if (cx !== undefined) { const ox = cx - innerWidth / 2, oy = cy - fh / 2; PX = ox - (ox - PX) * Z / old; PY = oy - (oy - PY) * Z / old; }
  fit();
}
addEventListener('resize', fit); addEventListener('orientationchange', () => setTimeout(fit, 250)); fit();
window.__zoom = () => Z;

/* ---------- player ---------- */
let playing = false, last = 0, rate = 1;
const ui = $('#ui'), pp = $('#pp'), scrub = $('#scrub'), timeEl = $('#time'), jump = $('#jump'), startBtn = $('#start');
const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
function updateUI() {
  if (!ui) return;
  scrub.value = (cur / TM.duration * 1000) | 0; timeEl.textContent = `${fmt(cur)} / ${fmt(TM.duration)}`;
  const sc = S.find(s => cur >= s.start && cur < s.end); if (sc && jump.value !== sc.id) jump.value = sc.id;
  pp.textContent = playing ? '❚❚' : '▶';
}
function tick(ts) {
  if (!playing) return;
  const dt = (ts - last) / 1000; last = ts;
  if (hasAudio && !audio.paused && !audio.ended) cur = audio.currentTime; else cur += dt * rate;
  if (cur >= TM.duration) { cur = TM.duration; pause(); }
  render(cur); updateUI(); requestAnimationFrame(tick);
}
function play() {
  if (cur >= TM.duration - 0.05) seek(0);
  playing = true; started = true; last = performance.now();
  if (hasAudio && cur < (audio.duration || 1e9)) { audio.playbackRate = rate; audio.currentTime = cur; audio.play().catch(() => {}); }
  requestAnimationFrame(tick); updateUI();
}
function pause() { playing = false; if (hasAudio) audio.pause(); updateUI(); }
function seek(t) { cur = clamp(t, 0, TM.duration); if (hasAudio && isFinite(audio.duration)) audio.currentTime = Math.min(cur, audio.duration); render(cur); updateUI(); }
window.__seek = t => { render(t); };
window.__t = () => cur; window.__playing = () => playing;            // used by render_mp4.py / shot.py
window.__duration = TM.duration; window.__cues = TM.cues; window.__scenes = TM.scenes;

/* ---------- init ---------- */
showAllForMeasure(true);
buildEdges();
showAllForMeasure(false);
buildItems();
window.__missing = [...missing];
if (missing.size) console.warn('[engine] cues used in markup but not in timing:', [...missing]);
render(Q.has('t') ? parseFloat(Q.get('t')) : 0);
(document.fonts ? document.fonts.ready : Promise.resolve()).then(() => { window.__ready = true; });

if (!EXPORT && ui) {
  S.forEach(s => { const o = document.createElement('option'); o.value = s.id; o.textContent = (TM.scenes[s.id].title || s.id); jump.appendChild(o); });
  pp.onclick = () => (playing ? pause() : play());
  startBtn.onclick = () => { startBtn.style.display = 'none'; play(); };
  scrub.oninput = () => seek(scrub.value / 1000 * TM.duration);
  jump.onchange = () => { const s = S.find(x => x.id === jump.value); if (s) seek(s.start + 0.05); };
  $('#cc').onclick = e => { document.body.classList.toggle('nocc'); e.target.classList.toggle('on', !document.body.classList.contains('nocc')); };
  $('#cc').classList.add('on');
  $('#rate').onchange = e => { rate = parseFloat(e.target.value); if (hasAudio) audio.playbackRate = rate; };
  const de = document.documentElement, canFs = !!(de.requestFullscreen || de.webkitRequestFullscreen);
  if (!canFs) $('#fs').style.display = 'none';
  $('#fs').onclick = () => {
    if (document.fullscreenElement || document.webkitFullscreenElement) { (document.exitFullscreen || document.webkitExitFullscreen).call(document); return; }
    Promise.resolve((de.requestFullscreen || de.webkitRequestFullscreen).call(de)).then(() => { try { screen.orientation && screen.orientation.lock && screen.orientation.lock('landscape').catch(() => {}); } catch (e) {} }).catch(() => {});
  };
  $('#zoom').onclick = () => setZoom(Z < 1.5 ? 1.8 : Z < 2.4 ? 2.6 : 1);
  // touch + mouse gestures on the picture: tap = play/pause, double-tap = zoom, pinch = zoom, drag = pan when zoomed
  const pts = new Map(); let moved = false, t0 = 0, lastTap = 0, pinch = null;
  frame.addEventListener('pointerdown', e => {
    try { frame.setPointerCapture(e.pointerId); } catch (err) {}
    pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); moved = false; t0 = performance.now();
    if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: Z }; }
  });
  frame.addEventListener('pointermove', e => {
    const p = pts.get(e.pointerId); if (!p) return; const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    if (pts.size === 2 && pinch) { const [a, b] = [...pts.values()]; moved = true; setZoom(pinch.z * Math.hypot(a.x - b.x, a.y - b.y) / pinch.d, (a.x + b.x) / 2, (a.y + b.y) / 2); }
    else if (pts.size === 1 && Z > 1) { PX += dx; PY += dy; if (Math.abs(dx) + Math.abs(dy) > 2) moved = true; fit(); }
    else if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
  });
  const end = e => {
    if (!pts.has(e.pointerId)) return; pts.delete(e.pointerId); if (pts.size < 2) pinch = null;
    if (e.type !== 'pointerup' || moved || performance.now() - t0 > 350 || pts.size) return;
    const now = performance.now();
    if (now - lastTap < 320) { lastTap = 0; setZoom(Z > 1 ? 1 : 2.2, e.clientX, e.clientY); }
    else { lastTap = now; setTimeout(() => { if (lastTap === now) { lastTap = 0; startBtn.style.display = 'none'; playing ? pause() : play(); } }, 330); }
  };
  frame.addEventListener('pointerup', end); frame.addEventListener('pointercancel', end);
  document.addEventListener('fullscreenchange', fit);
  addEventListener('keydown', e => {
    if (e.code === 'Space') { e.preventDefault(); startBtn.style.display = 'none'; playing ? pause() : play(); }
    else if (e.code === 'ArrowRight') seek(cur + 5); else if (e.code === 'ArrowLeft') seek(cur - 5);
    else if (e.key === ']') { const i = S.findIndex(s => cur < s.end); if (S[i + 1]) seek(S[i + 1].start + 0.05); }
    else if (e.key === '[') { const i = S.findIndex(s => cur < s.end); const p = S[Math.max(0, i - 1)]; seek(p.start + 0.05); }
    else if (e.key === 'c') $('#cc').click(); else if (e.key === 'f') $('#fs').click();
  });
  let hideT; const poke = () => { ui.classList.remove('hide'); clearTimeout(hideT); hideT = setTimeout(() => playing && !portrait && ui.classList.add('hide'), 2500); };
  addEventListener('mousemove', poke); addEventListener('pointerdown', poke); poke(); fit();
  if (Q.has('t')) startBtn.style.display = 'none';
  updateUI();
}
})();
