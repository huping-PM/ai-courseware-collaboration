// Offline integration checks using an existing Playwright + browser installation.
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const { pathToFileURL } = require('node:url'), { spawnSync } = require('node:child_process');
const { chromium } = require('playwright');
(async () => {
  const browserPath = process.argv[2], root = path.resolve(__dirname, '..');
  const sample = path.join(__dirname, 'smoke-002', 'animation');
  const browser = await chromium.launch({ executablePath: browserPath, headless: true });
  let first, second;
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    await page.goto(pathToFileURL(path.join(sample, 'p01.html')).href);
    await page.evaluate(async () => { await document.fonts.ready; await Promise.all(Array.from(document.images, image => image.decode())); });
    await page.evaluate(() => window.seek(.10)); first = await page.screenshot();
    await page.evaluate(() => window.seek(.75)); await page.screenshot();
    await page.evaluate(() => window.seek(.10)); second = await page.screenshot();
    assert.deepEqual(first, second, 'Same seek time must produce byte-identical screenshot');
  } finally { await browser.close(); }
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'video-skill-browser-'));
  fs.cpSync(sample, path.join(fixture, 'animation'), { recursive: true });
  const html = path.join(fixture, 'animation', 'p01.html');
  fs.appendFileSync(html, '<style>h1{transform:translateY(900px)}</style>');
  const result = spawnSync(process.execPath, [path.join(root, 'video-frame-render/scripts/render_frames.js'),
    '--manifest', path.join(fixture, 'animation/pages-manifest.json'), '--output', path.join(fixture, 'frames'),
    '--browser', browserPath, '--engine', 'playwright'], { encoding: 'utf8' });
  assert.notEqual(result.status, 0, 'Overflow must fail');
  assert.match(result.stderr, /outside safe canvas/);
  const report = { deterministic_seek: 'pass', screenshot_sha256: crypto.createHash('sha256').update(first).digest('hex'),
    overflow_rejected: 'pass', negative_test_exit: result.status, fixture };
  fs.writeFileSync(path.join(__dirname, 'browser-tests.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
})().catch(error => { console.error(error); process.exitCode = 1; });
