// usage: node driver.cjs <t1,t2,...> | --range N FPS   -> stdout: [u32 len][jpeg] per frame
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const dir = __dirname;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => process.stderr.write('[pageerror] ' + e + '\n'));
  page.on('console', m => { if (m.type() === 'error') process.stderr.write('[console] ' + m.text() + '\n'); });
  await page.route('http://scene.local/**', r => {
    const p = path.join(dir, decodeURIComponent(new URL(r.request().url()).pathname));
    const ct = p.endsWith('.js') ? 'text/javascript' : p.endsWith('.json') ? 'application/json' : p.endsWith('.ttf') ? 'font/ttf' : 'text/html';
    r.fulfill({ body: fs.readFileSync(p), contentType: ct });
  });
  await page.goto('http://scene.local/scene.html');
  await page.waitForFunction('window.ready === true', null, { timeout: 120000 });
  let times;
  if (process.argv[2] === '--range') { const n = +process.argv[3], f = +process.argv[4]; times = Array.from({ length: n }, (_, i) => i / f); }
  else times = process.argv[2].split(',').map(Number);
  for (const t of times) {
    const url = await page.evaluate(t => window.renderFrame(t), t);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    const hdr = Buffer.alloc(4); hdr.writeUInt32LE(buf.length);
    if (!(process.stdout.write(hdr) & process.stdout.write(buf))) await new Promise(r => process.stdout.once('drain', r));
  }
  await browser.close();
})();
