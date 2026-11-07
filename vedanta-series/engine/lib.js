// Motion-graphics primitives for the "Who Am I?" Vedanta series.
// Every frame is a pure function of time: render(t) -> SVG string. No state.
const W = 1080, H = 1920;
const PAL = {
  night0: '#0b0b2b', night1: '#2a1b4d', dusk0: '#1d1442', dusk1: '#c2547a', dusk2: '#f2a65a',
  saffron: '#ff9933', gold: '#ffd166', cream: '#fff4dc', ink: '#1a1033', skin: '#c98a5e',
  skin2: '#a86b45', teal: '#2ec4b6', sea0: '#0b3d5c', sea1: '#1b6f8f', sea2: '#58c4dd',
  clay: '#c4683a', clay2: '#8f4426', leaf: '#3a7d44', red: '#e63946', white: '#ffffff'
};

// ---------- math ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, k) => a + (b - a) * k;
const E = {
  lin: k => k,
  out: k => 1 - Math.pow(1 - k, 3),
  in: k => k * k * k,
  io: k => (k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  back: k => { const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
  elastic: k => k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - .75) * (2 * Math.PI) / 3) + 1,
};
// progress 0..1 of time t through [a, a+d]
const tw = (t, a, d = .6, e = E.out) => e(clamp((t - a) / d));
// smooth on/off window: fades in at a, out at b
const win = (t, a, b, f = .35) => clamp((t - a) / f) * clamp((b - t) / f);
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ---------- svg helpers ----------
const g = (inner, tr = '', op = 1, extra = '') =>
  `<g${tr ? ` transform="${tr}"` : ''}${op < 1 ? ` opacity="${Math.max(0, op).toFixed(3)}"` : ''} ${extra}>${inner}</g>`;
const rect = (x, y, w, h, fill, rx = 0, extra = '') => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" ${extra}/>`;
const circ = (x, y, r, fill, extra = '') => `<circle cx="${x}" cy="${y}" r="${Math.max(0, r)}" fill="${fill}" ${extra}/>`;
const path = (d, fill = 'none', stroke = 'none', sw = 0, extra = '') =>
  `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
const line = (x1, y1, x2, y2, stroke, sw, extra = '') =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${sw}" stroke-linecap="round" ${extra}/>`;
function text(x, y, s, o = {}) {
  const { size = 64, fill = PAL.cream, weight = 800, anchor = 'middle', font = "'Baloo 2'", op = 1, ls = 0, stroke, sw = 0 } = o;
  const st = stroke ? ` stroke="${stroke}" stroke-width="${sw}" paint-order="stroke" stroke-linejoin="round"` : '';
  return `<text x="${x}" y="${y}" font-family="${font}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${ls}" opacity="${op}"${st}>${esc(s)}</text>`;
}
// pop-in scale around a point
const pop = (inner, x, y, k) => g(inner, `translate(${x} ${y}) scale(${Math.max(0.001, k)}) translate(${-x} ${-y})`, clamp(k * 1.5));

