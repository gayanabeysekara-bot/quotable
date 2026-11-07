// Episode 2 — The Tenth Man (dasamas tvam asi: the seeker is the sought)
var EP = {
  num: 2, title: 'The Tenth Man', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'Ten men crossed a river.', sfx: 'splash', p: .2 },
    { s: 'hook', t: 'Only nine came out.', sfx: 'boom', p: .3, color: '#ff6b6b' },
    { s: 'hook', t: 'Or did they?', p: .5 },
    { s: 'cross', t: 'Ten friends wade across a fast, wild river.', sfx: 'splash@1.5' },
    { s: 'cross', t: 'They make it. Soaked, but safe.', p: .4 },
    { s: 'count', t: 'On the far bank, the leader counts, just to be sure.', p: .2 },
    { s: 'count', t: 'One, two, three, four, five, six, seven, eight... nine.', say: 'One. Two. Three. Four. Five. Six. Seven. Eight... nine.', sp: 1.05, p: .3 },
    { s: 'count', t: 'Nine?!', v: 'am_puck', sfx: 'boom', p: .5, color: '#ff6b6b' },
    { s: 'recount', t: 'He counts again. Nine.', p: .2 },
    { s: 'recount', t: 'Another man tries. Nine!', p: .2 },
    { s: 'recount', t: 'Every single one of them gets... nine.', p: .5 },
    { s: 'cry', t: '"Our friend has drowned!"', say: 'Our friend has drowned!', v: 'am_puck', p: .2, color: '#7ee0d6' },
    { s: 'cry', t: 'They sit on the bank and weep.', p: .2 },
    { s: 'cry', t: 'One of them starts writing a sad song about him.', p: .5 },
    { s: 'sage', t: 'A wise old traveller walks by.', sfx: 'chime' },
    { s: 'sage', t: '"Why all the tears?"', say: 'Why all the tears?', v: 'bm_lewis', sp: .95, color: '#ffd166' },
    { s: 'sage', t: '"We were ten. Now we are only nine!"', say: 'We were ten. Now we are only nine!', v: 'am_puck', p: .5, color: '#7ee0d6' },
    { s: 'reveal', t: 'The old man smiles. He lines them up, and counts.', p: .2 },
    { s: 'reveal', t: 'One, two, three, four, five, six, seven, eight, nine...', say: 'One, two, three, four, five, six, seven, eight, nine...', v: 'bm_lewis', sp: 1.1, p: .4, color: '#ffd166' },
    { s: 'reveal', t: '"...and you are the tenth."', say: 'And you... are the tenth.', v: 'bm_lewis', sp: .9, sfx: 'chime', p: .8, color: '#ffd166' },
    { s: 'lesson', t: 'Each man counted everyone...', p: .2 },
    { s: 'lesson', t: 'except himself.', sfx: 'pop', p: .6 },
    { s: 'us', t: 'Vedanta says, we all do this.', sfx: 'whoosh' },
    { s: 'us', t: 'We search for peace, for joy, for God, out there.' },
    { s: 'us', t: 'In things. In places. In people.', p: .3 },
    { s: 'us', t: 'We count everything, except the one who is counting.', p: .6 },
    { s: 'name', t: 'The old teachers put it in three words:', sfx: 'gong', p: .2 },
    { s: 'name', t: 'Dashamas tvam asi.', say: 'Dasha-mas, tvam asi.', sp: .85, p: .2, color: '#ffd166' },
    { s: 'name', t: 'You are the tenth.', p: .4 },
    { s: 'mirror', t: 'What you are looking for...', p: .2 },
    { s: 'mirror', t: 'is the one who is looking.', sfx: 'chime', p: .7 },
    { s: 'end', t: 'Next: a father, a lump of salt, and the biggest idea in India.', sfx: 'whoosh' },
    { s: 'end', t: 'Follow for part three.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const COLS = ['#e76f51', '#2a9d8f', '#e9c46a', '#f4a261', '#8ab17d', '#9b5de5', '#f15bb5', '#00bbf9', '#fee440', '#ff9933'];
  const LEADER = 9; // the orange one
  const man = (i, o) => person(Object.assign({ cloth: COLS[i], cloth2: COLS[i], turban: i % 3 === 0 ? '#f4ead5' : null, hair: i % 3 === 0 ? 'bald' : 'short', skin: i % 2 ? PAL.skin : PAL.skin2, s: .55 }, o));
  const river = (t, y = 1000) => sky([[0, '#ffd6a5'], [.5, '#ffb4a2'], [1, '#e5989b']]) + circ(820, 520, 110, '#fff3d6') + hills(820, '#b5838d', 60, 4) +
    rect(0, y - 40, W, 80, '#6d597a') + waveBand(y, 14, t, PAL.sea1, { speed: 2 }) + waveBand(y + 40, 10, t, PAL.sea2, { speed: 3, ph: 1 }) + waveBand(y + 120, 12, t, '#1b6f8f', { speed: 2.5, ph: 2 });
  const bank = (y = 1150) => rect(0, y, W, H - y, '#7a9e7e') + path(`M0 ${y} Q540 ${y - 30} 1080 ${y} L1080 ${y + 30} L0 ${y + 30} Z`, '#5d8a63');
  const lineup = (lt, o = {}) => { let s = ''; for (let i = 0; i < 10; i++) { const x = 95 + i * 99; s += man(i, Object.assign({ x, y: 1300, bob: Math.sin(lt * 3 + i) * 3, face: 'neutral' }, (o.per || (() => ({})))(i))); } return s; };
  const numTag = (x, y, n, k, col = PAL.gold) => pop(circ(x, y, 40, col) + text(x, y + 18, String(n), { size: 54, fill: PAL.ink }), x, y, k);

  S.hook = ({ lt, at }) => {
    const k2 = tw(lt, at(1), .4, E.back), k3 = tw(lt, at(2), .5, E.back);
    return rect(0, 0, W, H, '#0e1a33') + waveBand(1150, 18, lt, PAL.sea0, { speed: 2 }) + waveBand(1200, 12, lt, PAL.sea1, { speed: 3 }) +
      pop(text(540, 760, '10', { size: 360, fill: PAL.cream, stroke: '#0e1a33', sw: 14 }), 540, 640, (1 - k2) * (.6 + .4 * tw(lt, 0, .4, E.back))) +
      pop(text(540, 760, '9', { size: 380, fill: '#ff6b6b', stroke: '#0e1a33', sw: 14 }), 540, 640, k2) +
      pop(text(540, 960, 'OR DID THEY?', { size: 90, fill: PAL.gold }), 540, 930, k3);
  };
  S.cross = ({ lt, d }) => {
    let s = river(lt, 1010);
    for (let i = 0; i < 10; i++) {
      const x = lerp(-120 - i * 70, 1250 - i * 70 - 300, clamp(lt / d)) + (i % 2) * 30;
      const y = 1180 + (i % 3) * 22;
      s += g(man(i, { x, y, walk: lt * 6 + i, face: 'scared', armL: 120, armR: 120 }), '', 1);
    }
    s += waveBand(1170, 12, lt, 'rgba(27,111,143,.85)', { speed: 3, ph: 3 }) + waveBand(1240, 10, lt, 'rgba(88,196,221,.7)', { speed: 4, ph: 4 });
    return s;
  };
  S.count = ({ lt, at, dl }) => {
    let s = river(lt, 900) + bank(1150);
    s += lineup(lt, { per: i => i === LEADER ? { face: tw(lt, at(2), .2) > .5 ? 'scared' : 'neutral', armR: 95 + Math.sin(lt * 6) * 10, flip: true } : {} });
    for (let n = 1; n <= 9; n++) {
      const ta = at(1) + dl(1) * (n / 9) * .92;
      s += numTag(95 + (n - 1) * 99, 1010, n, tw(lt, ta, .25, E.back));
    }
    s += pop(text(540, 680, 'NINE?!', { size: 200, fill: '#ff6b6b', stroke: '#fff', sw: 10 }), 540, 620, tw(lt, at(2), .35, E.back));
    return s;
  };
  S.recount = ({ lt, at }) => {
    let s = river(lt, 900) + bank(1150) + lineup(lt, { per: i => ({ face: 'surprised' }) });
    // three different counters, each skipping themselves (shown as a missing number on their own head)
    const who = [9, 3, 6][Math.min(2, Math.floor(lt > at(2) ? 2 : lt > at(1) ? 1 : 0))];
    s += g(path(`M${95 + who * 99} 940 l-24 -40 h48 Z`, PAL.red), '', .9) + text(95 + who * 99, 880, 'me?', { size: 40, fill: PAL.red, op: .9 });
    const big = lt > at(2) ? 3 : lt > at(1) ? 2 : 1;
    for (let j = 0; j < big; j++) s += pop(text(240 + j * 300, 650, '9', { size: 220, fill: [PAL.gold, '#ff9f1c', '#ff6b6b'][j], stroke: '#fff', sw: 8 }), 240 + j * 300, 580, tw(lt, at(j) + .6, .35, E.back));
    return s;
  };
  S.cry = ({ lt, at }) => {
    let s = sky([[0, '#8d99ae'], [1, '#4a5568']]) + bank(1150);
    for (let i = 0; i < 40; i++) { const x = (i * 97) % W, y = ((lt * 900 + i * 173) % 1400); s += line(x, y, x - 10, y + 40, 'rgba(200,220,255,.5)', 3); }
    s += lineup(lt, { per: i => ({ face: 'sad', bob: Math.sin(lt * 9 + i) * 5 }) });
    for (let i = 0; i < 10; i++) s += path(`M${95 + i * 99 + 16} ${1300 - 200 + ((lt * 120 + i * 30) % 80)} q6 12 0 16 q-6 -4 0 -16 Z`, '#8fd3ff');
    s += pop(g(rect(-220, -90, 440, 180, '#fff4dc', 20) + text(0, -20, '♪ Ode to Number Ten ♪', { size: 38, fill: PAL.ink }) + text(0, 35, '"He was... probably nice"', { size: 34, fill: PAL.ink, weight: 600 }), 'translate(540 640) rotate(-4)'), 540, 640, tw(lt, at(2), .5, E.back));
    return s;
  };
  S.sage = ({ lt, at }) => {
    const sx = lerp(1250, 860, tw(lt, 0, 2, E.io));
    let s = river(lt, 900) + bank(1150);
    for (let i = 0; i < 9; i++) s += man(i, { x: 70 + i * 72, y: 1300, s: .5, face: 'sad', bob: Math.sin(lt * 4 + i) * 3 });
    s += man(LEADER, { x: 720, y: 1300, s: .62, face: 'sad', flip: false, armR: 60 });
    s += person({ x: sx, y: 1300, s: .8, flip: true, cloth: '#f4ead5', cloth2: '#d9c9a8', beard: true, hair: 'bald', shawl: PAL.saffron, face: 'calm', walk: lt < 2 ? lt * 6 : 0, armR: 20 });
    s += bubble(780, 760, 'Why all the tears?', tw(lt, at(1), .4) * (1 - tw(lt, at(2), .2)), { w: 460, size: 56, tail: 'right' });
    s += bubble(420, 860, 'We were ten. Now we are only nine!', tw(lt, at(2), .4) * (1), { w: 560, size: 50, tail: 'right' });
    return s;
  };
  S.reveal = ({ lt, at, dl }) => {
    let s = sky([[0, '#ffd6a5'], [1, '#ffb4a2']]) + bank(1150) + glow(540, 1000, 700, 'W', .25);
    const tapK = tw(lt, at(2), .4, E.back);
    s += lineup(lt, { per: i => i === LEADER ? { face: tapK > .5 ? 'happy' : 'surprised', armL: tapK * 150, armR: tapK * 150 } : { face: tapK > .5 ? 'happy' : 'neutral' } });
    for (let n = 1; n <= 9; n++) s += numTag(95 + (n - 1) * 99, 1010, n, tw(lt, at(1) + dl(1) * (n / 9) * .92, .25, E.back), PAL.cream);
    s += numTag(95 + 9 * 99, 1010, 10, tapK, PAL.saffron);
    s += glow(95 + 9 * 99, 1150, 300, 'W', tapK * .9) + motes(lt, 20, 986, 1150, 120, PAL.gold, 3, tapK);
    s += pop(text(540, 680, 'YOU ARE THE TENTH', { size: 96, fill: PAL.ink, stroke: '#fff', sw: 10 }), 540, 640, tw(lt, at(2) + .5, .5, E.back));
    return s;
  };
  S.lesson = ({ lt, at }) => {
    let s = rect(0, 0, W, H, '#1d1442') + stars(lt, 40, 4, 1900, .5);
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283 + lt * .2; const x = 540 + Math.cos(a) * 300, y = 1000 + Math.sin(a) * 300;
      s += man(i, { x, y: y + 100, s: .45, face: 'neutral', op: i === LEADER ? 1 : 1 - .6 * tw(lt, at(1), .5) }); }
    // the eye of the counter points outward only
    s += pop(g(`<ellipse cx="0" cy="0" rx="120" ry="70" fill="#fff"/>` + circ(0, 0, 44, '#3d5a80') + circ(0, 0, 20, PAL.ink) + circ(12, -12, 8, '#fff')), 540, 1000, tw(lt, 0, .5, E.back));
    s += pop(text(540, 560, 'EXCEPT HIMSELF', { size: 110, fill: PAL.gold }), 540, 520, tw(lt, at(1), .4, E.back));
    return s;
  };
  S.us = ({ lt, at }) => {
    const icons = [['🏠', 'house'], ['💰', 'money'], ['✈️', 'travel'], ['💑', 'love'], ['🏆', 'success'], ['🛍️', 'stuff']];
    let s = sky([[0, '#16112e'], [1, '#2b1d3f']]) + rect(0, 1240, W, 700, '#1c1433');
    const look = Math.sin(lt * 1.6);
    s += person({ x: 540 + look * 40, y: 1240, s: 1, cloth: '#3d5a80', cloth2: '#293f5c', face: 'surprised', look, armR: 100, prop: g(circ(30, -20, 34, 'none', `stroke="${PAL.gold}" stroke-width="10"`) + line(6, 4, -20, 30, PAL.gold, 12), '') });
    icons.forEach(([e, n], i) => {
      const a = i / icons.length * 6.283 + lt * .3, x = 540 + Math.cos(a) * 360, y = 820 + Math.sin(a) * 240;
      s += pop(circ(x, y, 74, 'rgba(255,255,255,.1)') + `<text x="${x}" y="${y + 28}" font-size="80" text-anchor="middle">${e}</text>`, x, y, tw(lt, at(1) + i * .3, .4, E.back));
    });
    s += g(text(540, 1080, 'the counter', { size: 44, fill: PAL.gold, weight: 700 }) + path('M540 1100 l0 40', 'none', PAL.gold, 6), '', tw(lt, at(3), .5));
    return s;
  };
  S.name = ({ lt, at }) => {
    const k = tw(lt, at(1), .6, E.back), k2 = tw(lt, at(2), .5);
    return sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + glow(540, 780, 700, 'W', .3) + motes(lt, 30, 540, 900, 300, PAL.gold, 8, .7) +
      lotus(540, 1150, 1.1, tw(lt, 0, .8), lt) +
      pop(text(540, 620, 'DASHAMAS', { size: 130, fill: PAL.gold, ls: 4, stroke: '#1d1442', sw: 10 }) + text(540, 750, 'TVAM ASI', { size: 130, fill: PAL.gold, ls: 4, stroke: '#1d1442', sw: 10 }), 540, 680, k) +
      text(540, 850, 'दशमस्त्वमसि', { size: 66, fill: PAL.cream, op: k * .85, weight: 600 }) +
      text(540, 940, '“you are the tenth”', { size: 54, fill: PAL.cream, op: k2, weight: 600 });
  };
  S.mirror = ({ lt, at }) => {
    const k = tw(lt, at(1), 1.2, E.io);
    let s = rect(0, 0, W, H, '#0b0b2b') + stars(lt, 60, 12, 1900, .5);
    // magnifying glass sweeping, then turning around to face the viewer
    const ang = lerp(Math.sin(lt * 2) * 30, 0, k);
    const r = lerp(120, 330, k);
    s += glow(540, 900, 500 + k * 300, 'W', .15 + k * .5);
    s += g(circ(0, 0, r, 'rgba(255,255,255,.06)', `stroke="${PAL.gold}" stroke-width="${18 + k * 6}"`) + line(r * .7, r * .7, r * 1.3, r * 1.3, PAL.gold, 30), `translate(540 900) rotate(${ang})`, 1);
    s += g(person({ x: 540, y: 1080, s: .8, cloth: '#3d5a80', cloth2: '#293f5c', face: 'happy' }), '', k);
    s += g(text(540, 600, '?', { size: 220, fill: PAL.cream }), '', 1 - k);
    return s;
  };
  S.end = ({ lt, at }) => endCard(lt, at, 'Salt in the Water',
    g(`<ellipse cx="540" cy="1000" rx="170" ry="40" fill="#cfe8f3"/>` + path('M370 1000 Q370 1110 540 1110 Q710 1110 710 1000', 'rgba(88,196,221,.7)', '#cfe8f3', 8) + circ(540, 880 + Math.min(110, lt * 60), 32, '#fff'), '', tw(lt, .4, .5)));
})();
