import json, pathlib, concurrent.futures, struct, subprocess
root=pathlib.Path(__file__).parent
items=json.loads((root/'下载清单.json').read_text(encoding='utf-8'))
out=root/'效果图';out.mkdir(exist_ok=True)
def download(item):
 p=out/item['filename']
 if not p.exists() or p.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':
  subprocess.run(['curl.exe','-L','--fail','--silent','--show-error','--retry','2','--max-time','90','-o',str(p),item['url']],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 data=p.read_bytes()
 if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError(str(p)+' is not PNG')
 w,h=struct.unpack('>II',data[16:24])
 return {'id':item['id'],'filename':p.name,'width':w,'height':h,'bytes':len(data)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(download,items))
(root/'导出核验.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'downloaded':len(results),'bytes':sum(x['bytes'] for x in results)}))
