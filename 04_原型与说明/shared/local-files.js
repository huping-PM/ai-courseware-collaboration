/* Prototype-only local persistence. No file is executed or sent to an external service. */
window.LocalFiles = (() => {
  const open = () => new Promise((resolve,reject) => { const r=indexedDB.open('content-collaboration-files',1); r.onupgradeneeded=()=>r.result.createObjectStore('files');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error); });
  async function access(mode,fn){const db=await open();return new Promise((resolve,reject)=>{const tx=db.transaction('files',mode),r=fn(tx.objectStore('files'));tx.oncomplete=()=>{db.close();resolve(r.result)};tx.onerror=()=>{db.close();reject(tx.error)};tx.onabort=()=>{db.close();reject(tx.error)}})}
  const put=(key,value)=>access('readwrite',s=>s.put(value,key)),get=key=>access('readonly',s=>s.get(key));
  async function unzip(file){
    if(file.size>50*1024*1024)throw Error('技能包不能超过50MB');
    const buffer=await file.arrayBuffer(),v=new DataView(buffer),bytes=new Uint8Array(buffer);let end=-1;
    for(let i=bytes.length-22;i>=Math.max(0,bytes.length-65557);i--)if(v.getUint32(i,true)===0x06054b50){end=i;break}
    if(end<0)throw Error('压缩包损坏或不是有效ZIP文件');
    if(v.getUint16(end+4,true)||v.getUint16(end+6,true))throw Error('暂不支持分卷压缩包');
    const count=v.getUint16(end+10,true);let pos=v.getUint32(end+16,true),total=0,files=[],seen=new Set();
    if(count>200)throw Error('技能包最多包含200个文件及目录');
    for(let i=0;i<count;i++){
      if(pos+46>bytes.length||v.getUint32(pos,true)!==0x02014b50)throw Error('压缩包目录损坏');
      const flags=v.getUint16(pos+8,true),method=v.getUint16(pos+10,true),packed=v.getUint32(pos+20,true),size=v.getUint32(pos+24,true),nl=v.getUint16(pos+28,true),el=v.getUint16(pos+30,true),cl=v.getUint16(pos+32,true),off=v.getUint32(pos+42,true);
      const name=new TextDecoder('utf-8',{fatal:true}).decode(bytes.slice(pos+46,pos+46+nl)).replaceAll('\\','/');
      if(!name||name.startsWith('/')||/^[a-z]:/i.test(name)||name.split('/').includes('..')||name.includes('\0'))throw Error('压缩包含不安全的文件路径');
      if(seen.has(name.toLowerCase()))throw Error('压缩包内文件路径重复：'+name);seen.add(name.toLowerCase());
      if(flags&1)throw Error('请上传未加密的ZIP压缩包');
      if(((v.getUint32(pos+38,true)>>>16)&0xf000)===0xa000)throw Error('技能包不能包含符号链接');
      total+=size;if(total>200*1024*1024)throw Error('解压后文件总量不能超过200MB');
      pos+=46+nl+el+cl;if(name.endsWith('/'))continue;
      if(off+30>bytes.length||v.getUint32(off,true)!==0x04034b50)throw Error('压缩包文件头损坏');
      const start=off+30+v.getUint16(off+26,true)+v.getUint16(off+28,true);if(start+packed>bytes.length)throw Error('压缩包文件不完整');
      let blob=new Blob([bytes.slice(start,start+packed)]);
      if(method===8){const reader=blob.stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader(),parts=[];let n=0;while(true){const x=await reader.read();if(x.done)break;n+=x.value.length;if(n>size){await reader.cancel();throw Error('解压后的文件大小异常')}parts.push(x.value)}blob=new Blob(parts)}else if(method!==0)throw Error('不支持该ZIP压缩方式，请使用标准ZIP');
      if(blob.size!==size)throw Error('文件大小校验失败：'+name);
      files.push({path:name,size,blob});
    }
    const entries=files.filter(x=>/^skills?\.md$/i.test(x.path.split('/').pop()));
    if(entries.length!==1)throw Error(entries.length?'识别到多个技能说明文件，请每个压缩包只保留一个 skills.md 或 SKILL.md':'未找到 skills.md 或 SKILL.md，请检查压缩包');
    return {files,entry:entries[0],name:file.name,blob:file};
  }
  return {put,get,unzip};
})();
