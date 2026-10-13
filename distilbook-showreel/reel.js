/* DistilBook — 40s motion showreel.
 * Every frame is a pure function of time t (seconds), so any frame can be
 * rendered independently (parallel rendering, scrubbing, motion-blur sampling).
 * 1920x1080 @ 30fps, 120 BPM: beat = 0.5s, bar = 2s. Cuts land on the grid.
 */
'use strict';

const W = 1920, H = 1080, FPS = 30, DUR = 40;
const C = {
  ink: '#0A0A14', ink2: '#0E0E1C', card: '#17172B', line: 'rgba(255,255,255,0.09)',
  paper: '#F5F0E6', amber: '#FF6B2C', amber2: '#FFB547', violet: '#7B5CFF',
  mint: '#2BE4A7', sky: '#4CC9F0', pink: '#FF4D8D', gray: '#8A8AA3',
  red: '#E5484D', blue: '#3B82F6', dark: '#1A1A2E',
};
const FALLBACK = '"DejaVu Sans", "WenQuanYi Zen Hei", "IPAGothic", "FreeSerif", sans-serif';
const F = (w, s, fam = 'Inter Display') => `${w} ${s}px "${fam}", "Inter", ${FALLBACK}`;
const MONO = (s, w = 400) => `${w} ${s}px "DejaVu Sans Mono", monospace`;

/* ---------- math ---------- */
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const P = (t, a, b) => clamp((t - a) / (b - a));
const TAU = Math.PI * 2;
const E = {
  lin: t => t,
  inQuad: t => t * t,
  outQuad: t => 1 - (1 - t) * (1 - t),
  inCubic: t => t * t * t,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outQuint: t => 1 - Math.pow(1 - t, 5),
  inOutQuint: t => (t < 0.5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2),
  inExpo: t => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
  outExpo: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  outElastic: t => t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1,
};
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
function rng(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const mix = (c1, c2, t) => {
  const a = hex(c1), b = hex(c2);
  return `rgb(${Math.round(lerp(a[0], b[0], t))},${Math.round(lerp(a[1], b[1], t))},${Math.round(lerp(a[2], b[2], t))})`;
};
function hex(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
const rgba = (h, a) => { const [r, g, b] = hex(h); return `rgba(${r},${g},${b},${a})`; };

/* ---------- drawing primitives ---------- */
function rr(c, x, y, w, h, r) {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  c.beginPath();
  c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function bg(c, col) { c.fillStyle = col; c.fillRect(0, 0, W, H); }
function dotGrid(c, t, col, a, sp = 48, drift = 12) {
  c.save(); c.fillStyle = rgba(col, a);
  const ox = (t * drift) % sp, oy = (t * drift * 0.5) % sp;
  for (let y = -sp + oy; y < H + sp; y += sp) for (let x = -sp + ox; x < W + sp; x += sp) c.fillRect(x - 1.5, y - 1.5, 3, 3);
  c.restore();
}
function glow(c, x, y, r, col, a = 1) {
  const g = c.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0));
  c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
}
function drop(c, x, y, r, col, stretch = 1) {
  // teardrop pointing up
  c.save(); c.translate(x, y); c.scale(1 / Math.sqrt(stretch), stretch);
  c.beginPath();
  c.moveTo(0, -r * 1.9);
  c.bezierCurveTo(r * 0.35, -r * 1.2, r, -r * 0.55, r, 0);
  c.arc(0, 0, r, 0, Math.PI, false);
  c.bezierCurveTo(-r, -r * 0.55, -r * 0.35, -r * 1.2, 0, -r * 1.9);
  c.fillStyle = col; c.fill(); c.restore();
}

/* Kinetic type: per-glyph masked rise-in / rise-out. */
function kin(c, str, x, y, o = {}) {
  const size = o.size || 100, fam = o.fam || 'Inter Display';
  c.save();
  c.font = o.font || F(o.weight || 800, size, fam);
  c.textBaseline = 'alphabetic';
  const tr = (o.track || 0) * size;
  const chars = [...str];
  const ws = chars.map(ch => c.measureText(ch).width + tr);
  const total = ws.reduce((a, b) => a + b, 0) - tr;
  const sx = o.align === 'left' ? x : o.align === 'right' ? x - total : x - total / 2;
  const n = chars.length, st = o.stagger ?? 0.05, span = 1 + st * (n - 1);
  const pin = o.p ?? 1, pout = o.out ?? 0;
  if (!o.noclip) { c.beginPath(); c.rect(sx - size, y - size * 1.02, total + size * 2, size * 1.34); c.clip(); }
  let cx = sx;
  for (let i = 0; i < n; i++) {
    const li = (o.ein || E.outExpo)(clamp(pin * span - i * st));
    const lo = E.inExpo(clamp(pout * span - i * st));
    const dy = (1 - li) * size * 1.15 - lo * size * 1.15;
    if (li > 0 && lo < 1) {
      const col = typeof o.color === 'function' ? o.color(i, chars[i]) : (o.color || C.paper);
      if (o.stroke) { c.strokeStyle = col; c.lineWidth = o.lw || 3; c.strokeText(chars[i], cx, y + dy); }
      else { c.fillStyle = col; c.fillText(chars[i], cx, y + dy); }
    }
    cx += ws[i];
  }
  c.restore();
  return { x: sx, w: total };
}
function measure(c, str, font) { c.save(); c.font = font; const w = c.measureText(str).width; c.restore(); return w; }

/* Hand-drawn polyline with 12fps "boil", drawn up to fraction `prog`. Returns pen tip. */
function sketch(c, pts, prog, o = {}) {
  if (prog <= 0) return null;
  const amp = o.amp ?? 2.2, boil = Math.floor((o.t || 0) * 8), seed = o.seed || 0;
  const q = pts.map((p, i) => [
    p[0] + (hash(i * 7.1 + boil * 13.3 + seed) - 0.5) * amp * 2,
    p[1] + (hash(i * 3.7 + boil * 17.9 + seed + 50) - 0.5) * amp * 2,
  ]);
  const L = [0];
  for (let i = 1; i < q.length; i++) L.push(L[i - 1] + Math.hypot(q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]));
  const target = L[L.length - 1] * clamp(prog);
  c.beginPath(); c.moveTo(q[0][0], q[0][1]);
  let tip = q[0];
  for (let i = 1; i < q.length; i++) {
    if (L[i] <= target) { c.lineTo(q[i][0], q[i][1]); tip = q[i]; }
    else {
      const f = (target - L[i - 1]) / (L[i] - L[i - 1] || 1);
      tip = [lerp(q[i - 1][0], q[i][0], f), lerp(q[i - 1][1], q[i][1], f)];
      c.lineTo(tip[0], tip[1]); break;
    }
  }
  c.strokeStyle = o.color || C.dark; c.lineWidth = o.lw || 5; c.lineCap = 'round'; c.lineJoin = 'round';
  if (o.alpha != null) c.globalAlpha = o.alpha;
  c.stroke(); c.globalAlpha = 1;
  return tip;
}
const linePts = (x1, y1, x2, y2, n = 14) => Array.from({ length: n + 1 }, (_, i) => [lerp(x1, x2, i / n), lerp(y1, y2, i / n)]);
const circPts = (cx, cy, rx, ry = rx, n = 64, a0 = -Math.PI / 2, over = 1.08) =>
  Array.from({ length: n + 1 }, (_, i) => { const a = a0 + TAU * over * i / n; return [cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]; });
const rectPts = (x, y, w, h, n = 6) => [...linePts(x, y, x + w, y, n), ...linePts(x + w, y, x + w, y + h, n).slice(1),
  ...linePts(x + w, y + h, x, y + h, n).slice(1), ...linePts(x, y + h, x, y + 4, n).slice(1)];

/* A document "page" icon centred on (0,0). */
function docShape(c, w, h, label, col, seed, opts = {}) {
  const fold = w * 0.2;
  c.save();
  c.shadowColor = 'rgba(10,10,20,0.25)'; c.shadowBlur = opts.shadow ?? 30; c.shadowOffsetY = 12;
  c.beginPath();
  c.moveTo(-w / 2, -h / 2); c.lineTo(w / 2 - fold, -h / 2); c.lineTo(w / 2, -h / 2 + fold);
  c.lineTo(w / 2, h / 2); c.lineTo(-w / 2, h / 2); c.closePath();
  c.fillStyle = opts.fill || '#FFFFFF'; c.fill();
  c.shadowColor = 'transparent';
  // fold
  c.beginPath(); c.moveTo(w / 2 - fold, -h / 2); c.lineTo(w / 2 - fold, -h / 2 + fold); c.lineTo(w / 2, -h / 2 + fold); c.closePath();
  c.fillStyle = '#DDD8CC'; c.fill();
  // badge
  const bw = w * 0.42, bh = h * 0.11;
  rr(c, -w / 2 + w * 0.1, -h / 2 + h * 0.1, bw, bh, bh * 0.25); c.fillStyle = col; c.fill();
  c.fillStyle = '#fff'; c.font = F(800, bh * 0.62, 'Inter'); c.textBaseline = 'middle'; c.textAlign = 'center';
  c.fillText(label, -w / 2 + w * 0.1 + bw / 2, -h / 2 + h * 0.1 + bh / 2 + 1);
  // text lines
  c.fillStyle = '#D9D4C8';
  for (let i = 0; i < 7; i++) {
    const lw = (0.55 + hash(seed * 9 + i) * 0.25) * w;
    rr(c, -w / 2 + w * 0.1, -h / 2 + h * 0.32 + i * h * 0.085, lw * (i === 6 ? 0.5 : 1), h * 0.032, 3); c.fill();
  }
  c.restore();
}

/* ============================================================
 * SCENE 1 — Cold open (0 – 4.0)
 * ============================================================ */
