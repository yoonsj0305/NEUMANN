/* NEUMANN P2.0: sound deletion of provably impossible P1.9 AST evaluations.
 * This imports the IDENTICAL immutable P1.9 primitive semantics, candidate inventory,
 * runtime compiler, target palette and output consensus rules. Source TEST labels are absent.
 * No neural/JEPA or teacher inference is performed.
 */
import {valid, primitive, execute, allASTs} from './q3_goal_conditioned_induction_p19.mjs';
const SPEC={version:'neumann.q3.p20.v1',baseline:'P1.9 immutable grammar',scope:'train-only shape abstract interpretation + incremental palette constraint'};
function uniqueMode(g){
 const count=new Map();for(const row of g)for(const v of row)count.set(v,(count.get(v)||0)+1);
 const sorted=[...count].sort((a,b)=>b[1]-a[1]);return sorted.length>1&&sorted[0][1]===sorted[1][1]?null:sorted[0][0];
}
function bboxShape(g){
 const bg=uniqueMode(g);if(bg===null)return null;
 let r0=Infinity,r1=-1,c0=Infinity,c1=-1;
 for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==bg){r0=Math.min(r0,r);r1=Math.max(r1,r);c0=Math.min(c0,c);c1=Math.max(c1,c);}
 return r1<0?null:[r1-r0+1,c1-c0+1];
}
function outputShape(input,ast){
 if(!valid(input))return null;
 if(ast.type==='affine'){
  const dims=ast.crop?bboxShape(input):[input.length,input[0].length];if(dims===null)return null;
  return ['rot90','rot270','transpose','antiTranspose'].includes(ast.orientation)?[dims[1],dims[0]]:dims;
 }
 const h=input.length,w=input[0].length;
 if(ast.type!=='split')return null;
 if(ast.orientation==='horizontal'){
  if(h<3||h%2!==1)return null;
  const n=(h-1)/2,separator=input[n][0];if(!input[n].every(v=>v===separator))return null;
  return [n,w];
 }
 if(ast.orientation==='vertical'){
  if(w<3||w%2!==1)return null;
  const n=(w-1)/2,separator=input[0][n];if(!input.every(r=>r[n]===separator))return null;
  return [h,n];
 }
 return null;
}
function sameDims(a,b){return a!==null&&a[0]===b.length&&a[1]===b[0].length;}
function makeShapeCache(train){
 const cache=new Map();
 for(const ast of allASTs()){
  const key=ast.type==='affine'?['affine',ast.crop,ast.orientation].join('/'):[ast.type,ast.orientation].join('/');
  if(cache.has(key))continue;
  cache.set(key,train.every(pair=>sameDims(outputShape(pair.input,ast),pair.output)));
 }
 return cache;
}
function candidateShapeKey(ast){return ast.type==='affine'?['affine',ast.crop,ast.orientation].join('/'):[ast.type,ast.orientation].join('/');}
function inferTrainPalette(ast,train,trace){
 const counts=new Map(),mapping=new Map();
 for(const pair of train){
  trace.actual_primitive_train_calls++;
  let raw=null;try{raw=primitive(pair.input,ast);}catch(e){}
  if(!valid(raw)||raw.length!==pair.output.length||raw[0].length!==pair.output[0].length){trace.invalid_or_shape_primitive_pruned++;return null;}
  for(let r=0;r<raw.length;r++)for(let c=0;c<raw[0].length;c++){
   const s=raw[r][c],t=pair.output[r][c];
   counts.set(s,(counts.get(s)||0)+1);
   if(mapping.has(s)&&mapping.get(s)!==t){trace.conflict_pruned++;return null;}
   mapping.set(s,t);
  }
 }
 if(ast.mode==='predicate'&&(!mapping.has(0)||!mapping.has(1)))return null;
 for(const count of counts.values())if(count<2)return null;
 return [...mapping].sort((a,b)=>a[0]-b[0]);
}
function propose(train,testInputs){
 const start=Date.now();
 const trace={candidate_ast_count:0,abstract_shape_classes:0,shape_pruned_ast_count:0,actual_primitive_train_calls:0,
  invalid_or_shape_primitive_pruned:0,conflict_pruned:0,training_fit_count:0,test_sample_evaluations:0,
  distinct_test_predictions:0,ambiguous:false,abstention:null,wall_ms:null,representative_ASTs:[],model_forwards:0};
 if(!Array.isArray(train)||!train.length||!train.every(p=>valid(p.input)&&valid(p.output))||!Array.isArray(testInputs)||!testInputs.length||!testInputs.every(valid)){
  trace.abstention='INVALID_INPUT';trace.wall_ms=Date.now()-start;return {prediction:null,trace};
 }
 const shapeCache=makeShapeCache(train);trace.abstract_shape_classes=shapeCache.size;
 let consensus=null,conflict=false;const predictions=new Set();
 for(const ast of allASTs()){
  trace.candidate_ast_count++;
  if(!shapeCache.get(candidateShapeKey(ast))){trace.shape_pruned_ast_count++;continue;}
  const palette=inferTrainPalette(ast,train,trace);
  if(palette===null)continue;
  const program={ast,palette};trace.training_fit_count++;
  const output=[];let works=true;
  for(const x of testInputs){trace.test_sample_evaluations++;let pred=null;try{pred=execute(x,program);}catch(e){}
   if(!valid(pred)){works=false;break;}output.push(pred);
  }
  if(!works){conflict=true;continue;}
  const signature=JSON.stringify(output);predictions.add(signature);
  if(consensus===null)consensus=output;
  else if(JSON.stringify(consensus)!==signature)conflict=true;
  if(trace.representative_ASTs.length<3)trace.representative_ASTs.push({ast,palette});
 }
 trace.distinct_test_predictions=predictions.size;trace.ambiguous=conflict||predictions.size>1;
 if(trace.training_fit_count===0)trace.abstention='NO_TRAIN_CONSISTENT_AST';
 else if(trace.ambiguous)trace.abstention='AMBIGUOUS_PREDICTIONS_OR_UNSUPPORTED_INPUT';
 else if(consensus===null)trace.abstention='NO_VALID_TEST_EXECUTION';
 trace.wall_ms=Date.now()-start;
 return {prediction:trace.abstention===null?consensus:null,trace};
}
function pairedScore(task,baselinePropose,optimizationPropose){
 const inputs=task.test.map(t=>t.input);
 const before=baselinePropose(task.train,inputs),after=optimizationPropose(task.train,inputs);
 const samePred=JSON.stringify(before.prediction)===JSON.stringify(after.prediction);
 const sameAbstain=before.trace.abstention===after.trace.abstention;
 // Original test labels are scored only after BOTH propositions have been constructed.
 const labels=task.test.map(t=>t.output);
 const equal=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((r,i)=>Array.isArray(r)&&r.length===b[i].length&&r.every((v,j)=>v===b[i][j]));
 const exact=p=>p!==null&&p.length===labels.length&&p.every((g,i)=>equal(g,labels[i]));
 return {same_exact_prediction:samePred,same_abstention_reason:sameAbstain,
  P19_correct:exact(before.prediction),P20_correct:exact(after.prediction),
  P19_false_accept:before.prediction!==null&&!exact(before.prediction),P20_false_accept:after.prediction!==null&&!exact(after.prediction),
  P19:before.trace,P20:after.trace,train_count:task.train.length,test_count:task.test.length};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(names,excluded){const ban=new Set(excluded);return names.filter(n=>n.endsWith('.json')&&!ban.has(n)).map(name=>({name,h:fnv32('neumann-q3-p20-20261105|'+name)})).sort((a,b)=>a.h-b.h||a.name.localeCompare(b.name)).slice(0,48).map(x=>x.name);}
export {SPEC,outputShape,propose,pairedScore,cohort};
