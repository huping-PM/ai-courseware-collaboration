const fs=require('fs'),path=require('path');
const root=__dirname,states=[];
function add(module,key,name,code,note,query=''){states.push({module,id:module+'-'+key,name,code,note,query});}
const tree=`const names=['全部资源','未分类','培训素材','安全培训','岗前培训','防护用品','安全帽','品牌素材'];const depths=[0,0,1,2,3,4,5,1];$('#categories').innerHTML=names.map((n,i)=>'<div class="cat '+(i===0?'active':'')+'" style="padding-left:'+(8+Math.max(0,depths[i]-1)*18)+'px">'+(i>=2&&i<=5?'<svg width="12" height="12" viewBox="0 0 16 16"><path d="m4 6 4 4 4-4" fill="none" stroke="#909399"/></svg>':icon('folder'))+'<span>'+n+'</span>'+(depths[i]===5?'<span class="muted" style="margin-left:auto;font-size:12px">5级</span>':'')+'</div>').join('');`;
const resourceNote='1. 资源类型与查询\na. 图片、文档、音频、视频按当前项目隔离；切换类型清空查询和勾选。\nb. 名称与格式共同筛选，查询回到第1页；重置保留当前类型及分类。\n2. 分类与资源列表\na. 自建分类最多5级，固定入口不计层级；选择分类后更新列表。\nb. 预览打开当前文件，编辑修改信息，更多提供删除。';
for(const [i,t,n]of [['01','image','图片资源'],['02','doc','文档资源'],['03','audio','音频资源'],['04','video','视频资源']])add('PG07',i,n,tree,resourceNote,'type='+t);
add('PG07','05','上传资源',`upload();`, '1. 上传资源\na. 项目只读，分类默认当前分类；从全部进入默认未分类。\nb. 选择或拖入文件形成队列，仅合法待上传项可提交。');
add('PG07','06','上传队列与格式校验',`upload();queue=[{name:'培训场景.png',size:'1.2MB',status:'待上传'},{name:'课程封面.jpg',size:'980KB',status:'待上传'},{name:'课程资料.pdf',size:'2MB',status:'文件格式与当前资源类型不匹配',bad:true}];dirty=true;renderQueue();`,'1. 文件队列\na. 各文件独立显示名称、大小及校验结果，错误项可移除。\nb. 不合法项不妨碍其他合法项提交。');
add('PG07','07','上传中',`upload();queue=[{name:'培训场景.png',size:'1.2MB',status:'上传中'},{name:'课程封面.jpg',size:'980KB',status:'上传中'}];busy=true;renderQueue();$('#uploadCat').disabled=true;`,'1. 上传中\na. 显示处理状态并禁止重复上传，关闭操作受保护。\nb. 无真实进度依据时不显示百分比。');
add('PG07','08','上传部分失败',`prototype.uploadFailure();`,'1. 上传结果\na. 成功文件进入资源列表，失败项保留原因、重试及移除入口。\nb. 重试只处理失败项，已成功文件不重复上传。');
add('PG07','09','放弃上传保护',`prototype.uploadFailure();close();`,'1. 关闭上传\na. 存在未处理或失败文件时确认是否放弃。\nb. 继续编辑保留队列；放弃后未成功文件不入库。');
add('PG07','10','编辑资源',`edit(data[type][0]);`,'1. 编辑资源\na. 名称必填1—100字，扩展名只读，说明最多200字。\nb. 保存仅修改名称、分类及说明，不替换原文件；取消不保存。');
add('PG07','11','编辑校验失败',`edit(data[type][0]);$('#editName').value='';$('#nameError').textContent='请输入资源名称';`,'1. 名称校验\na. 名称为空阻止保存并定位名称字段。\nb. 保留分类与说明，修正后可重新保存。');
add('PG07','12','五级分类展开',tree,'1. 分类树\na. 顶级自建分类为第1级，最多5级；支持展开与收起。\nb. 第1—4级可新增子分类，第5级不提供新增子分类入口。');
add('PG07','13','新增顶级分类',`categoryForm();`,'1. 新增分类\na. 分类栏加号新增顶级分类，名称必填1—10字，同类型不得重名。\nb. 成功后选中新分类；取消不改变分类。');
add('PG07','14','新增子分类',`categoryForm();$('#modalTitle').textContent='新增子分类';$('#modalBody').insertAdjacentHTML('afterbegin',field('所属父分类','<input readonly value="培训素材 / 安全培训 / 岗前培训">'));`,'1. 新增子分类\na. 从第1—4级分类进入，弹窗只读展示父分类路径。\nb. 保存成功展开所在路径并选中新分类；失败保留输入。');
add('PG07','15','分类超过五级拦截',`categoryForm();$('#modalTitle').textContent='新增子分类';$('#modalBody').insertAdjacentHTML('afterbegin',field('所属父分类','<input readonly value="培训素材 / 安全培训 / 岗前培训 / 防护用品 / 安全帽">'));$('#categoryName').value='佩戴示范';$('#catError').textContent='分类最多支持5级';`,'1. 分类层级校验\na. 第5级隐藏新增入口，提交仍需校验层级。\nb. 层级超过5级阻止保存，提示“分类最多支持5级”，保留输入。');
add('PG07','16','重命名分类',`categoryForm('培训素材');`,'1. 重命名分类\na. 回填原名称，必填1—10字，同类型不得重名。\nb. 保存保留原层级关系，取消不修改。');
add('PG07','17','分类删除保护',`open('删除分类','<p>确定删除分类“培训素材”？</p><div class="notice">该分类存在子分类或资源，请先处理下级分类及资源。</div>',cancel+'<button class="danger" disabled>删除</button>',500);`,'1. 删除分类\na. 有子分类或资源时阻止删除，并说明处理方式。\nb. 仅无子分类且无资源的自建分类可在确认后删除，成功返回全部资源。');
add('PG07','18','资源删除确认',`removeResource(data[type][0]);`,'1. 删除资源\na. 确认框显示具体资源名，取消保持原记录。\nb. 确认后先核对引用状态，删除失败保留资源。');
add('PG07','19','资源删除引用保护',`prototype.deleteBlocked();`,'1. 引用保护\na. 被引用或无法核实引用状态时阻止删除。\nb. 保留资源，不将引用查询失败视为未引用。');
for(const [i,t,n]of [['20','image','图片预览'],['21','doc','文档预览'],['23','audio','音频预览'],['24','video','视频预览']])add('PG07',i,n,`preview(data[type][0]);`,'1. '+n+'\na. 展示当前所选文件，名称与内容对应。\nb. 图片可缩放，文档只读；音视频可播放、暂停，关闭预览停止播放。','type='+t);
add('PG07','22','不支持在线预览',`preview(data.doc.find(r=>r.format==='DOCX'));`,'1. 文档预览边界\na. 不支持的格式显示明确提示，不以其他文件冒充。\nb. 关闭后返回原列表。','type=doc');
for(const [i,n,sc]of [['25','查询无结果','query'],['26','暂无资源','empty'],['27','列表加载中','loading'],['28','列表加载失败','error'],['29','只读资源列表','readonly']])add('PG07',i,n,sc==='query'?`keyword='不存在的资料';$('#keyword').value=keyword;render();`:sc==='readonly'?`readonly=true;render();`:`scene='${sc}';render();`,'1. '+n+'\na. '+({query:'保留查询条件并展示无匹配提示，重置后可重新查询。',empty:'展示当前类型暂无资源，有维护权限时可上传。',loading:'保留页面结构，加载完成后展示实际数据。',error:'提供重试，不把加载失败显示为空数据。',readonly:'保留查看入口，隐藏上传、编辑、分类维护及删除等写操作。'}[sc]));
const configNote='1. 查询与列表\na. 按名称和状态组合查询，重置返回第1页；配置按项目隔离。\nb. 智能体配置通过左侧菜单展开技能管理和提示词管理。';
add('SKILL','01','技能列表','',configNote);
add('SKILL','02','新增技能',`form();`,'1. 新增技能\na. 技能文件为第一项，必填；选择UTF-8的SKILL.md。\nb. 读取name和description自动填入名称、描述，允许修改后提交。');
add('SKILL','03','文件读取后自动填充',`form();fileText=skillSource('training_outline','提炼培训资料中的关键知识点');fileName='SKILL.md';$('#fileName').textContent=fileName;fillSkillMetadata(parseSkillMetadata(fileText));`,'1. 文件自动填充\na. 自动读取文件元信息填入名称与描述。\nb. 名称必填1—50字，描述必填1—200字，正文最多10000字；自动填入后可编辑。');
add('SKILL','04','文件校验失败',`form();$('#fileError').textContent='缺少有效的 description 字段，请检查 SKILL.md。';`,'1. 文件校验\na. 文件名、编码或元信息不符合规则时显示原因。\nb. 保留可修正内容，重新选择有效文件后可提交。');
add('SKILL','05','技能解析中',`skills[0].status='parsing';render();`,'1. 解析中\na. 提交后显示解析中，防止重复提交。\nb. 解析期间禁止编辑、启停及删除，完成后更新为启用或解析失败。');
add('SKILL','06','技能详情',`detail(skills[0]);`,'1. 技能详情\na. 抽屉展示名称、状态、描述、更新信息及完整文件正文。\nb. 关闭不修改数据，解析中隐藏编辑入口。');
add('SKILL','07','编辑技能',`form(skills[0]);`,'1. 编辑技能\na. 文件置顶，不替换时保留原文件；替换后重新读取元信息。\nb. 读取未结束不能提交，避免保存上一个文件的信息。');
add('SKILL','08','未保存关闭保护',`form(skills[0]);dirty=true;close();`,'1. 关闭保护\na. 表单有修改时确认是否放弃。\nb. 取消放弃继续编辑；确认放弃不保存。');
add('SKILL','09','停用确认',`toggle(skills[0]);`,'1. 停用技能\na. 确认对象及影响后停用，取消保持启用。\nb. 停用不改变历史成果。');
add('SKILL','10','启用确认',`toggle(skills[3]);`,'1. 启用技能\na. 确认后启用，成功更新列表；取消保持停用。');
add('SKILL','11','删除引用保护',`prototype.blocked();`,'1. 删除技能\na. 引用中或解析中阻止删除，并保留记录。\nb. 停用不等于可以删除，仍需核验引用。');
add('SKILL','12','解析失败',`prototype.parseFailure();detail(skills[3]);`,'1. 解析失败\na. 展示失败原因和文件正文，失败技能不能用于新生成。\nb. 重新提交进入编辑，修正文件后再次解析。');
for(const [i,n,sc]of [['13','技能查询无结果','query'],['14','暂无技能','empty'],['15','技能加载中','loading'],['16','技能加载失败','error'],['17','技能只读','readonly']])add('SKILL',i,n,sc==='query'?`kw='不存在';$('#keyword').value=kw;render();`:sc==='readonly'?`readOnly=true;render();`:`scene='${sc}';render();`,'1. '+n+'\na. '+(sc==='readonly'?'隐藏新增、编辑、启停和删除等维护操作，保留查看。':sc==='error'?'加载失败提供重试，不显示为空数据。':sc==='loading'?'保留表头与查询区，完成后显示实际数据。':sc==='query'?'保留筛选条件，重置后恢复查询。':'展示无数据提示，有维护权限时可以新增。'));
add('SKILL','18','提交失败保留表单',`form(skills[0]);$('#formError').textContent='保存失败，请重试';`,'1. 提交失败\na. 保留文件、名称和描述，明确提示原因。\nb. 修正或重试后再次提交，不显示虚假成功。');
add('PROMPT','01','提示词列表','',configNote+'\n2. 提示词状态\na. 草稿未发布版本显示“—”，已发布展示当前版本。','tab=prompt');
const pAdd=(i,n,c,note)=>add('PROMPT',i,n,c,note,'tab=prompt');
pAdd('02','新增提示词',`form();`,'1. 新增提示词\na. 维护名称、类型、正文；名称必填1—50字，类型必选，正文必填且最多10000字。\nb. 可保存草稿或发布，取消不保存。');
pAdd('03','编辑草稿',`form(prompts[2]);`,'1. 编辑草稿\na. 回填已保存内容，可继续保存草稿或发布。\nb. 保存草稿不产生发布版本。');
pAdd('04','编辑已发布提示词',`form(prompts[0]);`,'1. 编辑已发布提示词\na. 修改后通过发布新版本生效，不覆盖历史版本快照。\nb. 取消保持原发布内容。');
pAdd('05','发布确认',`form(prompts[0]);publish();`,'1. 发布确认\na. 表单校验后打开确认框，更新备注必填，最多200字。\nb. 取消确认回到编辑表单并保留内容。');
pAdd('06','发布失败',`form(prompts[0]);publish();$('#note').value='补充内容边界说明';$('#publishError').textContent='发布失败，请重试';`,'1. 发布失败\na. 保留表单与更新备注，允许继续修正或重试。\nb. 失败不创建新版本。');
pAdd('07','提示词详情',`detail(prompts[0]);`,'1. 提示词详情\na. 只读展示名称、状态、更新信息及正文。\nb. 有发布记录时可进入版本记录，有维护权限可编辑。');
pAdd('08','当前版本记录',`versions(prompts[0]);`,'1. 版本记录\na. 默认展示最新发布版本，左侧选择版本，右侧展示对应快照。\nb. 包括发布人、时间、更新备注及完整正文，历史内容只读。');
pAdd('09','历史版本查看',`versions(prompts[0]);document.querySelector('[data-version="1"]').click();`,'1. 历史版本\na. 选择旧版本后展示该版本原始正文与发布信息，标记已归档。\nb. 不套用当前正文，不修改或回滚历史。');
pAdd('10','关闭编辑保护',`form(prompts[0]);dirty=true;close();`,'1. 关闭保护\na. 有修改时先确认是否放弃；取消确认保留编辑内容。\nb. 确认放弃不发布新版本。');
pAdd('11','删除引用保护',`prototype.blocked();`,'1. 删除提示词\na. 删除前展示对象，引用中阻止删除。\nb. 取消或失败保留记录。');
for(const [i,n,sc]of [['12','提示词查询无结果','query'],['13','暂无提示词','empty'],['14','提示词加载中','loading'],['15','提示词加载失败','error'],['16','提示词只读','readonly']])pAdd(i,n,sc==='query'?`kw='不存在';$('#keyword').value=kw;render();`:sc==='readonly'?`readOnly=true;render();`:`scene='${sc}';render();`,'1. '+n+'\na. '+(sc==='readonly'?'隐藏新增、编辑、发布和删除，保留详情及版本查看。':sc==='error'?'加载失败提供重试，保留当前查询条件。':sc==='loading'?'保留页面结构，不将加载中视为无数据。':sc==='query'?'保留筛选条件，重置后重新查询。':'当前项目暂无提示词，有维护权限时可新增。'));
// Each route is an explicit visual fixture; production HTML remains in 04_原型与说明.
for(const module of ['PG07','SKILL','PROMPT']){
 const dir=module==='PG07'?'PG07-资源管理':'PG13-智能体配置';
 const file=module==='PG07'?'资源管理原型.html':'智能体配置原型.html';
 for(const s of states.filter(s=>s.module===module)){
  let html=fs.readFileSync(path.join(root,'source',dir,file),'utf8');
  html=html.replace(/<script src="generated-resources.js"><\/script>/g,'');
  html=html.replace('</body>',`<script>${s.code.replace(/<\/script/g,'<\\/script')}</script></body>`);
  fs.writeFileSync(path.join(root,'source',dir,s.id+'.html'),html);
  s.url='source/'+dir+'/'+s.id+'.html'+(s.query?'?'+s.query:'');
 }
}
fs.writeFileSync(path.join(root,'状态清单.json'),JSON.stringify(states,null,2));
for(let start=0;start<states.length;start+=8){const batch=states.slice(start,start+8),n=String(start/8+1).padStart(2,'0');fs.writeFileSync(path.join(root,'batch-'+n+'.html'),`<!doctype html><meta charset="utf-8"><title>状态设计 ${n}</title><style>body{margin:0;background:#edf0f5}section{width:1920px;height:1080px;margin-bottom:100px}iframe{border:0;width:1920px;height:1080px}</style><script src="freeze.js"></script>`+batch.map(s=>`<section id="${s.id}" data-name="${s.id} ${s.name}"><iframe src="${s.url}" onload="freezeFrame(this,this.parentElement)"></iframe></section>`).join('')+'<script src="https://mcp.figma.com/mcp/html-to-design/capture.js" async></script>');}
console.log(JSON.stringify({states:states.length,batches:Math.ceil(states.length/8)}));