// ---------- backgrounds ----------
let _gid = 0;
function defs() {
  return `<defs>
  <radialGradient id="glowW"><stop offset="0" stop-color="#fff6d5" stop-opacity="1"/><stop offset=".35" stop-color="#ffd166" stop-opacity=".55"/><stop offset="1" stop-color="#ff9933" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowB"><stop offset="0" stop-color="#e0f7ff" stop-opacity=".9"/><stop offset=".4" stop-color="#58c4dd" stop-opacity=".35"/><stop offset="1" stop-color="#58c4dd" stop-opacity="0"/></radialGradient>
  <radialGradient id="vig" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>
  <linearGradient id="capbg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset=".35" stop-color="#000" stop-opacity=".45"/><stop offset="1" stop-color="#000" stop-opacity=".0"/></linearGradient>
  </defs>`;
}
function sky(stops) { // stops: [[offset,color],...]
  const id = 'sky' + (_gid++);
  return `<defs><linearGradient id="${id}" x1="0" x2="0" y1="0" y2="1">${stops.map(([o, c]) => `<stop offset="${o}" stop-color="${c}"/>`).join('')}</linearGradient></defs>` + rect(0, 0, W, H, `url(#${id})`);
}
function stars(t, n = 70, seed = 7, ymax = 1100, op = 1) {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x = r() * W, y = r() * ymax, rad = 1.2 + r() * 3.2, ph = r() * 6.28, sp = .8 + r() * 2;
    s += circ(x.toFixed(1), y.toFixed(1), rad.toFixed(2), '#fff', `opacity="${(op * (.35 + .65 * (.5 + .5 * Math.sin(t * sp + ph)))).toFixed(2)}"`);
  }
  return s;
}
const glow = (x, y, r, kind = 'W', op = 1) => circ(x, y, r, `url(#glow${kind})`, `opacity="${clamp(op).toFixed(3)}"`);
function moon(x, y, r, op = 1) {
  return g(glow(x, y, r * 3.2, 'W', .35) + circ(x, y, r, '#fff1c9') + circ(x - r * .3, y - r * .2, r * .18, '#efd9a3') + circ(x + r * .35, y + r * .3, r * .12, '#efd9a3'), '', op);
}
function hills(y, color, amp = 60, seed = 3, freq = 1) {
  const r = rng(seed); const a = r() * 6, b = r() * 6;
  let d = `M0 ${H} L0 ${y}`;
  for (let x = 0; x <= W; x += 30) d += ` L${x} ${(y - amp * (.6 * Math.sin(x / 260 * freq + a) + .4 * Math.sin(x / 110 * freq + b))).toFixed(1)}`;
  return path(d + ` L${W} ${H} Z`, color);
}
// floating dust/particles for magic moments
function motes(t, n, cx, cy, spread, color = PAL.gold, seed = 11, op = 1) {
  const r = rng(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const a = r() * 6.28, sp = .2 + r() * .5, ph = r();
    const k = (t * sp + ph) % 1;
    const x = cx + Math.cos(a) * spread * (.3 + k) + Math.sin(t + i) * 10;
    const y = cy + Math.sin(a) * spread * .6 * (.3 + k) - k * 160;
    s += circ(x.toFixed(1), y.toFixed(1), (2 + r() * 5) * (1 - k), color, `opacity="${(op * Math.sin(k * Math.PI)).toFixed(2)}"`);
  }
  return s;
}

