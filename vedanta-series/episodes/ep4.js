// Episode 4 — The Wave Who Was Afraid (jiva and Brahman, nama-rupa: name and form)
var EP = {
  num: 4, title: 'The Wave Who Was Afraid', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'A little wave was having a panic attack.', sfx: 'splash', p: .5 },
    { s: 'sea', t: 'Out on the wide ocean, a little wave is rolling along.' },
    { s: 'sea', t: 'Sun on her face. Wind at her back. Living her best life.', p: .4 },
    { s: 'shore', t: 'Then she sees the shore.', sfx: 'boom', p: .3 },
    { s: 'shore', t: 'Up ahead, wave after wave smashes into the rocks...', sfx: 'splash@1.2 splash@2.4' },
    { s: 'shore', t: 'and vanishes.', p: .4 },
    { s: 'fear', t: '"Oh no. That\'s going to be me!"', say: "Oh no. Oh no no no. That's going to be me!", v: 'af_bella', sp: 1.1, color: '#7ee0d6', p: .2 },
    { s: 'fear', t: '"I\'m going to disappear!"', say: "I'm going to disappear!", v: 'af_bella', sp: 1.1, color: '#7ee0d6', p: .5 },
    { s: 'old', t: 'A big, old wave rolls up beside her.' },
    { s: 'old', t: '"Why so scared, little one?"', say: 'Why so scared, little one?', v: 'am_onyx', sp: .9, color: '#ffd166', p: .3 },
    { s: 'old', t: '"Can\'t you see? We\'re all going to crash. We\'ll be nothing!"', say: "Can't you see? We're all going to crash. We'll be nothing!", v: 'af_bella', sp: 1.1, color: '#7ee0d6', p: .5 },
    { s: 'truth', t: 'The old wave laughs.', p: .2 },
    { s: 'truth', t: '"You think you\'re a wave."', say: "You think you're a wave.", v: 'am_onyx', sp: .9, color: '#ffd166', p: .3 },
    { s: 'truth', t: '"You\'re not a wave. You\'re the ocean..."', say: "You're not a wave. You're the ocean...", v: 'am_onyx', sp: .88, sfx: 'chime', color: '#ffd166', p: .2 },
    { s: 'truth', t: '"...doing a wave, for a little while."', say: 'doing a wave, for a little while.', v: 'am_onyx', sp: .88, color: '#ffd166', p: .6 },
    { s: 'cycle', t: 'Before she rose: water.', p: .2 },
    { s: 'cycle', t: 'While she rolls: water.', p: .2 },
    { s: 'cycle', t: 'After she crashes... still water.', sfx: 'splash', p: .6 },
    { s: 'map', t: 'Vedanta says, this is you.', sfx: 'whoosh', p: .2 },
    { s: 'map', t: 'The wave is the little "me" you think you are. The jiva.', say: 'The wave is the little me, you think you are. The jeeva.', p: .3 },
    { s: 'map', t: 'The ocean is Brahman. The one reality behind everything.', say: 'The ocean is Brahman. The one reality behind everything.', p: .4 },
    { s: 'nama', t: 'Names and shapes come and go. Nama-rupa.', say: 'Names and shapes come and go. Naama roopa.', sfx: 'gong', p: .2 },
    { s: 'nama', t: 'The water never does.', p: .4 },
    { s: 'close', t: 'Your shape will change.', p: .3 },
    { s: 'close', t: "What you are... won't.", sfx: 'chime', p: .7 },
    { s: 'end', t: 'Next: smash a clay pot. Where does the space inside go?', sfx: 'whoosh' },
    { s: 'end', t: 'Follow for part five.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  // a wave character: curl with a face
  function waveChar(x, y, s, o = {}) {
    const { c1 = '#58c4dd', c2 = '#1b6f8f', face = 'happy', t = 0, eyes = 1 } = o;
    const curl = `M-170 120 Q-150 -40 -20 -110 Q90 -160 150 -80 Q180 -30 130 0 Q90 20 70 -20 Q60 -60 20 -50 Q-60 -20 -60 120 Z`;
    let f = '';
    const ex = [-20, 40], ey = 0;
    if (face === 'happy') f = path(`M${ex[0] - 12} ${ey} q12 -14 24 0`, 'none', PAL.ink, 7) + path(`M${ex[1] - 12} ${ey} q12 -14 24 0`, 'none', PAL.ink, 7) + path('M-6 30 q20 26 40 0 Z', '#5a1e2e');
    if (face === 'scared') f = circ(ex[0], ey, 15, '#fff') + circ(ex[1], ey, 15, '#fff') + circ(ex[0], ey, 6, PAL.ink) + circ(ex[1], ey, 6, PAL.ink) + `<ellipse cx="10" cy="44" rx="12" ry="16" fill="#5a1e2e"/>` + path(`M${ex[0] - 14} -26 l22 -8 M${ex[1] + 14} -26 l-22 -8`, 'none', PAL.ink, 6);
    if (face === 'calm') f = path(`M${ex[0] - 12} ${ey} q12 10 24 0`, 'none', PAL.ink, 7) + path(`M${ex[1] - 12} ${ey} q12 10 24 0`, 'none', PAL.ink, 7) + path('M-4 34 q14 12 28 0', 'none', PAL.ink, 6);
    if (face === 'surprised') f = circ(ex[0], ey, 10, PAL.ink) + circ(ex[1], ey, 10, PAL.ink) + circ(10, 40, 12, '#5a1e2e');
    const foam = [...Array(6)].map((_, i) => circ(-80 + i * 40, -110 + Math.sin(t * 3 + i) * 6 - (i > 3 ? (i - 3) * 20 : 0), 18 - i, '#fff', 'opacity=".9"')).join('');
    return g(path(curl, c1) + path('M-170 120 Q-140 20 -60 120 Z', c2, 'none', 0, 'opacity=".5"') + foam + g(f, '', eyes), `translate(${x} ${y}) scale(${s}) rotate(${Math.sin(t * 2) * 3})`);
  }
  const seaSky = (t, mood = 0) => sky([[0, mood ? '#3a4a6b' : '#9bd4f5'], [.6, mood ? '#6b7a99' : '#cdebff'], [1, mood ? '#8a9ab8' : '#e8f7ff']]) +
    circ(820, 360, 110, mood ? '#dfe6ee' : '#fff3c4') + glow(820, 360, 300, 'W', mood ? .2 : .6);
  const ocean = (t, y = 1050) => waveBand(y, 20, t, '#1b6f8f', { speed: 1.5 }) + waveBand(y + 60, 16, t, '#145a78', { speed: 2, ph: 2 }) + waveBand(y + 160, 14, t, '#0b3d5c', { speed: 2.5, ph: 4 });

  S.hook = ({ lt }) => {
    const shake = Math.sin(lt * 50) * 8;
    return rect(0, 0, W, H, '#0b3d5c') + glow(540, 900, 700, 'B', .4) + ocean(lt, 1200) +
      waveChar(540 + shake, 1000, 2.2, { face: 'scared', t: lt }) +
      pop(text(540, 520, 'PANIC ATTACK', { size: 120, fill: PAL.cream, stroke: '#0b3d5c', sw: 12 }), 540, 480, .6 + .4 * tw(lt, .2, .5, E.back)) +
      g(path(`M${200} 700 l-40 -40 M220 640 l-50 -10 M880 700 l40 -40 M860 640 l50 -10`, 'none', PAL.gold, 8), '', .5 + .5 * Math.sin(lt * 12));
  };
  S.sea = ({ lt }) => seaSky(lt) + ocean(lt, 1050) + waveChar(540 + Math.sin(lt) * 40, 1000 + Math.sin(lt * 2) * 15, 1.4, { face: 'happy', t: lt }) +
    g(path(`M300 600 q20 -20 40 0 q20 -20 40 0`, 'none', '#fff', 8) + path(`M620 520 q16 -16 32 0 q16 -16 32 0`, 'none', '#fff', 7), `translate(${-lt * 20} 0)`);
  S.shore = ({ lt, at }) => {
    let s = seaSky(lt, tw(lt, 0, 1)) + rect(0, 1000, W, H, '#145a78');
    // rocks on the right; waves ahead smash into them
    s += path('M760 1150 Q800 900 920 920 Q1060 900 1080 1000 L1080 1400 L740 1400 Z', '#4a4e69') + path('M820 1000 Q880 960 960 990', 'none', '#6c6f8c', 10);
    for (let i = 0; i < 3; i++) {
      const t0 = at(1) + i * 1.2, k = clamp((lt - t0) / 1.1);
      if (k > 0 && k < 1) { const x = lerp(300, 760, k); s += waveChar(x, 1060, .7 * (1 - k * k), { face: 'scared', t: lt, c1: '#7fd3ea' }); }
      if (lt > t0 + 1.0) s += g(motes(lt - t0, 18, 780, 980, 120, '#fff', 30 + i, 1), '', clamp(1 - (lt - t0 - 1) * .8));
    }
    s += ocean(lt, 1150);
    s += waveChar(220, 1120, 1.0, { face: lt > at(1) ? 'scared' : 'surprised', t: lt });
    return s;
  };
  S.fear = ({ lt }) => {
    const shake = Math.sin(lt * 45) * 10;
    return rect(0, 0, W, H, '#14213d') + glow(540, 900, 600, 'B', .3) + ocean(lt, 1250) + waveChar(540 + shake, 1050, 2, { face: 'scared', t: lt }) +
      g(path('M720 600 q10 20 0 30 q-10 -10 0 -30 Z', '#8fd3ff') + path('M380 640 q10 20 0 30 q-10 -10 0 -30 Z', '#8fd3ff'), `translate(0 ${(lt * 120) % 120})`);
  };
  S.old = ({ lt, at }) => {
    const ox = lerp(1300, 700, tw(lt, 0, 2.2, E.io));
    return seaSky(lt, .6) + ocean(lt, 1150) +
      waveChar(ox, 1000, 2.0, { face: 'calm', t: lt * .7, c1: '#2a8fb0', c2: '#0b3d5c' }) +
      g(path(`M${ox - 40} 860 q30 -10 60 0`, 'none', '#fff', 12), '', .9) + // bushy foam brow
      waveChar(260, 1100, 1.0, { face: 'scared', t: lt }) +
      bubble(700, 640, 'Why so scared, little one?', tw(lt, at(1), .4) * (1 - tw(lt, at(2), .2)), { w: 520, size: 54, tail: 'right' }) +
      bubble(380, 780, "We're all going to crash. We'll be nothing!", tw(lt, at(2), .4), { w: 560, size: 50, tail: 'left' });
  };
  S.truth = ({ lt, at }) => {
    const k = tw(lt, at(2), 2.5, E.io);
    // camera pulls back: the little wave shrinks, the ocean grows to fill everything
    let s = sky([[0, lerp(0, 1, k) > .5 ? '#0b3d5c' : '#3a4a6b'], [1, '#58c4dd']]);
    s += g(ocean(lt, lerp(1150, 700, k)) + rect(0, lerp(1250, 850, k), W, H, '#0b3d5c'), '');
    s += waveChar(540, lerp(1050, 680, k), lerp(1.4, .35, k), { face: k > .3 ? 'surprised' : 'scared', t: lt });
    s += glow(540, 1000, 300 + 700 * k, 'B', .2 + .5 * k);
    s += pop(text(540, 480, 'YOU ARE THE OCEAN', { size: 100, fill: '#fff', stroke: '#0b3d5c', sw: 12 }), 540, 440, tw(lt, at(2) + 1, .5, E.back));
    s += pop(text(540, 1250, '...doing a wave', { size: 72, fill: PAL.gold, stroke: '#0b3d5c', sw: 10 }), 540, 1220, tw(lt, at(3), .4, E.back));
    return s;
  };
  S.cycle = ({ lt, at }) => {
    const ph = lt > at(2) ? 2 : lt > at(1) ? 1 : 0;
    const kk = tw(lt, at(ph), .8, E.io);
    let s = rect(0, 0, W, H, '#0b3d5c') + glow(540, 900, 600, 'B', .35);
    s += rect(0, 1000, W, H, '#145a78') + waveBand(1000, 12, lt, '#1b6f8f', { speed: 1 });
    const h = ph === 0 ? 0 : ph === 1 ? 1 : 1 - kk;
    if (ph === 1) s += waveChar(540, 1000 - kk * 40, kk * 1.3 + .01, { face: 'happy', t: lt });
    if (ph === 2) s += waveChar(540, 1000 + kk * 200, 1.3 * (1 - kk) + .01, { face: 'calm', t: lt }) + g(motes(lt, 20, 540, 1000, 200, '#fff', 4, 1 - kk), '');
    ['BEFORE', 'DURING', 'AFTER'].forEach((w, i) => s += pop(g(rect(70 + i * 320, 1170, 300, 150, i === ph ? PAL.gold : 'rgba(255,255,255,.12)', 30) + text(220 + i * 320, 1235, w, { size: 48, fill: i === ph ? PAL.ink : PAL.cream }) + text(220 + i * 320, 1290, 'water', { size: 40, fill: i === ph ? PAL.ink : PAL.cream, weight: 600 })), 220 + i * 320, 1245, tw(lt, at(i), .4, E.back)));
    s += pop(text(540, 600, 'H₂O ALL ALONG', { size: 90, fill: PAL.cream }), 540, 570, tw(lt, at(2) + 1.2, .5, E.back));
    return s;
  };
  S.map = ({ lt, at }) => {
    const k1 = tw(lt, at(1), .5, E.back), k2 = tw(lt, at(2), .5, E.back);
    let s = sky([[0, '#1d1442'], [1, '#0b3d5c']]) + stars(lt, 40, 3, 900, .5);
    s += ocean(lt, 1050) + rect(0, 1150, W, H, '#0b3d5c');
    s += waveChar(330, 1000, .9, { face: 'calm', t: lt });
    s += pop(g(rect(150, 560, 360, 190, 'rgba(255,255,255,.12)', 30) + text(330, 640, 'WAVE', { size: 56, fill: PAL.cream }) + text(330, 710, 'jiva · “me”', { size: 44, fill: PAL.gold, weight: 600 })) + path('M330 760 l0 120', 'none', PAL.cream, 6, 'stroke-dasharray="10 10"'), 330, 650, k1);
    s += pop(g(rect(570, 560, 380, 190, 'rgba(255,255,255,.12)', 30) + text(760, 640, 'OCEAN', { size: 56, fill: PAL.cream }) + text(760, 710, 'Brahman', { size: 44, fill: PAL.gold, weight: 600 })) + path('M760 760 l0 280', 'none', PAL.cream, 6, 'stroke-dasharray="10 10"'), 760, 650, k2);
    s += glow(760, 1150, 500, 'B', k2 * .4);
    return s;
  };
  S.nama = ({ lt, at }) => {
    const shapes = ['🌊', '💧', '❄️', '☁️'];
    const idx = Math.floor(lt / 1.1) % shapes.length;
    let s = sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + glow(540, 760, 700, 'W', .3) + motes(lt, 30, 540, 900, 300, PAL.gold, 8, .7);
    s += pop(text(540, 600, 'NAMA · RUPA', { size: 120, fill: PAL.gold, ls: 4, stroke: '#1d1442', sw: 10 }), 540, 560, tw(lt, 0, .6, E.back));
    s += text(540, 700, 'नाम रूप  ·  name & form', { size: 56, fill: PAL.cream, weight: 600, op: tw(lt, .3, .5) });
    s += pop(`<text x="540" y="1060" font-size="240" text-anchor="middle">${shapes[idx]}</text>`, 540, 980, E.back(clamp((lt % 1.1) / .3)));
    s += pop(text(540, 1230, 'still water', { size: 70, fill: '#7ee0d6' }), 540, 1200, tw(lt, at(1), .5, E.back));
    return s;
  };
  S.close = ({ lt, at }) => {
    const k = tw(lt, at(1), 1.2, E.io);
    return sky([[0, '#ffb4a2'], [.5, '#e5989b'], [1, '#6d597a']]) + circ(540, 700, 160, '#fff3d6') + glow(540, 700, 500, 'W', .5 + k * .3) +
      ocean(lt * .6, 1050) + rect(0, 1150, W, H, '#0b3d5c') +
      waveChar(540, 1010 + k * 60, 1.1 * (1 - k * .7), { face: 'calm', t: lt }) + glow(540, 1100, 400, 'B', k * .6) + motes(lt, 30, 540, 1050, 300, '#fff', 2, k);
  };
  S.end = ({ lt, at }) => endCard(lt, at, 'The Space in the Pot',
    g(path('M440 880 Q400 900 420 960 Q380 1050 440 1110 L640 1110 Q700 1050 660 960 Q680 900 640 880 Z', PAL.clay) + `<ellipse cx="540" cy="880" rx="100" ry="22" fill="${PAL.clay2}"/>`, '', tw(lt, .3, .5)));
})();
