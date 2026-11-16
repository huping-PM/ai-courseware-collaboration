from pathlib import Path
import json,re,hashlib,subprocess
P=Path(__file__).resolve().parent.parent
data=json.loads((P/'timeline.json').read_text(encoding='utf-8'))
source=P.parent/'课程文案/商业车险产品地图-课程口播稿.md'
text=source.read_text(encoding='utf-8-sig')
spoken=''.join(re.findall(r'^(?:旁白|王女士|小林|陈老师|讲师|栗子精灵)：(.+)$',text,re.M))
actual=''.join(s['text'] for s in data['scenes'])
result={'manuscript_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exact_spoken_text_equal':spoken==actual,'source_chars':len(spoken),'audio_chars':len(actual),'scene_count':len(data['scenes']),'duration':data['duration'],'audio_seconds':sum(s['duration'] for s in data['scenes']),'intro_through_P05_seconds':data['scenes'][4]['end'],'audio_clipping':any(s['audio_start']+s['duration']>s['end'] for s in data['scenes'])}
(P/'qa/content-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
assert result['exact_spoken_text_equal'] and not result['audio_clipping']
args=[str(P/'tools/ffmpeg.exe'),'-hide_banner','-loglevel','error','-y']
for s in data['scenes']:args+=['-i',str(P/s['src'])]
filters=[]
for i,s in enumerate(data['scenes']):filters.append(f'[{i}:a]adelay={round(s["audio_start"]*1000)}:all=1[a{i}]')
filters.append(''.join(f'[a{i}]' for i in range(17))+f'amix=inputs=17:normalize=0,apad,atrim=0:{data["duration"]}[out]')
args+=['-filter_complex',';'.join(filters),'-map','[out]','-c:a','libmp3lame','-b:a','128k',str(P/'audio/完整配音-含段间停顿.mp3')]
subprocess.run(args,check=True)
print('Full audio exported')
