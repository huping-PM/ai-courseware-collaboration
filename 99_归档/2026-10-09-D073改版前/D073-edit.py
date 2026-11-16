from pathlib import Path
p=Path('04_原型与说明/AI协作工作台-风格探索/app.js')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("set('revision','D072')", "set('revision','D073')")
s=s.replace('studioResourceRefs=[],stagedResourceIds=', 'studioResourceRefs=[],studioResourceCategory=null,stagedReferenceCategory=null,stagedResourceIds=')
s=s.replace('resourceRefs:[...studioResourceRefs],filter:', 'resourceRefs:[...studioResourceRefs],resourceCategory:studioResourceCategory?{...studioResourceCategory}:null,filter:')
s=s.replace('studioResourceRefs=[...(snap?.resourceRefs||[])];', 'studioResourceRefs=[...(snap?.resourceRefs||[])];studioResourceCategory=snap?.resourceCategory?{...snap.resourceCategory}:null;')
s=s.replace('resourceRefs=[...studioResourceRefs],requestModel=', 'resourceRefs=[...studioResourceRefs],resourceCategory=studioResourceCategory?{...studioResourceCategory}:null,requestModel=')
old="human?.insertAdjacentHTML('afterbegin',resourceRefs.map(id=>{const r=resources.find(x=>x.id===id);return r?`<span class=\"canvas-citation\">${icon(r.kind)}${esc(r.name)}</span>`:''}).join(''));studioResourceRefs=[];renderStudioResourceRefs()"
new="human?.insertAdjacentHTML('afterbegin',renderSentResourceReferences(resourceRefs,resourceCategory));studioResourceRefs=[];studioResourceCategory=null;renderStudioResourceRefs()"
assert old in s
s=s.replace(old,new)
start=s.index(' referenceResource=function(')
end=s.index('\n',start)
s=s[:start]+" referenceResource=function(id,stay=false){const resource=resources.find(r=>r.id===id);if(!resource)return;studioResourceCategory={type:resource.type,path:pickerCategory(resource)};studioResourceRefs=categoryResourceItems(studioResourceCategory).map(r=>r.id);if(document.querySelector('#modal').open)closeModal();renderStudioResourceRefs();toast('已引用该分类下全部文件')};"+s[end:]
start=s.index('function beautifulReferences(){');end=s.index('\nfunction filterBeautifulReferences',start)
s=s[:start]+'''function beautifulReferences(){
 stagedReferenceCategory=studioResourceCategory?{...studioResourceCategory}:null;activeReferenceType=stagedReferenceCategory?.type||'文档';stagedResourceIds=new Set(categoryResourceItems(stagedReferenceCategory).map(r=>r.id));
 referenceExpandedCategories=Object.fromEntries(referenceTypes.map(type=>[type,new Set(resourceCategoryPaths(type).filter(path=>!path.includes(' / ')))]));
 if(stagedReferenceCategory){const parts=stagedReferenceCategory.path.split(' / ');for(let i=1;i<parts.length;i++)referenceExpandedCategories[activeReferenceType].add(parts.slice(0,i).join(' / '))}
 referenceQueries=Object.fromEntries(referenceTypes.map(type=>[type,'']));
 openModal('选择资源',`<div class="bui-resource-type-tabs" id="resourceTypeTabs" role="tablist" aria-label="资源类型">${renderReferenceTypeTabs()}</div><div class="bui-resource-layout"><aside class="bui-category-pane"><div class="bui-category-heading"><strong>资源分类</strong><button class="bui-category-clear" id="clearResourceCategories" onclick="clearReferenceCategories()">清除选择</button></div><div id="resourceCategoryTree">${renderResourceCategoryTree()}</div></aside><div class="bui-resource-pane"><div class="bui-reference-search">${icon('search')}<input id="referenceSearch" aria-label="搜索资源" placeholder="搜索资源名称" oninput="filterBeautifulReferences()"></div><div class="bui-resource-result-head"><strong id="resourceResultTitle">全部分类</strong><span id="resourceResultCount"></span></div><div class="bui-search-list" id="referenceResults">${beautifulReferenceRows()}</div></div></div><div class="bui-modal-caption">${icon('folder')}选择一个分类，引用其中全部文件（含子分类）；搜索仅筛选预览。</div>`,`<span class="bui-selected-count" id="referenceSelectedCount"></span><button onclick="closeModal()">取消</button><button class="primary" id="confirmReferences" onclick="confirmResourceSelection()">确认引用</button>`);
 document.querySelector('#modal').classList.add('bui-resource-modal');updateReferenceResults()
}
function categoryResourceItems(category){return category?resources.filter(r=>r.type===category.type&&(pickerCategory(r)===category.path||pickerCategory(r).startsWith(category.path+' / '))):[]}
function beautifulReferenceRows(){const q=(document.querySelector('#referenceSearch')?.value||'').trim().toLowerCase(),all=stagedReferenceCategory?categoryResourceItems(stagedReferenceCategory):resources.filter(r=>r.type===activeReferenceType),items=all.filter(r=>r.name.toLowerCase().includes(q));return items.length?items.map(r=>`<div class="bui-search-row bui-resource-row" data-reference-id="${r.id}"><span class="bui-reference-icon">${icon(r.kind)}</span><span class="bui-search-label"><strong>${esc(r.name)}</strong><small>${esc(pickerCategory(r))} · ${esc(r.size)}</small></span></div>`).join(''):`<div class="bui-search-empty">${icon('search')}<strong>${q?'没有匹配的资源':'该分类暂无文件'}</strong><span>${q?'调整关键词可查看其他文件，分类引用范围不变':'请选择其他分类'}</span></div>`}
''' +s[end:]
s=s.replace("checked=referenceCategoryChecks[type]||new Set()", "checked=new Set(stagedReferenceCategory?.type===type?[stagedReferenceCategory.path]:[])")
s=s.replace('type="checkbox" aria-label="筛选分类${esc(cat)}"', 'type="radio" name="referenceCategory" aria-label="引用分类${esc(cat)}"')
start=s.index('function updateReferenceResults(){');end=s.index('\nfunction filterBeautifulSkills',start)
s=s[:start]+'''function updateReferenceResults(){const list=document.querySelector('#referenceResults');if(!list)return;stagedResourceIds=new Set(categoryResourceItems(stagedReferenceCategory).map(r=>r.id));list.innerHTML=beautifulReferenceRows();document.querySelector('#resourceResultTitle').textContent=stagedReferenceCategory?.path||'全部分类';document.querySelector('#resourceResultCount').textContent='显示 '+list.querySelectorAll('[data-reference-id]').length+' 项';document.querySelector('#referenceSelectedCount').textContent=stagedReferenceCategory?`将引用该分类全部 ${stagedResourceIds.size} 个文件`:'请选择一个资源分类';document.querySelector('#clearResourceCategories').disabled=!stagedReferenceCategory;document.querySelector('#confirmReferences').disabled=!stagedReferenceCategory||!stagedResourceIds.size}
function confirmResourceSelection(){const items=categoryResourceItems(stagedReferenceCategory);if(!stagedReferenceCategory||!items.length)return;studioResourceCategory={...stagedReferenceCategory};studioResourceRefs=items.map(r=>r.id);renderStudioResourceRefs();closeModal();toast(`已引用该分类全部 ${studioResourceRefs.length} 个文件`)}
function renderStudioResourceRefs(){const el=document.querySelector('#referenceSelected');if(!el)return;if(!studioResourceRefs.length){el.innerHTML='';return}const label=studioResourceCategory?`${studioResourceCategory.type} · ${studioResourceCategory.path}`:'历史文件引用';el.innerHTML=`<span class="bui-reference-chip bui-category-reference">${icon('folder')}<span title="${esc(label)}">${esc(label)} · ${studioResourceRefs.length} 个文件</span><button aria-label="移除全部资源引用" onclick="removeStudioResourceRef()">${icon('x')}</button></span>`}
function removeStudioResourceRef(){studioResourceRefs=[];studioResourceCategory=null;renderStudioResourceRefs()}
function renderSentResourceReferences(ids,category){const label=category?`${category.type} · ${category.path}`:'历史文件引用';return `<details class="bui-sent-resource-group"><summary>${icon('folder')}<span>${esc(label)} · ${ids.length} 个文件</span>${icon('chevron')}</summary><div>${ids.map(id=>{const r=resources.find(x=>x.id===id);return r?`<span class="canvas-citation">${icon(r.kind)}${esc(r.name)}</span>`:''}).join('')}</div></details>`}
''' +s[end:]
s=s.replace('activeReferenceType=type;document.querySelector', 'activeReferenceType=type;stagedReferenceCategory=null;stagedResourceIds.clear();document.querySelector')
start=s.index('function toggleResourceCategoryChecked(cat,checked){')
s=s[:start]+'''function toggleResourceCategoryChecked(cat,checked){if(!checked)return;stagedReferenceCategory={type:activeReferenceType,path:cat};document.querySelector('#resourceCategoryTree').innerHTML=renderResourceCategoryTree();updateReferenceResults()}
function clearReferenceCategories(){stagedReferenceCategory=null;document.querySelector('#resourceCategoryTree').innerHTML=renderResourceCategoryTree();updateReferenceResults()}
'''
p.write_text(s,encoding='utf-8')
for name in ['04_原型与说明/AI协作工作台-风格探索/index.html','06_交付与验证/AI协作工作台UI风格方案/交互Demo.html']:
 p=Path(name);p.write_text(p.read_text(encoding='utf-8-sig').replace('revision=D072','revision=D073'),encoding='utf-8')
