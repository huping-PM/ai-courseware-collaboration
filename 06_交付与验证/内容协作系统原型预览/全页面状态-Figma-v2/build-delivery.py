import json,pathlib,html
from PIL import Image,ImageOps,ImageDraw,ImageFont
r=pathlib.Path(__file__).parent
data=json.loads((r/'Figma状态索引.json').read_text(encoding='utf-8'))
states=data['states']
payload=json.dumps(states,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>内容协作系统 · 状态效果图</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:#243047;font:14px "Microsoft YaHei",sans-serif}header{padding:28px 36px;background:white;border-bottom:1px solid #e6eaf0}h1{margin:0 0 10px;font-size:24px}p{color:#68768c;margin:8px 0}main{padding:24px 36px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}button,input,a.action{border:1px solid #dce2ec;background:white;border-radius:8px;padding:10px 15px;color:#354159;font:inherit}button{cursor:pointer}button.active{color:white;background:#247bf0;border-color:#247bf0}input{min-width:260px;margin-left:auto}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:20px}article{background:white;border:1px solid #e3e8f1;border-radius:12px;overflow:hidden}article img{width:100%;aspect-ratio:2.08;object-fit:contain;background:#fafbfe;cursor:zoom-in}article section{padding:16px}h2{font-size:15px;margin:0 0 14px}a{color:#247bf0;text-decoration:none}.links{display:flex;gap:20px}dialog{padding:12px;border:0;border-radius:10px;max-width:96vw;max-height:96vh}dialog::backdrop{background:#152339aa}dialog img{max-width:92vw;max-height:82vh}dialog button{float:right}#total{margin:0 0 18px;color:#6a768b}
</style><header><h1>内容协作系统 · 全页面状态效果图</h1><p>99 个状态 · 业务画面 + 右侧需求说明 · 2026-09-17</p><p>点击图片放大，点击 Figma 打开可编辑画板。此入口可离线查看；完整业务交互以 HTML 原型为准。</p></header><main><nav><button data-filter="all" class="active">全部</button><button data-filter="PG07">资源管理 · 30</button><button data-filter="SKILL">技能管理 · 18</button><button data-filter="PROMPT">提示词管理 · 16</button><button data-filter="PG11">内容协作 · 35</button><input id="search" placeholder="搜索名称或状态编号" aria-label="搜索状态"></nav><div id="total"></div><div id="grid"></div></main><dialog id="zoom"><button onclick="zoom.close()">关闭 ×</button><h2 id="zoomtitle"></h2><img id="zoomimg" alt=""></dialog><script>
const states=PAYLOAD;let filter='all';const grid=document.getElementById('grid');function render(){const q=document.getElementById('search').value.trim().toLowerCase();const items=states.filter(s=>(filter==='all'||s.id.startsWith(filter))&&s.name.toLowerCase().includes(q));grid.replaceChildren();document.getElementById('total').textContent='显示 '+items.length+' 个状态';for(const s of items){const a=document.createElement('article'),im=document.createElement('img'),sec=document.createElement('section'),h=document.createElement('h2'),links=document.createElement('div'),fig=document.createElement('a'),png=document.createElement('a');im.src='效果图/'+s.filename;im.alt=s.name;im.loading='lazy';im.onclick=()=>{zoomtitle.textContent=s.name;zoomimg.src=im.src;zoom.showModal()};h.textContent=s.name;links.className='links';fig.href=s.figmaUrl;fig.target='_blank';fig.rel='noopener';fig.textContent='在 Figma 查看 ↗';png.href=im.src;png.target='_blank';png.textContent='打开原尺寸图片';links.append(fig,png);sec.append(h,links);a.append(im,sec);grid.append(a)}}document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));render()});document.getElementById('search').oninput=render;render();
</script></html>'''.replace('PAYLOAD',payload)
(r/'效果图预览.html').write_text(page,encoding='utf-8')
notes=['# 全页面状态图旁说明 · 展示副本','日期：2026-09-17。由四页需求说明 v1.2 及各模块正文整理；本文件是状态画板的展示映射，不替代需求正文，不新增业务确认。','']
for s in states:
 notes+=['## '+s['name'],'[Figma画板]('+s['figmaUrl']+')','',s['noteText'],'']
(r/'状态图旁说明-展示副本.md').write_text('\n\n'.join(notes),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for part in range((len(states)+11)//12):
 chunk=states[part*12:(part+1)*12]; sheet=Image.new('RGB',(1500,4*280),'#e8edf4');d=ImageDraw.Draw(sheet)
 for i,s in enumerate(chunk):
  img=Image.open(r/'效果图'/s['filename']).convert('RGB');img.thumbnail((492,242));x=(i%3)*500;y=(i//3)*280;sheet.paste(img,(x,y+28));d.text((x+6,y+4),s['name'],font=font,fill='#233047')
 sheet.save(r/('核验缩略图-'+str(part+1)+'.jpg'))
print('gallery and notes created:',len(states))

