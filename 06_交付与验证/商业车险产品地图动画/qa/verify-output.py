from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw,ImageStat,ImageChops
P=Path(__file__).resolve().parent.parent
video=P/'renders/商业车险产品地图.mp4'
ffmpeg=str(P/'tools/ffmpeg.exe');ffprobe=str(P/'tools/ffprobe.exe')
data=json.loads((P/'timeline.json').read_text(encoding='utf-8'))
probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(video)],encoding='utf-8'))
(P/'qa/mp4-probe.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2),encoding='utf-8')
vs=next(s for s in probe['streams'] if s['codec_type']=='video');aus=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert vs['width']==1920 and vs['height']==1080 and vs['r_frame_rate']=='30/1' and vs['codec_name']=='h264' and aus['codec_name']=='aac'
assert abs(float(probe['format']['duration'])-data['duration'])<.15
decode=subprocess.run([ffmpeg,'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
(P/'qa/full-decode.log').write_text(decode.stderr,encoding='utf-8');assert decode.returncode==0 and not decode.stderr.strip()
out=P/'qa/mp4-frames';out.mkdir(exist_ok=True)
frames=[]
for i,s in enumerate(data['scenes']):
    t=round(s['end']-1,2);f=out/(s['id']+'.png')
    subprocess.run([ffmpeg,'-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(f)],check=True)
    im=Image.open(f).convert('RGB');ref=Image.open(P/f'qa/final-snapshots/frame-{i:02d}-at-{t:g}s.png').convert('RGB')
    error=sum(ImageStat.Stat(ImageChops.difference(im,ref)).mean)/3
    frames.append({'id':s['id'],'time':t,'file':str(f.relative_to(P)),'pixel_mean_difference_vs_source':round(error,3),'brightness':round(sum(ImageStat.Stat(im).mean)/3,2)})
for k in range(2):
    sheet=Image.new('RGB',(1440,900),(28,37,39));draw=ImageDraw.Draw(sheet)
    for j,entry in enumerate(frames[k*9:k*9+9]):
        im=Image.open(P/entry['file']);im.thumbnail((474,267));x=(j%3)*480;y=(j//3)*300
        draw.text((x+8,y+7),f'{entry["id"]} | {entry["time"]:.2f}s',fill='white');sheet.paste(im,(x+3,y+29))
    sheet.save(P/f'qa/mp4-contact-{k+1}.jpg',quality=92)
result={'file':str(video),'bytes':video.stat().st_size,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'duration':float(probe['format']['duration']),'video_codec':vs['codec_name'],'audio_codec':aus['codec_name'],'width':vs['width'],'height':vs['height'],'fps':vs['r_frame_rate'],'audio_stream_count':sum(s['codec_type']=='audio' for s in probe['streams']),'full_decode':'passed','frames':frames,'all_frames_match_source':all(f['pixel_mean_difference_vs_source']<5 for f in frames)}
(P/'qa/output-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='frames'},ensure_ascii=False))
assert result['all_frames_match_source']
