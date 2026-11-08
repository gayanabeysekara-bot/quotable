// Renders index.html frame-by-frame into an MP4 with ffmpeg.
// Usage: node render.cjs [out.mp4] [fps]      Preview stills: node render.cjs --stills 3,15,26,...
const { chromium } = require('playwright');
const { spawn, spawnSync } = require('child_process');
// Narration: Kokoro "am_michael", pitched ~5% deeper (duration unchanged) with a short courtyard echo,
// mixed over the drum / drone sound design from mix.py.
const AUDIO_FILTER = '[1:a]aresample=48000,asetrate=45600,aresample=48000,atempo=1.0526316,aecho=0.8:0.55:55|110:0.10|0.05,aformat=channel_layouts=stereo,volume=1.25[v];' +
  '[2:a]volume=0.55[m];[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]';
const path = require('path');

const args = process.argv.slice(2);
const stillsArg = args.indexOf('--stills');
const url = 'file://' + path.join(__dirname, 'index.html') + '?render=1';

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true);
  await page.evaluate(() => document.fonts.ready);
  const stage = await page.$('#stage');

  if (stillsArg >= 0) {
    const times = args[stillsArg + 1].split(',').map(Number);
    const outDir = args[stillsArg + 2] || __dirname;
    for (const t of times) {
      await page.evaluate(t => window.setTime(t), t);
      await stage.screenshot({ path: path.join(outDir, `still_${String(t).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 85 });
    }
    await browser.close();
    return;
  }

  const out = args[0] || path.join(__dirname, 'art-of-war-discipline.mp4');
  const fps = Number(args[1] || 30);
  const dur = await page.evaluate(() => window.DURATION);
  const frames = Math.round(dur * fps);

  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-i', path.join(__dirname, 'narration.wav'),
    '-i', path.join(__dirname, 'sfx.wav'),
    '-filter_complex', AUDIO_FILTER,
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  // audio-only preview for index.html playback
  spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', path.join(__dirname, 'narration.wav'), '-i', path.join(__dirname, 'sfx.wav'),
    '-filter_complex', AUDIO_FILTER, '-map', '[a]', '-c:a', 'aac', '-b:a', '160k', path.join(__dirname, 'preview-audio.m4a')]);
  const t0 = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.setTime(t), i / fps);
    const buf = await stage.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('done ->', out);
})();
