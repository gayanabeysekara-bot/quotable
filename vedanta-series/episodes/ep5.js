// Episode 5 — The Space in the Pot (ghatakasha: Gaudapada, Mandukya Karika ch. 3 — Atman and Brahman)
var EP = {
  num: 5, title: 'The Space in the Pot', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'Smash a clay pot.', sfx: 'crack', p: .3 },
    { s: 'hook', t: 'What happens to the space that was inside it?', p: .6 },
    { s: 'potter', t: 'A potter spins a lump of clay...' },
    { s: 'potter', t: 'and out comes a pot.', sfx: 'pop', p: .3 },
    { s: 'potter', t: 'Inside it, there is a little bit of space. Pot space.', p: .2 },
    { s: 'potter', t: 'Outside it, the huge, open sky.', p: .5 },
    { s: 'sep', t: 'Now, the pot space looks separate.', p: .2 },
    { s: 'sep', t: 'It has walls. A shape. A size.' },
    { s: 'sep', t: 'Practically its own postcode.', p: .5 },
    { s: 'smoke', t: 'Fill the pot with smoke.', sfx: 'whoosh', p: .2 },
    { s: 'smoke', t: 'Now the pot space looks dirty.', p: .3 },
    { s: 'smoke', t: 'But did the space itself get dirty?', p: .3 },
    { s: 'smoke', t: 'No. Space cannot get dirty. The smoke just passes through it.', p: .5 },
    { s: 'smash', t: 'Now... smash the pot.', sfx: 'crack@1.0', p: .4 },
    { s: 'smash', t: 'Did the space go anywhere?', p: .2 },
    { s: 'smash', t: 'Did it "join" the sky?', p: .4 },
    { s: 'smash', t: 'No. It was never apart. Only the walls made it look that way.', sfx: 'chime', p: .6 },
    { s: 'map', t: 'The sage Gaudapada used this exact picture.', say: 'The sage, Gowda-paada, used this exact picture.', sfx: 'gong' },
    { s: 'map', t: 'The pot is your body and mind.', p: .2 },
    { s: 'map', t: 'The space inside is the Atman. Your true self.', say: 'The space inside is the Aatman. Your true self.', p: .2 },
    { s: 'map', t: 'The open sky is Brahman. The one reality.', p: .5 },
    { s: 'one', t: 'And Atman and Brahman were never two.', say: 'And Aatman and Brahman were never two.', sfx: 'chime', p: .6 },
    { s: 'calm', t: 'Your moods, your bad days, your worst thoughts?', p: .2 },
    { s: 'calm', t: "That's the smoke.", p: .3 },
    { s: 'calm', t: 'It passes through you. It never stains what you are.', p: .6 },
    { s: 'end', t: 'Next: every night you visit three worlds. Something follows you into all of them.', sfx: 'whoosh' },
    { s: 'end', t: 'Follow for part six.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const POT = 'M-150 -170 Q-200 -150 -175 -60 Q-260 60 -170 200 Q-100 260 0 260 Q100 260 170 200 Q260 60 175 -60 Q200 -150 150 -170 Z';
  const INNER = 'M-120 -150 Q-160 -130 -140 -60 Q-220 60 -140 180 Q-80 230 0 230 Q80 230 140 180 Q220 60 140 -60 Q160 -130 120 -150 Z';
  // pot with see-through "x-ray" interior so the space is visible; space fill + optional smoke
  function pot(x, y, s, o = {}) {
    const { spaceK = 0, smoke = 0, t = 0, op = 1, crack = 0 } = o;
    let sm = '';
    if (smoke > 0) { const r = rng(9); for (let i = 0; i < 16; i++) sm += circ(-100 + r() * 200 + Math.sin(t + i) * 20, -100 + r() * 300 + Math.cos(t * .8 + i) * 20, 40 + r() * 50, '#6b6b7b', `opacity="${(smoke * .55).toFixed(2)}"`); }
    const id = 'clip' + Math.round(x) + Math.round(y);
    return g(`<defs><clipPath id="${id}"><path d="${INNER}"/></clipPath></defs>` +
      path(POT, PAL.clay) + path('M-150 -170 Q0 -130 150 -170', 'none', PAL.clay2, 14) +
      path(INNER, '#8ed1fc', 'none', 0, `opacity="${(spaceK * .85).toFixed(2)}"`) + g(sm, '', 1, `clip-path="url(#${id})"`) +
      (spaceK > 0 ? text(0, 60, 'pot space', { size: 46, fill: '#0b3d5c', op: spaceK }) : '') +
      (crack ? path('M-30 -160 l30 80 l-40 60 l50 70 l-20 80', 'none', PAL.ink, 8, `opacity="${crack}"`) : '') +
      `<ellipse cx="0" cy="-170" rx="150" ry="28" fill="${PAL.clay2}"/>`, `translate(${x} ${y}) scale(${s})`, op);
  }
  // shards flying apart after the smash
  function shards(x, y, k) {
    const r = rng(4); let s = '';
    for (let i = 0; i < 14; i++) { const a = r() * 6.283, d = k * (200 + r() * 500); const sx = x + Math.cos(a) * d, sy = y + Math.sin(a) * d * .8 + k * k * 400;
      s += g(path('M0 0 l40 -10 l20 40 l-50 20 Z', i % 2 ? PAL.clay : PAL.clay2), `translate(${sx} ${sy}) rotate(${k * 400 * (r() - .5)})`, clamp(1.4 - k)); }
    return s;
  }
  const bigSky = (k = 1) => sky([[0, '#4cc9f0'], [.6, '#a0e7ff'], [1, '#dff6ff']]) + circ(860, 340, 90, '#fff3c4') + glow(860, 340, 260, 'W', .6) +
    g(`<ellipse cx="220" cy="420" rx="120" ry="40" fill="#fff"/><ellipse cx="300" cy="400" rx="90" ry="50" fill="#fff"/>`, '', .9);

  S.hook = ({ lt, at }) => {
    const sm = tw(lt, .35, 1.6, E.out);
    return rect(0, 0, W, H, '#1d1442') + stars(lt, 40, 1, 1900, .5) + glow(540, 950, 500, 'W', .25) +
      (lt < .4 ? pot(540, 950, 1.5, { spaceK: .6 }) : shards(540, 950, sm) + g(path(INNER, '#8ed1fc', 'none', 0, 'opacity=".5"'), `translate(540 950) scale(${1.5 + sm * 3})`, 1 - sm)) +
      pop(text(540, 560, 'WHERE DID', { size: 110, fill: PAL.cream, stroke: '#1d1442', sw: 10 }) + text(540, 680, 'THE SPACE GO?', { size: 110, fill: PAL.gold, stroke: '#1d1442', sw: 10 }), 540, 620, tw(lt, at(1), .5, E.back));
  };
  S.potter = ({ lt, at }) => {
    const form = tw(lt, at(1) - .3, .8, E.back);
    const spin = lt * 8;
    let s = sky([[0, '#ffe8c2'], [1, '#f6bd60']]) + rect(0, 1200, W, H, '#c08552');
    // wheel
    s += `<ellipse cx="540" cy="1130" rx="260" ry="50" fill="#6d4c41"/>` + `<ellipse cx="540" cy="1120" rx="240" ry="40" fill="#8d6e63"/>` + line(540 + Math.cos(spin) * 200, 1120 + Math.sin(spin) * 30, 540, 1120, '#5d4037', 6);
    s += form < .05 ? `<ellipse cx="540" cy="1060" rx="${110 + Math.sin(lt * 8) * 10}" ry="80" fill="${PAL.clay}"/>` : pot(540, 900, .85 * form, { spaceK: tw(lt, at(2), .8) });
    s += person({ x: 220, y: 1300, s: .85, cloth: '#e9c46a', cloth2: '#c9a227', hair: 'short', face: 'happy', armR: 80, beard: '#3b2a20' });
    s += g(bigSky() , '', 0);
    s += pop(g(rect(640, 340, 380, 120, 'rgba(255,255,255,.7)', 30) + text(830, 420, 'big sky →', { size: 54, fill: '#0b3d5c' })), 830, 400, tw(lt, at(3), .4, E.back));
    return s;
  };
  S.sep = ({ lt, at }) => {
    const k = tw(lt, at(2), .5, E.back);
    return bigSky() + rect(0, 1250, W, H, '#c08552') + pot(540, 1000, 1.2, { spaceK: 1 }) +
      pop(g(rect(-180, -60, 360, 120, '#fff', 16, 'stroke="#c1121f" stroke-width="6"') + text(0, -8, '1 POT LANE', { size: 46, fill: PAL.ink }) + text(0, 38, 'SPACE ONLY · NO SKY', { size: 28, fill: '#c1121f', weight: 700 }), 'translate(800 650) rotate(6)'), 800, 650, k) +
      ['WALLS', 'SHAPE', 'SIZE'].map((w, i) => pop(text(220, 620 + i * 90, w, { size: 64, fill: '#0b3d5c' }), 220, 600 + i * 90, tw(lt, at(1) + i * .5, .3, E.back))).join('');
  };
  S.smoke = ({ lt, at }) => {
    const sm = tw(lt, 0, 1.5);
    const clear = tw(lt, at(3) + 1.5, 1.5);
    let s = bigSky() + rect(0, 1250, W, H, '#c08552') + pot(540, 1000, 1.25, { spaceK: 1, smoke: sm * (1 - clear * .9), t: lt });
    // smoke drifting out of the pot mouth and away, the sky untouched
    const r = rng(2); for (let i = 0; i < 10; i++) { const k = ((lt * .25 + r()) % 1); s += circ(540 + Math.sin(k * 6 + i) * 80 + k * 200, 780 - k * 520, 30 + k * 60, '#6b6b7b', `opacity="${(sm * .4 * (1 - k)).toFixed(2)}"`); }
    s += pop(g(rect(170, 1080, 740, 110, 'rgba(255,255,255,.85)', 55) + text(540, 1155, 'space: still perfectly clean', { size: 52, fill: '#0b3d5c' })), 540, 1135, tw(lt, at(3), .4, E.back));
    return s;
  };
  S.smash = ({ lt, at }) => {
    const hit = tw(lt, 1.0, .01);
    const fly = tw(lt, 1.0, 1.6, E.out);
    const k3 = tw(lt, at(3), 1.2, E.io);
    let s = bigSky() + rect(0, 1250, W, H, '#c08552');
    // hammer swing
    if (lt < 1.1) s += g(rect(-20, 0, 40, 260, '#6d4c41', 10) + rect(-90, -40, 180, 90, '#555', 16), `translate(860 620) rotate(${lerp(-60, 30, tw(lt, .3, .7, E.in))} 0 260)`);
    s += hit < 1 ? pot(540, 1000, 1.25, { spaceK: 1 }) : shards(540, 1000, fly);
    if (hit >= 1) s += g(path(INNER, '#8ed1fc', 'none', 0, `opacity="${(.85 * (1 - k3)).toFixed(2)}"`), 'translate(540 1000) scale(1.25)') + text(540, 1060, 'still here?', { size: 52, fill: '#0b3d5c', op: (1 - k3) * tw(lt, at(1), .3) });
    s += glow(540, 900, 300 + k3 * 700, 'W', k3 * .4);
    s += pop(text(540, 640, 'NEVER APART', { size: 120, fill: '#fff', stroke: '#0b3d5c', sw: 12 }), 540, 600, tw(lt, at(3) + .3, .5, E.back));
    return s;
  };
  S.map = ({ lt, at }) => {
    const ks = [1, 2, 3].map(i => tw(lt, at(i), .5, E.back));
    let s = bigSky() + rect(0, 1250, W, H, '#c08552') + pot(540, 1000, 1.1, { spaceK: 1 });
    s += person({ x: 540, y: 1220, s: .45, cloth: '#3d5a80', face: 'calm', op: ks[0] * .0 });
    const tag = (x, y, a, b, k) => pop(g(rect(x - 190, y - 60, 380, 130, 'rgba(255,255,255,.88)', 30) + text(x, y + 4, a, { size: 52, fill: PAL.ink }) + text(x, y + 52, b, { size: 38, fill: '#c1121f', weight: 700 })), x, y, k);
    s += tag(250, 1340, 'POT', 'body + mind', ks[0]) + path('M300 1270 L400 1150', 'none', PAL.ink, 6, `opacity="${ks[0]}"`);
    s += tag(830, 1340, 'POT SPACE', 'Atman · you', ks[1]) + path('M780 1270 L600 1060', 'none', PAL.ink, 6, `opacity="${ks[1]}"`);
    s += tag(540, 600, 'SKY', 'Brahman', ks[2]);
    return s;
  };
  S.one = ({ lt }) => {
    const k = tw(lt, 0, 2, E.io);
    return sky([[0, '#4cc9f0'], [1, '#dff6ff']]) + glow(540, 900, 900, 'W', .3 + k * .5) + motes(lt, 30, 540, 1000, 400, '#fff', 3, 1) +
      g(text(330, 900, 'ATMAN', { size: 110, fill: '#0b3d5c' }), `translate(${k * 210} 0)`, 1 - k * .99) +
      g(text(750, 900, 'BRAHMAN', { size: 110, fill: '#0b3d5c' }), `translate(${-k * 210} 0)`, 1 - k * .99) +
      pop(text(540, 910, 'ONE', { size: 260, fill: '#fff', stroke: '#0b3d5c', sw: 14 }), 540, 820, tw(lt, 1.6, .6, E.back)) +
      text(540, 1060, 'never two', { size: 60, fill: '#0b3d5c', op: tw(lt, 2, .5), weight: 700 });
  };
  S.calm = ({ lt, at }) => {
    const sm = tw(lt, 0, 1);
    const clear = tw(lt, at(2), 2.5);
    let s = sky([[0, '#2a1b4d'], [1, '#5b2a6e']]) + glow(540, 950, 500, 'W', .3 + clear * .4);
    s += person({ x: 540, y: 1240, s: 1.1, cloth: '#3d5a80', cloth2: '#293f5c', face: clear > .5 ? 'calm' : 'sad', armL: 15, armR: 15 });
    const words = ['stress', 'anger', 'regret', 'fear', 'bad day', 'ugh'];
    words.forEach((w, i) => { const k = ((lt * .18 + i / words.length) % 1); const x = -200 + k * 1500, y = 760 + Math.sin(i * 2 + lt) * 180;
      s += circ(x, y, 90, '#6b6b7b', `opacity="${(.5 * sm * (1 - clear * .7)).toFixed(2)}"`) + text(x, y + 16, w, { size: 44, fill: '#ddd', op: sm * (1 - clear * .7) }); });
    s += motes(lt, 30, 540, 1000, 220, PAL.gold, 7, clear);
    return s;
  };
  S.end = ({ lt, at }) => endCard(lt, at, 'Three Worlds Every Night',
    g(['☀️', '💭', '🌙'].map((e, i) => `<text x="${300 + i * 240}" y="1080" font-size="150" text-anchor="middle">${e}</text>`).join(''), '', tw(lt, .3, .5)));
})();