// ---------- characters ----------
// Feet at (x,y). Height ~ 380*s. Options control look and pose.
function person(o) {
  const { x = 540, y = 1300, s: sc = 1, skin = PAL.skin, cloth = PAL.saffron, cloth2, face = 'neutral', flip = false,
    armL = 12, armR = 12, walk = 0, hair = 'short', beard = false, turban = null, bob = 0, look = 0, blink = 0,
    shawl = null, prop = '', propHand = 'R', kid = false, sweat = 0, op = 1, lean = 0, hairColor = '#1b1020' } = o;
  const k = kid ? .82 : 1;
  const legLen = 100 * k, bodyH = 150 * k, headR = 66;
  const hipY = -legLen, shY = hipY - bodyH + 18, headY = shY - headR + 4;
  const sw = Math.sin(walk) * 22;
  let s = '';
  // legs
  s += line(-18, hipY, -18 + sw * .9, 0, skin, 22) + line(18, hipY, 18 - sw * .9, 0, skin, 22);
  s += path(`M${-18 + sw * .9 - 14} -2 h30`, 'none', PAL.ink, 14) + path(`M${18 - sw * .9 - 14} -2 h30`, 'none', PAL.ink, 14);
  // body (kurta / dhoti shape)
  const c2 = cloth2 || cloth;
  s += path(`M-52 ${hipY + 30} Q-60 ${shY + 30} -40 ${shY} L40 ${shY} Q60 ${shY + 30} 52 ${hipY + 30} Z`, cloth);
  s += path(`M-56 ${hipY + 30} L56 ${hipY + 30} L46 ${hipY - 20} L-46 ${hipY - 20} Z`, c2, 'none', 0, 'opacity=".55"');
  if (shawl) s += path(`M-42 ${shY + 4} L30 ${hipY + 10} L44 ${hipY - 4} L-28 ${shY - 2} Z`, shawl);
  // arms: angle in degrees from straight down; positive = forward (toward facing direction)
  const arm = (side, ang) => {
    const ax = side * 40, ay = shY + 16, L = 105 * k;
    const r = ang * Math.PI / 180; // 0 = hanging down, 90 = straight out to that side, 160 = raised
    const ex = ax + side * Math.sin(r) * L, ey = ay + Math.cos(r) * L;
    return { d: line(ax, ay, ex, ey, cloth, 24) + circ(ex, ey, 13, skin), ex, ey };
  };
  const aL = arm(-1, armL), aR = arm(1, armR);
  // head
  let hd = circ(0, headY, headR, skin);
  hd += circ(-headR + 4, headY + 6, 13, skin) + circ(headR - 4, headY + 6, 13, skin); // ears
  if (hair === 'short') hd += path(`M${-headR} ${headY - 4} Q${-headR} ${headY - headR - 14} 0 ${headY - headR - 10} Q${headR} ${headY - headR - 14} ${headR} ${headY - 4} Q${headR * .6} ${headY - headR * .55} 0 ${headY - headR * .6} Q${-headR * .6} ${headY - headR * .55} ${-headR} ${headY - 4} Z`, hairColor);
  if (hair === 'bun') hd += path(`M${-headR} ${headY} Q${-headR - 4} ${headY - headR - 10} 0 ${headY - headR - 6} Q${headR + 4} ${headY - headR - 10} ${headR} ${headY} Q${headR * .5} ${headY - headR * .5} 0 ${headY - headR * .5} Q${-headR * .5} ${headY - headR * .5} ${-headR} ${headY} Z`, hairColor) + circ(0, headY - headR - 18, 24, hairColor);
  if (hair === 'shikha') hd += path(`M${-headR * .55} ${headY - headR * .8} Q0 ${headY - headR - 8} ${headR * .55} ${headY - headR * .8}`, 'none', hairColor, 10) + path(`M0 ${headY - headR} q14 -30 -6 -46`, 'none', hairColor, 9);
  if (hair === 'bald') hd += '';
  if (turban) hd += path(`M${-headR - 6} ${headY - 8} Q${-headR - 10} ${headY - headR - 40} 0 ${headY - headR - 36} Q${headR + 10} ${headY - headR - 40} ${headR + 6} ${headY - 8} Q0 ${headY - headR * .45} ${-headR - 6} ${headY - 8} Z`, turban) + path(`M${-headR + 6} ${headY - 30} Q0 ${headY - headR - 4} ${headR - 6} ${headY - 34}`, 'none', 'rgba(0,0,0,.18)', 7) + circ(0, headY - headR - 8, 9, PAL.gold);
  // face
  const ex = 22, ey = headY + 2, lx = look * 6;
  const eyeOpen = 1 - clamp(blink);
  const F = {
    neutral: () => circ(-ex + lx, ey, 7 * eyeOpen + .5, PAL.ink) + circ(ex + lx, ey, 7 * eyeOpen + .5, PAL.ink) + path(`M-14 ${ey + 26} Q0 ${ey + 34} 14 ${ey + 26}`, 'none', PAL.ink, 5),
    happy: () => path(`M${-ex - 9 + lx} ${ey + 2} Q${-ex + lx} ${ey - 9} ${-ex + 9 + lx} ${ey + 2}`, 'none', PAL.ink, 6) + path(`M${ex - 9 + lx} ${ey + 2} Q${ex + lx} ${ey - 9} ${ex + 9 + lx} ${ey + 2}`, 'none', PAL.ink, 6) + path(`M-20 ${ey + 22} Q0 ${ey + 44} 20 ${ey + 22} Z`, '#5a1e2e') + circ(-38, ey + 20, 9, '#ff6b81', 'opacity=".45"') + circ(38, ey + 20, 9, '#ff6b81', 'opacity=".45"'),
    scared: () => circ(-ex + lx, ey, 12, '#fff') + circ(ex + lx, ey, 12, '#fff') + circ(-ex + lx, ey, 5, PAL.ink) + circ(ex + lx, ey, 5, PAL.ink) + path(`M${-ex - 12} ${ey - 22} L${-ex + 10} ${ey - 30}`, 'none', PAL.ink, 5) + path(`M${ex + 12} ${ey - 22} L${ex - 10} ${ey - 30}`, 'none', PAL.ink, 5) + `<ellipse cx="0" cy="${ey + 32}" rx="12" ry="15" fill="#5a1e2e"/>`,
    surprised: () => circ(-ex + lx, ey, 9, PAL.ink) + circ(ex + lx, ey, 9, PAL.ink) + path(`M${-ex - 10} ${ey - 24} Q${-ex} ${ey - 32} ${-ex + 10} ${ey - 24}`, 'none', PAL.ink, 5) + path(`M${ex - 10} ${ey - 24} Q${ex} ${ey - 32} ${ex + 10} ${ey - 24}`, 'none', PAL.ink, 5) + circ(0, ey + 30, 10, '#5a1e2e'),
    sad: () => circ(-ex + lx, ey + 2, 7, PAL.ink) + circ(ex + lx, ey + 2, 7, PAL.ink) + path(`M${-ex - 10} ${ey - 16} L${-ex + 10} ${ey - 22}`, 'none', PAL.ink, 5) + path(`M${ex + 10} ${ey - 16} L${ex - 10} ${ey - 22}`, 'none', PAL.ink, 5) + path(`M-14 ${ey + 34} Q0 ${ey + 24} 14 ${ey + 34}`, 'none', PAL.ink, 5),
    calm: () => path(`M${-ex - 9} ${ey} Q${-ex} ${ey + 7} ${-ex + 9} ${ey}`, 'none', PAL.ink, 5) + path(`M${ex - 9} ${ey} Q${ex} ${ey + 7} ${ex + 9} ${ey}`, 'none', PAL.ink, 5) + path(`M-14 ${ey + 26} Q0 ${ey + 36} 14 ${ey + 26}`, 'none', PAL.ink, 5),
    proud: () => path(`M${-ex - 9} ${ey} L${-ex + 9} ${ey}`, 'none', PAL.ink, 6) + path(`M${ex - 9} ${ey} L${ex + 9} ${ey}`, 'none', PAL.ink, 6) + path(`M-6 ${ey + 28} Q10 ${ey + 34} 20 ${ey + 22}`, 'none', PAL.ink, 5),
    angry: () => circ(-ex + lx, ey + 2, 7, PAL.ink) + circ(ex + lx, ey + 2, 7, PAL.ink) + path(`M${-ex - 12} ${ey - 24} L${-ex + 10} ${ey - 14}`, 'none', PAL.ink, 6) + path(`M${ex + 12} ${ey - 24} L${ex - 10} ${ey - 14}`, 'none', PAL.ink, 6) + path(`M-16 ${ey + 32} Q0 ${ey + 22} 16 ${ey + 32}`, 'none', PAL.ink, 6),
  };
  hd += (F[face] || F.neutral)();
  if (beard) hd += path(`M${-headR + 8} ${headY + 10} Q${-headR + 4} ${headY + headR + 60} 0 ${headY + headR + 74} Q${headR - 4} ${headY + headR + 60} ${headR - 8} ${headY + 10} Q${headR * .4} ${headY + 46} 0 ${headY + 46} Q${-headR * .4} ${headY + 46} ${-headR + 8} ${headY + 10} Z`, beard === true ? '#f1f1f1' : beard) + path(`M-20 ${headY + 30} Q0 ${headY + 22} 20 ${headY + 30}`, 'none', beard === true ? '#ddd' : beard, 8);
  if (sweat > 0) hd += g(path(`M${headR - 4} ${headY - 30} q10 18 0 26 q-10 -8 0 -26 Z`, '#8fd3ff'), `translate(0 ${(sweat * 40) % 40})`, .9);
  const pr = prop ? g(prop, `translate(${propHand === 'R' ? aR.ex : aL.ex} ${propHand === 'R' ? aR.ey : aL.ey})`) : '';
  s = g(s + aL.d + aR.d + pr + g(hd, `rotate(${lean * .5} 0 ${shY})`), `rotate(${lean} 0 0)`);
  return g(s, `translate(${x} ${y + bob}) scale(${flip ? -sc : sc} ${sc})`, op);
}