const splash = (() => { const r = rng(7); return Array.from({ length: 70 }, () => ({ a: -Math.PI / 2 + (r() - 0.5) * 2.6, v: 300 + r() * 900, s: 2 + r() * 7 })); })();
function sIntro(c, t) {
  bg(c, C.ink);
  dotGrid(c, t, C.paper, 0.05 * P(t, 0, 1));
  const imp = 1.0;
  if (t < imp) {
    const p = E.inQuad(P(t, 0.15, imp));
    const y = lerp(-120, 540, p);
    glow(c, 960, y, 140, C.amber, 0.25 * p);
    c.strokeStyle = rgba(C.amber, 0.25); c.lineWidth = 2;
    c.beginPath(); c.moveTo(960, y - 40 - 300 * p); c.lineTo(960, y - 40); c.stroke();
    drop(c, 960, y, 22, C.amber, 1 + p * 0.6);
  } else {
    const dt = t - imp;
    for (let k = 0; k < 4; k++) {
      const rt = dt - k * 0.13; if (rt <= 0) continue;
      const q = clamp(rt / 1.6);
      c.beginPath(); c.ellipse(960, 540, E.outExpo(q) * (1100 - k * 160), E.outExpo(q) * (1100 - k * 160) * 0.98, 0, 0, TAU);
      c.strokeStyle = rgba(k % 2 ? C.paper : C.amber, (1 - q) * 0.9); c.lineWidth = 10 * (1 - q) + 1; c.stroke();
    }
    for (const s of splash) {
      const q = dt; if (q > 1.3) break;
      const x = 960 + Math.cos(s.a) * s.v * q, y = 540 + Math.sin(s.a) * s.v * q + 0.5 * 2400 * q * q;
      c.globalAlpha = clamp(1 - q / 1.3); c.fillStyle = C.amber;
      c.beginPath(); c.arc(x, y, s.s, 0, TAU); c.fill();
    }
    c.globalAlpha = 1;
    glow(c, 960, 540, 500, C.amber, 0.5 * Math.exp(-dt * 4));
  }
  // "312 pages."
  const n = Math.round(312 * E.outExpo(P(t, 1.02, 1.7)));
  kin(c, `${n} pages.`, 960, 600, { size: 240, weight: 900, p: P(t, 1.02, 1.55), out: P(t, 2.0, 2.3), stagger: 0.04 });
  kin(c, '// the problem', 960, 360, { font: MONO(30), color: C.gray, p: P(t, 1.1, 1.5), out: P(t, 2.0, 2.25), track: 0.1 });
  kin(c, 'Nobody reads them.', 960, 600, { size: 180, weight: 900, color: C.amber, p: P(t, 2.05, 2.55), out: P(t, 3.15, 3.45), stagger: 0.03 });
  // strike-through on the beat
  if (t > 2.5 && t < 3.45) {
    const p = E.outExpo(P(t, 2.5, 2.75)), w = 1500;
    c.fillStyle = C.paper; c.globalAlpha = 1 - P(t, 3.1, 3.4);
    c.fillRect(960 - w / 2, 545, w * p, 14); c.globalAlpha = 1;
  }
}

/* ============================================================
 * SCENE 2 — The pile (3.5 – 8.0) : paper world
 * ============================================================ */
const DOC_TYPES = [['PDF', C.red], ['DOCX', C.blue], ['MD', C.dark], ['URL', C.violet], ['PNG', '#14B88A'], ['TXT', C.gray], ['PROMPT', C.amber]];
const docs = (() => {
  const r = rng(42);
  return Array.from({ length: 18 }, (_, i) => {
    const ty = DOC_TYPES[i % DOC_TYPES.length];
    return {
      t0: 4.0 + i * 0.125, x: 1080 + r() * 620, y: 380 + r() * 420 - i * 6, rot: (r() - 0.5) * 0.6,
      rot0: (r() - 0.5) * 2.2, s: 0.75 + r() * 0.35, label: ty[0], col: ty[1], seed: i, x0: 960 + (r() - 0.5) * 1600,
    };
  });
})();
const WORDS = ['Research papers.', 'Training manuals.', 'SOPs.', 'Pitch decks.', 'Textbooks.', 'Onboarding docs.'];
function sPile(c, t) {
  bg(c, C.paper);
  // faint ruled lines
  c.strokeStyle = 'rgba(26,26,46,0.06)'; c.lineWidth = 2;
  for (let y = 60; y < H; y += 60) { c.beginPath(); c.moveTo(0, y + (t * 20) % 60); c.lineTo(W, y + (t * 20) % 60); c.stroke(); }
  const vort = P(t, 6.9, 7.9);
  for (const d of docs) {
    const p = P(t, d.t0, d.t0 + 0.45); if (p <= 0) continue;
    const e = E.outBack(p, 1.4);
    let x = lerp(d.x0, d.x, E.outCubic(p)), y = lerp(-400, d.y, e), rot = lerp(d.rot0, d.rot, E.outCubic(p)), s = d.s;
    // idle breathing
    y += Math.sin(t * 2 + d.seed) * 4;
    if (vort > 0) {
      const v = E.inCubic(vort);
      const ang = Math.atan2(y - 600, x - 960) + v * 6;
      const rad = Math.hypot(x - 960, y - 600) * (1 - v);
      x = 960 + Math.cos(ang) * rad; y = 600 + Math.sin(ang) * rad; rot += v * 9; s *= 1 - v * 0.95;
    }
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s);
    docShape(c, 230, 300, d.label, d.col, d.seed);
    c.restore();
  }
  // Left headline column
  const out = P(t, 6.75, 7.1);
  kin(c, 'INPUT', 150, 330, { font: MONO(28, 700), color: C.amber, align: 'left', p: P(t, 4.05, 4.4), out, track: 0.3 });
  // slot machine word roll (each word holds half a beat pair)
  const slot = (t - 4.15) / 0.45, idx = Math.floor(slot), f = slot - idx;
  if (t > 4.15) {
    c.save(); c.beginPath(); c.rect(100, 380, 960, 150); c.clip();
    const roll = E.outExpo(clamp(f / 0.45));
    const fade = 1 - out;
    c.globalAlpha = fade;
    c.font = F(900, 108); c.fillStyle = C.dark; c.textBaseline = 'alphabetic';
    const cur = WORDS[Math.min(idx, WORDS.length - 1) % WORDS.length];
    const prev = WORDS[Math.max(0, Math.min(idx - 1, WORDS.length - 1))];
    if (idx >= WORDS.length) c.fillText(cur, 150, 495);
    else {
      c.fillText(cur, 150, 495 + (1 - roll) * 140);
      if (idx > 0) c.fillText(prev, 150, 495 - roll * 140);
    }
    c.restore();
  }
  kin(c, 'Long. Dense. Unread.', 150, 610, { size: 56, weight: 600, color: rgba(C.dark, 0.55), align: 'left', p: P(t, 5.0, 5.5), out });
  // Count chip
  if (t > 4.0 && out < 1) {
    const k = Math.min(docs.length, Math.floor((t - 4.0) / 0.125) + 1);
    c.save(); c.globalAlpha = 1 - out;
    rr(c, 150, 680, 330, 64, 32); c.fillStyle = C.dark; c.fill();
    c.fillStyle = C.paper; c.font = MONO(26, 700); c.textBaseline = 'middle';
    c.fillText(`files.length = ${String(k).padStart(2, '0')}`, 178, 713);
    c.restore();
  }
}

/* ============================================================
 * SCENE 3 — Distillation (7.2 – 11.0)
 * ============================================================ */
const GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789{}§¶∑∫#%&?!';
const parts = (() => {
  const r = rng(3);
  return Array.from({ length: 720 }, () => ({
    a: r() * TAU, r0: 500 + r() * 1200, t0: 7.6 + r() * 2.4, dur: 0.9 + r() * 1.1,
    ch: GLYPHS[Math.floor(r() * GLYPHS.length)], s: 14 + r() * 26, spin: (r() < 0.5 ? 1 : 1) * (2 + r() * 3),
  }));
})();
function sDistill(c, t) {
  bg(c, C.ink);
  const cx = 960, cy = 540;
  const implode = E.inExpo(P(t, 10.55, 11.0));
  glow(c, cx, cy, 700, C.violet, 0.16 * P(t, 7.6, 9));
  // particles
  c.textAlign = 'center'; c.textBaseline = 'middle';
  for (const p of parts) {
    const q = P(t, p.t0, p.t0 + p.dur);
    if (q >= 1) continue;
    const e = E.inCubic(q);
    const rad = p.r0 * (1 - e) * (1 - implode);
    const ang = p.a + p.spin * e + t * 0.4;
    const x = cx + Math.cos(ang) * rad, y = cy + Math.sin(ang) * rad * 0.82;
    c.globalAlpha = clamp(q * 6) * (1 - implode);
    c.fillStyle = mix(C.paper, C.amber, e);
    c.font = F(700, Math.max(4, p.s * (1 - e * 0.8)), 'Inter');
    c.fillText(p.ch, x, y);
  }
  c.globalAlpha = 1; c.textAlign = 'left';
  // rings
  const ringIn = E.outExpo(P(t, 7.7, 8.6)) * (1 - implode);
  const rings = [[170, 1, 26, C.amber], [250, -0.6, 60, C.paper], [350, 0.35, 120, C.violet], [470, -0.2, 8, C.paper]];
  rings.forEach(([R, sp, dash, col], i) => {
    const r = R * ringIn * (1 + 0.04 * Math.sin(t * 4 * TAU / 4 + i));
    if (r <= 1) return;
    c.save(); c.translate(cx, cy); c.rotate(t * sp);
    c.setLineDash(i === 3 ? [2, 14] : [dash, dash * 0.5]); c.lineWidth = i === 3 ? 3 : 2.5;
    c.strokeStyle = rgba(col, 0.75); c.beginPath(); c.arc(0, 0, r, 0, TAU); c.stroke();
    c.setLineDash([]);
    // tick
    c.fillStyle = col; c.beginPath(); c.arc(r, 0, 6, 0, TAU); c.fill();
    c.restore();
  });
  // core
  const grow = E.outCubic(P(t, 8.2, 10.4));
  const pulse = 1 + 0.08 * Math.sin(t * TAU * 2);
  const coreR = (14 + 46 * grow) * pulse * (1 - implode * 0.85);
  glow(c, cx, cy, coreR * 6, C.amber, 0.55);
  c.beginPath(); c.arc(cx, cy, coreR, 0, TAU); c.fillStyle = C.amber2; c.fill();
  c.beginPath(); c.arc(cx, cy, coreR * 0.55, 0, TAU); c.fillStyle = '#FFF4E0'; c.fill();
  // HUD
  const pct = Math.round(100 * E.inOutCubic(P(t, 8.0, 10.5)));
  const hud = P(t, 7.9, 8.3) * (1 - P(t, 10.5, 10.8));
  c.save(); c.globalAlpha = hud;
  c.font = MONO(26, 700); c.fillStyle = C.gray; c.fillText('DISTILLING', 660, 960);
  rr(c, 860, 942, 330, 22, 11); c.fillStyle = 'rgba(255,255,255,0.08)'; c.fill();
  rr(c, 860, 942, 330 * pct / 100, 22, 11); c.fillStyle = C.amber; c.fill();
  c.fillStyle = C.paper; c.fillText(`${String(pct).padStart(3, ' ')}%`, 1210, 960);
  c.font = MONO(22); c.fillStyle = rgba(C.paper, 0.4);
  c.fillText('read → understand → script → draw → narrate', 660, 1010);
  c.restore();
  kin(c, 'We read it.', 960, 170, { size: 92, weight: 800, p: P(t, 8.1, 8.6), out: P(t, 9.4, 9.7) });
  kin(c, 'So nobody has to.', 960, 170, { size: 92, weight: 800, color: C.amber, p: P(t, 9.55, 10.05), out: P(t, 10.5, 10.75) });
}

