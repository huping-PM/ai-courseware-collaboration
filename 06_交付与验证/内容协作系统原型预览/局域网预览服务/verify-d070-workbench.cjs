const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const release = process.argv[2];
const externalBase = process.argv[3];
if (!externalBase && !/^release-\d+$/.test(release || '')) throw Error('Provide candidate release name or LAN base URL');
const directory = release ? path.join(__dirname, 'releases', release) : null;
const types = ['doc', 'image', 'audio', 'video'];
const labels = { doc: '文稿', image: '图片', audio: '音频', video: '视频' };
const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = directory && http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.resolve(directory, '.' + pathname);
  if (!file.startsWith(directory + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return res.writeHead(404).end();
  res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

(async () => {
  if (!externalBase) await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = externalBase || `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const errors = [], failed = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.status() >= 400) failed.push(`${response.url()} ${response.status()}`); });
  try {
    await page.goto(`${base}/04_原型与说明/AI协作工作台-风格探索/index.html?style=b`);
    await page.locator('#outputShelf').waitFor();
    assert.deepEqual(await page.locator('[data-output-filter]').allTextContents(), ['文稿', '图片', '音频', '视频']);
    for (const type of types) {
      const filter = page.locator(`[data-output-filter="${type}"]`);
      await filter.click();
      assert.equal(await page.locator('[data-output-type]').count(), 1, `${labels[type]}筛选应只显示一项成果`);
      await filter.click();
      assert.equal(await page.locator('[data-output-type]').count(), 4, `${labels[type]}筛选应可取消`);
    }
    await page.locator('[data-output-filter="audio"]').click();
    await page.locator('[data-output-type="audio"]').click();
    await page.locator('#paper').getByText('沟通练习示范音频', { exact: true }).waitFor();
    assert.equal(await page.locator('#paper svg[aria-label="音频波形"]').count(), 1);
    await page.locator('[data-output-filter="audio"]').click();
    await page.locator('[data-output-filter="doc"]').click();
    await page.locator('[data-output-type="doc"]').click();
    await page.locator('#editButton').click();
    const editor = page.locator('#markdownEditor');
    await editor.fill('# 局域网 D070 保存核验');
    await page.locator('#editButton').click();
    await page.locator('#paper').getByText('局域网 D070 保存核验', { exact: true }).waitFor();
    assert.equal((await page.locator('#saveStatus').innerText()).includes('已保存'), true);
    await page.locator('.studio-module-nav a', { hasText: '资源管理' }).click();
    await page.frameLocator('.studio-original-frame').locator('body').waitFor();
    await page.locator('.studio-module-nav a', { hasText: '技能管理' }).click();
    await page.frameLocator('.studio-original-frame').locator('body').waitFor();
    assert.deepEqual(errors, []);
    assert.deepEqual(failed, []);
    console.log(JSON.stringify({ release: release || 'current', base, status: 'passed', checks: ['四类筛选及取消', '音频波形画布', '文稿编辑保存', '顶部资源与技能导航'], errors, failed }));
  } finally {
    await browser.close();
    if (server?.listening) server.close();
  }
})().catch(error => { console.error(error); if (server?.listening) server.close(); process.exitCode = 1; });
