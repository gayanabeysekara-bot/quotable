// Episode 1 — The Snake That Was Never There (rope & snake: adhyasa / superimposition)
var EP = {
  num: 1, title: 'The Snake That Was Never There', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: "You've been afraid of a snake your whole life.", sfx: 'boom', p: .2 },
    { s: 'hook', t: 'And it was never even there.', sfx: 'hiss', p: .5 },
    { s: 'walk', t: 'Ancient India. A man is walking home at dusk.' },
    { s: 'walk', t: 'The light is fading. Fast.', p: .4 },
    { s: 'freeze', t: 'Suddenly, he freezes.', sfx: 'whoosh', p: .25 },
    { s: 'freeze', t: 'Right there on the path... a SNAKE!', say: 'Right there on the path... a snake!', sfx: 'boom@1.1 hiss@1.2', p: .5, color: '#ff6b6b' },
    { s: 'panic', t: 'His heart is pounding.', sfx: 'heartbeat' },
    { s: 'panic', t: "He's sweating.", p: .2 },
    { s: 'panic', t: "He's already writing his will in his head.", p: .5 },
    { s: 'lamp', t: 'Then a neighbour strolls by, carrying a lamp.' },
    { s: 'lamp', t: "Uh... friend? That's a rope.", v: 'am_puck', sp: 1.0, sfx: 'chime', p: .6, color: '#7ee0d6' },
    { s: 'question', t: "Now here's the strange part.", p: .2 },
    { s: 'question', t: 'Where did the snake go?', sfx: 'pop', p: .6 },
    { s: 'never', t: 'Nowhere.', p: .3 },
    { s: 'never', t: 'It was never there.', p: .25 },
    { s: 'never', t: 'Not for one second did the rope become a snake.', p: .25 },
    { s: 'never', t: 'The snake lived only in the dim light... and in his mind.', p: .5 },
    { s: 'name', t: 'Shankara called this mistake adhyasa:', say: 'The sage Shankara called this mistake, adh-yaasa.', sfx: 'gong', p: .2 },
    { s: 'name', t: 'seeing one thing as another.', p: .5 },
    { s: 'us', t: "And Vedanta says, that's exactly our problem.", sfx: 'whoosh' },
    { s: 'us', t: 'In dim light, we look at ourselves...' },
    { s: 'us', t: 'and see something small and scared.', p: .2 },
    { s: 'us', t: "I'm my body. My job. My worries. What they think of me.", p: .3 },
    { s: 'us', t: "That's the snake.", sfx: 'hiss', p: .5, color: '#ff6b6b' },
    { s: 'rope', t: 'The rope is what you really are.', sfx: 'chime' },
    { s: 'rope', t: 'Pure awareness. Calm. Whole. Never bitten.', p: .4 },
    { s: 'lamp2', t: "Vedanta doesn't ask you to fight the snake.", p: .2 },
    { s: 'lamp2', t: 'It just hands you a lamp.', p: .25 },
    { s: 'lamp2', t: 'And that lamp is knowledge.', p: .5 },
    { s: 'end', t: 'Next: ten men cross a river, and one goes missing.', sfx: 'whoosh' },
    { s: 'end', t: 'Or does he? Follow, so you don\'t miss it.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const traveler = (o) => person(Object.assign({ cloth: '#f4ead5', cloth2: '#d9c9a8', shawl: PAL.saffron, turban: '#9b2335', skin: PAL.skin }, o));
  const neighbor = (o) => person(Object.assign({ cloth: '#2a9d8f', cloth2: '#1d6f65', beard: true, hair: 'bald', turban: '#f4ead5', skin: PAL.skin2 }, o));

  // a coil drawn in perspective; k=0 rope, k=1 snake
  function coil(cx, cy, r, k, t = 0, sc = 1) {
    const pts = []; const turns = 2.6, n = 120;
    for (let i = 0; i <= n; i++) {
      const a = i / n * turns * Math.PI * 2;
      const rr = r * (.22 + .78 * i / n);
      pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .42]);
    }
    // tail that leads out to a "head"
    const last = pts[pts.length - 1];
    const hx = last[0] + 120 * sc, hy = last[1] - 70 * sc - (k * Math.sin(t * 3) * 10);
    let d = `M${pts.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L')} Q${last[0] + 80 * sc} ${last[1] + 10} ${hx} ${hy}`;
    const rope = path(d, 'none', '#c9a26b', 30 * sc) + path(d, 'none', '#8a6a3a', 30 * sc, 'stroke-dasharray="6 18" opacity=".8"') + path(d, 'none', '#e8c98f', 8 * sc, 'opacity=".5"');
    const snake = path(d, 'none', '#2f6b3a', 34 * sc) + path(d, 'none', '#a8d06a', 12 * sc, 'stroke-dasharray="14 16"') +
      g(`<ellipse cx="0" cy="0" rx="${46 * sc}" ry="${30 * sc}" fill="#2f6b3a"/>` + circ(-14 * sc, -10 * sc, 9 * sc, '#ffdd00') + circ(14 * sc, -10 * sc, 9 * sc, '#ffdd00') +
        `<ellipse cx="${-14 * sc}" cy="${-10 * sc}" rx="${2.5 * sc}" ry="${8 * sc}" fill="#000"/><ellipse cx="${14 * sc}" cy="${-10 * sc}" rx="${2.5 * sc}" ry="${8 * sc}" fill="#000"/>` +
        (Math.sin(t * 8) > 0 ? path(`M0 ${24 * sc} l0 ${30 * sc} l-10 ${12 * sc} M0 ${54 * sc} l10 ${12 * sc}`, 'none', PAL.red, 5 * sc) : ''), `translate(${hx} ${hy})`);
    const ropeEnd = circ(hx, hy, 16 * sc, '#c9a26b') + path(`M${hx} ${hy} l18 -8 M${hx} ${hy} l16 10 M${hx} ${hy} l20 2`, 'none', '#8a6a3a', 5 * sc);
    return g(rope + ropeEnd, '', 1 - k) + g(snake, '', k);
  }
  const duskSky = (dim) => sky([[0, '#1d1442'], [.45, lerp(0, 1, 1) && '#5b2a6e'], [.75, '#c2547a'], [1, '#f2a65a']]) + rect(0, 0, W, H, '#0b0b2b', 0, `opacity="${dim}"`);
  const ground = (y = 1150) => rect(0, y, W, H - y, '#2b1d3f') + path(`M380 ${y} L700 ${y} L1080 1900 L0 1900 Z`, '#4a3555') + hills(y + 2, '#22163a', 40, 5);

  S.hook = ({ lt, at }) => {
    const k1 = .45 + .55 * tw(lt, 0, .8), k2 = tw(lt, at(1), .6);
    return rect(0, 0, W, H, '#07051a') + stars(lt, 50, 3, 1900, .5) +
      g(coil(540, 860, 230, 1, lt, 1.6), `translate(0 ${(1 - k1) * 80})`, k1 * (1 - k2 * .55)) +
      glow(540, 860, 520, 'W', k2 * .35) +
      pop(text(540, 1240, 'IT WAS NEVER THERE.', { size: 92, fill: PAL.gold, stroke: '#07051a', sw: 12 }), 540, 1220, tw(lt, at(1) + .9, .5, E.back));
  };
  S.walk = ({ lt, d }) => {
    const sun = 1060 + lt * 25;
    const x = 180 + lt * 55;
    return duskSky(clamp(lt / d) * .5) + circ(760, sun, 90, '#ffb36b') + glow(760, sun, 260, 'W', .5) + stars(lt, 40, 9, 700, clamp(lt / d)) +
      hills(1010, '#3a2552', 70, 2) + ground() +
      traveler({ x, y: 1240, s: .95, walk: lt * 7, armL: 15 + Math.sin(lt * 7) * 15, armR: 15 - Math.sin(lt * 7) * 15, face: 'calm', bob: -Math.abs(Math.sin(lt * 7)) * 6 });
  };
  S.freeze = ({ lt, at }) => {
    const kz = tw(lt, at(1), .5, E.back);
    const snakeK = tw(lt, at(1) + .9, .25);
    const shake = snakeK * Math.sin(lt * 70) * 6;
    return g(duskSky(.65) + stars(lt, 40, 9, 700, .9) + hills(1010, '#2a1b40', 70, 2) + ground() +
      coil(760, 1180, 90 + kz * 10, snakeK, lt, .85) + glow(760, 1180, 200, 'B', snakeK * .3) +
      traveler({ x: 410 + shake, y: 1240, s: .95, face: snakeK > .5 ? 'scared' : 'surprised', armL: 30 + snakeK * 110, armR: 30 + snakeK * 110, lean: -snakeK * 8 }),
      `translate(540 1100) scale(${1 + kz * .15}) translate(-540 -1100)`);
  };
  S.panic = ({ lt, at }) => {
    const beat = Math.pow(Math.abs(Math.sin(lt * 4.2)), 8);
    const willK = tw(lt, at(2), .5, E.back);
    return rect(0, 0, W, H, '#3a0d2e') + glow(540, 900, 900, 'W', .12 + beat * .1) +
      g(circ(0, 0, 70, PAL.red) + path('M-40 -10 Q-40 -50 0 -20 Q40 -50 40 -10 Q40 30 0 60 Q-40 30 -40 -10 Z', '#ff8fa3'), `translate(850 1000) scale(${1 + beat * .35})`, tw(lt, 0, .3)) +
      person({ x: 470, y: 1700, s: 1.7, cloth: '#f4ead5', shawl: PAL.saffron, turban: '#9b2335', face: 'scared', sweat: tw(lt, at(1), .3) * lt * 1.5, armL: 150, armR: 150 + Math.sin(lt * 30) * 4, bob: Math.sin(lt * 40) * 3 }) +
      pop(g(rect(-210, -150, 420, 300, '#fff4dc', 20) + text(0, -80, 'MY WILL', { size: 52, fill: PAL.ink }) +
        text(0, -20, '1. Goat → wife', { size: 36, fill: PAL.ink, weight: 600 }) + text(0, 30, '2. Other goat → wife', { size: 36, fill: PAL.ink, weight: 600 }) + text(0, 80, '3. Sorry about the roof', { size: 34, fill: PAL.ink, weight: 600 }), 'translate(560 520) rotate(5)'), 560, 520, willK);
  };
  S.lamp = ({ lt, at }) => {
    const nx = lerp(1200, 860, tw(lt, 0, 2.2, E.io));
    const light = tw(lt, at(1) - .3, .8);
    return duskSky(.85) + stars(lt, 50, 9, 800, 1) + hills(1010, '#1c1233', 70, 2) + ground() +
      glow(nx - 60, 1000, 600, 'W', light * .6 + .2) +
      coil(560, 1180, 100, 1 - light, lt, .85) + motes(lt, 24, 560, 1170, 160, PAL.gold, 4, light) +
      traveler({ x: 250, y: 1240, s: .95, face: light > .6 ? 'surprised' : 'scared', armL: 40, armR: 60 }) +
      neighbor({ x: nx, y: 1240, s: .95, flip: true, face: light > .3 ? 'happy' : 'calm', armR: 70, walk: lt < 2.2 ? lt * 7 : 0, prop: P.lamp(lt, 1) }) +
      bubble(760, 760, "Uh... friend? That's a rope.", tw(lt, at(1), .4), { w: 600, size: 58, tail: 'right' });
  };
  S.question = ({ lt, at }) => {
    const qk = tw(lt, at(1), .5, E.back);
    return rect(0, 0, W, H, '#140c33') + stars(lt, 60, 21, 1900, .6) +
      coil(540, 1080, 140, 0, lt, 1.1) + glow(540, 1050, 420, 'W', .25) +
      pop(text(540, 830, '?', { size: 420, fill: PAL.gold, stroke: '#140c33', sw: 14 }), 540, 700, qk) +
      g(coil(540 + Math.sin(lt * 2) * 30, 520, 60, 1, lt, .5), '', .25 * (1 - qk));
  };
  S.never = ({ lt, at }) => {
    const ks = [0, 1, 2, 3].map(i => tw(lt, at(i), .5, E.back));
    const mind = tw(lt, at(3) + 1.6, .6, E.back);
    let s = rect(0, 0, W, H, '#140c33') + stars(lt, 60, 21, 1900, .6) + glow(540, 900, 600, 'W', .2);
    s += g(coil(540, 1040, 140, 0, lt, 1.1), '', 1 - mind * .7);
    s += pop(text(540, 560, 'NOWHERE.', { size: 120, fill: PAL.cream }), 540, 520, ks[0] * (1 - ks[1]));
    s += pop(g(text(540, 520, 'ROPE', { size: 110, fill: '#e8c98f' }) + text(540, 640, '≠ ever ≠', { size: 64, fill: PAL.cream, weight: 600 }) + text(540, 760, 'SNAKE', { size: 110, fill: '#7bd389' }), '', 1), 540, 640, ks[2] * (1 - mind));
    // head with snake in thought bubble
    s += pop(g(person({ x: 330, y: 1300, s: 1.1, cloth: '#f4ead5', shawl: PAL.saffron, turban: '#9b2335', face: 'surprised', look: 1 }) +
      circ(560, 640, 26, '#fff') + circ(620, 560, 38, '#fff') + `<ellipse cx="800" cy="450" rx="230" ry="170" fill="#fff"/>` + coil(780, 470, 70, 1, lt, .6)), 540, 900, mind);
    return s;
  };
  S.name = ({ lt, at }) => {
    const k = tw(lt, 0, .7, E.back), k2 = tw(lt, at(1), .6, E.out);
    return sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + glow(540, 760, 700, 'W', .3) + motes(lt, 30, 540, 900, 300, PAL.gold, 8, .7) +
      pop(text(540, 640, 'ADHYASA', { size: 150, fill: PAL.gold, ls: 6, stroke: '#1d1442', sw: 10 }), 540, 600, k) +
      text(540, 730, 'अध्यास', { size: 70, fill: PAL.cream, op: k * .8, weight: 600 }) +
      g(coil(330, 1060, 80, 0, lt, .7) + text(540, 1070, '→', { size: 120, fill: PAL.cream }) + coil(720, 1060, 80, 1, lt, .7), `translate(0 ${(1 - k2) * 60})`, k2);
  };
  S.us = ({ lt, at, d }) => {
    const labels = ['my body', 'my job', 'my worries', 'what they think', 'my past', 'my bank balance'];
    const labK = tw(lt, at(3) - .3, .8);
    const snK = tw(lt, at(4), .6);
    const small = tw(lt, at(1), 1.2, E.io);
    let s = sky([[0, '#16112e'], [1, '#2b1d3f']]) + stars(lt, 40, 5, 1000, .4) + rect(0, 1240, W, 700, '#1c1433');
    s += person({ x: 540, y: 1240, s: lerp(1.1, .8, small), cloth: '#3d5a80', cloth2: '#293f5c', hair: 'short', face: small > .4 ? 'sad' : 'neutral', armL: 8, armR: 8, op: 1 });
    // dim spotlight
    s += glow(540, 1050, 420, 'W', .15);
    labels.forEach((L, i) => {
      const a = i / labels.length * Math.PI * 2 + lt * .5;
      const x = 540 + Math.cos(a) * 330, y = 960 + Math.sin(a) * 260;
      s += pop(g(rect(x - 175, y - 48, 350, 86, 'rgba(255,255,255,.12)', 37, 'stroke="rgba(255,255,255,.35)" stroke-width="2"') + text(x, y + 16, L, { size: 48, fill: PAL.cream, weight: 600 })), x, y, tw(labK, i / 8, .25, E.back) * (1 - snK * .6));
    });
    // the snake made of all those labels
    let d2 = ''; for (let i = 0; i <= 80; i++) { const a = i / 80 * Math.PI * 4 + lt * .5; const r = 120 + i * 2.6; d2 += (i ? ' L' : 'M') + (540 + Math.cos(a) * r).toFixed(1) + ' ' + (980 + Math.sin(a) * r * .7).toFixed(1); }
    s += g(path(d2, 'none', '#2f6b3a', 30) + path(d2, 'none', '#a8d06a', 10, 'stroke-dasharray="14 16"'), '', snK * .9);
    return s;
  };
  S.rope = ({ lt, at }) => {
    const k = tw(lt, 0, 1.5, E.io), k2 = tw(lt, at(1), 2);
    const words = ['AWARENESS', 'CALM', 'WHOLE', 'NEVER BITTEN'];
    let s = sky([[0, '#2a1b4d'], [.6, '#5b2a6e'], [1, '#f2a65a']]) + rect(0, 0, W, H, '#0b0b2b', 0, `opacity="${.6 - k * .5}"`);
    s += glow(540, 940, 760, 'W', k * .8) + motes(lt, 40, 540, 1000, 300, '#fff', 6, k);
    s += person({ x: 540, y: 1240, s: 1.1, cloth: '#3d5a80', cloth2: '#293f5c', face: 'calm', armL: 40 * k, armR: 40 * k });
    words.forEach((w, i) => { s += pop(text(540, 430 + i * 92, w, { size: 72, fill: i === 3 ? PAL.gold : PAL.cream, stroke: '#2a1b4d', sw: 8 }), 540, 410 + i * 92, tw(lt, at(1) + i * .55, .4, E.back)); });
    return s;
  };
  S.lamp2 = ({ lt, at }) => {
    const k = tw(lt, at(1), .6, E.back), k3 = tw(lt, at(2), .8);
    return rect(0, 0, W, H, '#100a26') + stars(lt, 50, 2, 1900, .6) +
      glow(540, 900, 300 + k3 * 500, 'W', .3 + k * .5) +
      pop(g(P.lamp(lt, k), 'translate(540 1000) scale(3.2)'), 540, 1000, k) +
      pop(text(540, 560, 'KNOWLEDGE', { size: 120, fill: PAL.gold, stroke: '#100a26', sw: 10 }), 540, 520, k3) +
      text(540, 650, 'jnana · ज्ञान', { size: 60, fill: PAL.cream, op: k3, weight: 600 });
  };
  S.end = ({ lt, at }) => {
    const k = tw(lt, .1, .6, E.back), kf = tw(lt, at(1) + .7, .5, E.back);
    let s = sky([[0, '#0b3d5c'], [1, '#0b0b2b']]) + stars(lt, 40, 31, 900, .5);
    s += pop(text(540, 470, 'NEXT EPISODE', { size: 56, fill: PAL.saffron, ls: 8 }) + text(540, 590, 'The Tenth Man', { size: 120, fill: PAL.cream, stroke: '#0b0b2b', sw: 10 }), 540, 520, k);
    // river with men
    s += path(`M0 1060 Q270 ${1030 + Math.sin(lt * 2) * 10} 540 1060 T1080 1060 L1080 1180 Q810 1150 540 1180 T0 1180 Z`, PAL.sea1, 'none', 0, 'opacity=".8"');
    for (let i = 0; i < 9; i++) s += person({ x: 130 + i * 102, y: 1290, s: .42, cloth: ['#e76f51', '#2a9d8f', '#e9c46a', '#f4a261', '#8ab17d', '#9b5de5', '#f15bb5', '#00bbf9', '#fee440'][i], face: 'sad', bob: Math.sin(lt * 4 + i) * 4 });
    s += pop(text(980, 1210, '?', { size: 150, fill: PAL.gold }), 980, 1160, tw(lt, .8, .5, E.back));
    s += pop(g(rect(330, 820, 420, 110, PAL.red, 55) + text(540, 893, 'FOLLOW', { size: 64, fill: '#fff', ls: 4 })), 540, 875, kf);
    return s;
  };
})();
