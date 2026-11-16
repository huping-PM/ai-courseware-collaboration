(()=>{if(scene==='denied')return;
// Additional bounded review conversations, with stable IDs to avoid duplicate insertion.
if(project==='a'){
 const examples=[
 {id:'pg11-history-safety-plan',title:'安全培训内容安排讨论',time:'09-14 14:20',counts:{doc:2,image:0,video:0}},
 {id:'pg11-history-helmet',title:'安全帽讲解画面制作',time:'09-14 15:40',counts:{doc:1,image:3,video:1}},
 {id:'pg11-history-short',title:'安全培训视频精简版',time:'09-14 16:30',counts:{doc:1,image:2,video:2}},
 {id:'pg11-history-review',title:'新员工培训内容复核',time:'09-15 09:10',counts:{doc:3,image:1,video:1}}
 ];
 const samples=examples.filter(e=>!store.s.some(s=>s.id===e.id)).map(e=>{
  const s=blank();Object.assign(s,{id:e.id,project:'a',title:e.title,time:e.time});s.artifacts=[];
  Object.entries(e.counts).forEach(([type,n])=>{for(let i=1;i<=n;i++){const name=type==='doc'?'安全培训内容安排-'+i+'.md':type==='image'?'安全帽示意图-'+i+'.png':'安全培训视频-第'+i+'稿.mp4';const a=artifact(type,name);a.time=e.time;s.artifacts.push(a)}});
  s.messages=[{role:'user',text:e.title+'，请整理对应的培训资料和成果。',time:e.time,refs:[]},{role:'agent',text:'本次内容已整理完成，可从右侧清单查看，或继续提出修改意见。',time:e.time,artifacts:s.artifacts.map(a=>a.id)}];return s;
 });
 store.s.unshift(...samples);persist();
}


})();