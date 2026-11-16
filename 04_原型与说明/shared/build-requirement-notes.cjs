// Generated display copies only; edit the Markdown sources, then run this builder.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..');
const sources=['AI课件协作平台-需求说明.md','项目与系统管理-需求说明.md'].map(name=>{const text=fs.readFileSync(path.join(root,'03_功能设计',name),'utf8').replace(/\r\n/g,'\n');return{name,text,hash:crypto.createHash('sha256').update(text).digest('hex'),version:(text.match(/版本[：:]?\s*(v[\d.]+)/)||[])[1]||'v1.0'}});
function section(src,title){const lines=src.text.split('\n'),start=lines.findIndex(l=>l.replace(/^#+\s*/, '')===title);if(start<0)throw Error('Missing requirement section: '+title);const level=lines[start].match(/^#+/)[0].length;let end=start+1;while(end<lines.length){const h=lines[end].match(/^(#+) /);if(h&&h[1].length<=level)break;end++}return lines.slice(start+1,end).join('\n').trim()}
const [main,system]=sources,entries={};
function add(key,title,src,text){if(!text.trim())throw Error('Empty notes: '+key);entries[key]={title,source:src.name,version:src.version,sourceHash:src.hash,markdown:text.trim()}}
add('resource','资源管理',main,section(main,'一、资源管理页（PG07）'));
add('globalSkill','全局技能管理',main,section(main,'二、全局技能管理页（PG18）与项目技能（PG13）')+'\n\n### 全局维护与项目引用\n\n'+section(system,'全局技能管理（已确认的管理模式）').split('\n').filter(line=>line.startsWith('- 已被项目启用')).join('\n'));
entries.globalSkill.additionalSource={name:system.name,hash:system.hash,version:system.version};
add('prompt','提示词管理',main,section(main,'三、提示词管理页（PG13·提示词）'));
add('chat','内容协作智能体',main,section(main,'四、内容协作智能体页（PG11）'));
for(const [key,title,heading]of [['projects','项目列表','项目列表'],['settings','项目基本信息','基本信息'],['members','项目成员管理','成员管理'],['projectSkill','项目技能管理','项目技能管理']])add(key,title,system,section(system,heading));
add('accounts','账号管理',system,section(system,'4. 账号管理'));
const admin=section(system,'5. 角色、导航与资源集');for(const [key,title,prefix]of [['roles','角色管理','- 角色：'],['navigation','导航管理','- 导航：'],['collections','资源集管理','- 资源集：']])add(key,title,system,admin.split('\n').filter(l=>l.startsWith(prefix)||(key!=='roles'&&l.startsWith('- 上述'))).join('\n\n'));
add('login','登录与退出',system,section(system,'7. 登录与退出'));
add('common','公共入口',system,section(system,'2. 公共入口'));
const payload={schema:1,sources:sources.map(({text,...metadata})=>metadata),entries};
fs.writeFileSync(path.join(__dirname,'requirement-notes-data.js'),'/* AUTO-GENERATED. DO NOT EDIT. */\nwindow.RequirementNotes='+JSON.stringify(payload,null,2)+';\n');
console.log('Requirement notes generated: '+Object.keys(entries).length+' sections from '+sources.length+' Markdown sources.');
