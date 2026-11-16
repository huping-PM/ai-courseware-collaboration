const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname,workspace=path.resolve(root,'../../..'),source=path.join(workspace,'04_原型与说明'),template=path.join(root,'../AI课件协作平台-原型预览包_2026-09-15_更新版');
const args=process.argv.slice(2),manifestPath=path.join(root,'current.json');
function activate(data){const temp=manifestPath+'.tmp';fs.writeFileSync(temp,JSON.stringify(data,null,2));fs.renameSync(temp,manifestPath)}
if(args[0]==='activate-existing'){
 const name=args[1];if(!/^release-\d+$/.test(name||''))throw Error('Invalid release');
 const dir=path.join(root,'releases',name),manifest=JSON.parse(fs.readFileSync(path.join(dir,'release-manifest.json')));
 for(const f of manifest.files){const file=path.resolve(dir,f.path);if(!file.startsWith(dir+path.sep)||crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')!==f.sha256)throw Error('Release integrity failed: '+f.path)}
 const previous=JSON.parse(fs.readFileSync(manifestPath)).release;activate({release:name,previous,publishedAt:new Date().toISOString()});console.log(JSON.stringify({release:name,previous,activated:true}));process.exit(0);
}
if(args[0]==='rollback'){const a=JSON.parse(fs.readFileSync(manifestPath));if(!a.previous)throw Error('No previous release');activate({release:a.previous,previous:a.release,publishedAt:new Date().toISOString()});console.log('Rolled back to '+a.previous);process.exit(0)}
require(path.join(source,'shared/build-requirement-notes.cjs'));
const release='release-'+new Date().toISOString().replace(/[^0-9]/g,''),target=path.join(root,'releases',release);fs.mkdirSync(target,{recursive:true});const files=[];
function add(relative,buffer){const out=path.join(target,relative);fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,buffer);files.push({path:relative,sha256:crypto.createHash('sha256').update(buffer).digest('hex')})}
const compat=`if(!crypto.randomUUID){crypto.randomUUID=function(){const b=crypto.getRandomValues(new Uint8Array(16));b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;const h=Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20)}};`;
add('compat.js',compat);
const allowed=/\.(html|css|js|png|jpe?g|svg|webm|mp4|wav|mp3|woff2|ico)$/i;
function walk(dir,prefix=''){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const relative=path.join(prefix,e.name);if(e.isSymbolicLink())throw Error('Symlink not allowed');if(e.isDirectory())walk(path.join(dir,e.name),relative);else if(allowed.test(e.name)){
 const live=path.join(source,relative);if(!fs.existsSync(live))throw Error('Source missing: '+live);let data=fs.readFileSync(live);if(e.name.endsWith('.html')){let html=data.toString('utf8');html=html.replace('<head>','<head><script src="/compat.js"></script>');data=Buffer.from(html)}add(path.join('页面',relative),data)
}}}
walk(path.join(template,'页面'));
// Explicit additions since the original offline dependency baseline.
for(const relative of ['PG07-资源管理/category-tree.js','PG07-资源管理/category-tree.css','shared/local-files.js','PG13-智能体配置/skill-packages.js','PG13-智能体配置/skill-packages.css','PG11-内容协作智能体/task-workspace.js','PG11-内容协作智能体/task-workspace.css','PG11-内容协作智能体/local-upload.js','PG07-资源管理/local-file-preview.js']){
 const published=path.join('页面',relative);if(!files.some(f=>f.path===published))add(published,fs.readFileSync(path.join(source,relative)));
}
for(const relative of ['shared/platform.js','shared/platform.css','shared/project-context.js','PG07-资源管理/project-data.js','PG13-智能体配置/skill-scope.js','PG02-项目管理/项目列表.html','PG02-项目管理/项目设置.html','PG02-项目管理/登录.html','PG02-项目管理/projects.js','PG02-项目管理/projects.css','PG14-系统管理/系统管理.html','PG14-系统管理/system.js','PG14-系统管理/system.css']){let content=fs.readFileSync(path.join(source,relative));if(relative.endsWith('.html'))content=Buffer.from(content.toString('utf8').replace('<head>','<head><script src="/compat.js"></script>'));add(path.join('页面',relative),content)}
for(const file of ['requirement-notes-loader.js','requirement-notes-data.js','requirement-notes.js','requirement-notes.css','需求说明预览.html'])add(path.join('页面','shared',file),fs.readFileSync(path.join(source,'shared',file)));
const portal=fs.readFileSync(path.join(root,'原型预览.html'),'utf8');add('原型预览.html',portal);

// Reject broken local references and script syntax before exposing a release.
for(const item of files){const absolute=path.join(target,item.path);if(item.path.endsWith('.js'))new (require('vm').Script)(fs.readFileSync(absolute,'utf8'),{filename:item.path});if(item.path.endsWith('.html')){const html=fs.readFileSync(absolute,'utf8');for(const m of html.matchAll(/(?:src|href)=["']([^"']+)["']/g)){const ref=m[1];if(/^(?:https?:|data:|blob:|#|javascript:)/i.test(ref))continue;const name=ref==='/'?'/原型预览.html':decodeURIComponent(ref.split(/[?#]/)[0]);const resolved=name.startsWith('/')?path.join(target,name.slice(1)):path.resolve(path.dirname(absolute),name);if(!resolved.startsWith(target+path.sep)||!fs.existsSync(resolved))throw Error('Missing or out-of-root dependency: '+item.path+' -> '+ref)}}}

fs.writeFileSync(path.join(target,'release-manifest.json'),JSON.stringify({release,created:new Date().toISOString(),files},null,2));
// Activation is a separate explicit step after browser validation.
if(args[0]==='activate'){let previous;try{previous=JSON.parse(fs.readFileSync(manifestPath)).release}catch{}activate({release,previous,publishedAt:new Date().toISOString()})}
console.log(JSON.stringify({release,files:files.length,activated:args[0]==='activate'}));
