/* Skills retain the uploaded archive and every unpacked file in local prototype storage. */
(()=>{
const savedKey='platform-global-skills-v1';let bundle=null,reading=false;
if(!localStorage.getItem(savedKey)){const legacy=localStorage.getItem('pg13-skills-packages-v1');if(legacy)localStorage.setItem(savedKey,legacy)}
try{const saved=JSON.parse(localStorage.getItem(savedKey)||'null');if(Array.isArray(saved)){skills.splice(0,skills.length,...saved);id=Math.max(id,...saved.map(s=>s.id+1));for(const s of skills)if(s.status==='parsing'){s.status='failed';s.error='上次解析中断，请重新提交'}}}catch{}
for(const x of skills)if(!x.skillType)x.skillType='global';
const oldRender=render;render=function(){for(const x of skills)if(!x.skillType){const q=new URLSearchParams(location.search);x.skillType=q.get('scope')==='global'?'global':'project';x.ownerProject=x.skillType==='project'?(q.get('project')||'a'):null;}oldRender();try{if(!window.readingGlobalSkillUpdate)localStorage.setItem(savedKey,JSON.stringify(skills))}catch{toast('技能信息保存失败，请检查浏览器存储空间')}};
const oldForm=form;form=function(x=null){oldForm(x);if(tab!=='skill')return;bundle=x?.bundle||null;if(x)fillSkillMetadata({name:x.name,description:x.desc});
 const input=$('#skillFile');input.accept='.zip,.md';const hint=input.closest('.control').querySelector('.muted');hint.textContent='支持 ZIP 技能包或 skills.md / SKILL.md；包内其他文件一并保留。';
 const box=document.createElement('div');box.id='packageFiles';box.className='package-files';input.closest('.control').append(box);draw();
 input.onchange=async e=>{const f=e.target.files[0];if(!f)return;const token=++formToken;bundle=null;fileText='';fileName='';reading=true;pendingReads=1;$('#save').disabled=true;$('#formName').value='';$('#formDesc').value='';$('#fileError').textContent='';$('#fileName').textContent='正在读取 '+f.name;draw();
 try{let parsed;if(/\.zip$/i.test(f.name))parsed=await LocalFiles.unzip(f);else{if(!/^skills?\.md$/i.test(f.name))throw Error('请选择ZIP技能包或 skills.md / SKILL.md');parsed={name:f.name,blob:f,files:[{path:f.name,size:f.size,blob:f}],entry:{path:f.name,blob:f}}}
 const text=new TextDecoder('utf-8',{fatal:true}).decode(await parsed.entry.blob.arrayBuffer());if(text.length>10000)throw Error('技能说明正文不能超过10000字');const meta=parseSkillMetadata(text);if(token!==formToken)return;
 bundle={key:crypto.randomUUID(),name:f.name,entry:parsed.entry.path,files:parsed.files.map(v=>({path:v.path,size:v.size})),payload:parsed};fileText=text;fileName=f.name;fillSkillMetadata(meta);$('#fileName').textContent=f.name;dirty=true;
 }catch(err){if(token===formToken){$('#fileError').textContent=err.message||'读取失败，请检查文件';$('#fileName').textContent='未选择有效文件'}}finally{if(token===formToken){reading=false;pendingReads=0;$('#save').disabled=false;draw()}}};
};
function draw(){const el=$('#packageFiles');if(!el)return;el.innerHTML=reading?'<div class="package-reading">正在解析文件结构…</div>':bundle?`<div class="package-heading">${esc(bundle.entry)} <span>技能入口 · 共${bundle.files.length}个文件</span></div><div class="package-file-list">${bundle.files.map(f=>`<div><span>${icon('folder')}${esc(f.path)}</span><small>${(f.size/1024).toFixed(1)} KB</small></div>`).join('')}</div>`:'';}
const oldSave=save;save=async function(){if(tab!=='skill')return oldSave();if(reading||!valid(values()))return;const pack=bundle,token=formToken;const v=values();if(failSave){$('#formError').textContent='保存失败，请重试';return}$('#save').disabled=true;
 try{if(pack?.payload)await LocalFiles.put(pack.key,pack.payload);if(!$('#modal').open||token!==formToken)return;const record=editing;oldSave();const x=record||skills.find(s=>s.name===v.name);if(x&&pack){const {payload,...meta}=pack;x.bundle=meta}render()}catch(e){if(token===formToken){$('#formError').textContent='技能包保存失败，请重试';$('#save').disabled=false}}
};
const oldDetail=detail;detail=function(x){oldDetail(x);if(tab!=='skill'||!x.bundle)return;$('#modalBody').insertAdjacentHTML('afterbegin',`<section class="package-detail"><div class="section-label">技能包文件 <button id="downloadPackage" class="link">下载原文件</button></div><div class="package-file-list">${x.bundle.files.map((f,i)=>`<div><span>${esc(f.path)}${f.path===x.bundle.entry?'（技能入口）':''}</span><button class="link" data-package-file="${i}">下载</button></div>`).join('')}</div></section>`);
 async function download(i){try{const p=await LocalFiles.get(x.bundle.key);if(!p)throw Error();const f=i===null?{blob:p.blob,path:p.name}:p.files[i];const url=URL.createObjectURL(f.blob),a=document.createElement('a');a.href=url;a.download=f.path.split('/').pop();a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}catch{toast('本地文件不可用，请重新上传技能包')}}
 $('#downloadPackage').onclick=()=>download(null);document.querySelectorAll('[data-package-file]').forEach(b=>b.onclick=()=>download(+b.dataset.packageFile));};
render();
})();
