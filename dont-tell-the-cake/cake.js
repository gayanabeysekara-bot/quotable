/* "Don't Tell the Cake" — 10s, 1080x1920 (9:16), 30fps.
 * One continuous locked-off shot. Every frame is a pure function of t, so the
 * renderer can sample sub-frames for motion blur and render in parallel.
 */
'use strict';

const W = 1080, H = 1920, FPS = 30, DUR = 10;
const C = {
  wall: '#CFEBDD', wallShade: '#BFE0D0', cab: '#F4EAD3', cabLine: '#D9CBA9', counter: '#E8DCC0',
  floor: '#DDBB8E', floorLine: '#C6A16F', ink: '#111114', white: '#FFFFFF', shade: '#D8E1EC',
  blue: '#4E79AD', blueDark: '#3D6290', purple: '#8A63B4', purpleDark: '#724E9C',
  skirt: '#1C1C20', hair: '#18181B', hairHi: '#3A3A40', lip: '#B97E86', lipDark: '#8E5560',
  fridge: '#EEF2F6', fridgeShade: '#D7DEE7', inside: '#F6FAFE', glow: '#FFF6D6',
  cake: '#5A3424', cakeDark: '#3E2217', frost: '#7A4A33', plate: '#FFFFFF',
};
const LW = 7; // outline weight

/* ---------- math ---------- */
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const P = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  sine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  back: (t, s = 1.7) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
};
/* keyframed value: keys = [[t, v, ease?], ...] */
function K(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1, ez] = keys[i];
      return lerp(v0, v1, (ez || E.inOut)(P(t, t0, t1)));
    }
  }
  return keys[keys.length - 1][1];
}
function lipAt(who, t) {
  const a = (window.LIPS && window.LIPS[who]) || [];
  const f = t * FPS, i = Math.floor(f), fr = f - i;
  return lerp(a[i] || 0, a[i + 1] || 0, fr);
}
const FREEZE = 9.15;
/* after the freeze nothing idles: everything samples time as if frozen */
const live = t => (t < FREEZE ? t : FREEZE);

/* ---------- primitives ---------- */
function rr(c, x, y, w, h, r) {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function inkFill(c, fill, lw = LW) { c.fillStyle = fill; c.fill(); c.lineWidth = lw; c.strokeStyle = C.ink; c.lineJoin = 'round'; c.stroke(); }
function limb(c, pts, w = 17) {
  c.beginPath(); c.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) c.lineTo(pts[i][0], pts[i][1]);
  c.strokeStyle = C.ink; c.lineWidth = w; c.lineCap = 'round'; c.lineJoin = 'round'; c.stroke();
}
/* two-bone IK: shoulder -> target, elbow bends toward `side` (+1 / -1) */
function ik(s, tg, l1, l2, side) {
  const dx = tg[0] - s[0], dy = tg[1] - s[1];
  let d = Math.hypot(dx, dy);
  const maxd = l1 + l2 - 1;
  const ang = Math.atan2(dy, dx);
  if (d > maxd) d = maxd;
  const a = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1));
  const e = [s[0] + Math.cos(ang + a * side) * l1, s[1] + Math.sin(ang + a * side) * l1];
  const h = [s[0] + Math.cos(ang) * d, s[1] + Math.sin(ang) * d];
  return [s, e, h];
}
function mitten(c, x, y, ang, s = 1) {
  c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s);
  c.beginPath(); c.ellipse(10, 0, 26, 19, 0, 0, Math.PI * 2); c.fillStyle = C.ink; c.fill();
  c.beginPath(); c.ellipse(4, -18, 9, 13, -0.5, 0, Math.PI * 2); c.fill(); // thumb
  c.restore();
}
function foot(c, x, y, dir) {
  c.beginPath(); c.ellipse(x + dir * 22, y, 50, 19, 0, 0, Math.PI * 2); c.fillStyle = C.ink; c.fill();
}

/* ============================================================
 * Kitchen
 * ============================================================ */
