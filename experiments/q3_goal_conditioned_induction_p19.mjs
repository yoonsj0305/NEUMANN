/* NEUMANN P1.9: task-conditioned *typed executable expression* synthesis.
 * This is classical, bounded grammar induction, NOT a learned JEPA or new arbitrary opcode.
 * Only original TRAIN example pairs and TEST INPUTS enter propose(); gold accessible to score() ONLY.
 * Immutable first experiment: all fitted programs must agree on test or ABSTAIN.
 */
const RULES={version:'neumann.q3.p19.v1',offset_min:-3,offset_max:3,types:['affine','split-predicate','split-value']};
const TRANSFORMS=['id','flipH','flipV','rot90','rot180','rot270','transpose','antiTranspose'];
const PREDS=['bothZero','eitherZero','oneZero','bothNonzero','same','different','sameNonzero','aZero','bZero','aNonzero','bNonzero'];
const EXPRS=['a','b','min','max'];
function valid(g){return Array.isArray(g)&&g.length>=1&&g.length<=30&&Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));}
function equal(a,b){return valid(a)&&valid(b)&&a.length===b.length&&a.every((r,i)=>r.length===b[i].length&&r.every((v,j)=>v===b[i][j]));}
function rotate(g){return Array.from({length:g[0].length},(_,r)=>Array.from({length:g.length},(_,c)=>g[g.length-c-1][r]));}
function orient(g,t){if(!valid(g))return null;switch(t){
 case 'id':return g.map(row=>row.slice());
 case 'flipH':return g.map(row=>row.slice().reverse());
 case 'flipV':return g.slice().reverse().map(row=>row.slice());
 case 'rot90':return rotate(g);
 case 'rot180':return rotate(rotate(g));
 case 'rot270':return rotate(rotate(rotate(g)));
 case 'transpose':return g[0].map((_,c)=>g.map(row=>row[c]));
 case 'antiTranspose':return rotate(rotate(g[0].map((_,c)=>g.map(row=>row[c]))));
 default:return null;
}}
function uniqueMode(g){if(!valid(g))return null;const counter=new Map();for(const r of g)for(const v of r)counter.set(v,(counter.get(v)||0)+1);const sorted=[...counter].sort((a,b)=>b[1]-a[1]);return sorted.length>1&&sorted[0][1]===sorted[1][1]?null:sorted[0][0];}
function nonBgCrop(g){const bg=uniqueMode(g);if(bg===null)return null;let pts=[];for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==bg)pts.push([r,c]);if(!pts.length)return null;const r0=Math.min(...pts.map(x=>x[0])),r1=Math.max(...pts.map(x=>x[0])),c0=Math.min(...pts.map(x=>x[1])),c1=Math.max(...pts.map(x=>x[1]));return g.slice(r0,r1+1).map(row=>row.slice(c0,c1+1));}
function affineSample(input,ast){
 let g=ast.crop?nonBgCrop(input):input;if(!g)return null;g=orient(g,ast.orientation);if(!g)return null;
 const bg=ast.fill==='zero'?0:uniqueMode(input);if(bg===null)return null;
 const h=g.length,w=g[0].length;
 return Array.from({length:h},(_,r)=>Array.from({length:w},(_,c)=>{
  const rr=r-ast.dy,cc=c-ast.dx;
  return rr>=0&&cc>=0&&rr<h&&cc<w?g[rr][cc]:bg;
 }));
}
function splitPanels(input,orientation){
 if(!valid(input))return null;const h=input.length,w=input[0].length;
 if(orientation==='horizontal'){
  if(h<3||h%2!==1)return null;
  const m=(h-1)/2,line=input[m],separator=line[0];if(!line.every(v=>v===separator))return null;
  return {a:input.slice(0,m),b:input.slice(m+1),separator};
 }
 if(orientation==='vertical'){
  if(w<3||w%2!==1)return null;
  const m=(w-1)/2,sep=input[0][m];if(!input.every(row=>row[m]===sep))return null;
  return {a:input.map(row=>row.slice(0,m)),b:input.map(row=>row.slice(m+1)),separator:sep};
 }
 return null;
}
function predicate(a,b,op){switch(op){
 case 'bothZero':return a===0&&b===0;
 case 'eitherZero':return a===0||b===0;
 case 'oneZero':return (a===0)!==(b===0);
 case 'bothNonzero':return a!==0&&b!==0;
 case 'same':return a===b;
 case 'different':return a!==b;
 case 'sameNonzero':return a===b&&a!==0;
 case 'aZero':return a===0;
 case 'bZero':return b===0;
 case 'aNonzero':return a!==0;
 case 'bNonzero':return b!==0;
 default:throw new Error('bad predicate');
}}
function baseExpr(a,b,op){switch(op){case 'a':return a;case 'b':return b;case 'min':return Math.min(a,b);case 'max':return Math.max(a,b);default:throw new Error('bad expr');}}
function splitSample(input,ast){
 const panels=splitPanels(input,ast.orientation);if(!panels)return null;
 return panels.a.map((row,r)=>row.map((a,c)=>{
  const b=panels.b[r][c];return ast.mode==='predicate'?(predicate(a,b,ast.op)?1:0):baseExpr(a,b,ast.op);
 }));
}
function primitive(input,ast){return ast.type==='affine'?affineSample(input,ast):splitSample(input,ast);}
function learnMap(replays,train,kind){
 const mapping=new Map(),counts=new Map();
 for(let k=0;k<train.length;k++){
  const x=replays[k],y=train[k].output;if(!valid(x)||!valid(y)||x.length!==y.length||x[0].length!==y[0].length)return null;
  for(let r=0;r<x.length;r++)for(let c=0;c<x[0].length;c++){
   const a=x[r][c],b=y[r][c];counts.set(a,(counts.get(a)||0)+1);
   if(mapping.has(a)&&mapping.get(a)!==b)return null;mapping.set(a,b);
  }
 }
 if(kind==='predicate'&&(!mapping.has(0)||!mapping.has(1)))return null;
 // Coverage: a candidate cannot be accepted from one example with unseen mapped class.
 for(const [v,count]of counts)if(count<2)return null;
 return [...mapping.entries()].sort((a,b)=>a[0]-b[0]);
}
function execute(input,program){
 const raw=primitive(input,program.ast);if(!valid(raw))return null;
 const palette=new Map(program.palette);return raw.every(row=>row.every(v=>palette.has(v)))?raw.map(row=>row.map(v=>palette.get(v))):null;
}
function *allASTs(){
 for(const crop of [false,true])for(const orientation of TRANSFORMS){
  for(let dy=-3;dy<=3;dy++)for(let dx=-3;dx<=3;dx++)for(const fill of ['zero','background'])yield {type:'affine',crop,orientation,dy,dx,fill};
 }
 for(const orientation of ['horizontal','vertical']){
  for(const op of PREDS)yield {type:'split',mode:'predicate',orientation,op};
  for(const op of EXPRS)yield {type:'split',mode:'value',orientation,op};
 }
}
function propose(train,testInputs){
 const start=Date.now();const trace={candidate_ast_count:0,train_sample_evaluations:0,test_sample_evaluations:0,training_fit_count:0,distinct_test_predictions:0,ambiguous:false,abstention:null,wall_ms:null,representative_ASTs:[],model_forwards:0};
 if(!Array.isArray(train)||!train.length||!train.every(p=>valid(p.input)&&valid(p.output))||!Array.isArray(testInputs)||!testInputs.length||!testInputs.every(valid)){
  trace.abstention='INVALID_INPUT';trace.wall_ms=Date.now()-start;return {prediction:null,trace};
 }
 let consensus=null,unique=new Set(),conflict=false;
 for(const ast of allASTs()){
  trace.candidate_ast_count++;let replays=[],works=true;
  for(const p of train){trace.train_sample_evaluations++;let r=null;try{r=primitive(p.input,ast);}catch(e){}if(!valid(r)){works=false;break;}replays.push(r);}
  if(!works)continue;
  const palette=learnMap(replays,train,ast.mode);
  if(palette===null)continue;
  const program={ast,palette};trace.training_fit_count++;
  const testOut=[];for(const x of testInputs){trace.test_sample_evaluations++;let z=null;try{z=execute(x,program);}catch(e){}if(!valid(z)){works=false;break;}testOut.push(z);}
  if(!works){conflict=true;continue;}
  const sig=JSON.stringify(testOut);unique.add(sig);
  if(consensus===null)consensus=testOut;else if(JSON.stringify(consensus)!==sig)conflict=true;
  if(trace.representative_ASTs.length<3)trace.representative_ASTs.push({ast,palette});
 }
 trace.distinct_test_predictions=unique.size;trace.ambiguous=conflict||unique.size>1;
 if(trace.training_fit_count===0)trace.abstention='NO_TRAIN_CONSISTENT_AST';
 else if(trace.ambiguous)trace.abstention='AMBIGUOUS_PREDICTIONS_OR_UNSUPPORTED_INPUT';
 else if(consensus===null)trace.abstention='NO_VALID_TEST_EXECUTION';
 trace.wall_ms=Date.now()-start;
 return {prediction:trace.abstention===null?consensus:null,trace};
}
function originalScore(task,baselineB,baselineQ){
 // proposer functions are given only train input/output and original TEST INPUT, never oracle answers.
 const x=task.test.map(e=>e.input);
 const B=baselineB(task.train,x,'B');const Q=baselineQ(task.train,x);
 const Bsig=B.proposals===null?null:JSON.stringify(B.proposals),Qsig=Q.prediction===null?null:JSON.stringify(Q.prediction);
 const baselineConflict=Bsig!==null&&Qsig!==null&&Bsig!==Qsig;
 const baselined=baselineConflict?null:(B.proposals!==null?B.proposals:Q.prediction);
 const C=baselined===null&&!baselineConflict?propose(task.train,x):null;
 const final=baselined!==null?baselined:(C?.prediction??null);
 // Original TEST outputs are first touched here, after ALL proposals are finalized.
 const target=task.test.map(e=>e.output);
 const exact=pred=>pred!==null&&pred.length===target.length&&pred.every((g,i)=>equal(g,target[i]));
 return {B_exact:exact(B.proposals),Q_exact:exact(Q.prediction),baseline_exact:exact(baselined),C_exact:C===null?null:exact(C.prediction),combined_exact:exact(final),
  C_new_correct:C!==null&&exact(C.prediction)&&!exact(baselined),C_false_accept:C!==null&&C.prediction!==null&&!exact(C.prediction),
  baseline_conflict:baselineConflict,combined_false_accept:final!==null&&!exact(final),
  B_attempted:B.trace.attempted,Q_operator_calls:Q.trace.operator_evaluations,Q_wall_ms:Q.trace.study_wall_ms,B_wall_ms:B.trace.elapsed_ms,
  C_trace:C?.trace??null,test_count:task.test.length,train_count:task.train.length};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(names,excluded){const bad=new Set(excluded);return names.filter(name=>name.endsWith('.json')&&!bad.has(name)).map(name=>({name,h:fnv32('neumann-q3-p19-20261105|'+name)})).sort((a,b)=>a.h-b.h||a.name.localeCompare(b.name)).slice(0,48).map(x=>x.name);}
export {RULES,TRANSFORMS,PREDS,valid,primitive,execute,learnMap,allASTs,propose,originalScore,cohort};
