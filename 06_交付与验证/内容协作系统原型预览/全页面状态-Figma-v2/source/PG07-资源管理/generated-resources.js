(()=>{
const key='pg07-saved-generated-v1',projectId=new URLSearchParams(location.search).get('project')||'a';
function read(){return JSON.parse(localStorage.getItem(key)||'[]')}
function load(){try{const rows=read().filter(r=>r.projectId===projectId);for(const k of Object.keys(data)){data[k]=[...rows.filter(r=>r.type===k),...data[k].filter(r=>!r.sourceArtifact)];for(const r of rows.filter(r=>r.type===k)){if(!kinds[k].formats.includes(r.format))kinds[k].formats.push(r.format);if(!categories[k].includes(r.cat))categories[k].push(r.cat)}}}catch{toast('保存的资源加载失败，请重试')}}
const previous=render;render=function(){previous();try{const others=read().filter(r=>r.projectId!==projectId),rows=Object.values(data).flat().filter(r=>r.sourceArtifact);localStorage.setItem(key,JSON.stringify([...others,...rows]))}catch{toast('资源修改未能保存在此浏览器中')}};
load();renderTypes();render();window.addEventListener('storage',e=>{if(e.key===key){load();renderTypes();previous()}});
})();