/* ============================================================
 * SCENE 4 — Logo slam (11.0 – 15.0)
 * ============================================================ */
function wordmark(c, x, y, size, p, opts = {}) {
  const font = F(900, size);
  const full = 'DistilBook';
  const w = measure(c, full, font);
  const sx = x - w / 2;
  c.save(); c.font = font; c.textBaseline = 'alphabetic';
  let cx = sx;
  [...full].forEach((ch, i) => {
    const cw = c.measureText(ch).width;
    const q = clamp(p * 1.45 - i * 0.05);
    if (q > 0) {
      const s = E.outBack(q, 2.2);
      const col = i < 6 ? C.paper : C.amber;
      c.save(); c.translate(cx + cw / 2, y - size * 0.35); c.scale(s, s); c.rotate((1 - E.outCubic(q)) * (i % 2 ? 0.4 : -0.4));
      if (opts.split > 0) {
        c.globalCompositeOperation = 'lighter';
        c.fillStyle = 'rgba(0,220,255,0.8)'; c.fillText(ch, -cw / 2 - opts.split, size * 0.35);
        c.fillStyle = 'rgba(255,40,120,0.8)'; c.fillText(ch, -cw / 2 + opts.split, size * 0.35);
        c.globalCompositeOperation = 'source-over';
      }
      c.fillStyle = col; c.fillText(ch, -cw / 2, size * 0.35);
      if (opts.shine != null) {
        const gx = opts.shine - (cx + cw / 2);
        const g = c.createLinearGradient(gx - 160, 0, gx + 160, 0);
        g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,255,255,0.85)'); g.addColorStop(1, 'rgba(255,255,255,0)');
        c.globalCompositeOperation = 'lighter'; c.fillStyle = g; c.fillText(ch, -cw / 2, size * 0.35); c.globalCompositeOperation = 'source-over';
      }
      c.restore();
    }
    cx += cw;
  });
  c.restore();
  return { sx, w, font };
}
function sLogo(c, t) {
  bg(c, C.ink);
  const cx = 960, cy = 470;
  // sunburst
  c.save(); c.translate(cx, cy); c.rotate(t * 0.15);
  const burst = E.outExpo(P(t, 11.0, 11.8));
  for (let i = 0; i < 36; i++) {
    c.rotate(TAU / 36);
    if (i % 2) continue;
    c.beginPath(); c.moveTo(0, 0); c.lineTo(1600 * burst, -70 * burst); c.lineTo(1600 * burst, 70 * burst); c.closePath();
    c.fillStyle = 'rgba(255,255,255,0.025)'; c.fill();
  }
  c.restore();
  // beat rings (every 0.5s)
  for (let b = 11.0; b <= t; b += 0.5) {
    const q = clamp((t - b) / 1.2); if (q >= 1) continue;
    c.beginPath(); c.arc(cx, cy, 180 + E.outCubic(q) * 900, 0, TAU);
    c.strokeStyle = rgba(C.amber, 0.35 * (1 - q)); c.lineWidth = 3; c.stroke();
  }
  glow(c, cx, cy, 800, C.violet, 0.18);
  // zoom-through
  const zp = E.inExpo(P(t, 14.25, 15.0));
  const size = 250;
  const font = F(900, size);
  const full = measure(c, 'DistilBook', font);
  const preO = measure(c, 'DistilB', font), oW = measure(c, 'o', font);
  const zx = cx - full / 2 + preO + oW * 0.11, zy = cy + size * 0.35 - size * 0.27;
  const z = Math.exp(lerp(0, Math.log(90), zp));
  c.save();
  c.translate(zx, zy); c.scale(z, z); c.translate(-zx, -zy);
  const split = 26 * Math.exp(-(t - 11.0) * 7);
  wordmark(c, cx, cy + size * 0.35, size, P(t, 11.0, 11.9), { split });
  // hovering drop over the "i" of Distil
  const iX = cx - full / 2 + measure(c, 'Dist', font) + measure(c, 'i', font) / 2;
  const dp = E.outElastic(P(t, 11.4, 12.4));
  if (dp > 0) {
    const bob = Math.sin(t * Math.PI * 2) * 6;
    glow(c, iX, cy - 190 + bob, 70, C.amber, 0.5 * dp);
    drop(c, iX, cy - 175 + bob - (1 - dp) * 120, 18 * dp, C.amber);
  }
  c.restore();
  if (zp > 0.55) { c.fillStyle = rgba(C.amber, E.inExpo(P(zp, 0.55, 1))); c.fillRect(0, 0, W, H); }
  // tagline
  const fade = 1 - P(t, 14.05, 14.3);
  c.save(); c.globalAlpha = fade;
  const tl = kin(c, 'Any document', 700, 800, { size: 64, weight: 700, color: C.paper, p: P(t, 12.4, 12.8), align: 'right' });
  const ap = E.outExpo(P(t, 12.65, 13.05));
  c.strokeStyle = C.amber; c.lineWidth = 6; c.lineCap = 'round';
  c.beginPath(); c.moveTo(740, 778); c.lineTo(740 + 160 * ap, 778); c.stroke();
  if (ap > 0.6) { c.beginPath(); c.moveTo(900 - 22, 760); c.lineTo(902, 778); c.lineTo(900 - 22, 796); c.stroke(); }
  kin(c, 'explainer video.', 945, 800, { size: 64, weight: 700, color: C.amber, p: P(t, 12.85, 13.3), align: 'left' });
  kin(c, 'PDF · WORD · MARKDOWN · IMAGES · LINKS · PROMPTS', 960, 880, { font: MONO(24, 700), color: C.gray, p: P(t, 13.2, 13.7), track: 0.12, stagger: 0.01 });
  c.restore();
  void tl;
}

/* ============================================================
 * SCENE 5 — How it works (15.0 – 24.0)
 * ============================================================ */