function kitchen(c, open) {
  c.fillStyle = C.wall; c.fillRect(0, 0, W, 1420);
  // soft wall vignette
  const g = c.createRadialGradient(540, 700, 200, 540, 700, 1100);
  g.addColorStop(0, 'rgba(255,255,255,0.18)'); g.addColorStop(1, 'rgba(0,60,40,0.06)');
  c.fillStyle = g; c.fillRect(0, 0, W, 1420);
  // upper cabinets
  for (let i = 0; i < 3; i++) {
    const x = 30 + i * 215;
    rr(c, x, 150, 200, 330, 16); inkFill(c, C.cab, 5);
    rr(c, x + 22, 172, 156, 286, 10); c.strokeStyle = C.cabLine; c.lineWidth = 4; c.stroke();
    c.beginPath(); c.arc(x + (i % 2 ? 36 : 164), 440, 7, 0, Math.PI * 2); c.fillStyle = C.ink; c.fill();
  }
  // lower counter (left), behind Mom
  rr(c, -20, 1060, 520, 360, 0); inkFill(c, C.cab, 5);
  c.fillStyle = C.counter; rr(c, -30, 1030, 545, 44, 10); inkFill(c, C.counter, 5);
  for (let i = 0; i < 2; i++) { rr(c, 20 + i * 240, 1100, 210, 290, 10); c.strokeStyle = C.cabLine; c.lineWidth = 4; c.stroke(); }
  // floor
  c.fillStyle = C.floor; c.fillRect(0, 1420, W, H - 1420);
  c.strokeStyle = C.floorLine; c.lineWidth = 4;
  c.beginPath(); c.moveTo(0, 1420); c.lineTo(W, 1420); c.strokeStyle = C.ink; c.lineWidth = 5; c.stroke();
  c.strokeStyle = C.floorLine; c.lineWidth = 3;
  for (let i = 0; i < 6; i++) { const y = 1480 + i * 80 + i * i * 6; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  for (let i = 0; i < 12; i++) {
    const row = i % 6, y0 = 1480 + row * 80 + row * row * 6, x = ((i * 337) % 1000) + 40;
    c.beginPath(); c.moveTo(x, y0); c.lineTo(x, y0 + 80 + row * 12); c.stroke();
  }
  // fridge light spill on floor/wall
  if (open > 0.01) {
    const gg = c.createRadialGradient(760, 1250, 40, 760, 1250, 620);
    gg.addColorStop(0, `rgba(255,246,214,${0.55 * open})`); gg.addColorStop(1, 'rgba(255,246,214,0)');
    c.fillStyle = gg; c.fillRect(0, 500, W, 1420);
  }
}

/* ============================================================
 * Fridge — hinge on the left; theta 0 = closed, 100deg = open.
 * ============================================================ */
const FR = { x: 680, w: 280, top: 360, split: 652, bot: 1460 };
const doorEdgeX = th => FR.x + FR.w * Math.cos(th);
const doorScale = th => 1 + 0.1 * Math.sin(th);
function handlePos(th) {
  const ex = doorEdgeX(th), s = doorScale(th), cy = (FR.split + 8 + FR.bot) / 2;
  const inset = 26 * Math.cos(th);                        // handle sits just inside the far edge
  return [ex - inset, cy - 20 * s];
}
function cake(c, x, y) {
  // plate
  c.beginPath(); c.ellipse(x, y + 4, 70, 15, 0, 0, Math.PI * 2); inkFill(c, C.plate, 5);
  // slice (wedge, side view): back tall side, pointy front
  c.beginPath(); c.moveTo(x - 50, y - 6); c.lineTo(x + 52, y - 6); c.lineTo(x + 52, y - 66); c.lineTo(x - 50, y - 34); c.closePath();
  inkFill(c, C.cake, 5);
  c.beginPath(); c.moveTo(x - 46, y - 22); c.lineTo(x + 50, y - 36); c.strokeStyle = C.frost; c.lineWidth = 7; c.stroke(); // cream layer
  c.beginPath(); c.moveTo(x - 50, y - 34); c.lineTo(x + 52, y - 66); c.lineTo(x + 52, y - 74); c.lineTo(x - 50, y - 40); c.closePath();
  c.fillStyle = C.cakeDark; c.fill(); c.lineWidth = 5; c.strokeStyle = C.ink; c.stroke();     // ganache top
  c.beginPath(); c.arc(x + 38, y - 78, 9, 0, Math.PI * 2); inkFill(c, '#D8343F', 4);           // cherry
}
function fridge(c, th) {
  const { x, w, top, split, bot } = FR;
  // body
  rr(c, x, top, w, bot - top, 26); inkFill(c, C.fridge);
  // interior (main compartment)
  const ix = x + 16, iy = split + 18, iw = w - 32, ih = bot - split - 40;
  rr(c, ix, iy, iw, ih, 12); c.fillStyle = C.inside; c.fill();
  const lg = c.createRadialGradient(x + w / 2, iy + 40, 10, x + w / 2, iy + 40, 420);
  lg.addColorStop(0, 'rgba(255,248,220,1)'); lg.addColorStop(1, 'rgba(225,236,246,1)');
  c.fillStyle = lg; rr(c, ix, iy, iw, ih, 12); c.fill();
  c.lineWidth = 4; c.strokeStyle = '#9AA7B5'; rr(c, ix, iy, iw, ih, 12); c.stroke();
  [iy + 200, iy + 400, iy + 600].forEach(y => { c.beginPath(); c.moveTo(ix + 4, y); c.lineTo(ix + iw - 4, y); c.strokeStyle = '#A9B7C6'; c.lineWidth = 6; c.stroke(); });
  cake(c, x + 205, iy + 398);
  // freezer door (always closed)
  rr(c, x + 6, top + 6, w - 12, split - top - 6, 22); inkFill(c, C.fridge, 5);
  rr(c, x + 30, top + 200, 14, 70, 7); inkFill(c, '#C9D2DC', 4);
  // main door
  const ex = doorEdgeX(th), s = doorScale(th);
  const cy = (split + 8 + bot) / 2, hh = (bot - split - 8) / 2;
  c.beginPath();
  c.moveTo(x + 4, cy - hh); c.lineTo(ex, cy - hh * s); c.lineTo(ex, cy + hh * s); c.lineTo(x + 4, cy + hh); c.closePath();
  const outer = Math.cos(th) >= 0;
  inkFill(c, outer ? C.fridge : '#E2E8EF', 6);
  if (!outer) {
    // inner face of the door: empty door bins, seen at a steep angle
    for (let k = 0; k < 3; k++) {
      const fy = (cy - hh) + (k + 0.6) * (2 * hh) / 3.2;
      c.beginPath(); c.moveTo(x + 4, fy); c.lineTo(ex, fy + (fy - cy) * (s - 1)); c.strokeStyle = '#A9B7C6'; c.lineWidth = 5; c.stroke();
    }
  } else {
    // subtle shading on the outer face as it turns
    c.fillStyle = `rgba(150,165,185,${0.25 * Math.sin(th)})`;
    c.beginPath(); c.moveTo(x + 4, cy - hh); c.lineTo(ex, cy - hh * s); c.lineTo(ex, cy + hh * s); c.lineTo(x + 4, cy + hh); c.closePath(); c.fill();
  }
  // handle
  const [hx, hy] = handlePos(th);
  const hw = Math.max(6, 16 * Math.abs(Math.cos(th)) + 6);
  rr(c, hx - hw / 2, hy - 85 * s, hw, 170 * s, hw / 2); inkFill(c, '#C9D2DC', 4);
}

/* ============================================================
 * Characters
 * ============================================================ */
function eye(c, x, y, rx, ry, gx, gy, lid, pupilS = 1, lashes = false, lashDir = 1) {
  c.save();
  c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); c.fillStyle = C.white; c.fill();
  c.clip();
  const px = x + gx * rx * 0.42, py = y + gy * ry * 0.35 + ry * 0.08;
  c.beginPath(); c.ellipse(px, py, rx * 0.47 * pupilS, ry * 0.5 * pupilS, 0, 0, Math.PI * 2); c.fillStyle = C.ink; c.fill();
  c.beginPath(); c.arc(px + rx * 0.14, py - ry * 0.2, rx * 0.15 * pupilS, 0, Math.PI * 2); c.fillStyle = C.white; c.fill();
  c.beginPath(); c.arc(px - rx * 0.1, py + ry * 0.18, rx * 0.06 * pupilS, 0, Math.PI * 2); c.fill();
  // eyelid (0 open .. 1 closed) drops from the top
  if (lid > 0.01) { c.fillStyle = C.white; c.fillRect(x - rx - 5, y - ry - 5, rx * 2 + 10, (ry * 2 + 5) * lid); }
  c.restore();
  c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); c.lineWidth = 5; c.strokeStyle = C.ink; c.stroke();
  if (lid > 0.01) {
    const ly = y - ry + 2 * ry * lid;
    const half = rx * Math.sqrt(Math.max(0, 1 - Math.pow((ly - y) / ry, 2)));
    c.beginPath(); c.moveTo(x - half, ly); c.lineTo(x + half, ly); c.lineWidth = 5; c.stroke();
  }
  if (lashes) {
    c.lineWidth = 4; c.lineCap = 'round';
    const lyTop = y - ry + 2 * ry * Math.max(lid, 0);
    for (let k = 0; k < 2; k++) {
      const ax = x + lashDir * rx * (0.55 + k * 0.25);
      c.beginPath(); c.moveTo(ax, lyTop + (k ? 12 : 4)); c.lineTo(ax + lashDir * 14, lyTop + (k ? 4 : -6)); c.stroke();
    }
  }
}
function brow(c, x, y, w, lift, tilt, thick = 9) {
  c.save(); c.translate(x, y - lift); c.rotate(tilt);
  c.beginPath(); c.moveTo(-w / 2, 6); c.quadraticCurveTo(0, -10, w / 2, 4);
  c.strokeStyle = C.ink; c.lineWidth = thick; c.lineCap = 'round'; c.stroke(); c.restore();
}
function shirtText(c, txt, x, y, size, col, ang = 0) {
  c.save(); c.translate(x, y); c.rotate(ang);
  c.font = `900 ${size}px "Inter Display", "Inter", sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillStyle = col; c.fillText(txt, 0, 0); c.restore();
}

/* ---------------- DAD ---------------- */
function dadState(t) {
  const lt = live(t);
  const th = K(t, [[0, 1.4], [6.6, 1.4], [7.88, 0.0, E.inOut], [8.42, 0.0], [8.78, 0.84, E.out]]);
  const turn = K(t, [[0, 0.65], [2.35, 0.65], [2.6, -0.55], [3.35, -0.55], [3.5, 0.45], [3.8, 0.45], [3.95, -0.55],
    [6.5, -0.55], [6.8, 0.45], [7.95, 0.45], [8.1, -0.75], [8.35, -0.75], [8.5, 0.7], [9.12, 0.7], [9.17, -0.2, E.out]]);
  const lean = K(t, [[0, 0.07], [2.35, 0.07], [2.65, -0.02], [5.3, -0.02], [5.5, -0.06], [6.5, -0.06], [6.9, 0.08],
    [7.9, 0.1], [8.1, 0.06], [8.35, 0.06], [8.8, 0.13, E.out], [9.15, 0.13]]);
  const gazeY = K(t, [[0, 0.5], [2.4, 0.5], [2.6, 0], [3.35, 0], [3.5, 0.5], [3.8, 0.5], [3.95, 0], [5.45, -0.2], [6.5, -0.2], [6.8, 0.5],
    [7.95, 0.5], [8.1, 0], [8.4, 0], [8.6, 0.5], [9.12, 0.5], [9.17, 0]]);
  const proud = P(t, 5.4, 5.6) * (1 - P(t, 6.45, 6.7));
  const shifty = P(t, 7.95, 8.1) * (1 - P(t, 8.36, 8.5));
  const eager = P(t, 8.45, 8.7);
  const frozen = t >= FREEZE ? E.out(P(t, FREEZE, FREEZE + 0.12)) : 0;
  // whisper hand cupped beside the mouth while whispering
  const cup = Math.max(P(t, 2.5, 2.7) * (1 - P(t, 4.2, 4.45)), P(t, 5.3, 5.45) * (1 - P(t, 6.5, 6.7)));
  let blink = 0;
  for (const b of [1.5, 4.6, 7.2]) blink = Math.max(blink, 1 - Math.abs(lt - b) / 0.07);
  return { th, turn, lean, gazeY, proud, shifty, eager, frozen, cup, blink: clamp(blink), lt, talk: lipAt('dad', t) };
}
function drawDad(c, t, S) {
  const cx = 515, foot0 = 1716, X = 515, Y = 1772, SC = 0.88;
  const breathe = Math.sin(S.lt * 2.2) * 3;
  const jolt = S.frozen > 0 ? (1 - P(t, FREEZE, FREEZE + 0.18)) * 10 : 0;
  c.save();
  c.translate(X, Y); c.rotate(S.lean); c.scale(SC, SC); c.translate(-cx, -foot0);
  // legs + feet
  limb(c, [[cx - 32, 1330], [cx - 46, foot0 - 6]]);
  limb(c, [[cx + 32, 1330], [cx + 42, foot0 - 6]]);
  foot(c, cx - 50, foot0, -1); foot(c, cx + 46, foot0, 1);
  const by = breathe * 0.4 - jolt;
  // shorts
  c.beginPath(); c.moveTo(cx - 102, 1230 + by); c.lineTo(cx + 102, 1230 + by); c.lineTo(cx + 110, 1372); c.lineTo(cx + 8, 1376);
  c.lineTo(cx, 1300); c.lineTo(cx - 8, 1376); c.lineTo(cx - 110, 1372); c.closePath(); inkFill(c, C.blue, 6);
  c.beginPath(); c.moveTo(cx - 6, 1252 + by); c.lineTo(cx + 34, 1244 + by); c.strokeStyle = C.ink; c.lineWidth = 5; c.stroke();
  // arms are computed before the shirt so sleeves sit on top
  const shL = [cx - 104, 975 + by], shR = [cx + 104, 975 + by];
  const [hx, hy] = handlePos(S.th);
  // map the handle (screen space) into this character's local space so the hand stays glued to it
  const loc = c.getTransform().inverse().transformPoint({ x: hx, y: hy });
  const armR = ik(shR, [loc.x - 8, loc.y], 200, 196, -1);
  // left arm: hangs, or cups beside the mouth for the whisper
  const hang = [cx - 150, 1290 + by];
  const cupPos = [cx - 92 + S.turn * 34, 800 + by];
  const tL = [lerp(hang[0], cupPos[0], E.inOut(S.cup)), lerp(hang[1], cupPos[1], E.inOut(S.cup))];
  const armL = ik(shL, tL, 180, 175, -1);
  const cupFront = S.cup > 0.35;          // once raised, the cupped hand sits in front of the face
  if (!cupFront) { limb(c, armL); mitten(c, armL[2][0], armL[2][1], lerp(1.75, -1.4, S.cup), 1); }
  limb(c, armR);
  mitten(c, armR[2][0], armR[2][1], Math.PI / 2 + 0.25, 1);
  // shirt
  c.beginPath();
  c.moveTo(cx - 70, 930 + by); c.quadraticCurveTo(cx, 960 + by, cx + 70, 930 + by);
  c.lineTo(cx + 150, 975 + by); c.lineTo(cx + 172, 1062 + by); c.lineTo(cx + 116, 1078 + by);
  c.lineTo(cx + 122, 1250 + by); c.quadraticCurveTo(cx, 1268 + by, cx - 122, 1250 + by);
  c.lineTo(cx - 116, 1078 + by); c.lineTo(cx - 172, 1062 + by); c.lineTo(cx - 150, 975 + by); c.closePath();
  inkFill(c, C.white, 6);
  c.save(); c.clip(); c.fillStyle = C.shade; c.fillRect(cx - 180, 900 + by, 40, 400); c.restore();
  shirtText(c, 'DAD', cx, 1112 + by, 92, C.ink);
  // neck
  rr(c, cx - 18, 880 + by, 36, 62, 10); inkFill(c, C.white, 5);
  c.beginPath(); c.moveTo(cx - 40, 934 + by); c.quadraticCurveTo(cx, 968 + by, cx + 40, 934 + by); c.strokeStyle = C.ink; c.lineWidth = 6; c.stroke();
  // head
  const hx0 = cx + S.turn * 6, hy0 = 735 + by - S.proud * 10 - S.frozen * 6;
  c.save(); c.translate(hx0, hy0); c.rotate(-S.proud * 0.08 + S.eager * 0.05);
  const r = 158;
  c.beginPath(); c.arc(0, 0, r, 0, Math.PI * 2); c.fillStyle = C.shade; c.fill();
  c.save(); c.beginPath(); c.arc(0, 0, r, 0, Math.PI * 2); c.clip();
  c.beginPath(); c.arc(14, -12, r - 6, 0, Math.PI * 2); c.fillStyle = C.white; c.fill(); c.restore();
  c.beginPath(); c.arc(0, 0, r, 0, Math.PI * 2); c.lineWidth = LW + 1; c.strokeStyle = C.ink; c.stroke();
  // face features shift with head turn
  const fx = S.turn * 34;
  const gx = clamp(S.turn * 1.3, -1, 1);
  const lid = Math.max(S.blink, S.proud * 0.42, S.shifty * 0.45);
  const eyeS = 1 + S.eager * 0.06 + S.frozen * 0.12;
  const pupS = 1 - S.frozen * 0.38 + S.eager * 0.06;
  eye(c, fx - 56, -18, 40 * eyeS, 56 * eyeS, gx, S.gazeY, lid, pupS);
  eye(c, fx + 56, -18, 40 * eyeS, 56 * eyeS, gx, S.gazeY, lid, pupS);
  const bl = 18 + S.proud * 14 + S.eager * 10 + S.frozen * 22 - S.shifty * 8;
  brow(c, fx - 58, -98, 58, bl, -0.1 - S.shifty * 0.25, 10);
  brow(c, fx + 58, -98, 58, bl + S.shifty * 6, 0.1 + S.shifty * 0.15, 10);
  // mouth: whisper = small rounded "o"/pursed shapes driven by the voice envelope
  const mx = fx + 4, my = 82;
  const o = S.talk;
  c.lineCap = 'round'; c.strokeStyle = C.ink;
  if (o > 0.04) {
    c.beginPath(); c.ellipse(mx, my, 16 + 10 * o, 4 + 20 * o, 0, 0, Math.PI * 2); c.fillStyle = '#3A1E22'; c.fill();
    c.lineWidth = 5; c.stroke();
  } else if (S.frozen > 0) {
    c.beginPath(); c.moveTo(mx - 22, my + 2); c.quadraticCurveTo(mx - 8, my - 6, mx, my + 2); c.quadraticCurveTo(mx + 10, my + 8, mx + 24, my - 2);
    c.lineWidth = 6; c.stroke();                       // wobbly guilty mouth
  } else {
    const sm = 10 + S.proud * 8 + S.eager * 12;
    c.beginPath(); c.moveTo(mx - 34, my - 6); c.quadraticCurveTo(mx, my + sm, mx + 34, my - 6); c.lineWidth = 6; c.stroke();
    c.beginPath(); c.moveTo(mx - 40, my - 10); c.lineTo(mx - 30, my - 2); c.stroke();
  }
  c.restore();
  if (cupFront) {
    // forearm rises from below the chin; the mitten cups the side of the mouth
    limb(c, [armL[0], armL[1], armL[2]]);
    c.save(); c.translate(armL[2][0], armL[2][1]); c.rotate(-0.25);
    c.beginPath(); c.ellipse(0, 0, 22, 34, 0, 0, Math.PI * 2); c.fillStyle = C.ink; c.fill();
    c.beginPath(); c.ellipse(16, 18, 9, 14, 0.6, 0, Math.PI * 2); c.fill();
    c.restore();
  }
  c.restore();
}

/* ---------------- MOM ---------------- */
function momState(t) {
  const lt = live(t);
  const turn = K(t, [[0, 0.5], [6.5, 0.5], [6.85, -0.6], [8.92, -0.6], [9.08, 0.55, E.out]]);
  const gazeX = K(t, [[0, 1], [6.5, 1], [6.8, -1], [8.92, -1], [9.05, 1, E.out]]);
  const tilt = K(t, [[0, 0], [4.75, 0], [4.95, 0.16, E.out], [5.6, 0.16], [5.9, 0.04], [6.5, 0.04], [6.8, -0.04], [8.92, -0.04], [9.05, 0.03]]);
  const browUp = Math.max(1 - P(t, 2.3, 2.6), P(t, 9.0, 9.12)) ;       // raised right brow
  const puzzled = P(t, 4.75, 4.95) * (1 - P(t, 5.5, 5.8));
  const skeptic = P(t, 5.5, 5.8) * (1 - P(t, 6.5, 6.7));
  let blink = 0;
  for (const b of [3.1, 6.1, 7.6]) blink = Math.max(blink, 1 - Math.abs(lt - b) / 0.07);
  return { turn, gazeX, tilt, browUp, puzzled, skeptic, blink: clamp(blink), lt, talk: lipAt('mom', t) };
}
function drawMom(c, t, S) {
  const cx = 218, foot0 = 1716, X = 196, Y = 1772, SC = 0.88;
  const breathe = Math.sin(S.lt * 2.0 + 1) * 3;
  const by = breathe * 0.4;
  c.save(); c.translate(X, Y); c.scale(SC, SC); c.translate(-cx, -foot0);
  // legs + feet
  limb(c, [[cx - 30, 1420], [cx - 40, foot0 - 6]]);
  limb(c, [[cx + 30, 1420], [cx + 38, foot0 - 6]]);
  foot(c, cx - 44, foot0, -1); foot(c, cx + 44, foot0, 1);
  // skirt
  c.beginPath(); c.moveTo(cx - 92, 1218 + by); c.lineTo(cx + 92, 1218 + by); c.lineTo(cx + 140, 1446); c.quadraticCurveTo(cx, 1462, cx - 140, 1446); c.closePath();
  inkFill(c, C.skirt, 6);
  // arms: screen-left hand on hip (akimbo), screen-right hangs
  const shL = [cx - 92, 1000 + by], shR = [cx + 92, 1000 + by];
  const armL = ik(shL, [cx - 96, 1206 + by], 150, 140, 1);
  const armR = ik(shR, [cx + 150, 1300 + by + Math.sin(S.lt * 2) * 3], 150, 140, -1);
  limb(c, armL); limb(c, armR);
  mitten(c, armL[2][0] + 6, armL[2][1], -0.3, 0.95);
  mitten(c, armR[2][0], armR[2][1], Math.PI / 2 - 0.3, 0.95);
  // shirt
  c.beginPath();
  c.moveTo(cx - 52, 958 + by); c.quadraticCurveTo(cx, 985 + by, cx + 52, 958 + by);
  c.lineTo(cx + 128, 996 + by); c.lineTo(cx + 150, 1078 + by); c.lineTo(cx + 100, 1092 + by);
  c.lineTo(cx + 98, 1228 + by); c.quadraticCurveTo(cx, 1240 + by, cx - 98, 1228 + by);
  c.lineTo(cx - 100, 1092 + by); c.lineTo(cx - 150, 1078 + by); c.lineTo(cx - 128, 996 + by); c.closePath();
  inkFill(c, C.purple, 6);
  c.save(); c.clip(); c.fillStyle = C.purpleDark; c.fillRect(cx + 90, 940 + by, 80, 320); c.restore();
  shirtText(c, 'MOM', cx, 1090 + by, 74, C.white);
  // neck
  rr(c, cx - 15, 900 + by, 30, 64, 10); inkFill(c, C.white, 5);
  // head group (tilt about the neck)
  const hx0 = cx + S.turn * 6, hy0 = 770 + by;
  c.save(); c.translate(hx0, hy0 + 130); c.rotate(S.tilt); c.translate(0, -130);
  const r = 140;
  const hs = -S.turn * 18; // hair shifts opposite the turn
  // back hair
  c.beginPath();
  c.moveTo(hs - 10, -r - 34);
  c.bezierCurveTo(hs + 150, -r - 30, hs + 190, -40, hs + 172, 70);
  c.bezierCurveTo(hs + 165, 130, hs + 200, 170, hs + 232, 168);
  c.bezierCurveTo(hs + 190, 205, hs + 130, 200, hs + 110, 170);
  c.lineTo(hs - 110, 170);
  c.bezierCurveTo(hs - 130, 200, hs - 190, 205, hs - 232, 168);
  c.bezierCurveTo(hs - 200, 170, hs - 165, 130, hs - 172, 70);
  c.bezierCurveTo(hs - 190, -40, hs - 150, -r - 30, hs - 10, -r - 34);
  c.closePath(); inkFill(c, C.hair, 6);
  c.beginPath(); c.moveTo(hs + 120, -60); c.quadraticCurveTo(hs + 160, 40, hs + 150, 120); c.strokeStyle = C.hairHi; c.lineWidth = 6; c.stroke();
  c.beginPath(); c.moveTo(hs - 120, -60); c.quadraticCurveTo(hs - 160, 40, hs - 150, 120); c.stroke();
  // face
  c.beginPath(); c.ellipse(0, 6, r - 6, r, 0, 0, Math.PI * 2); c.fillStyle = C.shade; c.fill();
  c.save(); c.beginPath(); c.ellipse(0, 6, r - 6, r, 0, 0, Math.PI * 2); c.clip();
  c.beginPath(); c.ellipse(12, -6, r - 12, r - 6, 0, 0, Math.PI * 2); c.fillStyle = C.white; c.fill(); c.restore();
  c.beginPath(); c.ellipse(0, 6, r - 6, r, 0, 0, Math.PI * 2); c.lineWidth = LW; c.strokeStyle = C.ink; c.stroke();
  // side-swept bangs
  c.beginPath();
  c.moveTo(hs - 150, -10);
  c.bezierCurveTo(hs - 150, -150, hs + 30, -190, hs + 140, -100);
  c.bezierCurveTo(hs + 80, -130, hs + 10, -110, hs - 40, -60);
  c.bezierCurveTo(hs - 70, -40, hs - 100, -60, hs - 112, -20);
  c.closePath(); inkFill(c, C.hair, 6);
  // features
  const fx = S.turn * 30;
  const lid = S.blink;
  eye(c, fx - 50, 0, 36, 46, S.gazeX, 0.05, lid, 1, true, -1);
  eye(c, fx + 50, 0, 36, 46, S.gazeX, 0.05, lid, 1, true, 1);
  // brows: right (screen-right) brow arches up for the raised-eyebrow look
  const pz = S.puzzled, sk = S.skeptic;
  brow(c, fx - 52, -66, 50, 6 + pz * 6 - sk * 4, -0.12 - pz * 0.15, 6);
  brow(c, fx + 52, -66, 50, 6 + S.browUp * 26 + pz * 18 + sk * 10, 0.12 + S.browUp * 0.18 + pz * 0.1, 6);
  // lips
  const mx = fx + 6, my = 84, o = S.talk;
  if (o > 0.04) {
    c.beginPath(); c.ellipse(mx, my + 2, 22 + 8 * o, 6 + 18 * o, 0, 0, Math.PI * 2); c.fillStyle = '#4A1F27'; c.fill();
    c.lineWidth = 7; c.strokeStyle = C.lip; c.stroke();
  } else {
    const smile = 6 - pz * 8 - sk * 4;
    c.beginPath(); c.moveTo(mx - 30, my); c.quadraticCurveTo(mx, my + smile + 16, mx + 30, my - (pz ? 4 : 0));
    c.quadraticCurveTo(mx, my + smile - 6, mx - 30, my); c.fillStyle = C.lip; c.fill();
    c.lineWidth = 3; c.strokeStyle = C.lipDark; c.stroke();
  }
  c.restore();
  c.restore();
}

/* ============================================================
 * Compositor
 * ============================================================ */
function drawScene(c, t) {
  c.setTransform(1, 0, 0, 1, 0, 0);
  const D = dadState(t), M = momState(t);
  const openAmt = clamp(Math.sin(D.th) * 1.1 + (D.th > Math.PI / 2 ? 1 : 0), 0, 1);
  kitchen(c, D.th > 0.02 ? Math.min(1, D.th / 1.2) : 0);
  fridge(c, D.th);
  // open-fridge light glow over the interior opening
  if (D.th > 0.02) {
    const g = c.createRadialGradient(840, 1050, 20, 860, 1050, 340);
    g.addColorStop(0, `rgba(255,250,225,${0.35 * Math.min(1, D.th / 1.2)})`); g.addColorStop(1, 'rgba(255,250,225,0)');
    c.fillStyle = g; c.fillRect(500, 650, 580, 850);
  }
  // contact shadows
  c.fillStyle = 'rgba(80,50,20,0.16)';
  c.beginPath(); c.ellipse(196, 1780, 135, 20, 0, 0, Math.PI * 2); c.fill();
  c.beginPath(); c.ellipse(515, 1780, 145, 20, 0, 0, Math.PI * 2); c.fill();
  drawMom(c, t, M);
  drawDad(c, t, D);
  void openAmt;
}

const main = document.getElementById('c');
const M_ = main.getContext('2d');
const work = document.createElement('canvas'); work.width = W; work.height = H;
const S_ = work.getContext('2d');
const SUB = 3, SHUTTER = 0.5 / FPS;
function renderFrame(t) {
  for (let i = 0; i < SUB; i++) {
    const st = clamp(t + (i / SUB - 0.5) * SHUTTER + SHUTTER / (2 * SUB), 0, DUR - 1e-3);
    drawScene(S_, st);
    M_.globalAlpha = 1 / (i + 1); M_.drawImage(work, 0, 0);
  }
  M_.globalAlpha = 1;
}
window.renderFrame = renderFrame;
window.DUR = DUR; window.FPS = FPS;
window.ready = document.fonts.load('900 90px "Inter Display"').then(() => true);

(function preview() {
  if (new URLSearchParams(location.search).has('render')) return;
  const scrub = document.getElementById('scrub'), tc = document.getElementById('tc'), btn = document.getElementById('play');
  let playing = false, start = 0, t0 = 0;
  const show = t => { renderFrame(t); scrub.value = t; tc.textContent = t.toFixed(2); };
  scrub.oninput = () => { playing = false; show(+scrub.value); };
  btn.onclick = () => { playing = !playing; start = performance.now(); t0 = +scrub.value % DUR; if (playing) loop(); };
  function loop() { if (!playing) return; show((t0 + (performance.now() - start) / 1000) % DUR); requestAnimationFrame(loop); }
  window.ready.then(() => show(0));
})();
