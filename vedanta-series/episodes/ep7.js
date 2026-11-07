// Episode 7 — The Boy Who Met Death (Katha Upanishad: Nachiketa and Yama; preyas vs shreyas; the Self is unborn, undying)
var EP = {
  num: 7, title: 'The Boy Who Met Death', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'A boy walked into the house of Death.', sfx: 'gong', p: .2 },
    { s: 'hook', t: "Death wasn't home. So he waited. Three days.", p: .6 },
    { s: 'gift', t: 'Long ago, a rich man held a grand ceremony, giving away his wealth.' },
    { s: 'gift', t: 'Well... sort of.', p: .2 },
    { s: 'gift', t: 'He gave away old cows that could barely walk, and had no milk left.', p: .5 },
    { s: 'boy', t: 'His young son, Nachiketa, noticed.', say: 'His young son, Nachiketa, noticed.', p: .2 },
    { s: 'boy', t: '"Father, and to whom will you give me?"', say: 'Father... and to whom will you give me?', v: 'am_echo', sp: 1.05, color: '#7ee0d6', p: .3 },
    { s: 'boy', t: 'He asked again. And again.', p: .2 },
    { s: 'boy', t: '"To Death I give you!"', say: 'To Death, I give you!', v: 'bm_lewis', sp: 1.05, sfx: 'boom', color: '#ff6b6b', p: .6 },
    { s: 'door', t: 'So Nachiketa went. Straight to the house of Yama, the Lord of Death.', sfx: 'whoosh' },
    { s: 'door', t: 'Yama was out. Nachiketa waited. Three days. No food.', p: .5 },
    { s: 'yama', t: 'Yama returns, horrified. A guest, kept waiting!', sfx: 'gong' },
    { s: 'yama', t: '"Forgive me. Ask me for three wishes."', say: 'Forgive me. Ask me for three wishes.', v: 'am_onyx', sp: .88, color: '#c77dff', p: .5 },
    { s: 'wish', t: 'Wish one: "Let my father be at peace with me." Granted.', sfx: 'pop', p: .2 },
    { s: 'wish', t: 'Wish two: "Teach me the sacred fire." Granted.', sfx: 'pop', p: .2 },
    { s: 'wish', t: 'Wish three: "When a person dies, what happens? Tell me the truth."', sfx: 'boom', p: .6 },
    { s: 'tempt', t: '"Not that one! Ask for anything else!"', say: 'Not that one! Ask for anything else!', v: 'am_onyx', sp: .95, color: '#c77dff' },
    { s: 'tempt', t: '"Gold. Horses. Kingdoms. A hundred years of life!"', say: 'Gold. Horses. Kingdoms. A hundred years of life!', v: 'am_onyx', sp: .95, color: '#c77dff', p: .4 },
    { s: 'tempt', t: '"Keep your horses. All of it wears out. Teach me."', say: 'Keep your horses. All of it wears out. Teach me.', v: 'am_echo', color: '#7ee0d6', p: .6 },
    { s: 'path', t: 'Yama is impressed. Most people take the gold.', p: .2 },
    { s: 'path', t: '"There are two paths: the pleasant, and the good. The wise choose the good."', say: 'There are two paths. The pleasant... and the good. The wise choose the good.', v: 'am_onyx', sp: .9, color: '#c77dff', p: .5 },
    { s: 'secret', t: 'Then he tells him the secret.', p: .3 },
    { s: 'secret', t: '"The Self is never born. It never dies."', say: 'The Self is never born. It never dies.', v: 'am_onyx', sp: .85, sfx: 'chime', color: '#ffd166', p: .3 },
    { s: 'secret', t: '"It is not killed, when the body is killed."', say: 'It is not killed... when the body is killed.', v: 'am_onyx', sp: .85, color: '#ffd166', p: .7 },
    { s: 'recap', t: 'Not the snake.', sfx: 'pop', p: .1 },
    { s: 'recap', t: 'Not the one who forgot to count himself.', sfx: 'pop', p: .1 },
    { s: 'recap', t: 'Not the wave. Not the pot. Not the dream.', sfx: 'pop', p: .3 },
    { s: 'recap', t: 'You are that which was never born... and never dies.', sfx: 'gong', p: .7 },
    { s: 'end', t: "That's Vedanta. Which story hit you hardest? Tell me in the comments.", sfx: 'chime' },
    { s: 'end', t: 'And follow for more.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const boy = o => person(Object.assign({ cloth: '#e9c46a', cloth2: '#c9a227', hair: 'shikha', kid: true, skin: PAL.skin }, o));
  const dad = o => person(Object.assign({ cloth: '#9b2335', cloth2: '#6a1a26', turban: PAL.gold, beard: '#3b2a20', skin: PAL.skin2, shawl: PAL.gold }, o));
  const yama = (o) => {
    const p = person(Object.assign({ cloth: '#240046', cloth2: '#10002b', skin: '#5e548e', hair: 'bald', beard: '#10002b', shawl: '#7b2cbf' }, o));
    const { x = 540, y = 1300, s = 1 } = o;
    const crown = g(path('M-80 0 L-70 -90 L-35 -40 L0 -110 L35 -40 L70 -90 L80 0 Z', PAL.gold) + circ(0, -60, 12, '#c77dff'), `translate(${x} ${y - 335 * s}) scale(${s})`);
    return glow(x, y - 200 * s, 380 * s, 'B', .25) + p + crown;
  };
  function cow(x, y, s, t, old = true) {
    const wob = Math.sin(t * 3) * 4;
    return g(`<ellipse cx="0" cy="-90" rx="120" ry="60" fill="#f1e3d3"/>` + circ(-40, -110, 22, '#5c4033') + circ(40, -80, 18, '#5c4033') +
      [-80, -40, 40, 80].map((lx, i) => line(lx, -50, lx + (i % 2 ? wob : -wob), 0, '#e0cfbd', 16)).join('') +
      `<ellipse cx="130" cy="-120" rx="44" ry="34" fill="#f1e3d3"/>` + path('M110 -150 l-14 -26 M150 -150 l14 -26', 'none', '#cbb79f', 8) +
      (old ? path('M120 -122 l12 0 M140 -122 l12 0', 'none', PAL.ink, 5) + path('M130 -100 q10 8 20 0', 'none', PAL.ink, 4) : circ(126, -124, 5, PAL.ink) + circ(146, -124, 5, PAL.ink)) +
      path('M-120 -100 q-30 30 -20 70', 'none', '#e0cfbd', 8) + (old ? g(text(-10, -170, 'zzz', { size: 36, fill: PAL.ink, weight: 600 }), '', .6) : ''), `translate(${x} ${y}) scale(${s}) rotate(${old ? Math.sin(t) * 2 : 0})`);
  }
  const palace = (t) => sky([[0, '#10002b'], [.5, '#240046'], [1, '#3c096c']]) + stars(t, 60, 13, 1300, .6) +
    rect(160, 520, 760, 700, '#1b1033') + path('M120 540 L540 300 L960 540 Z', '#2d1b4e') + rect(430, 820, 220, 400, '#0b0614', 110) +
    [0, 1, 2, 3].map(i => rect(200 + i * 200, 620, 50, 600, '#2d1b4e')).join('') + rect(0, 1220, W, H, '#140a24');

  S.hook = ({ lt, at }) => {
    const days = Math.min(3, Math.floor(tw(lt, at(1) + 1.2, 1.4, E.lin) * 3.2));
    return palace(lt) + glow(540, 1000, 400, 'B', .25) +
      boy({ x: 540, y: 1300, s: .9, face: 'calm', armL: 10, armR: 10 }) +
      pop(text(540, 230 + 200, 'HOUSE OF DEATH', { size: 100, fill: '#e0aaff', stroke: '#10002b', sw: 12 }), 540, 400, .5 + .5 * tw(lt, .1, .5, E.back)) +
      [0, 1, 2].map(i => pop(g(circ(0, 0, 56, i < days ? PAL.gold : 'rgba(255,255,255,.15)') + text(0, 20, 'DAY ' + (i + 1), { size: 30, fill: PAL.ink })), 300 + i * 240, 1460 - 120, i < days ? 1 : .001)).join('');
  };
  S.gift = ({ lt, at }) => {
    const old = tw(lt, at(2), .4);
    let s = sky([[0, '#ffe8c2'], [1, '#f6bd60']]) + rect(0, 1200, W, H, '#c08552') + path('M380 1200 l80 -180 l80 180 Z', PAL.saffron) + glow(460, 1050, 220, 'W', .6) + path('M430 1030 q30 -60 30 -100 q20 50 30 100', '#ffd166');
    s += dad({ x: 240, y: 1320, s: .95, face: lt > at(1) ? 'proud' : 'happy', armR: 90 });
    s += cow(720, 1290, .9, lt, old > .5);
    s += pop(g(rect(-220, -55, 440, 110, '#fff', 20, 'stroke="#c1121f" stroke-width="6"') + text(0, 18, '100% GENEROUS*', { size: 50, fill: PAL.ink }), 'translate(330 560) rotate(-5)'), 330, 560, tw(lt, .5, .5, E.back));
    s += pop(text(720, 820, '*no milk', { size: 54, fill: '#c1121f', stroke: '#fff', sw: 6 }), 720, 800, tw(lt, at(2) + 1.2, .4, E.back));
    return s;
  };
  S.boy = ({ lt, at }) => {
    const angry = tw(lt, at(3), .25);
    let s = sky([[0, angry ? '#9d0208' : '#ffe8c2'], [1, angry ? '#370617' : '#f6bd60']]) + rect(0, 1200, W, H, '#8a5a3c');
    s += dad({ x: 300, y: 1320, s: 1, face: angry > .5 ? 'angry' : 'neutral', armR: 30 + angry * 80, flip: false });
    s += boy({ x: 760, y: 1320, s: 1, flip: true, face: angry > .5 ? 'surprised' : 'neutral', armR: 70 });
    const qs = lt > at(2) ? 3 : lt > at(1) ? 1 : 0;
    for (let i = 0; i < qs; i++) s += pop(text(700 + i * 80, 700 - i * 60, '?', { size: 120 + i * 20, fill: '#7ee0d6', stroke: '#fff', sw: 4 }), 700 + i * 80, 660 - i * 60, tw(lt, at(Math.min(i, 1)) + (i ? .7 + i * .5 : .2), .3, E.back));
    s += bubble(380, 720, 'To Death I give you!', tw(lt, at(3), .3), { w: 520, size: 60, tail: 'left', fill: '#ffccd5' });
    return s;
  };
  S.door = ({ lt, at }) => {
    const walk = tw(lt, 0, 3, E.io);
    const days = Math.min(3, Math.floor(tw(lt, at(1) + .8, 2.2, E.lin) * 3.2));
    let s = palace(lt);
    s += boy({ x: lerp(-80, 540, walk), y: 1300, s: .9, face: 'calm', walk: walk < 1 ? lt * 6 : 0 });
    if (lt > at(1)) s += [0, 1, 2].map(i => pop(g(circ(0, 0, 56, i < days ? PAL.gold : 'rgba(255,255,255,.15)') + text(0, 12, ['🌙', '🌙', '🌙'][i], { size: 50 })), 300 + i * 240, 520, i < days ? 1 : .001)).join('');
    s += pop(g(rect(-120, -40, 240, 80, '#fff4dc', 12) + text(0, 14, 'OUT', { size: 46, fill: PAL.ink })), 540, 760, tw(lt, at(1), .4, E.back));
    return s;
  };
  S.yama = ({ lt, at }) => {
    const yk = tw(lt, 0, 1.2, E.out);
    return palace(lt) + glow(700, 1000, 600, 'B', .3 * yk) +
      boy({ x: 300, y: 1300, s: .85, face: 'neutral' }) +
      g(yama({ x: 720, y: 1300, s: 1.1, flip: true, face: lt > at(1) ? 'sad' : 'surprised', armL: 40, armR: 40 + 60 * tw(lt, at(1), .5) }), `translate(0 ${(1 - yk) * 80})`, yk) +
      bubble(640, 520, 'Forgive me. Ask me for three wishes.', tw(lt, at(1), .4), { w: 560, size: 52, tail: 'right', fill: '#e0aaff' });
  };
  S.wish = ({ lt, at }) => {
    let s = sky([[0, '#240046'], [1, '#10002b']]) + stars(lt, 60, 3, 1900, .6);
    const lab = ['Peace with my father', 'The sacred fire', 'What happens after death?'];
    lab.forEach((L, i) => {
      const k = tw(lt, at(i), .45, E.back);
      const y = 560 + i * 230;
      const hot = i === 2;
      s += pop(g(rect(110, y - 90, 860, 180, hot ? PAL.gold : 'rgba(255,255,255,.1)', 40, hot ? '' : 'stroke="rgba(255,255,255,.3)" stroke-width="3"') +
        circ(200, y, 56, hot ? PAL.ink : PAL.gold) + text(200, y + 22, String(i + 1), { size: 64, fill: hot ? PAL.gold : PAL.ink }) +
        text(590, y + 18, L, { size: 52, fill: hot ? PAL.ink : PAL.cream }) +
        (i < 2 ? text(900, y - 40, '✓', { size: 70, fill: '#7bd389', op: tw(lt, at(i) + 2, .3) }) : '')), 540, y, k);
    });
    return s;
  };
  S.tempt = ({ lt, at }) => {
    const items = ['💰', '🐎', '👑', '⏳', '💎', '🏰'];
    const showK = tw(lt, at(1), .3), refuse = tw(lt, at(2), .6);
    let s = palace(lt) + glow(540, 800, 600, 'W', .2 + showK * .3);
    items.forEach((e, i) => { const a = i / items.length * 6.283 + lt * .6; const x = 540 + Math.cos(a) * 340, y = 760 + Math.sin(a) * 200;
      s += pop(`<text x="${x}" y="${y + 40}" font-size="120" text-anchor="middle">${e}</text>`, x, y, tw(lt, at(1) + i * .35, .35, E.back) * (1 - refuse * .8)); });
    s += yama({ x: 800, y: 1320, s: .9, flip: true, face: refuse > .5 ? 'surprised' : 'happy', armL: 120, armR: 120 });
    s += boy({ x: 280, y: 1320, s: .85, face: refuse > .5 ? 'calm' : 'neutral', armR: refuse * 90 });
    s += pop(g(rect(-200, -55, 400, 110, PAL.cream, 55) + text(0, 18, 'NO, THANKS', { size: 60, fill: PAL.ink })), 300, 820, tw(lt, at(2) + .3, .4, E.back));
    return s;
  };
  S.path = ({ lt, at }) => {
    const k = tw(lt, at(1), .6, E.back), k2 = tw(lt, at(1) + 2.5, .6, E.back);
    let s = sky([[0, '#ffd6a5'], [.6, '#e5989b'], [1, '#6d597a']]);
    // a fork in the road
    s += path('M500 1900 L540 1250 L580 1900 Z', '#c9a26b') + path('M540 1250 Q400 1000 200 760 L260 740 Q450 980 540 1250 Z', '#e9c46a') + path('M540 1250 Q680 1000 880 760 L820 740 Q630 980 540 1250 Z', '#c9a26b');
    s += pop(g(rect(80, 600, 300, 130, '#ff8fab', 30) + text(230, 660, 'PLEASANT', { size: 50, fill: PAL.ink }) + text(230, 708, 'preyas · 🍭', { size: 38, fill: PAL.ink, weight: 600 })), 230, 665, k);
    s += pop(g(rect(700, 600, 300, 130, PAL.gold, 30) + text(850, 660, 'GOOD', { size: 50, fill: PAL.ink }) + text(850, 708, 'shreyas · 🪷', { size: 38, fill: PAL.ink, weight: 600 })), 850, 665, k2);
    s += boy({ x: lerp(540, 700, tw(lt, at(1) + 4, 2, E.io)), y: 1400, s: .7, face: 'calm', walk: lt * 5 });
    return s;
  };
  S.secret = ({ lt, at }) => {
    const k = tw(lt, at(1), .8, E.back), k2 = tw(lt, at(2), .8, E.back);
    return sky([[0, '#10002b'], [1, '#3c096c']]) + stars(lt, 100, 17, 1900, .8) + glow(540, 900, 300 + 600 * k, 'W', .2 + k * .5) + motes(lt, 40, 540, 1000, 300, PAL.gold, 5, k) +
      lotus(540, 1160, 1.2, k, lt) +
      pop(text(540, 560, 'NEVER BORN', { size: 130, fill: PAL.gold, stroke: '#10002b', sw: 10 }), 540, 520, k) +
      pop(text(540, 690, 'NEVER DIES', { size: 130, fill: PAL.cream, stroke: '#10002b', sw: 10 }), 540, 650, tw(lt, at(1) + 1.4, .6, E.back)) +
      text(540, 790, 'Katha Upanishad 1.2.18', { size: 40, fill: PAL.cream, weight: 600, op: k2 * .8 });
  };
  S.recap = ({ lt, at }) => {
    const items = [['🐍', 0], ['🔟', 1], ['🌊', 2], ['🏺', 2], ['💭', 2]];
    let s = rect(0, 0, W, H, '#0b0b2b') + stars(lt, 80, 21, 1900, .6);
    const fin = tw(lt, at(3), 1.2, E.io);
    items.forEach(([e, li], i) => {
      const k = tw(lt, at(li) + (li === 2 ? (i - 2) * .7 : 0), .35, E.back);
      const x = 180 + i * 180, y = 760;
      s += pop(g(`<text x="${x}" y="${y + 40}" font-size="120" text-anchor="middle">${e}</text>` + line(x - 70, y - 60, x + 70, y + 60, PAL.red, 12, `opacity="${tw(lt, at(li) + (li === 2 ? (i - 2) * .7 : 0) + .3, .2)}"`)), x, y, k * (1 - fin * .7));
    });
    s += glow(540, 1000, 200 + fin * 800, 'W', fin * .8) + motes(lt, 50, 540, 1100, 400, PAL.gold, 9, fin);
    s += pop(text(540, 1020, 'YOU ARE THAT', { size: 130, fill: PAL.gold, stroke: '#0b0b2b', sw: 12 }), 540, 980, tw(lt, at(3) + 1.5, .6, E.back));
    return s;
  };
  S.end = ({ lt, at }) => {
    const k = tw(lt, .1, .6, E.back), kf = tw(lt, at(1) + .2, .5, E.back);
    return sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + stars(lt, 60, 31, 1300, .6) + glow(540, 900, 600, 'W', .25) +
      pop(text(540, 470, 'SERIES COMPLETE', { size: 56, fill: PAL.saffron, ls: 8 }) + text(540, 600, 'WHO AM I?', { size: 140, fill: PAL.cream, stroke: '#0b0b2b', sw: 10 }), 540, 520, k) +
      lotus(540, 1020, 1, tw(lt, .5, .8), lt) +
      pop(g(rect(150, 1110, 780, 100, 'rgba(255,255,255,.12)', 50) + text(540, 1178, '💬  which story hit you hardest?', { size: 48, fill: PAL.cream, weight: 700 })), 540, 1160, tw(lt, 1.2, .5, E.back)) +
      pop(g(rect(330, 1240, 420, 110, PAL.red, 55) + text(540, 1313, 'FOLLOW', { size: 64, fill: '#fff', ls: 4 })), 540, 1295, kf);
  };
})();