// props (drawn at hand position)
const P = {
  lamp: (t, on = 1) => path('M-26 0 Q0 26 26 0 Z', PAL.gold) + path(`M0 -2 q-10 -20 0 -${34 + Math.sin(t * 18) * 5} q10 14 0 ${34 + Math.sin(t * 18) * 5}`, '#ffef9a', 'none', 0, `opacity="${on}"`) + glow(0, -16, 230, 'W', on * .8),
  stick: () => line(0, 0, 0, -170, '#7a4b2a', 12) ,
  cow: () => '',
};

// ---------- speech bubble ----------
function bubble(x, y, str, k, o = {}) {
  const { w = 560, size = 50, tail = 'left', fill = '#fff', color = PAL.ink } = o;
  const lines = wrap(str, Math.floor(w / (size * .5)));
  const h = lines.length * size * 1.15 + 50;
  const tx = tail === 'left' ? x - w / 2 + 70 : tail === 'right' ? x + w / 2 - 70 : x;
  let s = rect(x - w / 2, y - h, w, h, fill, 36) + path(`M${tx - 26} ${y - 4} L${tx + (tail === 'right' ? 34 : -34)} ${y + 46} L${tx + 26} ${y - 4} Z`, fill);
  lines.forEach((ln, i) => s += text(x, y - h + 25 + size * .95 + i * size * 1.15, ln, { size, fill: color, weight: 700 }));
  return pop(s, tx, y + 40, E.back(clamp(k)));
}
function wrap(str, n) {
  const ws = str.split(' '); const out = []; let cur = '';
  for (const w of ws) { if ((cur + ' ' + w).trim().length > n) { out.push(cur.trim()); cur = w; } else cur += ' ' + w; }
  if (cur.trim()) out.push(cur.trim()); return out;
}

