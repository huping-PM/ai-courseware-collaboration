(()=>{
const P=Platform,global=P.q.get('scope')==='global',projectId=P.projectId,selectionKey='platform-project-skills:'+projectId;
let enabled=P.read(selectionKey,[]);const globalKey='platform-global-skills-v1',baseRender=render,baseDetail=detail,baseTab=setTab;
if(global){
 document.title='全局技能管理 · 内容协作系统';document.querySelector('.sidebar .project')?.remove();document.querySelector('.sidebar nav').innerHTML=`<div style="height:56px;display:flex;align-items:center;padding:0 24px;gap:12px">${P.svg('settings')}系统管理</div>`+[['accounts','账号管理','user'],['roles','角色管理','user'],['navigation','导航管理','list'],['collections','资源集管理','folder']].map(([id,n,i])=>`<button class="nav" data-system-route="${id}" style="padding-left:44px;height:50px">${P.svg(i)}${n}</button>`).join('')+`<button class="nav active" aria-current="page" style="padding-left:44px;height:50px">${P.svg('skill')}技能管理</button>`;
 document.querySelectorAll('[data-system-route]').forEach(b=>b.onclick=()=>P.go(P.systemPath,{tab:b.dataset.systemRoute}));document.querySelector('.side-bottom').innerHTML=`<button class="nav" id="returnGlobalProjects">${P.svg('back')}返回项目列表</button>`;$('#returnGlobalProjects').onclick=()=>P.go(P.projectPath);
 const spans=[...document.querySelectorAll('.top > span:not(.crumb-sep)')];if(spans[0])spans[0].innerHTML=`<a href="${P.url(P.projectPath)}" style="color:inherit;text-decoration:none">项目管理</a>`;if(spans[1])spans[1].textContent='系统管理';
 setTab=function(){baseTab('skill');$('#listTitle').textContent='全局技能库'};setTab();

}else{
 // Project prompts remain independent; skills are globally maintained.
 const promptKey='platform-project-prompts:'+projectId,saved=P.read(promptKey,null);if(saved)prompts.splice(0,prompts.length,...saved);else if(projectId!=='a')prompts.splice(0,prompts.length);
 const renderWithSkills=render;render=function(){renderWithSkills();if(tab==='prompt')P.write(promptKey,prompts)};setTab(tab);
}
// Add project examples once, preserving existing skills and later user deletions.
if(!global){
 const exampleKey='platform-project-skill-examples-v1:'+projectId;
 if(!P.read(exampleKey,false)){
  const examples=[['岗位培训脚本编写','围绕本项目培训目标整理讲解脚本。','enabled','project_training_script'],['项目视频片尾规范','统一本项目视频片尾与署名格式。','disabled','project_video_ending']];
  for(const [name,desc,status,key] of examples){
   if(!skills.some(x=>x.exampleKey===key&&x.ownerProject===projectId))skills.push({id:id++,name,desc,status,content:skillSource(key,desc),skillType:'project',ownerProject:projectId,exampleKey:key,ref:false,file:'SKILL.md',user:'林悦',time:'2026-09-18 16:00'});
  }
  P.write(globalKey,skills);P.write(exampleKey,true);
 }
}
const scopeOf=x=>x.skillType||'global',visible=x=>scopeOf(x)==='global'||(!global&&x.ownerProject===projectId);
const canEdit=x=>!readOnly&&(scopeOf(x)==='global'?global:!global&&x.ownerProject===projectId);
const maintenanceDenied=x=>scopeOf(x)==='global'?'全局技能仅可在系统管理中维护':'项目专属技能仅可在所属项目中维护';
const previousForm=form;form=function(x=null){if(tab==='skill'&&readOnly)return toast('当前为只读状态，无法维护技能');if(tab==='skill'&&x&&!canEdit(x))return toast(maintenanceDenied(x));previousForm(x);if(tab==='skill')$('#modalBody').insertAdjacentHTML('beforeend',field('技能类型',`<input id="skillType" readonly value="${(x?scopeOf(x):global?'global':'project')==='global'?'全局技能':'项目专属'}">`))};
const previousDetail=detail;detail=function(x){const old=readOnly;if(tab==='skill'&&!canEdit(x))readOnly=true;try{previousDetail(x);if(tab==='skill')$('#modalBody').insertAdjacentHTML('afterbegin',`<p>技能类型：${scopeOf(x)==='global'?'全局技能':'项目专属'}</p>`)}finally{readOnly=old}};
for(const [name,fn] of [['remove',remove],['toggle',toggle]]){const guarded=function(x){if(tab==='skill'&&!canEdit(x))return toast(maintenanceDenied(x));return fn(x)};if(name==='remove')remove=guarded;else toggle=guarded}
const previousRender=render;render=function(){previousRender();if(tab!=='skill')return;$('#create').hidden=readOnly;$('#listTitle').textContent=global?'全局技能库':'项目技能';
 const list=(scene==='empty'?[]:skills).filter(x=>visible(x)&&(!kw||x.name.includes(kw))&&(!status||x.status===status));page=Math.min(page,Math.ceil(list.length/pageSize)||1);
 $('#heads').innerHTML='<tr><th>技能名称</th><th>技能类型</th><th>技能说明</th><th>状态</th><th>最近更新时间</th><th>操作</th></tr>';
 $('#rows').innerHTML=scene==='loading'?'<tr><td colspan="6">正在加载…</td></tr>':scene==='error'?'<tr><td colspan="6">配置加载失败 <button data-retry>重试</button></td></tr>':list.slice((page-1)*pageSize,page*pageSize).map(x=>`<tr><td>${esc(x.name)}</td><td>${scopeOf(x)==='global'?'全局技能':'项目专属'}</td><td class="desc">${esc(x.desc)}</td><td>${global?badge(x.status):`<button role="switch" class="platform-switch ${x.status==='enabled'?'on':''}" aria-label="启用${esc(x.name)}" aria-checked="${x.status==='enabled'}" data-project-skill="${x.id}" ${!canEdit(x)||!['enabled','disabled'].includes(x.status)?'disabled':''}></button> ${badge(x.status)}`}</td><td>${esc(x.time)}</td><td><div class="row-actions"><button class="link" data-act="view" data-id="${x.id}">查看</button>${canEdit(x)?`<button class="link" data-act="edit" data-id="${x.id}" ${x.status==='parsing'?'disabled':''}>编辑</button><button class="link" data-act="more" data-id="${x.id}">更多</button>`:''}</div></td></tr>`).join('')||'<tr><td colspan="6" class="empty-cell">暂无符合条件的技能</td></tr>';
 $('#count').textContent=$('#total').textContent='共 '+list.length+' 条';$('#page').textContent=page;$('#prev').disabled=page===1;$('#next').disabled=page*pageSize>=list.length;
 document.querySelectorAll('[data-project-skill]').forEach(b=>b.onclick=()=>toggle(skills.find(x=>x.id===+b.dataset.projectSkill)));
};
window.addEventListener('storage',ev=>{if(ev.key===globalKey){const latest=P.read(globalKey,[]);skills.splice(0,skills.length,...latest);id=Math.max(id,...latest.map(x=>x.id+1));window.readingGlobalSkillUpdate=true;try{render()}finally{window.readingGlobalSkillUpdate=false}}});
render();
})();
