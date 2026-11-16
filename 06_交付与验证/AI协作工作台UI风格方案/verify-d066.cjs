const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const host=pathToFileURL(path.resolve(__dirname,'../../04_原型与说明/AI协作工作台-风格探索/host.html')).href;
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1920,height:900}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 try{
  await page.goto(host+'?project=a');
  assert.deepEqual(await page.locator('.side-item').allTextContents(),['图片资源','文件资源集','课程资源','公告管理','审核中心待审核0']);
  assert.equal(await page.locator('.side-item').filter({hasText:/资源管理|技能管理|内容协作/}).count(),0);
  assert.equal(await page.locator('#resourceRows tr').count(),3);
  assert.equal(await page.locator('#imageWorkspace').isVisible(),true);
  const box=await page.locator('#aiEntry').boundingBox();
  assert(box&&box.x>1450&&box.y<60);
  await page.screenshot({path:path.join(__dirname,'D066原系统图片资源首页.png')});
  await page.locator('#fileSearch').fill('example');await page.locator('#searchButton').click();
  assert.equal(await page.locator('#resourceRows tr').count(),1);
  await page.locator('#resetButton').click();assert.equal(await page.locator('#resourceRows tr').count(),3);
  await page.locator('[data-category="测试"]').click();assert.match(await page.locator('#resourceRows').innerText(),/暂无符合条件/);
  await page.locator('[data-category="默认分类"]').click();
  await page.locator('#resourceRows input[type="checkbox"]').first().check();
  assert.match(await page.locator('#selectionCount').innerText(),/已选 1 项/);
  const source=page.url();
  const [popup]=await Promise.all([page.waitForEvent('popup'),page.locator('#aiEntry').click()]);
  await popup.frameLocator('#workbench').locator('.studio-top').waitFor();
  assert.equal(page.url(),source);
  assert.equal(await popup.frameLocator('#workbench').locator('.studio-return').getAttribute('href'),source);
  await popup.frameLocator('#workbench').locator('.studio-return').click();await popup.waitForURL(source);await popup.close();
  await page.locator('#resourceRows input[type="checkbox"]').first().uncheck();
  await page.setViewportSize({width:1440,height:900});await page.screenshot({path:path.join(__dirname,'D066原系统图片资源首页-1440.png')});
  assert.equal(await page.locator('#aiEntry').isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log('D066 checks passed');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
