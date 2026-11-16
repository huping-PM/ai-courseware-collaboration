(()=>{
  const $=selector=>document.querySelector(selector);
  const rows=[
    {id:1,name:'9f2886221fce194...jpg',size:'391.4 KB',format:'jpg',source:'百度图片',owner:'谢浪',time:'2025-09-18',dimensions:'1200×800',category:'默认分类',thumb:'landscape'},
    {id:2,name:'example.png',size:'8.79 KB',format:'png',source:'--',owner:'谢林清',time:'2025-09-17',dimensions:'200×200',category:'默认分类',thumb:'smile'},
    {id:3,name:'微信图片_20250...png',size:'620.9 KB',format:'png',source:'网络',owner:'刘鸣',time:'2025-09-16',dimensions:'690×690',category:'默认分类',thumb:'portrait'}
  ];
  const state={module:'图片资源',category:'默认分类',keyword:'',status:'全部',selected:new Set(),view:'list'};
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const imageSvg={
    landscape:'<svg class="thumb" viewBox="0 0 46 42" aria-hidden="true"><defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#c4e6f8"/><stop offset="1" stop-color="#e7f5e9"/></linearGradient></defs><rect width="46" height="42" fill="url(#sky)"/><path d="M0 30 11 18l9 7 9-16 17 20v13H0Z" fill="#4e9272"/><path d="M0 33 15 25l8 7 11-8 12 9v9H0Z" fill="#315e55"/></svg>',
    smile:'<svg class="thumb" viewBox="0 0 46 42" aria-hidden="true"><rect width="46" height="42" fill="#fff"/><circle cx="23" cy="21" r="13" fill="none" stroke="#13a6e5" stroke-width="2.5"/><circle cx="18" cy="18" r="1.2" fill="#13a6e5"/><circle cx="28" cy="18" r="1.2" fill="#13a6e5"/><path d="M17 24q6 8 12 0" fill="none" stroke="#13a6e5" stroke-width="2.3" stroke-linecap="round"/></svg>',
    portrait:'<svg class="thumb" viewBox="0 0 46 42" aria-hidden="true"><rect width="46" height="42" fill="#a7784e"/><path d="M0 0h46v15L0 33Z" fill="#cb9e62"/><circle cx="24" cy="20" r="10" fill="#cda47b"/><path d="M12 18q0-17 18-11 8 6 4 20l-7-7-6 2-6-4Z" fill="#443226"/><path d="M10 42q2-14 13-14t14 14" fill="#4b5944"/></svg>'
  };
  const toast=message=>{const node=$('#toast');node.textContent=message;node.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>node.hidden=true,2500)};
  const visible=()=>rows.filter(row=>(state.category==='全部'||row.category===state.category)&&row.name.toLowerCase().includes(state.keyword.toLowerCase())&&(state.status==='全部'||state.status==='正常'));
  function render(){
    const list=visible();
    $('#resourceRows').innerHTML=list.length?list.map(row=>`<tr data-id="${row.id}"><td class="check-cell"><input type="checkbox" data-select="${row.id}" aria-label="选择${esc(row.name)}" ${state.selected.has(row.id)?'checked':''}></td><td><div class="file-cell">${imageSvg[row.thumb]||imageSvg.landscape}<span class="file-label"><strong title="${esc(row.name)}">${esc(row.name)}</strong><small>${esc(row.dimensions)}</small></span></div></td><td title="https://...">https://...</td><td>${esc(row.size)}</td><td>${esc(row.format)}</td><td>${esc(row.source)}</td><td>${esc(row.owner)}</td><td>${esc(row.time)}</td><td>--</td><td><span class="status-pill">正常</span></td><td><div class="row-actions"><button type="button" data-action="download" data-id="${row.id}">下载</button><button type="button" data-action="edit" data-id="${row.id}">编辑</button><button type="button" data-action="move" data-id="${row.id}">移动</button><button class="delete" type="button" data-action="delete" data-id="${row.id}">删除</button><button class="preview" type="button" data-action="preview" data-id="${row.id}">预览</button></div></td></tr>`).join(''):'<tr class="empty-row"><td colspan="11">暂无符合条件的图片资源</td></tr>';
    $('#totalCount').textContent=`共 ${list.length} 条`;
    $('#selectionCount').textContent=state.selected.size?`已选 ${state.selected.size} 项`:'';
    $('#selectAll').checked=list.length>0&&list.every(row=>state.selected.has(row.id));
    $('#selectAll').indeterminate=list.some(row=>state.selected.has(row.id))&&!$('#selectAll').checked;
    for(const category of document.querySelectorAll('.category'))category.classList.toggle('active',category.dataset.category===state.category);
  }
  function setModule(module){
    state.module=module;
    for(const item of document.querySelectorAll('.side-item')){const active=item.dataset.module===module;item.classList.toggle('active',active);if(active)item.setAttribute('aria-current','page');else item.removeAttribute('aria-current')}
    $('#breadcrumbModule').textContent=module;$('#breadcrumbPage').textContent=module;$('#tabTitle').textContent=module;
    $('#imageWorkspace').hidden=module!=='图片资源';$('#otherModule').hidden=module==='图片资源';$('#otherTitle').textContent=module;
    document.title=`${module} · 内部数据资产管理系统`;
  }
  const workbench=new URL('../../06_交付与验证/AI协作工作台UI风格方案/交互Demo.html',location.href);
  workbench.searchParams.set('project',new URLSearchParams(location.search).get('project')||'a');
  workbench.searchParams.set('from',location.href);
  $('#aiEntry').href=workbench.href;
  document.querySelectorAll('.side-item').forEach(item=>item.addEventListener('click',()=>setModule(item.dataset.module)));
  $('#collapseNav').onclick=()=>{document.body.classList.toggle('collapsed');$('#collapseNav').setAttribute('aria-label',document.body.classList.contains('collapsed')?'展开导航':'收起导航')};
  $('#closeTab').onclick=()=>setModule('图片资源');
  $('#categoryList').onclick=event=>{const item=event.target.closest('.category');if(!item)return;state.category=item.dataset.category;render()};
  $('#categorySearch').oninput=event=>{const q=event.target.value.trim();for(const item of document.querySelectorAll('.category'))item.hidden=!item.dataset.category.includes(q)};
  $('#addCategory').onclick=()=>{const name=prompt('请输入分类名称');if(!name?.trim())return;const value=name.trim();if([...document.querySelectorAll('.category')].some(node=>node.dataset.category===value)){toast('分类已存在');return}const button=document.createElement('button');button.type='button';button.className='category';button.dataset.category=value;button.textContent=value+'(0)';$('#categoryList').append(button);state.category=value;render()};
  $('#searchButton').onclick=()=>{state.keyword=$('#fileSearch').value.trim();state.status=$('#statusFilter').value;render()};
  $('#fileSearch').onkeydown=event=>{if(event.key==='Enter')$('#searchButton').click()};
  $('#resetButton').onclick=()=>{$('#fileSearch').value='';$('#statusFilter').value='全部';state.keyword='';state.status='全部';render()};
  $('#selectAll').onchange=event=>{for(const row of visible())event.target.checked?state.selected.add(row.id):state.selected.delete(row.id);render()};
  $('#resourceRows').onchange=event=>{const id=Number(event.target.dataset.select);if(!id)return;event.target.checked?state.selected.add(id):state.selected.delete(id);render()};
  $('#resourceRows').onclick=event=>{const button=event.target.closest('[data-action]');if(!button)return;const id=Number(button.dataset.id),row=rows.find(item=>item.id===id);if(!row)return;switch(button.dataset.action){case 'preview':alert(`${row.name}\n${row.dimensions} · ${row.size}`);break;case 'edit':{const name=prompt('文件名称',row.name);if(name?.trim()){row.name=name.trim();render()}break}case 'move':{const next=prompt('移动到分类',row.category);if(next?.trim()){row.category=next.trim();state.selected.delete(id);render()}break}case 'delete':if(confirm(`确定删除“${row.name}”？`)){rows.splice(rows.indexOf(row),1);state.selected.delete(id);render()}break;case 'download':toast('文件暂不可下载');break}};
  $('#batchDeleteButton').onclick=()=>{if(!state.selected.size){toast('请先选择图片');return}if(!confirm(`确定删除选中的 ${state.selected.size} 项？`))return;for(let index=rows.length-1;index>=0;index--)if(state.selected.has(rows[index].id))rows.splice(index,1);state.selected.clear();render()};
  $('#batchMoveButton').onclick=()=>{if(!state.selected.size){toast('请先选择图片');return}const category=prompt('移动到分类');if(!category?.trim())return;for(const row of rows)if(state.selected.has(row.id))row.category=category.trim();state.selected.clear();render()};
  $('#batchImportButton').onclick=()=>$('#filePicker').click();
  $('#uploadButton').onclick=()=>$('#filePicker').click();
  $('#filePicker').onchange=event=>{let count=0;for(const file of event.target.files){if(!file.type.startsWith('image/'))continue;rows.unshift({id:Date.now()+count,name:file.name,size:`${(file.size/1024).toFixed(1)} KB`,format:file.name.split('.').pop()?.toLowerCase()||'图片',source:'本地上传',owner:'胡平',time:new Date().toISOString().slice(0,10),dimensions:'--',category:state.category==='全部'?'默认分类':state.category,thumb:'landscape'});count++}render();toast(count?`已添加 ${count} 张图片`:'请选择图片文件');event.target.value=''};
  $('#listView').onclick=()=>toast('已切换到列表视图');
  $('.notification').onclick=()=>toast('暂无新通知');
  $('.account').onclick=()=>toast('当前用户：胡平');
  render();
})();