const CARD = { x: 880, y: 210, w: 920, h: 660 };
const SCRIPT = [
  ['#', 'Scene 1 — Why it matters'],
  ['', 'Most teams write docs nobody reads.'],
  ['#', 'Scene 2 — The idea'],
  ['', 'Turn every page into a story you watch.'],
  ['#', 'Scene 3 — How it works'],
  ['', 'Read. Script. Draw. Narrate.'],
];
function stepText(c, t, s, e, num, title, sub, last) {
  const pin = P(t, s + 0.05, s + 0.55), out = last ? P(t, e - 0.6, e - 0.35) : P(t, e - 0.35, e - 0.05);
  // giant outlined number with fill wipe
  c.save();
  kin(c, num, 140, 420, { size: 300, weight: 900, stroke: true, lw: 3, color: rgba(C.amber, 0.9), align: 'left', p: pin, out, stagger: 0.15 });
  const fillP = E.outExpo(P(t, s + 0.4, s + 1.2));
  c.beginPath(); c.rect(100, 420 - 300 * fillP, 700, 300 * fillP + 40); c.clip();
  kin(c, num, 140, 420, { size: 300, weight: 900, color: rgba(C.amber, 0.95), align: 'left', p: pin, out, stagger: 0.15 });
  c.restore();
  kin(c, title[0], 140, 560, { size: 82, weight: 800, align: 'left', p: P(t, s + 0.15, s + 0.65), out, stagger: 0.025 });
  if (title[1]) kin(c, title[1], 140, 655, { size: 82, weight: 800, align: 'left', color: C.amber, p: P(t, s + 0.25, s + 0.75), out, stagger: 0.025 });
  kin(c, sub, 142, 740, { size: 30, weight: 500, fam: 'Inter', color: C.gray, align: 'left', p: P(t, s + 0.4, s + 0.9), out, stagger: 0.008 });
}
function cardChrome(c, label) {
  const { x, y, w, h } = CARD;
  c.save();
  c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = 80; c.shadowOffsetY = 30;
  rr(c, x, y, w, h, 28); c.fillStyle = C.card; c.fill();
  c.restore();
  rr(c, x, y, w, h, 28); c.strokeStyle = C.line; c.lineWidth = 2; c.stroke();
  ['#FF5F57', '#FEBC2E', '#28C840'].forEach((col, i) => { c.beginPath(); c.arc(x + 36 + i * 26, y + 34, 8, 0, TAU); c.fillStyle = col; c.fill(); });
  c.font = MONO(20); c.fillStyle = C.gray; c.textBaseline = 'middle'; c.fillText(label, x + 130, y + 35);
  c.fillStyle = C.line; c.fillRect(x, y + 66, w, 2);
}
function step1(c, t) {
  const { x, y, w, h } = CARD;
  cardChrome(c, 'distilbook — new video');
  const zx = x + 60, zy = y + 100, zw = w - 120, zh = h - 290;
  const landed = t > 16.35;
  const flash = landed ? Math.exp(-(t - 16.35) * 5) : 0;
  rr(c, zx, zy, zw, zh, 22);
  c.fillStyle = rgba(C.mint, 0.05 + 0.2 * flash); c.fill();
  c.setLineDash([18, 12]); c.lineDashOffset = -t * 40; c.lineWidth = 3;
  c.strokeStyle = landed ? mix('#3A3A5A', C.mint, Math.max(flash, 0.6)) : '#3A3A5A'; c.stroke(); c.setLineDash([]);
  c.textAlign = 'center'; c.textBaseline = 'middle';
  if (!landed) {
    c.font = F(600, 30, 'Inter'); c.fillStyle = C.gray; c.fillText('Drop a PDF, doc, link — or just a prompt', zx + zw / 2, zy + zh / 2 + 120);
    // arrow bob
    const b = Math.sin(t * TAU) * 8;
    c.strokeStyle = C.gray; c.lineWidth = 4; c.lineCap = 'round';
    c.beginPath(); c.moveTo(zx + zw / 2, zy + zh / 2 + 10 + b); c.lineTo(zx + zw / 2, zy + zh / 2 + 60 + b);
    c.moveTo(zx + zw / 2 - 18, zy + zh / 2 + 42 + b); c.lineTo(zx + zw / 2, zy + zh / 2 + 62 + b); c.lineTo(zx + zw / 2 + 18, zy + zh / 2 + 42 + b); c.stroke();
  }
  // flying file
  const fp = P(t, 15.75, 16.35);
  if (fp > 0) {
    const ex = zx + zw / 2, ey = zy + zh / 2 - 20;
    const e = E.inOutCubic(fp);
    const fx = lerp(560, ex, e), fy = lerp(140, ey, e) - Math.sin(e * Math.PI) * 220;
    const land = E.outElastic(P(t, 16.35, 17.0));
    const s = landed ? 1 + 0.15 * (1 - land) : 1.1;
    c.save(); c.translate(fx, fy); c.rotate(landed ? 0 : lerp(-0.6, 0.1, e)); c.scale(s * 0.62, s * 0.62);
    docShape(c, 230, 300, 'PDF', C.red, 4, { shadow: 40 });
    c.restore();
  }
  // progress
  const pp = E.inOutCubic(P(t, 16.5, 17.35));
  if (t > 16.45) {
    const py = y + h - 110;
    c.textAlign = 'left';
    c.font = MONO(22, 700); c.fillStyle = C.paper; c.fillText('research_paper.pdf', x + 60, py - 24);
    c.font = MONO(22); c.fillStyle = C.gray; c.textAlign = 'right';
    c.fillText(`42 pages · ${Math.round(pp * 100)}%`, x + w - 60, py - 24);
    rr(c, x + 60, py, w - 120, 14, 7); c.fillStyle = 'rgba(255,255,255,0.07)'; c.fill();
    rr(c, x + 60, py, (w - 120) * pp, 14, 7); c.fillStyle = C.mint; c.fill();
  }
  const bp = E.outBack(P(t, 17.35, 17.65), 2.5);
  if (bp > 0) {
    c.save(); c.translate(x + w / 2, y + 150); c.scale(bp, bp);
    rr(c, -200, -32, 400, 64, 32); c.fillStyle = C.mint; c.fill();
    c.fillStyle = C.ink; c.font = F(800, 26, 'Inter'); c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText('✓  18 key ideas found', 0, 2);
    c.restore();
  }
  c.textAlign = 'left';
}
function step2(c, t) {
  const { x, y, w, h } = CARD;
  cardChrome(c, 'script.md — review');
  const total = SCRIPT.reduce((a, l) => a + l[1].length, 0);
  let chars = Math.floor(E.lin(P(t, 18.25, 19.75)) * total);
  c.textBaseline = 'alphabetic';
  let cy = y + 140, caret = null;
  SCRIPT.forEach(([kind, text], i) => {
    c.font = MONO(22); c.fillStyle = '#4A4A6A'; c.textAlign = 'right'; c.fillText(String(i + 1), x + 70, cy);
    c.textAlign = 'left';
    const n = Math.max(0, Math.min(text.length, chars)); chars -= text.length;
    const s = (kind ? '# ' : '') + text.slice(0, n);
    c.font = kind ? MONO(26, 700) : MONO(26); c.fillStyle = kind ? C.amber : C.paper;
    if (n > 0 || i === 0) { c.fillText(s, x + 100, cy); caret = [x + 100 + c.measureText(s).width + 4, cy]; }
    cy += kind ? 56 : 72;
  });
  if (caret && Math.floor(t * 4) % 2 === 0) { c.fillStyle = C.amber; c.fillRect(caret[0], caret[1] - 26, 3, 32); }
  // Approve button
  const bx = x + w - 380, by = y + h - 110, bw = 320, bh = 68;
  const clickT = 20.35;
  const press = t > clickT ? 1 - 0.08 * Math.exp(-(t - clickT) * 12) * Math.sin(Math.min(1, (t - clickT) * 8) * Math.PI) : 1;
  const ok = t > clickT;
  c.save(); c.translate(bx + bw / 2, by + bh / 2); c.scale(press, press);
  rr(c, -bw / 2, -bh / 2, bw, bh, 18); c.fillStyle = ok ? C.mint : C.amber; c.fill();
  c.fillStyle = C.ink; c.font = F(800, 26, 'Inter'); c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillText(ok ? '✓  Script approved' : 'Approve script  →', 0, 2);
  c.restore();
  if (ok) {
    const q = clamp((t - clickT) / 0.6);
    c.beginPath(); c.arc(bx + bw / 2, by + bh / 2, 20 + 260 * E.outCubic(q), 0, TAU);
    c.strokeStyle = rgba(C.mint, 1 - q); c.lineWidth = 4; c.stroke();
  }
  c.font = MONO(20); c.fillStyle = C.gray; c.textAlign = 'left'; c.textBaseline = 'middle';
  c.fillText('Edit any line before render.', x + 60, by + bh / 2);
  // mouse cursor
  const mp = E.inOutCubic(P(t, 19.8, 20.3));
  if (mp > 0) {
    const mx = lerp(x + w + 140, bx + bw * 0.62, mp), my = lerp(y + h + 120, by + bh * 0.6, mp);
    c.save(); c.translate(mx, my); c.scale(t > clickT && t < clickT + 0.12 ? 0.85 : 1, t > clickT && t < clickT + 0.12 ? 0.85 : 1);
    c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 42); c.lineTo(11, 32); c.lineTo(19, 50); c.lineTo(26, 47); c.lineTo(18, 30); c.lineTo(32, 30); c.closePath();
    c.fillStyle = '#fff'; c.fill(); c.strokeStyle = C.ink; c.lineWidth = 2.5; c.stroke();
    c.restore();
  }
}
/* Whiteboard diagram, drawn in an arbitrary rect via transform. Design space 860x470. */
function whiteboard(c, t, t0, t1) {
  const strokes = [];
  const add = (pts, o = {}) => strokes.push({ pts, ...o });
  add(linePts(20, 92, 330, 96, 20), { lw: 6 });                                  // title underline
  const bx = [20, 250, 480, 710], bw = 150, by = 210, bh = 110;
  bx.forEach((x, i) => {
    add(rectPts(x - 10 + i * 0, by, bw + 10, bh, 8), { lw: 5, box: i });
    if (i < 3) {
      add(linePts(x + bw + 10, by + bh / 2, bx[i + 1] - 22, by + bh / 2, 8), { lw: 5 });
      add([[bx[i + 1] - 40, by + bh / 2 - 16], [bx[i + 1] - 20, by + bh / 2], [bx[i + 1] - 40, by + bh / 2 + 16]], { lw: 5 });
    }
  });
  add(circPts(770, 70, 38, 42, 40), { lw: 5 });                                  // bulb
  add([[755, 112], [758, 138], [782, 138], [785, 112]], { lw: 5 });
  [[-1.2, 60], [-0.6, 64], [0, 66], [0.6, 64], [1.2, 60]].forEach(([a, r]) =>
    add(linePts(770 + Math.sin(a) * r, 70 - Math.cos(a) * r, 770 + Math.sin(a) * (r + 22), 70 - Math.cos(a) * (r + 22), 3), { lw: 4, color: C.amber }));
  add(circPts(555, 265, 125, 82, 50, -2.6, 1.12), { lw: 14, color: rgba(C.amber, 0.55), amp: 3 }); // marker highlight
  add(linePts(20, 420, 840, 420, 3).map((p, i) => [p[0], p[1] + Math.sin(i) * 0]), { lw: 0 });     // spacer
  const total = strokes.length - 1;
  const g = P(t, t0, t1) * total;
  let tip = null;
  strokes.forEach((s, i) => {
    if (!s.lw) return;
    const pr = clamp(g - i);
    const tp = sketch(c, s.pts, pr, { lw: s.lw, color: s.color || C.dark, t, seed: i * 10, amp: s.amp ?? 1.6 });
    if (pr > 0 && pr < 1) tip = tp;
  });
  // labels
  c.fillStyle = C.dark; c.textBaseline = 'alphabetic';
  const tp = clamp(g * 1.4);
  c.save(); c.beginPath(); c.rect(0, 0, 20 + 340 * tp, 120); c.clip();
  c.font = F(800, 52); c.fillText('How it works', 20, 76); c.restore();
  ['Read', 'Script', 'Draw', 'Narrate'].forEach((l, i) => {
    const boxIdx = 1 + i * 3;
    const q = E.outBack(P(g, boxIdx + 0.6, boxIdx + 1.1));
    if (q <= 0) return;
    c.save(); c.translate(bx[i] + bw / 2 - 5, by + bh / 2 + 12); c.scale(q, q);
    c.font = F(800, 36); c.textAlign = 'center'; c.fillText(l, 0, 0); c.restore();
  });
  return tip;
}
function marker(c, x, y) {
  c.save(); c.translate(x, y); c.rotate(-0.7);
  c.fillStyle = C.dark; c.beginPath(); c.moveTo(0, 0); c.lineTo(10, -16); c.lineTo(-10, -16); c.closePath(); c.fill();
  rr(c, -14, -120, 28, 104, 6); c.fillStyle = C.amber; c.fill();
  rr(c, -14, -136, 28, 22, 6); c.fillStyle = C.dark; c.fill();
  c.restore();
}
function step3(c, t, expand) {
  const { x, y, w, h } = CARD;
  if (expand <= 0) cardChrome(c, 'render — whiteboard · 16:9');
  // board rect morphs to full screen
  const r0 = { x: x + 30, y: y + 90, w: w - 60, h: h - 200 };
  const e = E.inOutExpo(expand);
  const bxr = lerp(r0.x, 0, e), byr = lerp(r0.y, 0, e), bwr = lerp(r0.w, W, e), bhr = lerp(r0.h, H, e);
  rr(c, bxr, byr, bwr, bhr, lerp(16, 0, e)); c.fillStyle = '#FAF7F0'; c.fill();
  c.save(); rr(c, bxr, byr, bwr, bhr, lerp(16, 0, e)); c.clip();
  // fit design space 860x470 into board
  const k = Math.min(bwr / 900, bhr / 470);
  c.translate(bxr + (bwr - 860 * k) / 2, byr + (bhr - 440 * k) / 2); c.scale(k, k);
  const tip = whiteboard(c, t, 21.2, 23.2);
  if (tip && expand <= 0) marker(c, tip[0], tip[1]);
  c.restore();
  if (expand > 0) return;
  // waveform + karaoke subtitle
  const wy = y + h - 70;
  for (let i = 0; i < 40; i++) {
    const a = 0.25 + 0.75 * Math.abs(Math.sin(t * 9 + i * 0.7) * Math.sin(t * 3.3 + i * 0.31));
    c.fillStyle = rgba(C.amber, 0.8); rr(c, x + 40 + i * 9, wy - 22 * a, 5, 44 * a, 2.5); c.fill();
  }
  const words = ['Read.', 'Script.', 'Draw.', 'Narrate.'];
  c.font = F(700, 30, 'Inter'); c.textBaseline = 'middle';
  let wx = x + 440;
  words.forEach((wd, i) => {
    const on = P(t, 21.4 + i * 0.5, 21.5 + i * 0.5);
    c.fillStyle = on > 0 ? C.paper : '#4A4A6A'; c.fillText(wd, wx, wy); wx += c.measureText(wd + ' ').width;
  });
}
function sSteps(c, t) {
  bg(c, C.ink2);
  dotGrid(c, t, C.paper, 0.06);
  glow(c, 1340, 540, 900, C.violet, 0.12);
  // amber panel collapses into sidebar
  const sb = E.outExpo(P(t, 15.0, 15.7));
  c.fillStyle = C.amber; c.fillRect(0, 0, lerp(W, 14, sb), H);
  // step progress ticks on sidebar
  if (sb > 0.9) {
    [15, 18, 21].forEach((s, i) => {
      const on = t > s;
      c.fillStyle = on ? C.paper : rgba(C.paper, 0.2);
      c.fillRect(30, 400 + i * 100, 6, 70 * (on ? E.outExpo(P(t, s, s + 0.5)) : 1));
    });
  }
  if (sb < 0.4) return;
  const expand = P(t, 23.35, 24.0);
  if (expand <= 0) {
    stepText(c, t, 15.2, 18.0, '01', ['Drop in', 'anything.'], 'PDFs, scans, Word, notes, images, links.');
    stepText(c, t, 18.0, 21.0, '02', ['Approve', 'the script.'], 'You stay the editor. AI does the heavy lifting.');
    stepText(c, t, 21.0, 24.0, '03', ['Watch it', 'draw itself.'], 'Every idea illustrated, synced to narration.', true);
  }
  // card entrance + flips
  const enter = E.outExpo(P(t, 15.35, 16.0));
  const cardCX = CARD.x + CARD.w / 2, cardCY = CARD.y + CARD.h / 2;
  let sx = 1, ang = 0;
  for (const T of [18.0, 21.0]) { const f = P(t, T - 0.2, T + 0.2); if (f > 0 && f < 1) { sx = Math.abs(Math.cos(f * Math.PI)); ang = Math.sin(f * Math.PI) * 0.04; } }
  c.save();
  if (expand <= 0) {
    c.translate(cardCX, cardCY + (1 - enter) * 700); c.rotate((1 - enter) * 0.15 + ang); c.scale(sx, 1); c.translate(-cardCX, -cardCY);
  }
  if (t < 18.0) step1(c, t);
  else if (t < 21.0) step2(c, t);
  else step3(c, t, expand);
  c.restore();
}