// ---------- captions (karaoke chunks) ----------
// Split each spoken line into chunks of a few words; show one chunk at a time, highlighting words as spoken.
function chunkLine(txt) {
  const ws = txt.split(/\s+/).filter(Boolean); const chunks = []; let cur = [];
  for (const w of ws) {
    cur.push(w);
    const len = cur.join(' ').length;
    if (len >= 16 || /[.!?,:;—]$/.test(w) && len >= 8 || cur.length >= 5) { chunks.push(cur); cur = []; }
  }
  if (cur.length) { if (chunks.length && cur.join(' ').length < 7) chunks[chunks.length - 1].push(...cur); else chunks.push(cur); }
  return chunks;
}
function captions(t, TL, y = 1480) {
  const L = TL.lines.find(l => t >= l.start && t < l.start + l.dur + l.pause);
  if (!L || L.nocap) return '';
  const chunks = chunkLine(L.text);
  const total = chunks.reduce((a, c) => a + c.join(' ').length + 1, 0);
  const lt = clamp((t - L.start) / L.dur) * total;
  let acc = 0, ci = 0, cstart = 0;
  for (let i = 0; i < chunks.length; i++) { const n = chunks[i].join(' ').length + 1; if (lt < acc + n || i === chunks.length - 1) { ci = i; cstart = acc; break; } acc += n; }
  const ch = chunks[ci];
  const since = (lt - cstart) / total * L.dur;
  const k = E.back(clamp(since / .22));
  // word highlight
  let pos = cstart, spans = '';
  ch.forEach((w, i) => {
    const on = lt >= pos;
    const col = on ? (L.color || PAL.gold) : '#ffffff';
    spans += `<tspan fill="${col}">${esc(w)}${i < ch.length - 1 ? ' ' : ''}</tspan>`;
    pos += w.length + 1;
  });
  const str = ch.join(' ');
  const size = str.length > 18 ? 84 : 96;
  const tx = `<text x="540" y="${y}" font-family="'Baloo 2'" font-size="${size}" font-weight="800" text-anchor="middle" stroke="#120a26" stroke-width="16" paint-order="stroke" stroke-linejoin="round">${spans}</text>`;
  return pop(tx, 540, y - 30, k);
}

