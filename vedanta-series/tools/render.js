// Render an episode to MP4 (1080x1920, 30fps) with its mixed audio.
// usage: node render.js <episode-id> [--still t1,t2,...] [--workers 3]
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path'), fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const ep = process.argv[2];
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const FPS = 30, WORKERS = +arg('--workers', 3);
const out = path.join(ROOT, 'out', ep);
const url = 'file://' + path.join(ROOT, 'engine', 'stage.html') + '?ep=' + ep;

async function page(browser) {
  const p = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await p.goto(url);
  const info = await p.evaluate(() => window.ready);
  return { p, info };
}

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const stills = arg('--still');
  if (stills) {
    const { p } = await page(browser);
    fs.mkdirSync(path.join(out, 'stills'), { recursive: true });
    for (const t of stills.split(',').map(Number)) {
      await p.evaluate(t => window.render(t), t);
      await p.screenshot({ path: path.join(out, 'stills', `t${String(t).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 80 });
    }
    await browser.close(); return;
  }
  const { info } = await page(browser);
  const frames = Math.ceil(info.total * FPS);
  const per = Math.ceil(frames / WORKERS);
  const t0 = Date.now();
  await Promise.all([...Array(WORKERS)].map(async (_, w) => {
    const { p } = await page(browser);
    const a = w * per, b = Math.min(frames, a + per);
    const seg = path.join(out, `seg${w}.mp4`);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = a; f < b; f++) {
      await p.evaluate(t => window.render(t), f / FPS);
      const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (w === 0 && (f - a) % 300 === 0) console.log(`  frame ${f - a}/${b - a} (worker 0)  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }));
  await browser.close();
  const list = path.join(out, 'segs.txt');
  fs.writeFileSync(list, [...Array(WORKERS)].map((_, w) => `file 'seg${w}.mp4'`).join('\n'));
  const final = path.join(ROOT, 'out', `${ep}.mp4`);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-i', path.join(out, 'mix.wav'),
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-shortest', '-movflags', '+faststart', final]);
  for (let w = 0; w < WORKERS; w++) fs.unlinkSync(path.join(out, `seg${w}.mp4`));
  console.log(`${ep}: ${frames} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${final}`);
})();