/* ============================================================
 * SCENE 6 — 19 styles (24.0 – 30.0)
 * Style names are illustrative of the range (whiteboard + motion graphics).
 * ============================================================ */
const STYLES = [
  { n: 'Whiteboard', bg: '#FAF7F0', ink: C.dark, a1: C.amber, a2: C.dark, sketch: 1, lw: 7 },
  { n: 'Chalkboard', bg: '#23362B', ink: '#EDEDE6', a1: '#F7D774', a2: '#9ED8C3', sketch: 1, chalk: 1, lw: 7 },
  { n: 'Blueprint', bg: '#1D4E89', ink: '#FFFFFF', a1: '#9FD3FF', a2: '#FFFFFF', grid: 1, lw: 4 },
  { n: 'Neon', bg: '#08041A', ink: '#FFFFFF', a1: '#FF2E97', a2: '#22E5FF', glow: 1, lw: 6 },
  { n: 'Flat Pastel', bg: '#FFE8D6', ink: '#3D2C4E', a1: '#FF9F9F', a2: '#9AD0EC', fill: 1 },
  { n: 'Paper Cutout', bg: '#F2E3C6', ink: '#3B2A1A', a1: '#E76F51', a2: '#2A9D8F', fill: 1, shadow: 1 },
  { n: 'Comic Halftone', bg: '#FFE14D', ink: '#111111', a1: '#FF3B3B', a2: '#2E6BFF', fill: 1, half: 1, lw: 8 },
  { n: 'Pixel', bg: '#1B1B2F', ink: '#F5F0E6', a1: '#FF6B2C', a2: '#2BE4A7', pixel: 1 },
  { n: 'Ink Sketch', bg: '#F4F1EA', ink: '#222222', a1: '#222222', a2: '#555555', sketch: 2, lw: 3 },
  { n: 'Isometric', bg: '#E9F1FF', ink: '#1E2A55', a1: '#5B7CFF', a2: '#FFB547', fill: 1, iso: 1 },
  { n: 'Retro 70s', bg: '#F4E1C1', ink: '#5A2D0C', a1: '#E8702A', a2: '#C0392B', fill: 1, stripes: 1 },
  { n: 'Minimal Mono', bg: '#FFFFFF', ink: '#111111', a1: '#111111', a2: '#111111', lw: 3 },
  { n: 'Glass', bg: '#5B3BFF', bg2: '#22C1F0', ink: '#FFFFFF', a1: 'rgba(255,255,255,0.35)', a2: 'rgba(255,255,255,0.6)', fill: 1, glass: 1 },
  { n: 'Terminal', bg: '#0B0F14', ink: '#2BE4A7', a1: '#2BE4A7', a2: '#2BE4A7', lw: 3, scan: 1, mono: 1 },
  { n: 'Watercolor', bg: '#FBF8F2', ink: '#33415C', a1: '#F28482', a2: '#84A59D', fill: 1, wash: 1, lw: 3 },
  { n: 'Bauhaus', bg: '#EFE9DD', ink: '#111111', a1: '#D62828', a2: '#1D3D8F', a3: '#F2C14E', fill: 1 },
  { n: 'Duotone', bg: '#2B1055', ink: '#FF6B9D', a1: '#FF6B9D', a2: '#FF6B9D', fill: 1 },
  { n: 'Kraft Marker', bg: '#C9A57A', ink: '#1A1208', a1: '#1A1208', a2: '#FFFFFF', sketch: 1, lw: 12 },
  { n: 'Line Color', bg: '#FFFFFF', ink: '#1A1A2E', a1: '#FF6B2C', a2: '#7B5CFF', lw: 5 },
];
const patCache = {};
function halftone(c, col) {
  if (patCache[col]) return patCache[col];
  const p = document.createElement('canvas'); p.width = p.height = 22;
  const g = p.getContext('2d'); g.fillStyle = col; g.beginPath(); g.arc(11, 11, 6.5, 0, TAU); g.fill();
  return (patCache[col] = c.createPattern(p, 'repeat'));
}
const pixCan = document.createElement('canvas'); pixCan.width = 64; pixCan.height = 36;
/* Draw style s into design space 1920x1080 (caller sets transform). */
function styleArt(c, s, t, flat) {
  // background
  if (s.bg2) { const g = c.createLinearGradient(0, 0, W, H); g.addColorStop(0, s.bg); g.addColorStop(1, s.bg2); c.fillStyle = g; }
  else c.fillStyle = s.bg;
  c.fillRect(0, 0, W, H);
  if (s.pixel && !flat) {
    const g = pixCan.getContext('2d');
    g.setTransform(1, 0, 0, 1, 0, 0); g.scale(64 / W, 36 / H);
    styleArt(g, { ...s, pixel: 0, fill: 1 }, t, true);
    c.imageSmoothingEnabled = false; c.drawImage(pixCan, 0, 0, W, H); c.imageSmoothingEnabled = true;
    return;
  }
  if (s.grid) { c.strokeStyle = 'rgba(255,255,255,0.13)'; c.lineWidth = 2; for (let x = 0; x < W; x += 60) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); } for (let y = 0; y < H; y += 60) { c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); } }
  if (s.stripes) { [s.a1, s.a2, s.ink].forEach((col, i) => { c.fillStyle = col; c.fillRect(0, 760 + i * 50, W, 28); }); }
  const lw = s.lw || 5;
  const paint = (path, col, kind) => {
    // path: function that builds a path. kind: 'fill' | 'stroke'
    c.save();
    if (s.glow) { c.shadowColor = col; c.shadowBlur = 40; }
    if (s.shadow) { c.shadowColor = 'rgba(0,0,0,0.3)'; c.shadowOffsetX = 14; c.shadowOffsetY = 18; c.shadowBlur = 0; }
    if (s.wash) { c.globalAlpha = 0.55; c.filter = 'blur(6px)'; }
    path();
    if (s.fill || kind === 'fill') { c.fillStyle = s.half ? halftone(c, col) : col; c.fill(); }
    c.filter = 'none'; c.globalAlpha = 1; c.shadowColor = 'transparent';
    if (!s.fill || s.half || s.wash || s.glass) {
      path(); c.strokeStyle = s.fill ? s.ink : col; c.lineWidth = s.half ? 8 : lw; c.lineJoin = 'round'; c.lineCap = 'round';
      if (s.chalk) { c.globalAlpha = 0.85; c.setLineDash([24, 4, 10, 3]); }
      if (s.glow) { c.shadowColor = col; c.shadowBlur = 30; }
      c.stroke(); c.setLineDash([]);
    }
    c.restore();
  };
  const jit = (x, y, i) => s.sketch ? [x + (hash(i + Math.floor(t * 8) * 31) - 0.5) * 8, y + (hash(i * 3 + Math.floor(t * 8) * 17) - 0.5) * 8] : [x, y];
  const polyPath = (pts) => () => { c.beginPath(); pts.forEach((p, i) => { const q = jit(p[0], p[1], i); i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1]); }); };
  // title block
  c.fillStyle = s.ink; c.textBaseline = 'alphabetic';
  c.font = s.mono ? MONO(110, 700) : F(900, 120);
  c.fillText(s.mono ? '> idea_' : 'The Idea', 140, 230);
  c.fillStyle = s.fill ? s.ink : s.a2; c.globalAlpha = 0.35;
  for (let i = 0; i < 3; i++) c.fillRect(140, 290 + i * 40, [520, 440, 300][i], 16);
  c.globalAlpha = 1;
  // circle "sun / concept"
  const pr = 1 + 0.05 * Math.sin(t * 4);
  const cr = 210 * pr;
  if (s.iso) {
    c.save(); c.translate(560, 680); c.scale(1, 0.58); c.beginPath(); c.arc(0, 0, cr, 0, TAU); c.fillStyle = s.a1; c.fill(); c.restore();
    c.fillStyle = s.ink; c.globalAlpha = 0.15; c.save(); c.translate(560, 720); c.scale(1, 0.58); c.beginPath(); c.arc(0, 0, cr, 0, TAU); c.fill(); c.restore(); c.globalAlpha = 1;
  } else if (s.n === 'Bauhaus') {
    c.fillStyle = s.a1; c.beginPath(); c.arc(560, 640, cr, 0, TAU); c.fill();
    c.fillStyle = s.a3; c.beginPath(); c.moveTo(560, 640 - cr); c.lineTo(560 + cr, 640 + cr * 0.9); c.lineTo(560 - cr, 640 + cr * 0.9); c.closePath(); c.globalAlpha = 0.9; c.fill(); c.globalAlpha = 1;
  } else {
    paint(polyPath(circPts(560, 640, cr, cr, 60, 0, 1.0)), s.a1, s.fill ? 'fill' : 'stroke');
  }
  // orbiting dot
  const oa = t * 3;
  c.fillStyle = s.a2; c.beginPath(); c.arc(560 + Math.cos(oa) * 290, 640 + Math.sin(oa) * 290 * (s.iso ? 0.58 : 1), 26, 0, TAU); c.fill();
  // bars
  [0, 1, 2].forEach(i => {
    const bh = [260, 420, 580][i] * (0.82 + 0.18 * Math.sin(t * 5 + i * 1.3));
    const x0 = 1060 + i * 230, bw = 150, base = 900;
    const col = i === 1 ? s.a1 : s.a2;
    if (s.iso) {
      const d = 60;
      c.fillStyle = col; c.fillRect(x0, base - bh, bw, bh);
      c.fillStyle = mix(s.a1.startsWith('#') ? col : '#888888', '#000000', 0.25);
      c.beginPath(); c.moveTo(x0 + bw, base - bh); c.lineTo(x0 + bw + d, base - bh - d * 0.6); c.lineTo(x0 + bw + d, base - d * 0.6); c.lineTo(x0 + bw, base); c.fill();
      c.fillStyle = mix(col, '#FFFFFF', 0.3);
      c.beginPath(); c.moveTo(x0, base - bh); c.lineTo(x0 + d, base - bh - d * 0.6); c.lineTo(x0 + bw + d, base - bh - d * 0.6); c.lineTo(x0 + bw, base - bh); c.fill();
    } else if (s.n === 'Bauhaus') {
      c.fillStyle = [s.a2, s.ink, s.a1][i]; c.fillRect(x0, base - bh, bw, bh);
    } else {
      paint(polyPath(rectPts(x0, base - bh, bw, bh, 4)), col, s.fill ? 'fill' : 'stroke');
    }
  });
  // wave
  if (!s.stripes) {
    const pts = []; for (let i = 0; i <= 60; i++) pts.push([100 + i * 29, 990 + Math.sin(i * 0.35 + t * 5) * 26]);
    c.save(); c.beginPath(); pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]));
    c.strokeStyle = s.fill ? s.ink : s.a1; c.lineWidth = Math.max(4, lw * 0.8); c.lineCap = 'round';
    if (s.glow) { c.shadowColor = s.a2; c.shadowBlur = 30; c.strokeStyle = s.a2; }
    c.globalAlpha = 0.8; c.stroke(); c.restore();
  }
  if (s.scan) { c.fillStyle = 'rgba(0,0,0,0.35)'; for (let y = 0; y < H; y += 8) c.fillRect(0, y, W, 3); }
}
function tile(c, si, x, y, w, h, t) {
  c.save(); c.beginPath(); c.rect(x, y, w, h); c.clip();
  c.translate(x, y); c.scale(w / W, h / H);
  styleArt(c, STYLES[si], t);
  c.restore();
}
const GRID = (() => {
  const cols = 5, rows = 4, gap = 18, mx = 130;
  const cw = (W - mx * 2 - gap * (cols - 1)) / cols, ch = cw * 9 / 16;
  const top = 250;
  const cells = [];
  for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++) cells.push({ x: mx + q * (cw + gap), y: top + r * (ch + gap), w: cw, h: ch, r, q });
  return { cells, cw, ch };
})();
function sStyles(c, t) {
  bg(c, C.ink);
  const A = 26.0;            // end of full-screen cuts
  const cutIdx = Math.min(7, Math.floor((t - 24.0) / 0.25));
  const zoomOut = E.inOutExpo(P(t, A, A + 1.1));
  if (t < A) {
    const lt = (t - 24.0) % 0.25;
    const punch = 1 + 0.06 * Math.exp(-lt * 14);
    c.save(); c.translate(W / 2, H / 2); c.scale(punch, punch); c.translate(-W / 2, -H / 2);
    styleArt(c, STYLES[cutIdx], t); c.restore();
    // label
    c.fillStyle = 'rgba(10,10,20,0.85)'; rr(c, 60, H - 170, 560, 110, 18); c.fill();
    c.font = MONO(24, 700); c.fillStyle = C.amber; c.fillText(`STYLE ${String(cutIdx + 1).padStart(2, '0')} / 19`, 92, H - 125);
    c.font = F(800, 44); c.fillStyle = C.paper; c.fillText(STYLES[cutIdx].n, 92, H - 78);
    return;
  }
  // camera: from cell 7 full-frame to grid
  const focus = GRID.cells[7];
  const sc = lerp(W / focus.w, 1, zoomOut);
  const fx = focus.x + focus.w / 2, fy = focus.y + focus.h / 2;
  const camX = lerp(fx, W / 2, zoomOut), camY = lerp(fy, H / 2, zoomOut);
  const flipOut = P(t, 29.35, 30.0);
  c.save();
  c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-camX, -camY);
  GRID.cells.forEach((cell, i) => {
    // ripple on beats
    const d = Math.hypot(cell.q - 2, cell.r - 1.5);
    const beatPh = ((t - A) * 2) % 1;
    const wave = t > A + 1.1 ? 0.05 * Math.exp(-Math.max(0, beatPh * 2 - d * 0.3) * 6) * (beatPh * 2 > d * 0.3 ? 1 : 0) : 0;
    const fo = E.inExpo(clamp(flipOut * 2.2 - (cell.q + cell.r) * 0.12));
    const s = (1 + wave) * (1 - fo);
    if (s <= 0.001) return;
    c.save(); c.translate(cell.x + cell.w / 2, cell.y + cell.h / 2); c.scale(1 + wave, s * (1 + wave)); c.translate(-cell.w / 2, -cell.h / 2);
    if (i === 19) {
      rr(c, 0, 0, cell.w, cell.h, 10); c.fillStyle = C.amber; c.fill();
      const n = Math.max(1, Math.round(19 * E.outCubic(P(t, A + 0.9, A + 2.0))));
      c.fillStyle = C.ink; c.font = F(900, 150); c.textAlign = 'center'; c.textBaseline = 'alphabetic';
      c.fillText(String(n), cell.w / 2, cell.h * 0.78);
      c.font = MONO(18, 700); c.fillText('STYLES', cell.w / 2, cell.h * 0.93); c.textAlign = 'left';
    } else {
      c.save(); rr(c, 0, 0, cell.w, cell.h, 10 * zoomOut); c.clip();
      tile(c, i, 0, 0, cell.w, cell.h, t + i * 0.37);
      c.restore();
    }
    c.restore();
  });
  c.restore();
  kin(c, '19 styles.', 130, 175, { size: 96, weight: 900, align: 'left', p: P(t, 27.2, 27.6), out: P(t, 29.3, 29.6) });
  kin(c, 'Zero design skills.', 650, 175, { size: 96, weight: 900, align: 'left', color: C.amber, p: P(t, 27.6, 28.0), out: P(t, 29.35, 29.65) });
}

