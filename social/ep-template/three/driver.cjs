// usage: node driver.cjs <times-comma-list> | node driver.cjs --range N FPS
// writes per frame: bg RGBA 540x960 then fg RGBA 640x640 (bottom-up rows) to stdout
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = __dirname;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage();
  page.on('console', m => process.stderr.write('[page] ' + m.text() + '\n'));
  page.on('pageerror', e => process.stderr.write('[pageerror] ' + e + '\n'));
  await page.route('http://kawaii.local/**', r => {
    const p = path.join(dir, new URL(r.request().url()).pathname);
    r.fulfill({ body: fs.readFileSync(p), contentType: p.endsWith('.js') ? 'text/javascript' : 'text/html' });
  });
  await page.goto('http://kawaii.local/scene.html');
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  let times;
  if (process.argv[2] === '--range') { const n = +process.argv[3], f = +process.argv[4]; times = Array.from({ length: n }, (_, i) => i / f); }
  else times = process.argv[2].split(',').map(Number);
  for (const t of times) {
    const [bg, fg] = await page.evaluate(t => window.renderFrame(t), t);
    const ok = process.stdout.write(Buffer.from(bg, 'base64')) & process.stdout.write(Buffer.from(fg, 'base64'));
    if (!ok) await new Promise(r => process.stdout.once('drain', r));
  }
  await browser.close();
})();
