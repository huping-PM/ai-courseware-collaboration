const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const { chromium } = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const release = process.argv[2];
if (!/^release-\d+$/.test(release || '')) throw Error('Provide candidate release name');
const directory = path.join(__dirname, 'releases', release);
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.webm': 'video/webm', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.resolve(directory, '.' + (pathname === '/' ? '/原型预览.html' : pathname));
  if (!file.startsWith(directory + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); return res.end(); }
  res.setHeader('Content-Type', mime[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
(async () => {
  const externalBase = process.argv[3];
  if (!externalBase) await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = externalBase || 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage(), errors = [], missing = [];
  context.on('page', tab => tab.on('pageerror', error => errors.push(error.message)));
  page.on('pageerror', error => errors.push(error.message));
  context.on('response', response => { if (response.status() >= 400) missing.push(response.url() + ' ' + response.status()); });
  try {
    await page.goto(base + '/');
    await page.waitForURL(/host\.html/);
    await page.locator('#resourceRows tr').first().waitFor();
    assert.equal(await page.locator('#resourceRows tr').count(), 3);
    await page.locator('#accountButton').click();
    assert.equal(await page.locator('#projectManagementLink').isVisible(), true);
    await page.locator('#projectManagementLink').click();
    await page.waitForURL(url => decodeURIComponent(url.pathname).includes('项目列表.html'));
    await page.locator('#userIcon').click();
    await page.getByText('系统管理', { exact: true }).last().click();
    await page.waitForURL(url => decodeURIComponent(url.pathname).includes('系统管理.html'));
    await page.getByText('技能管理', { exact: true }).last().click();
    await page.waitForURL(url => decodeURIComponent(url.pathname).includes('智能体配置原型.html'));
    await page.goto(base + '/04_原型与说明/AI协作工作台-风格探索/host.html');
    const [popup] = await Promise.all([page.waitForEvent('popup'), page.locator('#aiEntry').click()]);
    await popup.frameLocator('#workbench').locator('.studio-top').waitFor();
    assert.equal(await popup.frameLocator('#workbench').locator('.studio-top').isVisible(), true);
    await popup.frameLocator('#workbench').locator('.studio-module-nav a').filter({ hasText: '资源管理' }).click();
    await popup.frameLocator('#workbench').frameLocator('.studio-original-frame').locator('body').waitFor();
    await popup.frameLocator('#workbench').locator('.studio-module-nav a').filter({ hasText: '技能管理' }).click();
    await popup.frameLocator('#workbench').frameLocator('.studio-original-frame').locator('body').waitFor();
    await popup.close();
    assert.deepEqual(errors, []);
    assert.deepEqual(missing, []);
    console.log(JSON.stringify({ release, browser: 'passed', route: 'home → project → system → global skills; home → AI workbench → resources → skills', errors, missing }));
  } finally {
    await browser.close();
    if (server.listening) server.close();
  }
})().catch(error => { console.error(error); if (server.listening) server.close(); process.exitCode = 1; });
