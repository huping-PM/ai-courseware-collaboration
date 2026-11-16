async function freezeFrame(iframe, target) {
 const doc=iframe.contentDocument, win=iframe.contentWindow;
 await doc.fonts.ready;
 function copy(el){
  if(['SCRIPT','LINK','STYLE','NOSCRIPT'].includes(el.tagName))return null;
  if(el.nodeType===3)return document.createTextNode(el.textContent);
  if(el.nodeType!==1)return null;
  const style=win.getComputedStyle(el);if(style.display==='none')return null;
  const clone=el.cloneNode(false);clone.removeAttribute('id');
  for(const key of style)clone.style.setProperty(key,style.getPropertyValue(key));
  if(el instanceof win.HTMLImageElement)clone.src=el.src;
  if(el instanceof win.HTMLInputElement){clone.setAttribute('value',el.value);if(el.checked)clone.setAttribute('checked','');}
  if(el instanceof win.HTMLTextAreaElement)clone.textContent=el.value;
  else for(const child of el.childNodes){const c=copy(child);if(c)clone.appendChild(c);}
  if(el.tagName==='DIALOG'&&el.open){const r=el.getBoundingClientRect();clone.style.cssText+=';position:absolute;margin:0;left:'+r.x+'px;top:'+r.y+'px;z-index:1001';}
  if(el.tagName==='SELECT'){for(let i=0;i<clone.options.length;i++)clone.options[i].selected=el.options[i].selected;}
  return clone;
 }
 const root=copy(doc.body);root.style.cssText+=';position:relative;width:1920px;height:1080px;overflow:hidden;transform:translateZ(0);margin:0';
 if(doc.querySelector('dialog[open]')){const shade=document.createElement('div');shade.style.cssText='position:absolute;inset:0;background:rgba(0,0,0,.35);z-index:1000';root.append(shade);}
 target.replaceChildren(root);iframe.remove();target.dataset.ready='true';
 if(!document.querySelector('iframe')&&!document.querySelector('[data-capture-loader]')){const s=document.createElement('script');s.dataset.captureLoader='true';s.src='https://mcp.figma.com/mcp/html-to-design/capture.js';document.body.append(s);}
}