/* ============================================================
 * SCENE 7 — 20+ languages (30.0 – 34.0)
 * ============================================================ */
const SPHERE = (() => {
  const n = 1100, pts = [], g = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) { const y = 1 - (i / (n - 1)) * 2, r = Math.sqrt(1 - y * y), th = g * i; pts.push([Math.cos(th) * r, y, Math.sin(th) * r]); }
  return pts;
})();
const ARCS = (() => { const r = rng(11); return Array.from({ length: 9 }, () => { const p = () => { const u = r() * 2 - 1, th = r() * TAU, s = Math.sqrt(1 - u * u); return [Math.cos(th) * s, u * 0.8, Math.sin(th) * s]; }; return { a: p(), b: p(), t0: 30.4 + r() * 2.6 }; }); })();
const HELLO = [['Hello', 'EN'], ['Hola', 'ES'], ['Bonjour', 'FR'], ['नमस्ते', 'HI'], ['Hallo', 'DE'], ['こんにちは', 'JA'], ['Olá', 'PT'], ['你好', 'ZH'], ['Привет', 'RU'], ['مرحبا', 'AR'], ['안녕하세요', 'KO'], ['Ciao', 'IT']];
function sGlobe(c, t) {
  bg(c, C.ink);
  const cx = 960, cy = 590;
  const enter = E.outBack(P(t, 30.0, 30.7), 1.2);
  const exitZ = E.inExpo(P(t, 33.55, 34.0));
  const R = 380 * enter * (1 + exitZ * 6);
  glow(c, cx, cy, R * 1.8, C.violet, 0.25);
  const ry = t * 0.7, tx = 0.38;
  const proj = v => {
    const x1 = Math.cos(ry) * v[0] + Math.sin(ry) * v[2], z1 = -Math.sin(ry) * v[0] + Math.cos(ry) * v[2];
    const y2 = Math.cos(tx) * v[1] - Math.sin(tx) * z1, z2 = Math.sin(tx) * v[1] + Math.cos(tx) * z1;
    return [cx + x1 * R, cy + y2 * R, z2];
  };
  for (const v of SPHERE) {
    const [x, y, z] = proj(v);
    c.globalAlpha = (z > 0 ? 0.35 + 0.65 * z : 0.16) * (1 - exitZ);
    c.fillStyle = z > 0.55 ? C.paper : z > 0 ? '#B9B4D8' : C.violet;
    const s = 2.6 + Math.max(0, z) * 3.6;
    c.fillRect(x - s / 2, y - s / 2, s, s);
  }
  c.globalAlpha = 1;
  // great-circle arcs
  for (const a of ARCS) {
    const q = P(t, a.t0, a.t0 + 0.9); if (q <= 0) continue;
    const fade = 1 - P(t, a.t0 + 1.2, a.t0 + 1.7);
    const dot = a.a[0] * a.b[0] + a.a[1] * a.b[1] + a.a[2] * a.b[2], om = Math.acos(clamp(dot, -1, 1));
    c.beginPath();
    const N = 40, end = Math.floor(N * E.outCubic(q));
    let head = null;
    for (let i = 0; i <= end; i++) {
      const u = i / N, s1 = Math.sin((1 - u) * om) / Math.sin(om), s2 = Math.sin(u * om) / Math.sin(om);
      const lift = 1 + 0.28 * Math.sin(Math.PI * u);
      const v = [0, 1, 2].map(k => (a.a[k] * s1 + a.b[k] * s2) * lift);
      const p = proj(v); head = p;
      i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1]);
    }
    c.strokeStyle = rgba(C.amber, 0.85 * fade * (1 - exitZ)); c.lineWidth = 3; c.stroke();
    if (head && fade > 0) { c.fillStyle = C.amber2; c.beginPath(); c.arc(head[0], head[1], 7, 0, TAU); c.fill(); }
  }
  // greetings
  const gi = (t - 30.35) / 0.27;
  if (gi > 0 && exitZ < 0.5) {
    const idx = Math.min(HELLO.length - 1, Math.floor(gi)), f = gi - Math.floor(gi);
    const roll = idx === HELLO.length - 1 ? 1 : E.outExpo(clamp(f / 0.5));
    c.save(); c.beginPath(); c.rect(0, cy - 140, W, 230); c.clip();
    c.textAlign = 'center'; c.textBaseline = 'alphabetic';
    c.font = F(900, 150);
    c.shadowColor = 'rgba(0,0,0,0.7)'; c.shadowBlur = 40;
    c.fillStyle = C.paper; c.fillText(HELLO[idx][0], cx, cy + 50 + (1 - roll) * 200);
    if (idx > 0 && roll < 1) c.fillText(HELLO[idx - 1][0], cx, cy + 50 - roll * 200);
    c.restore();
    c.save(); c.font = MONO(26, 700); c.textAlign = 'center';
    rr(c, cx - 44, cy + 92, 88, 44, 22); c.fillStyle = C.amber; c.fill();
    c.fillStyle = C.ink; c.textBaseline = 'middle'; c.fillText(HELLO[idx][1], cx, cy + 115); c.restore();
  }
  kin(c, 'Narrated in 20+ languages.', 960, 150, { size: 88, weight: 900, p: P(t, 30.3, 30.9), out: P(t, 33.4, 33.7), stagger: 0.02, color: (i) => i < 12 ? C.paper : C.amber });
}

