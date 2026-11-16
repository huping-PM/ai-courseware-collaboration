const assert=require('node:assert/strict');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..');
const file=(relative,query='')=>pathToFileURL(path.join(root,'04_原型与说明',relative)).href+query;
const pages=[
 'PG02-项目管理/项目设置.html',
 'PG07-资源管理/资源管理原型.html',
 'PG13-智能体配置/智能体配置原型.html',
 'PG11-内容协作智能体/内容协作智能体原型.html',
 'PG11-内容协作智能体/内容协作状态原型.html',
 'PG11-内容协作智能体/课件编辑器/editor.html',
 'PG11-内容协作智能体/任务处理记录/prototype.html'
];
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
 page.on('pageerror',error=>errors.push(error.message));
 try{
  for(const relative of pages){
   await page.goto(file(relative,'?notes=off&project=b'));
   const entry=page.locator('header.top .ai-workbench-entry,header.system-top .ai-workbench-entry');
   await entry.waitFor();
   assert.equal(await entry.count(),1,relative);
   assert.equal(await entry.getAttribute('target'),'_blank',relative);
   const href=new URL(await entry.getAttribute('href'));
   assert(decodeURIComponent(href.pathname).endsWith('交互Demo.html')&&href.searchParams.get('project')==='b',relative);
   const box=await entry.boundingBox();
   assert(box&&box.x>500&&box.x+box.width<=1440,relative+' entry position');
   if(relative.startsWith('PG07-'))await page.screenshot({path:path.join(__dirname,'D065原系统资源页入口.png')});
   if(relative.includes('课件编辑器/'))await page.screenshot({path:path.join(__dirname,'D065课件编辑器入口.png')});
   console.log('PASS',relative);
  }
  await page.goto(file(pages[1],'?notes=off&project=b'));
  const original=page.url();
  const [popup]=await Promise.all([page.waitForEvent('popup'),page.locator('.ai-workbench-entry').click()]);
  await popup.waitForLoadState();
  const frame=popup.frameLocator('#workbench');
  await frame.locator('.studio-top').waitFor();
  await popup.screenshot({path:path.join(__dirname,'D065从原系统打开工作台.png')});
  assert.equal(page.url(),original,'source page stays open');
  assert.equal(new URL(popup.url()).searchParams.get('project'),'b');
  assert.equal(await frame.locator('.studio-return').getAttribute('href'),original);
  await frame.getByRole('link',{name:'资源管理'}).click();
  await frame.locator('.studio-original-frame').waitFor();
  assert.match(await frame.locator('.studio-original-frame').getAttribute('src'),/project=b/);
  assert.equal(await frame.locator('.studio-return').getAttribute('target'),'_top');
  await frame.locator('.studio-return').click();
  await popup.waitForURL(original);
  await popup.close();
  for(const [relative,query] of [
   ['PG13-智能体配置/智能体配置原型.html','?notes=off&scope=global'],
   ['PG07-资源管理/资源管理原型.html','?notes=off&embed=ai'],
   ['PG02-项目管理/项目列表.html','?notes=off'],
   ['PG02-项目管理/登录.html','?notes=off'],
   ['PG14-系统管理/系统管理.html','?notes=off']]){
    await page.goto(file(relative,query));
    assert.equal(await page.locator('.ai-workbench-entry').count(),0,relative+' excluded');
  }
  assert.deepEqual(errors,[]);
  console.log('PASS new tab, return path, module context, exclusions, zero page errors');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