// ---------- chrome: series tag, progress, episode title ----------
function chrome(t, EP, TL) {
  const p = clamp(t / TL.total);
  let s = rect(0, 0, W, 10, 'rgba(255,255,255,.15)') + rect(0, 0, W * p, 10, PAL.saffron);
  s += g(rect(330, 150, 420, 64, 'rgba(18,10,38,.55)', 32) + text(540, 196, `WHO AM I?  ·  EP ${EP.num}`, { size: 38, fill: PAL.gold, ls: 3 }), '', .92);
  return s;
}

// ---------- water ----------
function waveBand(y, amp, t, fill, o = {}) {
  const { len = 260, speed = 1, x0 = 0, x1 = W, bottom = H, ph = 0 } = o;
  let d = `M${x0} ${bottom} L${x0} ${y}`;
  for (let x = x0; x <= x1; x += 20) d += ` L${x} ${(y + amp * Math.sin((x / len) * 6.283 + t * speed + ph) + amp * .35 * Math.sin((x / (len * .43)) * 6.283 - t * speed * 1.3 + ph)).toFixed(1)}`;
  return path(d + ` L${x1} ${bottom} Z`, fill);
}

// ---------- shared end card ----------
function endCard(lt, at, nextTitle, art = '') {
  const k = tw(lt, .1, .6, E.back), kf = tw(lt, at(1) + .4, .5, E.back);
  return sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + stars(lt, 50, 31, 1200, .6) + glow(540, 1000, 600, 'W', .18) +
    pop(text(540, 470, 'NEXT EPISODE', { size: 56, fill: PAL.saffron, ls: 8 }) + text(540, 590, nextTitle, { size: nextTitle.length > 20 ? 80 : nextTitle.length > 16 ? 94 : 112, fill: PAL.cream, stroke: '#0b0b2b', sw: 10 }), 540, 520, k) +
    art + pop(g(rect(330, 1190, 420, 110, PAL.red, 55) + text(540, 1263, 'FOLLOW', { size: 64, fill: '#fff', ls: 4 })), 540, 1245, kf);
}
// a simple lotus, nice for title moments
function lotus(x, y, s = 1, op = 1, t = 0) {
  let p = '';
  const pet = (rot, c, len) => `<path d="M0 0 Q${-34} ${-len * .55} 0 ${-len} Q34 ${-len * .55} 0 0 Z" fill="${c}" transform="rotate(${rot})"/>`;
  [-70, 70, -48, 48].forEach((r, i) => p += pet(r, i < 2 ? '#e76f8a' : '#f497b0', 120));
  [-24, 24, 0].forEach((r, i) => p += pet(r, i < 2 ? '#ffb3c6' : '#ffd6e0', 140));
  return g(glow(0, -60, 260, 'W', .4 + .1 * Math.sin(t * 2)) + p + `<ellipse cx="0" cy="8" rx="120" ry="18" fill="#2a9d8f"/>`, `translate(${x} ${y}) scale(${s})`, op);
}
