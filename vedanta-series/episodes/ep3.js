// Episode 3 — Salt in the Water (Chandogya Upanishad 6: Uddalaka teaches Svetaketu, "tat tvam asi")
var EP = {
  num: 3, title: 'Salt in the Water', voice: 'bm_george', speed: 1.0,
  lines: [
    { s: 'hook', t: 'A father dropped salt into a cup of water...', sfx: 'splash@1.6', p: .2 },
    { s: 'hook', t: 'and taught his son the biggest idea in Indian philosophy.', p: .5 },
    { s: 'home', t: 'Svetaketu comes home after twelve years of study.', say: 'Shvetaketu comes home, after twelve years of study.' },
    { s: 'home', t: "He's twenty-four, and very, very pleased with himself.", p: .4 },
    { s: 'father', t: 'His father Uddalaka asks him one question.', say: 'His father, Ooddaalaka, asks him one question.', p: .2 },
    { s: 'father', t: '"Did you learn the thing that, once you know it, everything is known?"', say: 'Did you learn the one thing... that once you know it, everything is known?', v: 'bm_lewis', sp: .95, color: '#ffd166', p: .3 },
    { s: 'father', t: '"Um... what?"', say: 'Um... what?', v: 'am_echo', color: '#7ee0d6', p: .3 },
    { s: 'father', t: '"My teachers must not have known that one."', say: 'My teachers... must not have known that one.', v: 'am_echo', color: '#7ee0d6', p: .5 },
    { s: 'salt', t: 'So his father hands him a lump of salt.', sfx: 'pop', p: .2 },
    { s: 'salt', t: '"Put this in water. Come back in the morning."', say: 'Put this in water. Come back in the morning.', v: 'bm_lewis', sp: .95, sfx: 'splash@2.2', color: '#ffd166', p: .5 },
    { s: 'morning', t: 'Next morning: "Bring me the salt."', say: 'Next morning. Bring me the salt.', sfx: 'chime', p: .3 },
    { s: 'morning', t: 'He looks. It is gone. Completely dissolved.', p: .5 },
    { s: 'taste', t: '"Sip from the top." Salty.', say: 'Sip from the top... Salty.', p: .25 },
    { s: 'taste', t: '"From the middle." Salty.', say: 'From the middle... Salty.', p: .25 },
    { s: 'taste', t: '"From the bottom." Salty!', say: 'From the bottom... Salty!', p: .5 },
    { s: 'teach', t: '"You cannot see it. But it is everywhere in the water."', say: 'You cannot see it. But it is everywhere in the water.', v: 'bm_lewis', sp: .95, color: '#ffd166', p: .3 },
    { s: 'teach', t: '"In the same way, an unseen essence is in everything that exists."', say: 'In the same way, an unseen essence is in everything that exists.', v: 'bm_lewis', sp: .95, color: '#ffd166', p: .3 },
    { s: 'teach', t: '"That is the truth. That is the Self."', say: 'That is the truth. That is the Self.', v: 'bm_lewis', sp: .9, color: '#ffd166', p: .3 },
    { s: 'teach', t: '"And Svetaketu... you are that."', say: 'And Shvetaketu... you are that.', v: 'bm_lewis', sp: .85, sfx: 'gong', color: '#ffd166', p: .8 },
    { s: 'name', t: 'Tat tvam asi. You are that.', say: 'Tat, tvam, asi. You are that.', sp: .9, color: '#ffd166', p: .3 },
    { s: 'name', t: 'In the Upanishad, the father says it nine times.', say: 'In the Upanishad, the father says it nine times.', p: .3 },
    { s: 'name', t: 'Apparently it takes a while to sink in.', p: .5 },
    { s: 'us', t: "Here's what it means for you.", sfx: 'whoosh' },
    { s: 'us', t: "You are not a visitor in this universe.", p: .2 },
    { s: 'us', t: "You're made of the same essence as everything you see.", p: .3 },
    { s: 'us', t: 'Like salt in water. Invisible... but everywhere.', p: .6 },
    { s: 'end', t: 'Next: a little wave has a panic attack.', sfx: 'whoosh' },
    { s: 'end', t: 'Follow, so you catch part four.', p: .3 },
  ],
  scenes: {}
};
if (typeof module !== 'undefined') module.exports = EP;

