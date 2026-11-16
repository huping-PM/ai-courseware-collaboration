from pathlib import Path
import json,re,shutil
root=Path(__file__).resolve().parents[2]
here=Path(__file__).parent
dest=root/'06_交付与验证/内容协作系统原型预览/全页面状态-Figma-v2'
index=json.loads((dest/'Figma状态索引.json').read_text(encoding='utf-8-sig'))
updates=json.loads((here/'原位合并索引.json').read_text(encoding='utf-8-sig'))
for u in updates:
 old=next((x for x in index['states'] if x['section']==u['section']),None)
 u['filename']=old['filename'] if old else u['id']+'_'+u['name'].split(' ',1)[-1]+'.png'
 u['figmaUrl']='https://www.figma.com/design/EjC3IegY9kqwAAmg5M5mrR?node-id='+u['section'].replace(':','-')
 u['noteX']=40+u['width']+28;u['screenRight']=40+u['width']
 if old is not None: old.update(u)
 else: index['states'].append(u)
 source=dest/u['filename'];target=dest/'效果图'/u['filename']
 assert source.exists(),source
 shutil.copy2(source,target);source.unlink()
index['version']='原位维护';index['date']='2026-09-17'
(dest/'Figma状态索引.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
gallery=dest/'效果图预览.html';s=gallery.read_text(encoding='utf-8-sig');s=re.sub(r'const states=.*?;\s*let ',lambda m:'const states='+json.dumps(index['states'],ensure_ascii=False)+';let ',s,flags=re.S);s=s.replace('99 个状态','102 个状态').replace('内容协作 · 35','内容协作 · 38');gallery.write_text(s,encoding='utf-8')
(dest/'状态图旁说明-展示副本.md').write_text('# 状态图旁说明展示副本\n\n需求正文的展示摘录，2026-09-17原位同步。\n\n'+'\n\n'.join('## '+x['name']+'\n\n'+x['noteText'] for x in index['states']),encoding='utf-8')
p=dest/'Figma设计资产索引.md';s=p.read_text(encoding='utf-8-sig');s='# 当前维护说明 · 2026-09-17\n\n按用户要求，后续直接修改原页面、原画板并保留节点链接，不再复制版本页面。本次已合并技能包与会话任务改动，删除临时v3页；上传确认等3个独有状态移入原PG11页面。当前共102个状态，PG11为38个。原位导出与索引同步；下方早期99状态验证为历史记录。\n\n'+s;p.write_text(s,encoding='utf-8')
redirect='''<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../内容协作系统原型预览/全页面状态-Figma-v2/效果图预览.html"><title>已合并至统一预览</title><p>效果图已合并回原页面，请使用<a href="../内容协作系统原型预览/全页面状态-Figma-v2/效果图预览.html">统一预览入口</a>。</p>'''
(here/'效果图预览.html').write_text(redirect,encoding='utf-8')
mapping={'SKILL-V3-01':'SKILL-03','SKILL-V3-02':'SKILL-07','SKILL-V3-03':'SKILL-04','SKILL-V3-04':'SKILL-06','PG11-V3-01':'PG11-I00','PG11-V3-02':'PG11-C08','PG11-V3-03':'PG11-U01','PG11-V3-04':'PG11-U02','PG11-V3-05':'PG11-U03'}
old=json.loads((here/'Figma索引.json').read_text(encoding='utf-8-sig'));old['status']='已合并，使用原页面节点';old.pop('created',None);old['page']=None;old['states']=[dict(next(x for x in index['states'] if x['id']==target),previousId=source) for source,target in mapping.items()];(here/'Figma索引.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
p=here/'交付与核验.md';s=p.read_text(encoding='utf-8-sig');s='> 当前入口已合并回原页面，临时v3页已删除。请使用[统一效果图预览](../内容协作系统原型预览/全页面状态-Figma-v2/效果图预览.html)。本目录PNG仅为合并前工作快照。\n\n'+s
for x in old['states']:
 oldstate=next((z for z in json.loads((here/'原位合并索引.json').read_text(encoding='utf-8-sig')) if z['id']==x['id']),None)
links='\n'.join('- ['+x['name']+']('+x['figmaUrl']+')' for x in old['states']);s=s.split('## Figma入口')[0]+'## 当前Figma入口\n\n'+links;p.write_text(s,encoding='utf-8')
def edit(p,fn):
 p=root/p;p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
edit(Path('README.md'),lambda s:re.sub(r'^- \*\*最新优化v3：\*\*.*$', '- **当前效果图：** 技能包、会话列表及上传交互已合并回原Figma页面，保留原画板链接；使用下方统一预览入口，不再单独维护v3页面。',s,flags=re.M).replace('四页共99个状态','四页共102个状态'))
edit(Path('00_项目管理/项目状态.md'),lambda s:s.replace('## 当前阶段\n','## 当前阶段\n\n按用户要求已将临时v3图合并回原技能/内容协作页面，保留已有画板链接；删除重复v3页面，3个独有上传状态归入原PG11，当前统一入口共102状态。原位导出、旁注副本与索引同步。以下为此前进展。\n',1))
edit(Path('00_项目管理/决策与待确认.md'),lambda s:s.replace('| D036 |','| D037 | Figma设计修改直接维护原页面、原画板，避免另建版本造成混乱 | 用户2026-09-17明确纠正 | 已合并临时v3；独有新状态归入原模块，现有画板链接保留 |\n| D036 |',1))
edit(Path('00_项目管理/工作记录.md'),lambda s:s+'\n## W049 · 2026-09-17 · Figma原位合并\n\n- 依据D037：用户要求直接修改原效果图。\n- 保留原技能和PG11画板节点；合并更新公共会话列表与上传入口，3个独有上传状态移到原PG11，删除临时v3页及6个重复状态。\n- 原有索引、PNG及统一预览同步，临时预览跳转统一入口。现有资源及提示词页面未修改。\n- 核验：页面归属及节点回读、原位效果图导出；静态视觉交付，不代表全部Figma交互连线验收。\n')
print('merged',len(index['states']))
