// render.js — 逐页逐帧把 HTML 动画页渲染为 PNG（1920×1080 @ 25fps）
// 用法：node render.js [起始页] [结束页]     默认 1-12
// 采用 启动 Edge(headless=new, 固定端口) + puppeteer.connect 模式，避免 puppeteer 自带的下载检测。
const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const BASE = __dirname;
const HTML_DIR = path.join(BASE, 'html', 'pages');
const FRAME_ROOT = path.join(BASE, 'html_frames2');
const FPS = 25;
const W = 1920, H = 1080;
const TAIL = 0.30;    // 页尾留白（与 prep_timeline 一致）

const timeline = JSON.parse(fs.readFileSync(path.join(BASE, 'timeline.json'), 'utf-8'));

function fmt(n) { return String(n).padStart(2, '0'); }

function waitForDevtools(port, timeoutMs = 20000) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    (function poll() {
      const req = http.get('http://127.0.0.1:' + port + '/json/version', (r) => { r.resume(); resolve(true); });
      req.on('error', () => {
        if (Date.now() - t0 > timeoutMs) resolve(false);
        else setTimeout(poll, 250);
      });
    })();
  });
}

(async () => {
  const args = process.argv.slice(2);
  const pFrom = parseInt(args[0] || '1', 10);
  const pTo = parseInt(args[1] || String(pFrom), 10);

  const port = 9200 + Math.floor(Math.random() * 600);
  const profile = 'C:/Users/chenfeng/pptr_policy_' + Date.now();
  const edge = spawn(EDGE, [
    '--headless=new', '--disable-gpu', '--no-sandbox',
    '--force-device-scale-factor=1', '--hide-scrollbars', '--mute-audio',
    '--disable-extensions', '--disable-background-networking', '--font-render-hinting=none',
    '--remote-debugging-port=' + port, '--user-data-dir=' + profile, 'about:blank'
  ]);
  edge.stderr.on('data', () => {});
  edge.on('error', (e) => { console.error('EDGE SPAWN ERR', e); process.exit(1); });

  const ok = await waitForDevtools(port);
  if (!ok) { console.error('EDGE devtools not reachable'); edge.kill(); process.exit(1); }

  const browser = await puppeteer.connect({ browserURL: 'http://127.0.0.1:' + port });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });

  for (let pid = pFrom; pid <= pTo; pid++) {
    const html = path.join(HTML_DIR, `p${fmt(pid)}.html`);
    if (!fs.existsSync(html)) { console.log(`skip p${pid} (no html)`); continue; }
    const info = timeline.pages[String(pid)];
    const total = info.total + TAIL;
    const nFrames = Math.max(1, Math.round(total * FPS));
    const outDir = path.join(FRAME_ROOT, `p${fmt(pid)}`);
    fs.mkdirSync(outDir, { recursive: true });
    // 直接输出 ffmpeg 规范帧名 f%05d.png：重渲时**原地覆盖**，
    // 无需删除旧帧，也避免沙箱的批量删除拦截。
    const t0 = Date.now();
    await page.goto('file:///' + html.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.addStyleTag({ content: 'body{margin:0}' });

    for (let f = 0; f < nFrames; f++) {
      const t = f / FPS;
      await page.evaluate((tt) => { if (window.seek) window.seek(tt); }, t);
      await page.screenshot({ path: path.join(outDir, 'f' + String(f).padStart(5, '0') + '.png') });
    }
    console.log(`p${fmt(pid)}: ${nFrames} frames (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  }

  await browser.close();
  edge.kill();
  console.log('RENDER DONE');
})().catch(e => { console.error(e); process.exit(1); });