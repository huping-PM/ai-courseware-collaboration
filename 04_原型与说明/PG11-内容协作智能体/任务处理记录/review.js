(()=>{
  const $=s=>document.querySelector(s),frame=$('#prototype'),data=window.TR_NOTES;
  const params=new URLSearchParams(location.search);let active=data.states.find(s=>s.id===params.get('state'))?.id||'TR03';
  if(params.has('capture'))document.body.classList.add('capture');
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const noteKey=id=>'pg11-task-record-note-'+id;
  const format=text=>text.split(/\r?\n/).filter(Boolean).map(line=>/^\d+\. /.test(line)?'<h3>'+esc(line)+'</h3>':'<p>'+esc(line)+'</p>').join('');
  const defaultText=()=>data.states.find(s=>s.id===active).text;
  function getDraft(){try{return localStorage.getItem(noteKey(active));}catch{return null;}}
  function showNotes(id){
    const state=data.states.find(s=>s.id===id);if(!state)return;
    active=id;window.reviewState=id;$('#stateSelect').value=id;$('#noteTitle').textContent=id+' '+state.title;
    const draft=getDraft();$('#noteBody').innerHTML=format(draft===null?state.text:draft);
    $('#noteStatus').textContent=draft===null?'正文来源：需求说明主本。浏览器编辑不会修改主本。':'已加载本浏览器保存的说明草稿；主本未修改。';
    $('#pureLink').href='prototype.html?state='+id;
  }
  function navigate(id){showNotes(id);frame.src='prototype.html?state='+encodeURIComponent(id);const url=new URL(location.href);url.searchParams.set('state',id);history.replaceState(null,'',url);}
  function updateActions(){
    try{const snapshot=frame.contentWindow.TRDemo?.getData();if(!snapshot)return;const attempts=(snapshot.conversations||[]).flatMap(c=>(c.requests||[]).flatMap(r=>r.attempts||[]));const running=attempts.some(a=>a.status==='running');$('#advance').disabled=!attempts.some(a=>a.status==='running'||a.status==='stopping'||a.loading);$('#fail').disabled=!running;$('#cancel').disabled=!running;}catch{}
  }
  function action(name){frame.contentWindow.postMessage({type:'tr-demo-action',action:name},location.origin==='null'?'*':location.origin);}
  $('#stateSelect').innerHTML=data.states.map(s=>'<option value="'+s.id+'">'+esc(s.id+' '+s.title)+'</option>').join('');
  $('#stateSelect').onchange=e=>navigate(e.target.value);
  for(const name of ['advance','fail','cancel'])$('#'+name).onclick=()=>action(name);
  $('#toggleNotes').onclick=()=>{const hidden=document.body.classList.toggle('notes-hidden');$('#toggleNotes').textContent=hidden?'展开说明':'收起说明';$('#toggleNotes').setAttribute('aria-expanded',String(!hidden));};
  $('#noteBody').addEventListener('input',()=>$('#noteStatus').textContent='说明已修改，尚未保存；不会自动更新需求主本。');
  $('#saveDraft').onclick=()=>{try{localStorage.setItem(noteKey(active),$('#noteBody').innerText);$('#noteStatus').textContent='已保存本状态的本地草稿；正式规则仍以需求主本为准。';}catch{$('#noteStatus').textContent='浏览器不允许本地保存，请下载说明HTML。';}};
  $('#restoreDefault').onclick=()=>{$('#noteBody').innerHTML=format(defaultText());$('#noteStatus').textContent='已恢复文件默认正文；已保存草稿仍保留，清除后才会移除。';};
  $('#clearDraft').onclick=()=>{try{localStorage.removeItem(noteKey(active));}catch{}$('#noteBody').innerHTML=format(defaultText());$('#noteStatus').textContent='已清除本状态的本地修改，恢复文件默认。';};
  $('#exportHtml').onclick=async()=>{
    const id=active,title=$('#noteTitle').textContent,text=$('#noteBody').innerText;
    let img='';
    try{
      const response=await fetch('../../../06_交付与验证/任务处理记录原型预览/原型图/'+id+'.png');
      if(response.ok){const blob=await response.blob();const src=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});img='<img alt="'+esc(title)+'" src="'+src+'">';}
    }catch{}
    const html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+esc(title)+' · 说明修订</title><style>body{margin:0;display:flex;align-items:flex-start;font:14px/1.8 "Microsoft YaHei",sans-serif;color:#5c543e;background:#f2f4f7}img{width:1440px;flex-shrink:0}aside{width:400px;box-sizing:border-box;padding:28px;background:#fffbe6;flex-shrink:0;min-height:960px}h1{font-size:20px}h3{font-size:15px;margin:18px 0 5px}p{margin:0 0 8px}small{color:#8e805c}</style>'+img+'<aside><h1>'+esc(title)+'</h1><small>需求说明浏览器修订稿 · 未自动更新项目主本</small>'+format(text)+'</aside></html>';
    const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=id+'-任务处理记录-说明修订.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);$('#noteStatus').textContent=img?'已下载图文HTML；需要采纳的修改请同步需求主本。':'已下载说明HTML；未能读取原型图，导出仅含正文。';
  };
  window.addEventListener('message',e=>{if(e.source!==frame.contentWindow||e.data?.type!=='tr-state')return;if(location.origin!=='null'&&e.origin!==location.origin)return;if(e.data.state!==active)showNotes(e.data.state);updateActions();});
  frame.addEventListener('load',updateActions);
  navigate(active);
})();
