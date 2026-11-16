(function(){
 const s=(title,status,time,summary,skill)=>({title,status,time,summary,skill});
 const skill={name:'课程大纲整理',version:'1.2',started:'10:21:06',status:'成功',duration:'18 秒',result:'已形成新人培训课程大纲初稿'};
 const common=[s('读取培训资料','success','10:21:04','已读取可用培训资料'),s('调用课程大纲整理技能','success','10:21:06','已生成课程大纲初稿',skill),s('整理最终输出','success','10:21:25','已生成可编辑文档')];
 const req={id:'r1',title:'根据培训资料整理一份新人培训课程大纲',result:'已完成新人培训课程大纲，已同步至右侧内容画布。'};
 const att=x=>Object.assign({id:'a1',number:1,status:'success',summary:'已生成新人培训课程大纲',duration:'24 秒',expanded:false,steps:common},x||{});
 const secondary={id:'s2',title:'试用期培训计划',meta:'课程结构 · 昨天 16:08',requests:[{id:'r2',title:'根据培训资料整理试用期培训计划',result:'已整理试用期培训计划。',attempts:[att({id:'b1',steps:[s('读取培训资料','success','昨天 16:08','已读取可用培训资料'),s('整理最终输出','success','昨天 16:16','已生成课程结构')]})]}]};
 const pack=(id,attempts,more={})=>Object.assign({id,conversations:[{id:'s1',title:'新员工培训微课',meta:'新人培训课程大纲 · 今天 10:21',requests:[Object.assign({},req,{attempts})]},secondary]},more);
 window.TRStateData={
 TR01:pack('TR01',[att({status:'running',summary:'正在处理',expanded:true,result:'',steps:[common[0],s('调用课程大纲整理技能','running','10:21:06','正在整理课程结构',Object.assign({},skill,{status:'运行中',duration:'15 秒',result:'等待结果'}))]})]),
 TR02:pack('TR02',[att({status:'running',summary:'正在处理',expanded:false,result:'',steps:[common[0],common[1]]})]),TR03:pack('TR03',[att()]),TR04:pack('TR04',[att({expanded:true,skillOpen:true})]),
 TR05:Object.assign(pack('TR05',[att()]),{conversations:[{id:'s1',title:'新员工培训微课',meta:'新人培训课程大纲 · 今天 10:21',requests:[Object.assign({},req,{attempts:[att()]}),{id:'r3',title:'把第2节改为案例练习',result:'已将第2节调整为案例练习。',attempts:[att({id:'a3',steps:[s('分析修改要求','success','10:34:01','已识别第2节调整范围'),s('整理最终输出','success','10:34:09','已更新课程大纲')]})]}]},secondary]}),
 TR06:pack('TR06',[att({status:'failed',summary:'处理失败',expanded:true,result:'技能执行未完成，请重新尝试。',steps:[common[0],s('调用课程大纲整理技能','failed','10:21:06','技能执行未完成',Object.assign({},skill,{status:'失败',duration:'12 秒',result:'未返回可用结果'}))]})]),
 TR07:pack('TR07',[att({id:'a1',status:'failed',summary:'第 1 次 · 失败',expanded:false,result:'',steps:[common[0],s('调用课程大纲整理技能','failed','10:21:06','技能执行未完成',Object.assign({},skill,{status:'失败',result:'未返回可用结果'}))]}),att({id:'a2',number:2,status:'running',summary:'第 2 次正在处理',expanded:true,result:'',steps:[s('读取培训资料','success','10:22:01','已重新开始处理'),s('调用课程大纲整理技能','running','10:22:04','正在整理课程结构',Object.assign({},skill,{started:'10:22:04',status:'运行中',duration:'6 秒',result:'等待结果'}))]})]),
 TR08:pack('TR08',[att({status:'cancelled',summary:'已取消',expanded:true,result:'本次处理已取消，未生成新的文档。',steps:[common[0],s('调用课程大纲整理技能','cancelled','10:21:06','已停止',Object.assign({},skill,{status:'已取消',duration:'7 秒',result:'未生成文档'}))]})]),
 TR09:pack('TR09',[att({loading:true})]),TR10:pack('TR10',[att({loadError:true})]),TR11:pack('TR11',[att({empty:true,steps:[]})]),TR12:{id:'TR12',denied:true,conversations:[{id:'s1',title:'新员工培训微课',meta:'',requests:[]}]},TR13:pack('TR13',[att({duration:'8 秒',steps:[s('读取培训资料','success','10:21:04','已读取可用培训资料'),s('整理最终输出','success','10:21:11','已生成可编辑文档')],noSkills:true})])};
})();
