/* Shared entry from project pages to the independent AI courseware workbench. */
(()=>{
  const params=new URLSearchParams(location.search);
  if(params.get('embed')==='ai'||params.get('scope')==='global')return;
  const source=document.currentScript?.src;
  if(!source)return;
  const target=new URL('../../06_交付与验证/AI协作工作台UI风格方案/交互Demo.html',source);
  target.searchParams.set('project',params.get('project')||'a');
  target.searchParams.set('from',location.href);
  const style=new URL('ai-workbench-entry.css',source);
  const insert=()=>{
    const header=document.querySelector('header.system-top, header.top');
    if(!header||header.querySelector('.ai-workbench-entry'))return;
    const link=document.createElement('link');
    link.rel='stylesheet';link.href=style.href;document.head.append(link);
    const entry=document.createElement('a');
    entry.className='ai-workbench-entry';
    entry.href=target.href;
    entry.target='_blank';
    entry.rel='noopener noreferrer';
    entry.setAttribute('aria-label','在新标签页打开AI课件协作工作台');
    entry.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 2 2.3 7.7L22 12l-7.7 2.3L12 22l-2.3-7.7L2 12l7.7-2.3L12 2Z"/></svg><span>AI课件协作</span>';
    const user=header.querySelector('.user');
    header.classList.add('ai-has-workbench-entry');
    if(user)header.insertBefore(entry,user);else header.append(entry);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',insert,{once:true});else insert();
})();