/* ============================================================
 * SCENE 8 — Every format (34.0 – 37.0)
 * ============================================================ */
const MARQUEE = 'RESEARCH PAPERS  ✦  SOPs  ✦  TRAINING  ✦  PITCH DECKS  ✦  ONBOARDING  ✦  PRODUCT DOCS  ✦  TEXTBOOKS  ✦  ';
function sFormats(c, t) {
  bg(c, C.ink2);
  dotGrid(c, t, C.paper, 0.05);
  const cx = 960, cy = 520;
  const fmts = [[960, 540, '16:9', 'YouTube · LMS · Slides'], [380, 676, '9:16', 'Shorts · Reels · TikTok'], [620, 620, '1:1', 'Feeds · LinkedIn']];
  const k1 = E.inOutExpo(P(t, 34.85, 35.25)), k2 = E.inOutExpo(P(t, 35.85, 36.25));
  let fw = lerp(lerp(fmts[0][0], fmts[1][0], k1), fmts[2][0], k2);
  let fh = lerp(lerp(fmts[0][1], fmts[1][1], k1), fmts[2][1], k2);
  const enter = E.outExpo(P(t, 34.0, 34.5));
  const collapse = E.inOutExpo(P(t, 36.55, 37.0));
  fw *= enter; fh *= enter;
  const rad = lerp(24, 0, 0);
  const fxw = lerp(fw, 44, collapse), fxh = lerp(fh, 44, collapse);
  const fr = lerp(rad, 22, collapse);
  const fi = t < 35.05 ? 0 : t < 36.05 ? 1 : 2;
  if (fxw > 2) {
    c.save();
    rr(c, cx - fxw / 2, cy - fxh / 2, fxw, fxh, fr); c.clip();
    const art = [0, 3, 15][fi];
    // cover-fit the 16:9 art in the frame
    const s = Math.max(fxw / W, fxh / H);
    c.translate(cx - W * s / 2, cy - H * s / 2); c.scale(s, s);
    styleArt(c, STYLES[art], t);
    c.restore();
    c.fillStyle = rgba(C.amber, collapse); rr(c, cx - fxw / 2, cy - fxh / 2, fxw, fxh, fr); c.fill();
    rr(c, cx - fxw / 2, cy - fxh / 2, fxw, fxh, fr); c.strokeStyle = rgba(C.paper, 1 - collapse); c.lineWidth = 5; c.stroke();
    // corner ticks + labels
    if (collapse < 0.2 && enter > 0.5) {
      const lx = cx + fxw / 2 + 40, ly = cy - fxh / 2 + 20;
      const lp = fi === 0 ? P(t, 34.3, 34.7) : fi === 1 ? P(t, 35.2, 35.5) : P(t, 36.2, 36.5);
      const lo = fi === 0 ? P(t, 34.75, 34.9) : fi === 1 ? P(t, 35.75, 35.9) : P(t, 36.45, 36.6);
      kin(c, fmts[fi][2], lx, ly + 90, { size: 110, weight: 900, color: C.amber, align: 'left', p: lp, out: lo });
      kin(c, fmts[fi][3], lx + 4, ly + 150, { font: MONO(26, 700), color: C.gray, align: 'left', p: lp, out: lo, stagger: 0.01 });
    }
  }
  kin(c, 'One document. Every format.', 960, 140, { size: 80, weight: 900, p: P(t, 34.1, 34.6), out: P(t, 36.45, 36.75), stagger: 0.02, color: (i) => i < 14 ? C.paper : C.amber });
  // marquee band
  const band = E.outExpo(P(t, 34.2, 34.7)) * (1 - E.inExpo(P(t, 36.5, 36.9)));
  if (band > 0) {
    c.save(); c.translate(960, 990); c.rotate(-0.025); c.scale(1, band);
    c.fillStyle = C.amber; c.fillRect(-1100, -46, 2200, 92);
    c.font = F(900, 46); c.fillStyle = C.ink; c.textBaseline = 'middle';
    const mw = c.measureText(MARQUEE).width;
    let off = -((t - 34) * 420) % mw - 1100;
    for (let x = off; x < 1100; x += mw) c.fillText(MARQUEE, x, 3);
    c.restore();
  }
}

