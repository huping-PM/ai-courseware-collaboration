#!/usr/bin/env node
'use strict';
// Local deterministic renderer. Install either puppeteer-core or playwright.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const crypto = require('node:crypto');

function parseArgs() {
  const args = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    if (process.argv[i] === '--help') {
      console.log('node render_frames.js --manifest pages-manifest.json --output NEW_DIR --browser BROWSER_EXE [--engine puppeteer|playwright]'); process.exit(0);
    }
    if (!process.argv[i].startsWith('--') || !process.argv[i + 1]) throw Error('Expected --option value');
    args[process.argv[i].slice(2)] = process.argv[i + 1];
  }
  for (const k of ['manifest', 'output', 'browser']) if (!args[k]) throw Error(`Missing --${k}`);
  if (Object.keys(args).some(k => !['manifest', 'output', 'browser', 'engine'].includes(k))) throw Error('Unknown option');
  return args;
}
function local(base, rel) {
  if (typeof rel !== 'string' || !rel || path.isAbsolute(rel) || /[:\x00]/.test(rel) || rel.startsWith('\\')) throw Error('Invalid local path');
  const full = path.resolve(base, rel);
  const inside = path.relative(base, full);
  if (inside.startsWith('..') || path.isAbsolute(inside)) throw Error('Path escapes manifest directory');
  if (!fs.existsSync(full)) throw Error(`Missing file: ${rel}`);
  const actual = fs.realpathSync(full), root = fs.realpathSync(base);
  const resolved = path.relative(root, actual);
  if (resolved.startsWith('..') || path.isAbsolute(resolved)) throw Error('Symlink escapes manifest directory');
  return actual;
}
async function main() {
  const a = parseArgs(), source = path.resolve(a.manifest), base = path.dirname(source);
  const data = JSON.parse(fs.readFileSync(source, 'utf8').replace(/^\uFEFF/, ''));
  if (data.schema_version !== 1 || !Number.isInteger(data.fps) || data.fps < 1 || data.fps > 60 || data.width !== 1280 || data.height !== 720) throw Error('Unsupported manifest format');
  for (const h of ['project_sha256', 'timeline_sha256']) if (!/^[a-f0-9]{64}$/.test(data[h])) throw Error(`Invalid ${h}`);
  if (!Array.isArray(data.pages) || !data.pages.length) throw Error('Empty page list');
  const ids = new Set();
  for (const p of data.pages) {
    if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(p.id) || ids.has(p.id)) throw Error('Invalid/duplicate page id');
    ids.add(p.id);
    if (!Number.isInteger(p.frames) || p.frames < 1 || !Number.isFinite(p.duration) || Math.abs(p.frames / data.fps - p.duration) > 1e-6) throw Error('Invalid frame budget');
    local(base, p.html); local(base, p.audio);
  }
  const out = path.resolve(a.output);
  if (fs.existsSync(out) && (!fs.statSync(out).isDirectory() || fs.readdirSync(out).length)) throw Error('Output must be empty/new; use a new run directory');
  if (!fs.existsSync(a.browser)) throw Error('Browser executable missing');
  const engine = a.engine || 'puppeteer';
  if (!['puppeteer', 'playwright'].includes(engine)) throw Error('Unknown engine');
  const lib = require(engine === 'playwright' ? 'playwright' : 'puppeteer-core');
  const launcher = engine === 'playwright' ? lib.chromium : lib;
  const browser = await launcher.launch({ executablePath: path.resolve(a.browser), headless: true });
  fs.mkdirSync(out, { recursive: true }); fs.mkdirSync(path.join(out, 'audio'));
  const result = { schema_version: 1, project_sha256: data.project_sha256, timeline_sha256: data.timeline_sha256,
    pages_manifest_sha256: crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),
    width: data.width, height: data.height, fps: data.fps, pages: [] };
  try {
    for (const item of data.pages) {
      const page = await browser.newPage(engine === 'playwright' ? { viewport: { width: data.width, height: data.height }, deviceScaleFactor: 1 } : undefined);
      if (engine === 'puppeteer') await page.setViewport({ width: data.width, height: data.height, deviceScaleFactor: 1 });
      const errors = [];
      page.on('pageerror', e => errors.push(String(e)));
      if (engine === 'playwright') await page.route('**/*', route => /^https?:/.test(route.request().url()) ? route.abort() : route.continue());
      else { await page.setRequestInterception(true); page.on('request', request => /^https?:/.test(request.url()) ? request.abort() : request.continue()); }
      await page.goto(pathToFileURL(local(base, item.html)).href, { waitUntil: 'load' });
      if (engine === 'playwright') await page.waitForFunction('window.__videoReady === true && typeof window.seek === "function"', null, { timeout: 30000 });
      else await page.waitForFunction('window.__videoReady === true && typeof window.seek === "function"', { timeout: 30000 });
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all(Array.from(document.images, image => image.decode())); });
      const layoutErrors = await page.evaluate(() => {
        const failures = [...(window.__layoutErrors || [])];
        document.querySelectorAll('h1, li, .page-image').forEach(element => {
          const r = element.getBoundingClientRect();
          if (r.left < 0 || r.top < 0 || r.right > 1280.5 || r.bottom > 672.5) failures.push(`${element.tagName}: outside safe canvas`);
          if (element.scrollHeight > element.clientHeight + 1 || element.scrollWidth > element.clientWidth + 1) failures.push(`${element.tagName}: text overflow`);
          const style = getComputedStyle(element);
          if (style.transitionDuration.split(',').some(x => parseFloat(x) !== 0) || style.animationName !== 'none') failures.push(`${element.tagName}: nondeterministic CSS animation`);
        });
        return failures;
      });
      if (layoutErrors.length) throw Error(`Page ${item.id} layout: ${layoutErrors.join('; ')}`);
      const dir = path.join(out, item.id); fs.mkdirSync(dir);
      for (let f = 0; f < item.frames; f++) {
        await page.evaluate(t => window.seek(t), f / data.fps);
        if (errors.length) throw Error(`Page ${item.id} JavaScript errors: ${errors.join('; ')}`);
        await page.screenshot({ path: path.join(dir, `f${String(f).padStart(5, '0')}.png`), type: 'png' });
      }
      const audio = `audio/${item.id}.wav`; fs.copyFileSync(local(base, item.audio), path.join(out, audio));
      result.pages.push({ id: item.id, directory: item.id, frames: item.frames, duration: item.duration, audio });
      console.log(`${item.id}: ${item.frames} frames`); await page.close();
    }
    fs.writeFileSync(path.join(out, 'frames-manifest.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(path.join(out, 'frames-manifest.json'));
  } finally { await browser.close(); }
}
main().catch(error => { console.error(`FAILED: ${error.message}`); process.exitCode = 1; });
