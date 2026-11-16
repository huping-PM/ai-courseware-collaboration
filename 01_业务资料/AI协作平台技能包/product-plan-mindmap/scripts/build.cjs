#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const [input,out,...flags]=process.argv.slice(2);
if(!input||!out||flags.some(v=>v!=='--force')){console.error('Usage: node build.cjs <plan.json> <output-dir> [--force]');process.exit(1);}
const base=path.dirname(path.resolve(input)),dest=path.resolve(out);
const config=JSON.parse(fs.readFileSync(input,'utf8').replace(/^\uFEFF/,''));
const str=(v,label)=>{if(typeof v!=='string'||!v.trim())throw Error(label+' must be nonempty text');};
const arr=(v,label)=>{if(!Array.isArray(v)||!v.length)throw Error(label+' must be a nonempty array');};
str(config.title,'title');config.subtitle??='业务场景与功能方向讨论稿';str(config.subtitle,'subtitle');arr(config.groups,'groups');
const imageCopies=[];
for(const g of config.groups){str(g.title,'group.title');g.subtitle??='';arr(g.sections,'sections');for(const s of g.sections){str(s.title,'section.title');s.structure??='comparison';if(!['comparison','modules','conditional'].includes(s.structure))throw Error('Invalid structure');arr(s.topics,'topics');for(const t of s.topics){str(t.title,'topic.title');arr(t.items,'topic.items');t.items.forEach(v=>str(v,'item'));if(t.priority!==undefined&&![1,2,3].includes(t.priority))throw Error('priority must be 1,2,3');if(t.recommended!==undefined&&typeof t.recommended!=='boolean')throw Error('recommended must be boolean');for(const mod of t.modules||[]){str(mod.title,'module.title');arr(mod.items,'module.items');mod.items.forEach(v=>str(v,'module item'));}for(const im of t.images||[]){str(im.title,'image.title');str(im.src,'image.src');const original=path.resolve(base,im.src),ext=path.extname(original).toLowerCase();if(!['.png','.jpg','.jpeg','.webp','.svg'].includes(ext))throw Error('Unsupported image: '+im.src);const bytes=fs.readFileSync(original),name=crypto.createHash('sha256').update(bytes).digest('hex').slice(0,16)+ext;im.src='assets/'+name;imageCopies.push({bytes,name});}}}}
const names=['产品方案-交互导图.html','产品方案-讨论稿.md','方案数据.json'];
if(!flags.includes('--force'))for(const n of names)if(fs.existsSync(path.join(dest,n)))throw Error('Output already exists: '+n+'; use --force only for an intended update');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const values={__TITLE__:esc(config.title),__SUBTITLE__:esc(config.subtitle),__DATE__:esc(config.date||'方向讨论稿'),__CONFIG__:JSON.stringify(config).replace(/</g,'\\u003c')};
let html=fs.readFileSync(path.join(__dirname,'../assets/template.html'),'utf8').replace(/__TITLE__|__SUBTITLE__|__DATE__|__CONFIG__/g,k=>values[k]);
for(const m of html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g))new Function(m[1]);
let md='# '+config.title+'\n\n'+config.subtitle+'\n\n';
for(const [i,g] of config.groups.entries()){md+='## '+String(i+1).padStart(2,'0')+' '+g.title+'\n\n'+(g.subtitle?g.subtitle+'\n\n':'');for(const s of g.sections){md+='### '+s.title+'\n\n';for(const t of s.topics){md+='#### '+t.title+(t.recommended?'【推荐】':'')+(t.priority?'　`'+t.priority+'`':'')+'\n\n'+t.items.map(x=>'- '+x).join('\n')+'\n\n';for(const im of t.images||[])md+='!['+im.title+']('+im.src+')\n\n';if(t.modules?.length)md+='**核心功能模块**\n\n'+t.modules.map(m=>'- **'+m.title+'**：'+m.items.join(' ')).join('\n')+'\n\n';}}}
fs.mkdirSync(dest,{recursive:true});if(imageCopies.length)fs.mkdirSync(path.join(dest,'assets'),{recursive:true});
for(const im of imageCopies)fs.writeFileSync(path.join(dest,'assets',im.name),im.bytes);
fs.writeFileSync(path.join(dest,names[0]),html);fs.writeFileSync(path.join(dest,names[1]),md);fs.writeFileSync(path.join(dest,names[2]),JSON.stringify(config,null,2)+'\n');
console.log(JSON.stringify({output:dest,files:names,groups:config.groups.length,images:imageCopies.length}));
