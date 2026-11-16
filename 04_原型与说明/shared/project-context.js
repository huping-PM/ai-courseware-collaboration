(()=>{
const P=Platform,p=P.projectId;
if(typeof getCatalog==='function'){
 const previous=getCatalog;getCatalog=function(kind){if(kind==='skill'){return P.read('platform-global-skills-v1',[]).filter(x=>(x.skillType||'global')==='global'||x.ownerProject===p).map(x=>({id:'global-skill-'+x.id,name:x.name,extra:x.desc,disabled:x.status!=='enabled'}))}if(!['a','b'].includes(p)&&kind!=='target')return[];return previous(kind)};
}
})();