p=Path('04_原型与说明/AI协作工作台-风格探索/beautiful-ui.css')
s=p.read_text(encoding='utf-8-sig')+'''
/* D073: one category, all files; result rows are preview only. */
.style-b .bui-resource-row{cursor:default}
.style-b .bui-tree-label:has(input:checked){background:var(--inset);color:var(--ink)!important;font-weight:600!important}
.style-b .bui-resource-result-head{gap:12px;align-items:flex-start}
.style-b .bui-resource-result-head strong{min-width:0;overflow-wrap:anywhere;line-height:1.5}
.style-b .bui-resource-result-head>span{white-space:nowrap;padding-top:2px}
.style-b .bui-category-reference{max-width:100%}
.style-b .bui-category-reference>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.style-b .bui-sent-resource-group{margin-bottom:9px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--inset);font-size:11px}
.style-b .bui-sent-resource-group summary{display:flex;align-items:center;gap:6px;cursor:pointer;list-style:none}
.style-b .bui-sent-resource-group summary>span{flex:1;min-width:0;overflow-wrap:anywhere}
.style-b .bui-sent-resource-group svg{width:14px;height:14px;flex-shrink:0}
.style-b .bui-sent-resource-group[open] summary>svg:last-child{transform:rotate(90deg)}
.style-b .bui-sent-resource-group>div{display:flex;flex-direction:column;gap:4px;margin-top:8px}
'''
p.write_text(s,encoding='utf-8')
