#!/usr/bin/env node
/* Render the showreel.
 *   node render.cjs --stills 1.2,5,12      -> out/still_<t>.png
 *   node render.cjs                        -> out/distilbook-showreel.mp4 (needs out/soundtrack.wav)
 * Frames are pure functions of time, so N headless pages render disjoint
 * frame ranges in parallel, each piped into its own lossless-ish segment.
 */
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const ROOT = __dirname, OUT = path.join(ROOT, 'out');
const URL = 'file://' + path.join(ROOT, 'index.html') + '?render';
const args = process.argv.slice(2);
const WORKERS = +(process.env.WORKERS || 4);
fs.mkdirSync(OUT, { recursive: true });

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1200 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
  await page.goto(URL);
  await page.evaluate(() => window.ready);
  return page;
}
const grab = (page, t, fi) => page.evaluate(([t, fi]) => { window.renderFrame(t, fi); return document.getElementById('c').toDataURL('image/png'); }, [t, fi])
  .then(d => Buffer.from(d.split(',')[1], 'base64'));

function run(cmd, a) {
  return new Promise((res, rej) => { const p = spawn(cmd, a, { stdio: ['ignore', 'inherit', 'inherit'] }); p.on('exit', c => (c ? rej(new Error(cmd + ' ' + c)) : res())); });
}

(async () => {
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--font-render-hinting=none'] });
  if (args[0] === '--stills') {
    const page = await openPage(browser);
    for (const ts of args[1].split(',')) {
      const t = +ts;
      fs.writeFileSync(path.join(OUT, `still_${t.toFixed(2)}.png`), await grab(page, t, Math.round(t * 30)));
    }
    await browser.close();
    return;
  }
  const { FPS, DUR } = await (await openPage(browser)).evaluate(() => ({ FPS: window.FPS, DUR: window.DUR }));
  const total = Math.round(FPS * DUR);
  const per = Math.ceil(total / WORKERS);
  const t0 = Date.now();
  let done = 0;
  await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
    const page = await openPage(browser);
    const a = w * per, b = Math.min(total, a + per);
    const seg = path.join(OUT, `seg_${w}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '10', '-pix_fmt', 'yuv444p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    const closed = new Promise(r => ff.on('exit', r));
    for (let f = a; f < b; f++) {
      const buf = await grab(page, f / FPS, f);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 60 === 0) process.stdout.write(`\r${done}/${total} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await closed;
  }));
  await browser.close();
  console.log(`\nframes done in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  const list = path.join(OUT, 'segments.txt');
  fs.writeFileSync(list, Array.from({ length: WORKERS }, (_, w) => `file 'seg_${w}.mp4'`).join('\n'));
  const audio = path.join(OUT, 'soundtrack.wav');
  const final = path.join(ROOT, 'distilbook-showreel.mp4');
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
    ...(fs.existsSync(audio) ? ['-i', audio] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart',
    ...(fs.existsSync(audio) ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []), final]);
  console.log('wrote', final);
})().catch(e => { console.error(e); process.exit(1); });
