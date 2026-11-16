// 派生展示只读取03目录的正文主本；不在此维护业务规则。
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../../..');
const source=path.join(root,'03_功能设计/内容协作智能体-需求说明.md');
const md=fs.readFileSync(source,'utf8');
const names=['01_初始状态','02_协作状态_文档','03_协作状态_图片','04_协作状态_视频','05_历史会话筛选','06_保存至资源库','07_保存成功'];
const ids=['3:2','6:2','5:2','4:2','8:2','7:2','9:2'];
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const states=[...md.matchAll(/^## (0[1-7]) (.+)\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)].map((m,i)=>{
 const sections=[...m[3].matchAll(/^### (.+)\n([\s\S]*?)(?=^### |$(?![\s\S]))/gm)].map(x=>({title:x[1],points:x[2].split('\n').filter(x=>/^[a-z]\. /.test(x))}));
 return {key:m[1],title:m[2],nodeId:ids[i],image:'效果图/'+names[i]+'.png',sections};
});
if(states.length!==7||states.some(x=>x.sections.length===0))throw Error('正文状态解析不完整');
const manifest={source:'03_功能设计/内容协作智能体-需求说明.md',version:'v1.0',sourceSha256:crypto.createHash('sha256').update(md).digest('hex'),fileKey:'EjC3IegY9kqwAAmg5M5mrR',states};
fs.writeFileSync(path.join(__dirname,'需求旁注派生数据.json'),JSON.stringify(manifest,null,2));
const record=path.join(__dirname,'需求旁注核验.json');
const pairs=fs.existsSync(record)?JSON.parse(fs.readFileSync(record,'utf8')).pairs:[];
const blocks=states.map(s=>`<section id="state-${s.key}"><h2>${escape(s.key+' '+s.title)} <a href="https://www.figma.com/design/${manifest.fileKey}?node-id=${(pairs.find(p=>p.key===s.key)?.id||s.nodeId).replace(':','-')}" target="_blank" rel="noopener">Figma图文画板 ↗</a> <a href="需求旁注效果图/${s.image.split('/')[1]}" target="_blank">图文效果图 PNG ↗</a></h2><div class="pair"><img width="1280" height="720" src="${s.image}" alt="${escape(s.title)}原型"><aside aria-label="${escape(s.title)}需求说明"><h3>需求说明 · ${s.key}</h3>${s.sections.map(g=>`<h4>${escape(g.title)}</h4><ol>${g.points.map(p=>`<li>${escape(p.slice(3))}</li>`).join('')}</ol>`).join('')}</aside></div></section>`).join('\n');
fs.writeFileSync(path.join(__dirname,'需求说明预览.html'),`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>内容协作智能体 · 原型与需求说明</title><style>*{box-sizing:border-box}body{margin:0;padding:32px;background:#eef0f4;color:#20242b;font-family:"Microsoft YaHei","Noto Sans SC",sans-serif}header{margin-bottom:36px}h1{font-size:25px;margin:0 0 12px}header p{font-size:14px;line-height:1.8;max-width:1080px;color:#566070}a{color:#1769aa;text-decoration:none}nav{display:flex;gap:20px;margin-top:18px;flex-wrap:wrap}section{margin-bottom:48px;width:max-content}section>h2{font-size:18px;margin:0 0 16px}section>h2 a{font-size:13px;font-weight:400;margin-left:20px}.pair{display:flex;flex-wrap:nowrap;align-items:flex-start;gap:28px;width:max-content}.pair>img{flex:0 0 1280px;display:block;width:1280px;height:720px;box-shadow:0 2px 12px #10182812}aside{flex:0 0 460px;width:460px;background:#fff2a8;color:#302b1b;padding:24px;font-size:16px;line-height:1.65}aside h3{font-size:20px;margin:0 0 20px}aside h4{font-size:16px;margin:18px 0 7px}aside ol{list-style-type:lower-alpha;margin:0;padding-left:23px}aside li{margin-bottom:7px;padding-left:2px;overflow-wrap:anywhere}@media print{body{background:white;padding:0}header,section>h2 a{display:none}section{break-after:page}}</style><header><h1>内容协作智能体 · 原型与需求说明</h1><p>v1.0 · 2026-09-15 · 七个状态示例，待评审。左侧保留1280×720原画板，右侧为需求旁注；窄窗口可横向滚动查看。旁注用于开发交接，不属于产品界面。</p><p><a href="../../../03_功能设计/内容协作智能体-需求说明.md">需求说明正文主本</a> · <a href="效果图预览.html">纯效果图预览</a> · <a href="https://www.figma.com/design/${manifest.fileKey}">Figma设计文件</a></p><nav>${states.map(s=>`<a href="#state-${s.key}">${s.key} ${escape(s.title)}</a>`).join('')}</nav></header>${blocks}</html>`);
console.log(JSON.stringify(manifest));