/* ============================================================
 * SCENE 9 — End card (37.0 – 40.0)
 * ============================================================ */
function sEnd(c, t) {
  bg(c, C.ink);
  const cx = 960;
  // drop falls from frame centre to the "floor", bounces into rings
  const fall = P(t, 37.0, 37.27);
  const floorY = 860;
  if (t < 37.27) {
    const y = lerp(520, floorY, E.inQuad(fall));
    glow(c, cx, y, 120, C.amber, 0.4);
    if (fall < 0.15) { c.beginPath(); c.arc(cx, y, 22, 0, TAU); c.fillStyle = C.amber; c.fill(); }
    else drop(c, cx, y, 22, C.amber, 1 + fall * 0.5);
  }
  for (const [t0, col, amp] of [[37.27, C.amber, 1], [38.5, C.paper, 1.4]]) {
    for (let k = 0; k < 3; k++) {
      const q = clamp((t - t0 - k * 0.1) / 1.5); if (q <= 0 || q >= 1) continue;
      const y0 = t0 < 38 ? floorY : 540;
      c.beginPath(); c.ellipse(cx, y0, E.outExpo(q) * 1000 * amp, E.outExpo(q) * (t0 < 38 ? 160 : 1000) * amp, 0, 0, TAU);
      c.strokeStyle = rgba(col, (1 - q) * 0.7); c.lineWidth = 6 * (1 - q) + 1; c.stroke();
    }
  }
  const out = P(t, 38.2, 38.45);
  kin(c, "Don't read it.", cx, 470, { size: 170, weight: 900, p: P(t, 37.2, 37.6), out, stagger: 0.04 });
  kin(c, 'Watch it.', cx, 660, { size: 170, weight: 900, color: C.amber, p: P(t, 37.7, 38.05), out, stagger: 0.05 });
  // final lockup
  const lp = P(t, 38.45, 39.2);
  if (lp > 0) {
    glow(c, cx, 500, 700, C.violet, 0.22 * lp);
    const sw = P(t, 39.15, 39.6);
    wordmark(c, cx, 560, 210, lp, { split: 18 * Math.exp(-(t - 38.45) * 8), shine: sw > 0 && sw < 1 ? lerp(300, 1620, E.inOutCubic(sw)) : null });
    kin(c, 'Turn any document into an explainer video.', cx, 690, { size: 40, weight: 600, fam: 'Inter', color: C.paper, p: P(t, 38.8, 39.3), stagger: 0.008 });
    kin(c, 'distilbook.com', cx, 790, { font: MONO(34, 700), color: C.amber, p: P(t, 39.0, 39.4), track: 0.08, stagger: 0.03 });
  }
  // fade
  c.fillStyle = `rgba(0,0,0,${E.inCubic(P(t, 39.65, 40.0))})`; c.fillRect(0, 0, W, H);
}

/* ============================================================
 * Timeline + compositor
 * ============================================================ */
const SCENES = [
  { a: 0.0, b: 4.0, fn: sIntro },
  { a: 3.5, b: 8.0, fn: sPile, iris: [3.5, 4.0, 960, 540] },
  { a: 7.15, b: 11.0, fn: sDistill, iris: [7.15, 7.95, 960, 600] },
  { a: 11.0, b: 15.0, fn: sLogo },
  { a: 15.0, b: 24.0, fn: sSteps },
  { a: 24.0, b: 30.0, fn: sStyles },
  { a: 30.0, b: 34.0, fn: sGlobe },
  { a: 34.0, b: 37.0, fn: sFormats },
  { a: 37.0, b: 40.01, fn: sEnd },
];
const FLASH = [[1.0, 0.55], [11.0, 0.95], [24.0, 0.25], [30.0, 0.2], [37.27, 0.4], [38.5, 0.6]];
const SHAKE = [[1.0, 16], [11.0, 26], [16.35, 6], [24.0, 8], [37.27, 12], [38.5, 14]];

const main = document.getElementById('c');
const M = main.getContext('2d');
const work = document.createElement('canvas'); work.width = W; work.height = H;
const S = work.getContext('2d');
const grain = [0, 1, 2, 3].map(i => {
  const g = document.createElement('canvas'); g.width = g.height = 256;
  const x = g.getContext('2d'), d = x.createImageData(256, 256), r = rng(100 + i);
  for (let k = 0; k < d.data.length; k += 4) { const v = r() * 255; d.data[k] = d.data[k + 1] = d.data[k + 2] = v; d.data[k + 3] = 255; }
  x.putImageData(d, 0, 0); return g;
});

function drawScene(c, t) {
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none';
  c.textAlign = 'left'; c.textBaseline = 'alphabetic';
  c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
  // camera shake
  let sh = 0;
  for (const [t0, amp] of SHAKE) if (t >= t0) sh += amp * Math.exp(-(t - t0) * 9);
  if (sh > 0.3) {
    const z = 1 + sh / 400;
    c.translate(W / 2 + (hash(t * 91) - 0.5) * sh * 2, H / 2 + (hash(t * 53 + 4) - 0.5) * sh * 2); c.scale(z, z); c.translate(-W / 2, -H / 2);
  }
  for (const s of SCENES) {
    if (t < s.a || t >= s.b) continue;
    c.save();
    if (s.iris && t < s.iris[1]) {
      const r = E.inExpo(P(t, s.iris[0], s.iris[1])) * 2300;
      c.beginPath(); c.arc(s.iris[2], s.iris[3], Math.max(0.01, r), 0, TAU); c.clip();
    }
    s.fn(c, t);
    c.restore();
  }
  c.setTransform(1, 0, 0, 1, 0, 0);
  let fl = 0;
  for (const [t0, amp] of FLASH) if (t >= t0) fl += amp * Math.exp(-(t - t0) / 0.07);
  if (fl > 0.005) { c.fillStyle = `rgba(255,248,235,${Math.min(1, fl)})`; c.fillRect(0, 0, W, H); }
}

const SUB = 4, SHUTTER = 0.5 / FPS; // 180° shutter
function renderFrame(t, fi) {
  M.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < SUB; i++) {
    const st = t + (i / SUB - 0.5) * SHUTTER + SHUTTER / (2 * SUB);
    drawScene(S, Math.max(0, st));
    M.globalAlpha = 1 / (i + 1); M.drawImage(work, 0, 0);
  }
  M.globalAlpha = 1;
  // grain
  M.save(); M.globalCompositeOperation = 'overlay'; M.globalAlpha = 0.07;
  const g = grain[(fi ?? Math.round(t * FPS)) % 4];
  const ox = Math.floor(hash(t * 13) * 256), oy = Math.floor(hash(t * 29) * 256);
  for (let y = -oy; y < H; y += 256) for (let x = -ox; x < W; x += 256) M.drawImage(g, x, y);
  M.restore();
  // vignette
  const v = M.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.5)');
  M.fillStyle = v; M.fillRect(0, 0, W, H);
}

window.renderFrame = renderFrame;
window.DUR = DUR; window.FPS = FPS;
window.ready = (async () => {
  const fonts = [F(900, 100), F(800, 100), F(700, 100), F(600, 100), F(500, 40, 'Inter'), F(600, 40, 'Inter'),
    F(700, 40, 'Inter'), F(800, 40, 'Inter'), MONO(30), MONO(30, 700)];
  await Promise.all(fonts.map(f => document.fonts.load(f, 'AaBb012नमस्तेこんにちは你好안녕مرحبا✦✓')));
  // warm up multi-script fallback rendering
  S.font = F(900, 150); S.fillText('नमस्ते こんにちは 你好 안녕하세요 مرحبا Привет ✦ ✓', 0, 0);
  return true;
})();

// Interactive preview
(function preview() {
  const scrub = document.getElementById('scrub'), tc = document.getElementById('tc'), btn = document.getElementById('play');
  if (!scrub || new URLSearchParams(location.search).has('render')) return;
  let playing = false, start = 0, t0 = 0;
  const show = t => { renderFrame(t); scrub.value = t; tc.textContent = t.toFixed(2); };
  scrub.oninput = () => { playing = false; btn.textContent = 'play'; show(+scrub.value); };
  btn.onclick = () => { playing = !playing; btn.textContent = playing ? 'pause' : 'play'; start = performance.now(); t0 = +scrub.value % DUR; if (playing) loop(); };
  function loop() { if (!playing) return; const t = (t0 + (performance.now() - start) / 1000) % DUR; show(t); requestAnimationFrame(loop); }
  window.ready.then(() => show(0));
})();
