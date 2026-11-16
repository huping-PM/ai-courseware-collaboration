const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {createServer} = require('./serve.cjs');
const feature='/04_原型与说明/PG11-内容协作智能体/任务处理记录/';
(async()=>{
  const server=createServer();
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const base='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1});
  const review=await browser.newPage({viewport:{width:1840,height:1024},deviceScaleFactor:1});
  const errors=[],failedResources=[],records=[];
  for(const p of [page,review]){
    p.on('pageerror',e=>errors.push(e.message));
    p.on('response',r=>{if(r.status()>=400)failedResources.push({url:r.url(),status:r.status()});});
  }
  for(const folder of ['原型图','图文说明'])fs.mkdirSync(path.join(__dirname,folder),{recursive:true});
  try {
    for(let n=1;n<=13;n++){
      const id='TR'+String(n).padStart(2,'0');
      await page.goto(base+feature+'prototype.html?state='+id);
      await page.waitForFunction(()=>window.TRReady===true);
      await page.evaluate(()=>document.fonts.ready);
      const metrics=await page.evaluate(()=>({state:document.body.dataset.state,overflow:document.documentElement.scrollWidth>innerWidth,controls:[...document.querySelectorAll('button')].filter(e=>e.offsetWidth>0&&e.getBoundingClientRect().right>innerWidth+1).map(e=>e.textContent)}));
      assert.equal(metrics.state,id);
      assert.equal(metrics.overflow,false,id+' horizontal overflow');
      await page.screenshot({path:path.join(__dirname,'原型图',id+'.png')});
      await review.goto(base+feature+'review.html?state='+id+'&capture=1');
      await review.waitForFunction(()=>document.querySelector('iframe')?.contentWindow.TRReady===true&&document.querySelector('#noteBody')?.innerText.length>20);
      await review.evaluate(()=>document.fonts.ready);
      const note=await review.evaluate(()=>{
        const frame=document.querySelector('iframe').getBoundingClientRect(), panel=document.querySelector('#notesPanel').getBoundingClientRect();
        return {right:panel.left>=frame.right-1,text:document.querySelector('#noteBody').innerText.length,editable:document.querySelector('#noteBody').isContentEditable};
      });
      assert(note.right && note.editable,id+' notes placement or editing');
      await review.screenshot({path:path.join(__dirname,'图文说明',id+'.png'),fullPage:true});
      records.push({id,metrics,note});
      console.log(id+' captured');
    }
    await page.setViewportSize({width:1920,height:1080});
    await page.goto(base+feature+'prototype.html?state=TR04');
    await page.waitForFunction(()=>window.TRReady===true);
    await page.screenshot({path:path.join(__dirname,'原型图','TR04-1920.png')});
    assert.equal(errors.length,0,'browser errors: '+errors.join('; '));
    assert.equal(failedResources.length,0,'resource failures: '+JSON.stringify(failedResources));
    fs.writeFileSync(path.join(__dirname,'截图核验.json'),JSON.stringify({date:'2026-09-28',scope:'本地原型画面与说明布局检查；不替代后端、权限或真实生成验证',states:records.length,errors,failedResources,records},null,2));
    console.log(JSON.stringify({states:records.length,errors,failedResources}));
  } finally { await browser.close();await new Promise(r=>server.close(r)); }
})().catch(e=>{console.error(e);process.exitCode=1;});
