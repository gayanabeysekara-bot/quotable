// Episode 6 — Three Worlds Every Night (Mandukya Upanishad: waking, dream, deep sleep, and turiya the witness)
var EP = {
  num: 6, title: 'Three Worlds Every Night', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'Every night, you travel through three different worlds.', sfx: 'boom', p: .2 },
    { s: 'hook', t: 'And someone comes with you to all of them.', p: .6 },
    { s: 'wake', t: 'World one: waking.', sfx: 'pop', p: .2 },
    { s: 'wake', t: 'Emails. Traffic. Bills. That one neighbour with the leaf blower.', p: .5 },
    { s: 'dream', t: 'World two: dreaming.', sfx: 'whoosh', p: .2 },
    { s: 'dream', t: "Suddenly you can fly. You're a king. A tiger is chasing you.", p: .2 },
    { s: 'dream', t: 'And it all feels completely real.', p: .3 },
    { s: 'dream', t: 'Until you wake up. Phew.', p: .5 },
    { s: 'sleep', t: 'World three: deep, dreamless sleep.', sfx: 'gong', p: .3 },
    { s: 'sleep', t: 'No world. No body. No problems. Nothing at all.', p: .5 },
    { s: 'morning', t: 'And yet, in the morning, you say...', p: .2 },
    { s: 'morning', t: '"I slept so well."', say: 'Ahh. I slept so well.', v: 'af_heart', color: '#7ee0d6', p: .5 },
    { s: 'who', t: 'Wait.', sfx: 'boom', p: .3 },
    { s: 'who', t: 'If nothing was there... who knew you slept well?', p: .6 },
    { s: 'witness', t: 'Something was there. Quietly watching all three.', sfx: 'chime', p: .2 },
    { s: 'witness', t: "It didn't wake up. It didn't dream. It didn't fall asleep.", p: .2 },
    { s: 'witness', t: 'It just... knew.', p: .5 },
    { s: 'name', t: 'The Mandukya Upanishad calls it Turiya:', say: 'The Maandookya Upanishad calls it, Tureeya.', sfx: 'gong', p: .2 },
    { s: 'name', t: '"the fourth."', say: 'the fourth.', p: .3 },
    { s: 'name', t: 'Not a fourth world, but the one who sees all three.', p: .5 },
    { s: 'us', t: 'The waking you, the dreaming you, the sleeping you...', p: .2 },
    { s: 'us', t: 'they come and go.', p: .3 },
    { s: 'us', t: 'The one who knows them never leaves.', sfx: 'chime', p: .3 },
    { s: 'us', t: "Vedanta says: that's who you really are. The witness. Sakshi.", say: "Vedanta says, that's who you really are. The witness. Saakshi.", p: .6 },
    { s: 'end', t: 'Final episode: a boy walks into the house of Death, and asks him a question.', sfx: 'whoosh' },
    { s: 'end', t: "Follow. You won't want to miss this one.", p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const hero = o => person(Object.assign({ cloth: '#3d5a80', cloth2: '#293f5c', hair: 'bun', skin: PAL.skin, hairColor: '#2b1a12' }, o));
  // the witness: a soft golden eye-of-light
  const witness = (x, y, s, k, t) => g(glow(0, 0, 260, 'W', .7) + `<ellipse cx="0" cy="0" rx="110" ry="${60 * (.2 + .8 * k)}" fill="#fff8e1"/>` + circ(0, 0, 40 * k, PAL.saffron) + circ(0, 0, 16 * k, PAL.ink) + circ(12, -12, 7 * k, '#fff'), `translate(${x} ${y + Math.sin(t * 1.5) * 10}) scale(${s})`);
  // three worlds as orbs: sun, dream cloud, moon
  const orb = (x, y, r, kind, t, hi = 0) => {
    const c = { wake: ['#ffd166', '#f4a261'], dream: ['#c77dff', '#7b2cbf'], sleep: ['#1b263b', '#0d1b2a'] }[kind];
    const icon = { wake: '☀️', dream: '💭', sleep: '🌙' }[kind];
    return g(glow(0, 0, r * 2, kind === 'dream' ? 'B' : 'W', .3 + hi * .4) + circ(0, 0, r, c[1]) + circ(-r * .15, -r * .15, r * .85, c[0]) + `<text x="0" y="${r * .32}" font-size="${r * .9}" text-anchor="middle">${icon}</text>`, `translate(${x} ${y}) scale(${1 + hi * .12})`);
  };

  S.hook = ({ lt, at }) => {
    const ks = [0, 1, 2].map(i => tw(lt, .2 + i * .5, .5, E.back));
    const wk = tw(lt, at(1) + .6, .8, E.back);
    return rect(0, 0, W, H, '#0b0b2b') + stars(lt, 80, 2, 1900, .7) +
      pop(orb(260, 900, 120, 'wake', lt), 260, 900, ks[0]) + pop(orb(540, 900, 120, 'dream', lt), 540, 900, ks[1]) + pop(orb(820, 900, 120, 'sleep', lt), 820, 900, ks[2]) +
      path('M260 1060 Q540 1220 820 1060', 'none', PAL.gold, 6, `stroke-dasharray="14 14" opacity="${wk}"`) +
      pop(witness(540, 1180, .6, 1, lt), 540, 1180, wk) +
      pop(text(540, 560, '3 WORLDS', { size: 150, fill: PAL.gold, stroke: '#0b0b2b', sw: 12 }) + text(540, 660, 'EVERY NIGHT', { size: 80, fill: PAL.cream }), 540, 600, ks[2]);
  };
  S.wake = ({ lt, at }) => {
    const k = tw(lt, at(1), .3);
    let s = sky([[0, '#bde0fe'], [1, '#e9f5ff']]) + rect(0, 1200, W, H, '#adb5bd');
    for (let i = 0; i < 5; i++) s += rect(40 + i * 210, 640 - (i % 2) * 120, 170, 560 + (i % 2) * 120, ['#8d99ae', '#6c757d', '#adb5bd', '#495057', '#8d99ae'][i], 8);
    s += hero({ x: 540, y: 1300, s: 1, face: 'sad', armL: 10, armR: 100, prop: rect(-26, -60, 52, 90, '#222', 8) });
    const items = [['📧', 220, 520], ['🚗', 820, 540], ['🧾', 260, 820], ['🍂', 840, 840]];
    items.forEach(([e, x, y], i) => s += pop(`<text x="${x}" y="${y + Math.sin(lt * 3 + i) * 10}" font-size="120" text-anchor="middle">${e}</text>`, x, y - 40, tw(lt, at(1) + i * .55, .35, E.back)));
    return s;
  };
  S.dream = ({ lt, at }) => {
    const fly = tw(lt, at(1), 1, E.io), wakeK = tw(lt, at(3), .4);
    let s = sky([[0, '#7b2cbf'], [.5, '#c77dff'], [1, '#ffafcc']]) + stars(lt, 60, 5, 1900, .7);
    for (let i = 0; i < 5; i++) s += `<ellipse cx="${(i * 260 + lt * 60) % 1300 - 100}" cy="${500 + i * 160}" rx="140" ry="50" fill="#fff" opacity=".5"/>`;
    const hy = lerp(1300, 950, fly) + Math.sin(lt * 3) * 20;
    s += hero({ x: 520, y: hy, s: 1, face: lt > at(2) ? 'scared' : 'happy', armL: 160, armR: 160, turban: lt > at(1) + 1 ? null : null, lean: fly * 10 });
    // crown pops on
    s += pop(path('M-60 0 L-60 -60 L-30 -30 L0 -70 L30 -30 L60 -60 L60 0 Z', PAL.gold) + circ(0, -40, 8, PAL.red), 520, hy - 420, tw(lt, at(1) + 1.2, .4, E.back));
    // tiger chasing
    const tx = lerp(-300, 180, tw(lt, at(1) + 2.2, 1.5, E.io));
    s += `<text x="${tx}" y="${hy + 40}" font-size="200" text-anchor="middle">🐅</text>`;
    s += rect(0, 0, W, H, '#fff', 0, `opacity="${(wakeK * (1 - tw(lt, at(3) + .5, .6))).toFixed(2)}"`);
    s += pop(text(540, 600, 'PHEW.', { size: 200, fill: PAL.ink, stroke: '#fff', sw: 12 }), 540, 540, tw(lt, at(3) + .6, .4, E.back));
    return s;
  };
  S.sleep = ({ lt, at }) => {
    const fade = tw(lt, at(1), 2.5, E.io);
    let s = rect(0, 0, W, H, '#05050f') + stars(lt, 30, 8, 1900, .3 * (1 - fade));
    s += g(hero({ x: 540, y: 1100, s: 1, face: 'calm', armL: 10, armR: 10 }), 'rotate(-90 540 1000) translate(-90 -60)', 1 - fade);
    s += g(text(760, 760, 'z', { size: 90, fill: PAL.cream }) + text(820, 680, 'z', { size: 70, fill: PAL.cream }) + text(860, 610, 'z', { size: 50, fill: PAL.cream }), `translate(0 ${-((lt * 30) % 30)})`, 1 - fade);
    ['NO WORLD', 'NO BODY', 'NO PROBLEMS'].forEach((w, i) => s += g(text(540, 1380 + i * 0, ''), ''));
    s += pop(text(540, 600, 'NOTHING.', { size: 150, fill: '#3a3a5a' }), 540, 560, fade);
    return s;
  };
  S.morning = ({ lt, at }) => {
    const k = tw(lt, 0, 1.5);
    let s = sky([[0, '#ffd6a5'], [1, '#fff3d6']]) + circ(820, 400, 120, '#ffd166') + glow(820, 400, 360, 'W', .6 * k);
    s += rect(150, 1060, 780, 60, '#e5989b', 20) + rect(150, 1110, 780, 160, '#b5838d', 20); // bed
    s += hero({ x: 540, y: 1100, s: 1, face: 'happy', armL: 160 * tw(lt, at(1), .5), armR: 160 * tw(lt, at(1), .5) });
    s += bubble(540, 520, 'Ahh, I slept SO well.', tw(lt, at(1), .4), { w: 560, size: 60, tail: 'center' });
    return s;
  };
  S.who = ({ lt, at }) => {
    const k = tw(lt, 0, .3, E.back), k2 = tw(lt, at(1), .5, E.back);
    return rect(0, 0, W, H, '#14082b') + glow(540, 900, 500, 'W', .15) +
      pop(text(540, 700, 'WAIT.', { size: 220, fill: PAL.cream }), 540, 620, k * (1 - k2 * .4)) +
      pop(text(540, 1000, 'WHO KNEW?', { size: 150, fill: PAL.gold, stroke: '#14082b', sw: 10 }), 540, 950, k2) +
      pop(text(540, 1200, '🕵️', { size: 160 }), 540, 1150, tw(lt, at(1) + 1, .4, E.back));
  };
  S.witness = ({ lt, at }) => {
    const k = tw(lt, 0, 1, E.out);
    const ph = Math.floor(lt / 1.3) % 3;
    let s = rect(0, 0, W, H, '#0b0b2b') + stars(lt, 80, 2, 1900, .7);
    s += orb(220, 1150, 100, 'wake', lt, ph === 0) + orb(540, 1150, 100, 'dream', lt, ph === 1) + orb(860, 1150, 100, 'sleep', lt, ph === 2);
    [220, 540, 860].forEach((x, i) => s += line(540, 760, x, 1040, PAL.gold, i === ph ? 8 : 3, `opacity="${k * (i === ph ? 1 : .35)}" stroke-dasharray="10 12"`));
    s += pop(witness(540, 700, 1.1, 1, lt), 540, 700, k);
    s += pop(text(540, 460, 'IT JUST KNEW', { size: 96, fill: PAL.cream }), 540, 430, tw(lt, at(2), .5, E.back));
    return s;
  };
  S.name = ({ lt, at }) => {
    const k = tw(lt, 0, .6, E.back);
    return sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + glow(540, 760, 700, 'W', .3) + motes(lt, 30, 540, 900, 300, PAL.gold, 8, .7) +
      pop(text(540, 620, 'TURIYA', { size: 170, fill: PAL.gold, ls: 6, stroke: '#1d1442', sw: 10 }), 540, 580, k) +
      text(540, 720, 'तुरीय  ·  “the fourth”', { size: 60, fill: PAL.cream, op: tw(lt, at(1), .4), weight: 600 }) +
      pop(g(orb(300, 1040, 70, 'wake', lt) + orb(540, 1040, 70, 'dream', lt) + orb(780, 1040, 70, 'sleep', lt) + witness(540, 880, .5, 1, lt)), 540, 980, tw(lt, at(2), .5, E.back));
  };
  S.us = ({ lt, at }) => {
    const come = tw(lt, at(1), 2);
    const stay = tw(lt, at(2), .8, E.back);
    let s = rect(0, 0, W, H, '#0b0b2b') + stars(lt, 80, 2, 1900, .6);
    ['wake', 'dream', 'sleep'].forEach((kd, i) => { const a = lt * .9 + i * 2.09; const x = 540 + Math.cos(a) * 330, y = 900 + Math.sin(a) * 240; s += g(orb(x, y, 80, kd, lt), '', 1 - come * .6 * (.5 + .5 * Math.sin(lt * 2 + i))); });
    s += witness(540, 900, .9 + stay * .3, 1, lt) + glow(540, 900, 300 + stay * 400, 'W', stay * .5);
    s += pop(text(540, 520, 'SAKSHI', { size: 140, fill: PAL.gold, stroke: '#0b0b2b', sw: 10 }) + text(540, 600, 'साक्षी · the witness', { size: 54, fill: PAL.cream, weight: 600 }), 540, 520, tw(lt, at(3) + 1.5, .5, E.back));
    return s;
  };
  S.end = ({ lt, at }) => endCard(lt, at, 'The Boy Who Met Death',
    g(person({ x: 380, y: 1120, s: .55, cloth: '#e9c46a', hair: 'shikha', kid: true, face: 'calm' }) + person({ x: 700, y: 1120, s: .75, cloth: '#1b1b2f', cloth2: '#000', turban: '#3c096c', face: 'neutral', flip: true, skin: '#5e548e' }), '', tw(lt, .3, .5)));
})();
