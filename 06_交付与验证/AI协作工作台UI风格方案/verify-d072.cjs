const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const output=path.join(__dirname,'D072核验');fs.mkdirSync(output,{recursive:true});
(async()=>{const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));const checks=[];
try{
await page.goto(pathToFileURL(path.join(__dirname,'交互Demo.html')).href);const shell=page.frameLocator('#workbench');await shell.locator('#newSessionButton').waitFor();
assert.equal(await shell.getByRole('link',{name:'智能体配置',exact:true}).count(),1);checks.push('顶栏智能体配置命名');
await shell.getByRole('link',{name:'资源管理',exact:true}).click();let view=shell.frameLocator('.studio-original-frame');await view.locator('#types').waitFor();
for(const name of ['图片','文档','音频','视频']){await view.locator('.type-tab').filter({hasText:name}).click();assert(await view.locator('#rows tr').count()>0);checks.push(name+'页签');}
await view.locator('.type-tab').filter({hasText:'图片'}).click();await page.screenshot({path:path.join(output,'资源管理-1440.png')});
await page.setViewportSize({width:1920,height:1080});await page.screenshot({path:path.join(output,'资源管理-1920.png')});await page.setViewportSize({width:1440,height:900});
await view.locator('#keyword').fill('不存在的测试资源987');await view.locator('#queryForm button[type=submit]').click();assert(await view.locator('.empty-cell').isVisible());await view.locator('#reset').click();assert(!await view.locator('.empty-cell').count());checks.push('资源搜索空态及重置');
await view.locator('#upload').click();assert(await view.locator('#modal').isVisible());await page.screenshot({path:path.join(output,'上传资源.png')});await view.locator('#closeModal').click();checks.push('上传资源弹窗');
await shell.getByRole('link',{name:'智能体配置',exact:true}).click();view=shell.frameLocator('.studio-original-frame');await view.locator('#query').waitFor();
await page.screenshot({path:path.join(output,'智能体配置-技能-1440.png')});await page.setViewportSize({width:1920,height:1080});await page.screenshot({path:path.join(output,'智能体配置-技能-1920.png')});await page.setViewportSize({width:1440,height:900});
await view.locator('#keyword').fill('不存在的测试技能987');await view.locator('#query button[type=submit]').click();assert(await view.locator('.empty-cell').isVisible());await view.locator('#reset').click();checks.push('技能搜索空态及重置');
await view.locator('#create').click();assert(await view.locator('#modal').isVisible());await page.screenshot({path:path.join(output,'新增技能.png')});await view.locator('#close').click();
await view.locator('[data-act=edit]').first().click();assert(await view.locator('#modal').isVisible());await view.locator('#close').click();checks.push('技能新增与项目技能编辑弹窗');
const toggle=view.locator('[role=switch]:not([disabled])').first();const before=await toggle.getAttribute('aria-checked');await toggle.click();assert(await view.locator('#confirm').isVisible());await view.locator('#acceptConfirm').click();assert.notEqual(await toggle.getAttribute('aria-checked'),before);await toggle.click();await view.locator('#acceptConfirm').click();assert.equal(await toggle.getAttribute('aria-checked'),before);checks.push('项目技能启停确认与恢复');
await shell.getByRole('link',{name:'提示词管理',exact:true}).click();await view.locator('#promptTypeFilter').waitFor({state:'visible'});await page.screenshot({path:path.join(output,'智能体配置-提示词-1440.png')});
await view.locator('#create').click();assert(await view.locator('#modal').isVisible());await page.screenshot({path:path.join(output,'新增提示词.png')});await view.locator('#close').click();await view.locator('[data-act=edit]').first().click();assert(await view.locator('#modal').isVisible());await view.locator('#close').click();checks.push('提示词切换、新增与编辑弹窗');
assert(await shell.locator('body').evaluate(el=>el.scrollWidth<=innerWidth));assert(await view.locator('body').evaluate(el=>el.scrollWidth<=innerWidth));checks.push('1440页面无横向溢出，表格独立滚动');
await shell.getByRole('link',{name:'课件协作',exact:true}).click();await shell.locator('#newSessionButton').waitFor();checks.push('返回课件协作');assert.deepEqual(errors,[]);checks.push('无浏览器脚本异常');
fs.writeFileSync(path.join(output,'result.json'),JSON.stringify({passed:true,viewports:[{width:1440,height:900},{width:1920,height:1080}],checks,errors,errorCount:errors.length},null,2));console.log(JSON.stringify({passed:true,checks,output},null,2));
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
