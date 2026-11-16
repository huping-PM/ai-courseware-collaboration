from pathlib import Path
import json
P=Path(__file__).parent
data=json.loads((P/'timeline.json').read_text(encoding='utf-8'))
source=(P/'index.html').read_text(encoding='utf-8')
source=source.replace('<head>','<head><base href="__PROJECT_BASE__">')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>商业车险产品地图 · 动画预览</title><style>*{box-sizing:border-box}body{margin:0;background:#182c31;color:#fff;font:16px "Microsoft YaHei",sans-serif}.shell{max-width:1500px;margin:20px auto;padding:0 24px}header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}h1{font-size:23px;margin:0}a{color:#d8c1a5}.frame{position:relative;aspect-ratio:16/9;width:100%;overflow:hidden;background:#efeae1}iframe{border:0;width:1920px;height:1080px;transform-origin:0 0;position:absolute}.controls{display:flex;gap:18px;align-items:center;padding:18px 0}button,select{border:0;border-radius:5px;padding:10px 15px;font:inherit;background:#eee8df;color:#203c42}button{cursor:pointer;min-width:90px}input{flex:1;accent-color:#b4d2c8}footer{color:#b8c5c4;line-height:1.8;font-size:14px}select{max-width:370px}.error{color:#ffd3c3}</style><div class="shell"><header><h1>商业车险产品地图</h1><a href="renders/商业车险产品地图.mp4">打开完整 MP4</a></header><div class="frame"><iframe title="动画画面" id="stage"></iframe></div><div class="controls"><button id="toggle">播放</button><span id="clock">00:00 / 09:11</span><input id="seek" type="range" min="0" step="0.05" aria-label="播放进度"><select id="chapter" aria-label="跳转章节"></select></div><footer>晓晓配音 · 无背景音乐 · 可按章节检查。原稿仍有待复审事项，本文件用于试看。<span id="status"></span></footer></div><script>
const meta=__DATA__,html=__HTML__;
const frame=document.querySelector('#stage'),slider=document.querySelector('#seek'),toggle=document.querySelector('#toggle'),clock=document.querySelector('#clock'),chapter=document.querySelector('#chapter'),status=document.querySelector('#status');
let ready=false,playing=false,t=0,anchor=0,wall=0,active=-1,audio=null;
slider.max=meta.duration;
meta.scenes.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=s.title;chapter.appendChild(o)});
function size(){frame.style.transform=`scale(${frame.parentElement.clientWidth/1920})`}
new ResizeObserver(size).observe(frame.parentElement);
function stamp(x){return `${Math.floor(x/60).toString().padStart(2,'0')}:${Math.floor(x%60).toString().padStart(2,'0')}`}
function pauseAudio(){if(audio)audio.pause()}
function paint(force=false){if(!ready)return;const w=frame.contentWindow;const idx=meta.scenes.findIndex(s=>t>=s.start&&t<s.end);w.document.querySelectorAll('section.clip').forEach((el,i)=>{el.style.visibility=i===idx?'visible':'hidden'});w.__timelines.root.seek(t,false);slider.value=t;clock.textContent=`${stamp(t)} / ${stamp(meta.duration)}`;if(idx>=0)chapter.value=idx;if(idx!==active){pauseAudio();active=idx;audio=idx>=0?w.document.getElementById('voice-'+meta.scenes[idx].id):null;force=true}if(!audio)return;const s=meta.scenes[idx],pos=t-s.audio_start;if(pos<0||pos>=s.duration){audio.pause();return}if(force||Math.abs(audio.currentTime-pos)>.35)audio.currentTime=pos;if(playing&&audio.paused)audio.play().catch(e=>{status.textContent=' 配音播放受浏览器限制，请使用 MP4。';status.className='error'});if(!playing)audio.pause();}
function loop(now){if(playing){t=Math.min(meta.duration,anchor+(now-wall)/1000);paint();if(t>=meta.duration){playing=false;toggle.textContent='重播';pauseAudio()}}requestAnimationFrame(loop)}
toggle.onclick=()=>{if(!ready)return;if(t>=meta.duration)t=0;playing=!playing;anchor=t;wall=performance.now();toggle.textContent=playing?'暂停':'播放';paint(true)};
slider.oninput=()=>{t=Number(slider.value);anchor=t;wall=performance.now();paint(true)};
chapter.onchange=()=>{t=meta.scenes[Number(chapter.value)].start;anchor=t;wall=performance.now();paint(true)};
frame.onload=()=>{ready=!!frame.contentWindow.__timelines?.root;size();paint(true);if(!ready)status.textContent=' 动画资源未加载，请保持文件夹完整。'};
frame.srcdoc=html.replace('__PROJECT_BASE__',new URL('../',location.href).href);requestAnimationFrame(loop);
</script></html>'''
page=page.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')).replace('__HTML__',json.dumps(source,ensure_ascii=False).replace('</','<\\/'))
(P/'preview').mkdir(exist_ok=True)
page=page.replace('href="renders/','href="../renders/')
(P/'preview/动画预览.html').write_text(page,encoding='utf-8')
print('Preview created')
