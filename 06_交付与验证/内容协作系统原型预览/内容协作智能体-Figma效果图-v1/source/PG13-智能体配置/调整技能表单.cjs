const fs=require('fs'),p=__dirname+'/config.js';let s=fs.readFileSync(p,'utf8');
s=s.replace("['关联智能体',170],",'').replace('<td><span class="agent">${x.agent}</span></td>','');
s=s.replace("+field('关联智能体','<input disabled value=\"内容协作智能体\">',true)",'');
s=s.replace('<dt>关联智能体</dt><dd>${x.agent}</dd>',"${tab==='prompt'?`<dt>关联智能体</dt><dd>${x.agent}</dd>`:''}");
s=s.replace('<button class="primary" id="use" ${![\'enabled\',\'published\'].includes(x.status)?\'disabled\':\'\'}>用于对话</button>',"${tab==='prompt'?`<button class=\"primary\" id=\"use\" ${x.status!=='published'?'disabled':''}>用于对话</button>`:''}");
s=s.replace("$('#use').onclick=()=>handoff(x)","$('#use')?.addEventListener('click',()=>handoff(x))");s=s.replace("if(['enabled','published'].includes(x.status))items.push", "if(tab==='prompt'&&x.status==='published')items.push");s=s.replace('function handoff(x){','function handoff(x){if(tab!==\'prompt\')return;');
s=s.replace("if(tab==='skill'){$('#pickFile').onclick", "if(tab==='skill'){const f=$('#skillFile').closest('.field');$('#modalBody').prepend(f);$('#formName').placeholder='选择技能文件后自动读取';$('#formDesc').placeholder='选择技能文件后自动读取';if(x){try{const meta=parseSkillMetadata(x.content);fillSkillMetadata(meta)}catch{}}$('#pickFile').onclick");
s=s.replace("const token=formToken;fileText=null;fileName='';pendingReads++;", "const token=++formToken;fileText='';fileName='';$('#formName').value='';$('#formDesc').value='';pendingReads=1;");
s=s.replace("fileText=text;fileName=f.name;", "const meta=parseSkillMetadata(text);fileText=text;fileName=f.name;fillSkillMetadata(meta);");
s=s.replace("pendingReads--;if(token===formToken)$('#save').disabled=false", "if(token===formToken){pendingReads=0;$('#save').disabled=false}");
s=s.replace("if(!v.name)e='请输入名称';", "if(tab==='skill'&&!v.content)e='请上传有效的 SKILL.md 文件';else if(!v.name)e='请输入名称';");
s=s.replace("{id:id++,projectId:'PRJ-DEMO-001',agent:'内容协作智能体',ref:false}","{id:id++,projectId:'PRJ-DEMO-001',ref:false}");
s+=String.raw`
function parseSkillMetadata(text){
 const match=text.replace(/^\uFEFF/,'').match(/^---\s*\r?\n([\s\S]*?)\r?\n---(?:\s*\r?\n|\s*$)/);
 if(!match)throw Error('文件需包含 YAML 元信息区（---），以及 name、description 字段。');
 const lines=match[1].split(/\r?\n/),result={};
 for(let i=0;i<lines.length;i++){
  const m=lines[i].match(/^(name|description):\s*(.*)$/);if(!m)continue;
  if(result[m[1]]!==undefined)throw Error('元信息字段重复：'+m[1]);
  let value=m[2].trim();
  if(/^[|>][-+]?$/.test(value)){const folded=value[0]==='>',chunks=[];while(i+1<lines.length&&(/^[ \t]+/.test(lines[i+1])||!lines[i+1].trim()))chunks.push(lines[++i].trim());value=chunks.join(folded?' ':'\n').trim()}
  else if(value.startsWith('"')){try{value=JSON.parse(value)}catch{throw Error('字段引号格式错误：'+m[1])}}
  else if(value.startsWith("'")){if(!value.endsWith("'"))throw Error('字段引号格式错误：'+m[1]);value=value.slice(1,-1).replace(/''/g,"'")}
  else value=value.replace(/\s+#.*$/,'').trim();
  result[m[1]]=value;
 }
 if(!result.name||!result.description)throw Error('未读取到有效的 name（技能名称）或 description（技能描述）。');
 if(result.name.length>50||result.description.length>200)throw Error('技能名称不能超过50字，技能描述不能超过200字，请调整文件后重新选择。');
 return result;
}
function fillSkillMetadata(meta){$('#formName').value=meta.name;$('#formDesc').value=meta.description;$('#nameCount').textContent=meta.name.length+'/50';$('#descCount').textContent=meta.description.length+'/200'}
`;
fs.writeFileSync(p,s);
