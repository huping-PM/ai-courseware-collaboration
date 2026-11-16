(()=>{
if(!document.querySelector('#saveResource')||scene==='denied')return;
const key='pg07-saved-generated-v1';
function read(){return JSON.parse(localStorage.getItem(key)||'[]')}
function source(a){return project+':'+current.id+':'+a.id}
function state(){const a=current.artifacts.find(a=>a.id===selected),b=$('#saveResource');let saved=false;try{saved=!!a&&read().some(r=>r.sourceArtifact===source(a))}catch{}b.disabled=!a||a.status!=='ready'||saved;b.textContent=saved?'已保存至资源库':'保存至资源库'}
const previous=renderViewer;renderViewer=function(){previous();state()};state();
$('#saveResource').onclick=()=>{
const a=current.artifacts.find(a=>a.id===selected);if(!a||a.status!=='ready')return;
const targetProject=project,targetSession=current.id,sourceId=source(a);const extension=a.type==='image'?'.png':a.type==='video'?'.webm':'.md';const filename=a.name.replace(/\.[^.]+$/,'')+extension;
$('#confirmTitle').textContent='保存至资源库';$('#confirmBody').innerHTML=`<div class="field"><label>所属项目</label><div class="control"><input value="${esc(projects[targetProject])}" disabled></div></div><div class="field"><label class="required" for="resourceName">资源名称</label><div class="control"><input id="resourceName" maxlength="100" value="${esc(filename)}"></div></div><div class="field"><label for="resourceCategory">资源分类</label><div class="control"><select id="resourceCategory"><option>未分类</option><option selected>培训素材</option><option>品牌素材</option></select></div></div><div class="error" id="saveResourceError" role="alert"></div>`;
$('#confirmFooter').innerHTML='<button id="cancelSaveResource">取消</button><button class="primary" id="confirmSaveResource">保存</button>';
$('#cancelSaveResource').onclick=()=>$('#confirm').close();$('#confirmSaveResource').onclick=async()=>{
const button=$('#confirmSaveResource'),name=$('#resourceName').value.trim(),category=$('#resourceCategory').value;
if(!name||/[\\/:*?"<>|]/.test(name)||!name.toLowerCase().endsWith(extension)){$('#saveResourceError').textContent='请输入有效文件名，并保留 '+extension+' 扩展名。';return}
button.disabled=true;button.textContent='保存中';
try{const bank=read();if(bank.some(r=>r.sourceArtifact===sourceId)){throw Error('该内容已保存，请在资源管理中查看。')}if(bank.some(r=>r.projectId===targetProject&&r.type===a.type&&r.name===name)){throw Error('资源库已有同名文件，请修改名称后保存。')}
let content='',url='',thumb=helmetUrl,bytes=0;if(a.type==='doc'){const doc=new DOMParser().parseFromString(documentHtml,'text/html');content=[...doc.querySelector('.document').children].map(el=>el.tagName==='H2'?'# '+el.textContent:el.tagName==='H3'?'## '+el.textContent:el.tagName==='UL'?[...el.children].map(li=>'- '+li.textContent).join('\n'):el.textContent).join('\n\n');bytes=new Blob([content]).size}else if(a.type==='image'){const img=new Image();img.src=helmetUrl;await img.decode();const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;canvas.getContext('2d').drawImage(img,0,0);url=canvas.toDataURL('image/png');thumb=url;bytes=Math.round((url.length-url.indexOf(',')-1)*.75)}else{url='assets/preview.webm';bytes=9986}
const row={id:Date.now()+Math.floor(Math.random()*1000),projectId:targetProject,type:a.type,sourceArtifact:sourceId,sourceSession:targetSession,name,cat:category,format:extension.slice(1).toUpperCase(),size:Math.max(.1,bytes/1024).toFixed(1)+'KB',detail:a.type==='image'?'800×600':a.type==='video'?'00:01':'',who:'演示成员甲',time:new Date().toLocaleString('sv-SE').slice(0,16),desc:'来自内容协作智能体',referenced:false,thumb,url,content};const latest=read();if(latest.some(r=>r.sourceArtifact===sourceId))throw Error('该内容已保存，请在资源管理中查看。');if(latest.some(r=>r.projectId===targetProject&&r.type===a.type&&r.name===name))throw Error('资源库已有同名文件，请修改名称后保存。');latest.push(row);localStorage.setItem(key,JSON.stringify(latest));$('#confirm').close();state();toast('已保存至资源库');
}catch(e){$('#saveResourceError').textContent=e.message||'保存失败，请重试。';button.disabled=false;button.textContent='保存'}
};$('#confirm').showModal();
};window.addEventListener('storage',e=>{if(e.key===key)state()});
})();
