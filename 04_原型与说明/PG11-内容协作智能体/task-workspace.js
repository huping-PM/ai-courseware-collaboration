(()=>{
if(scene==='denied')return;
if(decodeURIComponent(location.pathname).includes('内容协作智能体原型')&&!params.get('session')){current=blank();store.s.push(current);selected=null;}
labels.local='本地文件';
const statusOf=s=>s.busy?'running':s.awaiting?'waiting':s.messages.filter(m=>m.role==='agent').at(-1)?.failure?'failed':s.artifacts.length?'done':s.messages.length?'waiting':'draft';
const statusNames={running:'执行中',waiting:'待确认',done:'已完成',failed:'执行失败',draft:'草稿'};
const statusPath={running:'M20 12a8 8 0 1 1-4-7M20 4v5h-5',waiting:'M12 8v5m0 4v.1M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18',done:'m7 12 3 3 7-7M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18',failed:'m9 9 6 6m0-6-6 6M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18',draft:'M5 4h14v16H5ZM8 8h8M8 12h6'};
function stateIcon(s){return `<svg class="task-status-icon ${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${statusPath[s]}"/></svg>`}
$('#sessionList').remove();const list=document.createElement('aside');list.className='task-rail';list.innerHTML=`<header><strong>会话任务</strong><button class="icon-button" id="taskNew" aria-label="新建任务" title="新建任务">${icon('plus')}</button></header><div class="task-search"><input id="taskSearch" placeholder="搜索会话任务" aria-label="搜索会话任务"></div><div class="task-filters"><button class="active" data-task-filter="all">全部</button><button data-task-filter="running">执行中</button><button data-task-filter="done">已完成</button></div><div id="sessionList" class="task-list"></div><footer id="taskSummary" aria-live="polite"></footer>`;$('#workbench').prepend(list);
let filter='all',query='';
function renderTasks(){const items=store.s.filter(s=>s.project===project&&(s.messages.length||s.draft||s.refs.length||s===current));const match=items.filter(s=>(filter==='all'||statusOf(s)===filter)&&s.title.toLowerCase().includes(query));$('#sessionList').innerHTML=match.length?match.slice().reverse().map(s=>{const status=statusOf(s);return `<button class="task-row ${s===current?'active':''}" data-task-id="${s.id}" aria-current="${s===current}" aria-label="${esc(s.title)} · ${statusNames[status]}" title="${esc(s.title)} · ${statusNames[status]}"><span class="task-name">${esc(s.title)}</span><span class="task-state-icon" title="${statusNames[status]}" aria-label="${statusNames[status]}">${stateIcon(status)}</span></button>`}).join(''):'<div class="task-empty">未找到匹配的任务</div>';$('#taskSummary').textContent=items.filter(s=>s.busy).length+' 个任务执行中';}
const beforeRender=render;render=function(){beforeRender();$('#workbench').classList.toggle('task-initial',!current.artifacts.length);$('#chatTitle').textContent=current.messages.length?current.title:'新建任务';renderTasks()};
const beforePersist=persist;persist=function(){beforePersist();renderTasks()};
$('#historyChat').onclick=null;$('#historyChat').removeAttribute('aria-haspopup');$('#historyChat').removeAttribute('aria-expanded');$('#historyChat').setAttribute('aria-label','当前会话任务');$('#historyChat').classList.add('plain-session-title');$('#historyChat').title='当前会话任务';$('#sessionDropdown').hidden=true;
function createTask(){const previous=current;persist();const s=blank();if(!previous.messages.length&&!previous.draft&&!previous.refs.length){setCurrent(previous);return}store.s.push(s);setCurrent(s)}
$('#taskNew').onclick=$('#newChat').onclick=createTask;
$('#sessionList').onclick=e=>{const b=e.target.closest('[data-task-id]');if(!b)return;const s=store.s.find(s=>s.id===b.dataset.taskId&&s.project===project);if(s&&s!==current){persist();setCurrent(s)}};
$('#taskSearch').oninput=e=>{query=e.target.value.trim().toLowerCase();renderTasks()};$$('[data-task-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.taskFilter;$$('[data-task-filter]').forEach(x=>x.classList.toggle('active',x===b));renderTasks()});
const previousValid=validRefs;validRefs=function(refs){return refs.filter(r=>r.kind==='local').every(r=>r.status==='ready'&&!invalid.has(r.id))&&previousValid(refs.filter(r=>r.kind!=='local'))};
const previousSend=send;send=function(approve=false){if(current.refs.some(r=>r.kind==='local'&&r.status!=='ready')){$('#inputError').textContent='请先完成本地文件上传确认，或移除未成功文件。';return}previousSend(approve)};
window.taskPrototype={statusOf,renderTasks};
render();for(const s of store.s.filter(s=>s.busy&&s.lastRequest))process(s,s.lastRequest,s.resumeApprove,s.resumeRetry);
})();
