// Renders index.html frame-by-frame into an MP4 with ffmpeg.
// Usage: node render.cjs [out.mp4] [fps]      Preview stills: node render.cjs --stills 3,15,26,...
const { chromium } = require('playwright');
const { spawn } = require('child_process');
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

  const out = args[0] || path.join(__dirname, 'deep-work-short.mp4');
  const fps = Number(args[1] || 30);
  const dur = await page.evaluate(() => window.DURATION);
  const frames = Math.round(dur * fps);

  // Narration (Kokoro TTS) + quiet synthesised pad underneath.
  const pad = [
    '0.07*sin(2*PI*110*t)*(0.65+0.35*sin(2*PI*0.11*t))',
    '0.05*sin(2*PI*164.81*t)*(0.6+0.4*sin(2*PI*0.07*t+1))',
    '0.04*sin(2*PI*220*t)*(0.5+0.5*sin(2*PI*0.05*t+2))',
    '0.025*sin(2*PI*261.63*t)*(0.5+0.5*sin(2*PI*0.09*t+3))',
    '0.02*sin(2*PI*329.63*t)*(0.5+0.5*sin(2*PI*0.13*t))',
  ].join('+');
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-i', path.join(__dirname, 'narration.wav'),
    '-f', 'lavfi', '-t', String(dur), '-i', `aevalsrc=${pad}:s=48000:c=stereo`,
    '-filter_complex', `[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0[v];[2:a]lowpass=f=1800,volume=0.35,afade=t=in:d=1.5,afade=t=out:st=${dur - 2}:d=2[m];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]`,
    '-map', '0:v', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

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
