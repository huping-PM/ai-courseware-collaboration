const assert=require('node:assert/strict');
const path=require('node:path');
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base='http://127.0.0.1:8775/06_%E4%BA%A4%E4%BB%98%E4%B8%8E%E9%AA%8C%E8%AF%81/AI%E5%8D%8F%E4%BD%9C%E5%B7%A5%E4%BD%9C%E5%8F%B0UI%E9%A3%8E%E6%A0%BC%E6%96%B9%E6%A1%88/%E4%BA%A4%E4%BA%92Demo.html?revision=D061';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const frame=page.frameLocator('#workbench');const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(base);await frame.locator('#newSessionButton').waitFor();
  await frame.locator('body').evaluate(()=>localStorage.clear());await page.reload();await frame.locator('#newSessionButton').waitFor();
  assert.equal(await frame.locator('.studio-project-context').count(),0);
  assert(await frame.getByRole('button',{name:'添加本地文件'}).isVisible());
  assert(await frame.getByRole('button',{name:'资源',exact:true}).isVisible());
  assert(await frame.locator('#modelSelect').isVisible());
  await page.screenshot({path:path.join(__dirname,'D061工作台.png')});
  await frame.getByRole('button',{name:'资源',exact:true}).click();
  assert(await frame.getByRole('heading',{name:'选择资源'}).isVisible());
  await frame.locator('#referenceType').selectOption('图片');
  assert.equal(await frame.locator('[data-reference-id]').count(),2);
  await frame.locator('#referenceCategory').selectOption('未分类');
  assert.equal(await frame.locator('[data-reference-id]').count(),1);
  assert((await frame.locator('[data-reference-id]').innerText()).includes('倾听与回应'));
  await frame.locator('#referenceSearch').fill('没有结果');
  assert(await frame.getByText('没有匹配的资源').isVisible());
  await frame.getByRole('button',{name:'关闭'}).click();
  await frame.locator('#modelSelect').click();
  assert.equal(await frame.locator('#modelMenu [role="option"]').count(),4);
  await frame.locator('[data-model="deepseek-flash"]').click();
  assert.equal(await frame.locator('#modelLabel').innerText(),'deepseek-flash');
  await frame.locator('#localFilePicker').setInputFiles([
   {name:'课程脚本.md',mimeType:'text/markdown',buffer:Buffer.from('# course')},
   {name:'场景配图.png',mimeType:'image/png',buffer:Buffer.from('sample')}
  ]);
  assert(await frame.getByRole('heading',{name:'确认上传文件'}).isVisible());
  assert.equal(await frame.locator('#localUploadRows tr').count(),2);
  assert(await frame.locator('#localUploadRows tr').first().locator('select').isDisabled());
  await frame.locator('#localUploadRows tr').first().locator('input[type="checkbox"]').check();
  assert(await frame.locator('#localUploadRows tr').first().locator('select').isEnabled());
  await frame.locator('#localUploadRows tr').first().locator('select').selectOption('培训素材');
  await page.screenshot({path:path.join(__dirname,'D061本地上传弹窗.png')});
  await frame.locator('#confirmLocalUpload').click();
  assert.equal(await frame.locator('#localAttachments .bui-reference-chip').count(),2);
  await frame.locator('#message').fill('请参考这两份本地文件');await frame.locator('#message').press('Enter');
  const msg=await frame.locator('#chatLog .human').last().innerText();
  assert(msg.includes('课程脚本.md')&&msg.includes('场景配图.png')&&msg.includes('deepseek-flash'));
  assert.equal(await frame.locator('#localAttachments .bui-reference-chip').count(),0);
  await frame.locator('#newSessionButton').click();await frame.locator('#newSessionName').fill('模型隔离会话');await frame.locator('#confirmNewSession').click();
  assert.equal(await frame.locator('#modelLabel').innerText(),'qwen3.7-plus');
  await frame.locator('[data-session-id="s-communication"]').click();
  assert.equal(await frame.locator('#modelLabel').innerText(),'deepseek-flash');
  const href=await frame.locator('.studio-module-nav a').nth(1).getAttribute('href');
  await page.goto(href.startsWith('http')?href:'http://127.0.0.1:8775/04_%E5%8E%9F%E5%9E%8B%E4%B8%8E%E8%AF%B4%E6%98%8E/AI%E5%8D%8F%E4%BD%9C%E5%B7%A5%E4%BD%9C%E5%8F%B0-%E9%A3%8E%E6%A0%BC%E6%8E%A2%E7%B4%A2/'+href);
  await page.locator('#resourceSearch').fill('课程脚本');
  assert((await page.locator('#resourceResults').innerText()).includes('课程脚本.md'));
  const size=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth}));
  assert(size.scroll<=size.client);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({passed:true,checks:17,errors,size},null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
