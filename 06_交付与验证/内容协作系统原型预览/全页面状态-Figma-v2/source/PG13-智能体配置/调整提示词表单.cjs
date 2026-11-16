const fs=require('fs'),p=__dirname+'/config.js';let s=fs.readFileSync(p,'utf8');
s=s.replace("+field(tab==='skill'?'技能描述':'用途说明',", "+(tab==='skill'?field('技能描述',");s=s.replace("`,tab==='skill');if(tab==='skill')body", "`,true):'');if(tab==='skill')body");
s=s.replace("+field('关联智能体','<input disabled value=\"内容协作智能体\">')",'');
s=s.replace("desc:$('#formDesc').value.trim(),", "...(tab==='skill'?{desc:$('#formDesc').value.trim()}:{}),");
s=s.replace("${tab==='prompt'?`<dt>关联智能体</dt><dd>${x.agent}</dd>`:''}<dt>用途说明</dt><dd>${esc(x.desc||'—')}</dd>","${tab==='skill'?`<dt>技能描述</dt><dd>${esc(x.desc||'—')}</dd>`:''}");
s=s.replace("${tab==='prompt'?`<button class=\"primary\" id=\"use\" ${x.status!=='published'?'disabled':''}>用于对话</button>`:''}",'');
s=s.replace(";$('#use')?.addEventListener('click',()=>handoff(x))",'');
s=s.replace(/^function handoff\(x\).*\r?\n/m,'');s=s.replace("if(tab==='prompt'&&x.status==='published')items.push(['用于对话',()=>handoff(x)]);",'');s=s.replace(",handoff:()=>handoff(current()[0])",'');
fs.writeFileSync(p,s);