if (typeof window !== 'undefined') (function () {
  const S = EP.scenes;
  const dad = o => person(Object.assign({ cloth: '#f4ead5', cloth2: '#d9c9a8', beard: true, hair: 'bald', shawl: PAL.saffron, skin: PAL.skin2 }, o));
  const son = o => person(Object.assign({ cloth: '#3d5a80', cloth2: '#293f5c', hair: 'shikha', shawl: '#e9c46a', skin: PAL.skin, kid: false }, o));
  const hut = () => sky([[0, '#ffe8c2'], [1, '#f6bd60']]) + rect(0, 1150, W, H, '#c08552') + rect(0, 1150, W, 20, '#9c6644') +
    rect(80, 420, 300, 360, '#e8c39e', 20) + path('M60 440 L230 300 L400 440 Z', '#9c6644') + rect(170, 560, 120, 220, '#7f5539', 60) + // hut + door
    circ(880, 360, 80, '#fff3d6') + glow(880, 360, 260, 'W', .4);
  const cup = (x, y, s, salt = 0, glowK = 0) => {
    const water = `<path d="M-120 -20 L-100 160 Q0 190 100 160 L120 -20 Z" fill="rgba(88,196,221,.55)"/>`;
    return g(glow(0, 60, 260, 'W', glowK * .8) + `<path d="M-140 -60 L-110 170 Q0 210 110 170 L140 -60 Z" fill="rgba(255,255,255,.25)" stroke="#e0f2f7" stroke-width="8"/>` + water +
      (salt > 0 ? g(rect(-34, -34 + (1 - salt) * 160, 68, 60, '#fff', 12, 'transform="rotate(12)"'), '', salt) : '') +
      `<ellipse cx="0" cy="-60" rx="140" ry="22" fill="none" stroke="#e0f2f7" stroke-width="8"/>`, `translate(${x} ${y}) scale(${s})`);
  };
  // salt particles spread evenly through the water
  const grains = (x, y, s, k, t) => { const r = rng(5); let o = ''; for (let i = 0; i < 70; i++) { const gx = -95 + r() * 190, gy = -20 + r() * 170; o += circ(x + gx * s, y + (gy + Math.sin(t * 2 + i) * 4) * s, 4 * s, '#fff', `opacity="${(k * (.4 + .6 * r())).toFixed(2)}"`); } return o; };

  S.hook = ({ lt, at }) => {
    const drop = tw(lt, .8, .8, E.in);
    return rect(0, 0, W, H, '#10162f') + stars(lt, 50, 6, 1900, .5) + glow(540, 1000, 500, 'B', .4) +
      cup(540, 980, 1.6, 0) + (drop < 1 ? rect(500, 520 + drop * 480, 80, 70, '#fff', 14) : grains(540, 980, 1.6, tw(lt, 1.7, 2), lt)) +
      pop(text(540, 560, 'THE BIGGEST IDEA', { size: 96, fill: PAL.gold, stroke: '#10162f', sw: 10 }) + text(540, 660, 'IN INDIA', { size: 96, fill: PAL.gold, stroke: '#10162f', sw: 10 }), 540, 600, tw(lt, at(1) + 1, .5, E.back));
  };
  S.home = ({ lt, at }) => {
    const x = lerp(-100, 640, tw(lt, 0, 2.5, E.io));
    const puff = tw(lt, at(1), .5, E.back);
    let s = hut();
    s += son({ x, y: 1300, s: 1, face: puff > .5 ? 'proud' : 'happy', walk: lt < 2.5 ? lt * 6 : 0, armL: 30 + puff * 60, armR: 30 + puff * 60, lean: -puff * 4 });
    // scrolls on his back
    s += pop(g(rect(-110, -40, 220, 80, '#fff4dc', 30) + text(0, 16, '12 YEARS', { size: 46, fill: PAL.ink }), `translate(${x} 780)`), x, 780, tw(lt, .5, .5, E.back));
    s += pop(g(text(0, 0, '✨ GENIUS ✨', { size: 64, fill: PAL.saffron, stroke: '#fff', sw: 8 }), `translate(${x} 680) rotate(-5)`), x, 680, puff);
    return s;
  };
  S.father = ({ lt, at }) => {
    let s = hut();
    s += dad({ x: 300, y: 1300, s: 1, face: 'calm', armR: lt > at(1) && lt < at(2) ? 80 : 20 });
    s += son({ x: 780, y: 1300, s: 1, flip: true, face: lt > at(2) ? (lt > at(3) ? 'sad' : 'surprised') : 'proud', armL: lt > at(3) ? 150 : 12, armR: lt > at(3) ? 150 : 12 });
    s += bubble(400, 760, 'The one thing that makes everything known?', tw(lt, at(1), .4) * (1 - tw(lt, at(2), .2)), { w: 600, size: 52, tail: 'left' });
    s += bubble(700, 760, 'Um... what?', tw(lt, at(2), .4) * (1 - tw(lt, at(3), .2)), { w: 380, size: 60, tail: 'right' });
    s += bubble(660, 760, 'My teachers must not have known that one.', tw(lt, at(3), .4), { w: 560, size: 50, tail: 'right' });
    return s;
  };
  S.salt = ({ lt, at }) => {
    const drop = tw(lt, at(1) + 2.0, .5, E.in);
    let s = hut();
    s += dad({ x: 280, y: 1300, s: 1, face: 'calm', armR: 80, prop: drop <= 0 ? rect(-30, -60, 60, 50, '#fff', 10) : '' });
    s += son({ x: 820, y: 1300, s: 1, flip: true, face: 'surprised' });
    s += cup(560, 1080, .7, 0);
    if (drop > 0 && drop < 1) s += rect(530, 700 + drop * 360, 60, 50, '#fff', 10);
    s += grains(560, 1080, .7, tw(lt, at(1) + 2.5, 1.5), lt);
    s += bubble(360, 760, 'Put this in water. Come back in the morning.', tw(lt, at(1), .4), { w: 580, size: 50, tail: 'left' });
    return s;
  };
  S.morning = ({ lt, at }) => {
    const peek = tw(lt, at(1), .6, E.back);
    let s = sky([[0, '#bde0fe'], [1, '#ffe8c2']]) + circ(200, 300, 100, '#ffd166') + glow(200, 300, 300, 'W', .6) + rect(0, 1150, W, H, '#c08552');
    s += cup(540, 1000, 1.5, 0, .2) + grains(540, 1000, 1.5, .25, lt);
    s += pop(text(540, 620, 'GONE?!', { size: 180, fill: PAL.ink, stroke: '#fff', sw: 10 }), 540, 560, peek);
    s += son({ x: 900, y: 1420, s: .8, flip: true, face: 'surprised', look: -1 });
    return s;
  };
  S.taste = ({ lt, at }) => {
    const lvl = lt > at(2) ? 2 : lt > at(1) ? 1 : 0;
    const ys = [880, 1000, 1120];
    let s = rect(0, 0, W, H, '#10162f') + stars(lt, 30, 8, 1900, .4) + cup(540, 1000, 1.6, 0) + grains(540, 1000, 1.6, .5, lt);
    for (let i = 0; i <= lvl; i++) {
      const k = tw(lt, at(i) + .9, .35, E.back);
      s += line(240, ys[i], 820, ys[i], 'rgba(255,209,102,.5)', 4, 'stroke-dasharray="14 14"');
      s += pop(g(rect(820, ys[i] - 50, 220, 80, PAL.gold, 40) + text(930, ys[i] + 8, 'SALTY', { size: 50, fill: PAL.ink })), 930, ys[i] - 10, k);
      s += pop(text(150, ys[i] + 20, ['TOP', 'MID', 'BOTTOM'][i], { size: 40, fill: PAL.cream, weight: 700 }), 150, ys[i], tw(lt, at(i), .3, E.back));
    }
    s += son({ x: 540, y: 1960, s: 1.3, face: lvl === 2 ? 'surprised' : 'neutral', op: 0 });
    return s;
  };
  S.teach = ({ lt, at }) => {
    const k = tw(lt, at(1), 1.5, E.io);
    const finale = tw(lt, at(3) + .8, .8, E.back);
    let s = sky([[0, '#1d1442'], [1, '#2a1b4d']]) + stars(lt, 80, 14, 1900, .5 + .4 * k);
    // the essence spreading into everything: tree, mountain, bird, people
    s += glow(540, 900, 900 * k, 'W', .3 * k);
    s += g(hills(1150, '#3a2552', 90, 3) + path('M820 1150 l0 -200', 'none', '#7f5539', 26) + circ(820, 900, 120, '#3a7d44') + path('M260 600 q30 -30 60 0 q30 -30 60 0', 'none', PAL.cream, 8), '', .5 + .5 * k);
    s += grains(540, 900, 4.2, k * .8, lt);
    s += dad({ x: 340, y: 1300, s: .9, face: 'calm', armR: 70 + k * 40 });
    s += son({ x: 720, y: 1300, s: .9, flip: true, face: finale > .5 ? 'surprised' : 'neutral' });
    s += glow(720, 1100, 280, 'W', finale) + motes(lt, 30, 720, 1100, 150, PAL.gold, 9, finale);
    s += pop(text(540, 600, 'YOU ARE THAT', { size: 120, fill: PAL.gold, stroke: '#1d1442', sw: 10 }), 540, 560, finale);
    return s;
  };
  S.name = ({ lt, at }) => {
    const k = tw(lt, 0, .6, E.back), n = tw(lt, at(1) + .5, 2.2, E.lin);
    let s = sky([[0, '#2a1b4d'], [1, '#0b0b2b']]) + glow(540, 760, 700, 'W', .3) + motes(lt, 30, 540, 900, 300, PAL.gold, 8, .7);
    s += pop(text(540, 640, 'TAT TVAM ASI', { size: 140, fill: PAL.gold, ls: 4, stroke: '#1d1442', sw: 10 }), 540, 600, k);
    s += text(540, 740, 'तत् त्वम् असि', { size: 72, fill: PAL.cream, op: k * .85, weight: 600 });
    for (let i = 0; i < 9; i++) s += pop(text(170 + (i % 5) * 185, 920 + Math.floor(i / 5) * 120, '×' + (i + 1), { size: 64, fill: i === 8 ? PAL.saffron : PAL.cream, weight: 700 }), 170 + (i % 5) * 185, 900 + Math.floor(i / 5) * 120, tw(n, i / 9, .12, E.back));
    s += pop(text(540, 1210, '(he really wanted it to stick)', { size: 46, fill: PAL.cream, weight: 600 }), 540, 1190, tw(lt, at(2), .4, E.back));
    return s;
  };
  S.us = ({ lt, at }) => {
    const k = tw(lt, at(2), 1.5, E.io);
    let s = sky([[0, '#0b0b2b'], [1, '#1d1442']]) + stars(lt, 120, 19, 1900, .8);
    // galaxy swirl of grains around a person
    const r = rng(3);
    for (let i = 0; i < 160; i++) { const a = r() * 6.283 + lt * (.1 + r() * .2), rad = 80 + r() * 460; s += circ(540 + Math.cos(a) * rad, 900 + Math.sin(a) * rad * .6, 2 + r() * 4, i % 3 ? '#fff' : PAL.gold, `opacity="${(.3 + .7 * k).toFixed(2)}"`); }
    s += glow(540, 1000, 400, 'W', .3 + k * .5);
    s += person({ x: 540, y: 1240, s: 1, cloth: '#3d5a80', cloth2: '#293f5c', face: k > .5 ? 'happy' : 'neutral', armL: 40 + 60 * k, armR: 40 + 60 * k });
    s += pop(text(540, 520, 'NOT A VISITOR', { size: 100, fill: PAL.cream, stroke: '#0b0b2b', sw: 10 }), 540, 480, tw(lt, at(1), .4, E.back) * (1 - tw(lt, at(3), .3)));
    s += pop(text(540, 520, 'INVISIBLE. EVERYWHERE.', { size: 80, fill: PAL.gold, stroke: '#0b0b2b', sw: 10 }), 540, 480, tw(lt, at(3), .5, E.back));
    return s;
  };
  S.end = ({ lt, at }) => endCard(lt, at, 'The Wave Who Was Afraid',
    g(waveBand(1060, 22, lt, PAL.sea1, { speed: 2 }) + waveBand(1100, 16, lt, PAL.sea2, { speed: 3 }) + rect(0, 1110, W, 60, PAL.sea2), '', tw(lt, .3, .5)) );
})();
