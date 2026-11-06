/* Q3 P45 pinned FIRST audit. An independent implementation of the
 * mathematical mask/merge source language. Never imports P45 proposal code
 * or reruns it, but does score the immutable original 400 again.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const PIN={
 p45:'38e41ddd312eb451745f2d73194840e98464e9660d14c52c30537fb7e30bfff5',
 p44:'8efe48796c15f8f322124afa6751dca1ea7816c93e038e4a38b90d08dcc3e639',
 p43:'8b5cb4927133930f6238adb17dbeba5a73d6955a368965b67318cc6aca78a398',
 p30:'0fb747b4fd7355649465b8ff3424c0170d6d178f47fd1ea64ca486c416672b79',
 seed:'d82f09406b4b3ee4e9651c261013c8ce8aa850c7'
};
const sha=x=>createHash('sha256').update(x).digest('hex');
const blob=x=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+x.length+'\0'),x])).digest('hex');
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const shape=g=>Array.isArray(g)&&g.length>0&&g.length<=30&&
   Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&
   g.every(row=>Array.isArray(row)&&row.length===g[0].length&&
     row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));

function independentDelta(task){
 let source=-1,destination=-1,total=0;
 for(const pair of task.train){
  const a=pair.input,b=pair.output;
  if(!shape(a)||!shape(b)||a.length!==b.length||a[0].length!==b[0].length)
   return null;
  for(let y=0;y<a.length;y++)for(let x=0;x<a[0].length;x++){
   if(a[y][x]===b[y][x])continue;
   if(source===-1){source=a[y][x];destination=b[y][x];}
   if(a[y][x]!==source||b[y][x]!==destination)return null;
   total++;
  }
 }
 if(total===0||source===destination)return null;
 return {b:source,c:destination,changed:total};
}
function independentMask(input,params){
 const {axis,b,c,marker}=params;
 if(!shape(input))return null;
 const H=input.length,W=input[0].length;
 const out=input.map(row=>row.slice());
 const lines=axis==='row'?H:W;
 const length=axis==='row'?W:H;
 for(let line=0;line<lines;line++){
  let first=-1,last=-1;
  for(let n=0;n<length;n++){
   const pixel=(axis==='row')?input[line][n]:input[n][line];
   const selected=marker==='ANY'?pixel!==b:pixel===marker;
   if(selected){
    if(first===-1)first=n;
    last=n;
   }
  }
  if(first<0||last<=first)continue;
  for(let n=first+1;n<last;n++){
   const y=axis==='row'?line:n,x=axis==='row'?n:line;
   if(input[y][x]===b)out[y][x]=c;
  }
 }
 return out;
}
function independentCandidates(task){
 const d=independentDelta(task);
 if(!d)return {delta:null,fitting:[],pred:null,trainN:0,testN:0,ambiguous:false,
  reason:'NO_UNIFORM_NONTRIVIAL_SOURCE_DELTA'};
 const fitting=[];let trainN=0,testN=0;
 for(const axis of ['row','column']){
  const markers=['ANY',...Array.from({length:10},(_,i)=>i).filter(x=>x!==d.b)];
  for(const marker of markers){
   const p={axis,b:d.b,c:d.c,marker};
   let pass=true;
   for(const example of task.train){
    trainN++;
    if(!eq(independentMask(example.input,p),example.output)){
     pass=false;break;
    }
   }
   if(!pass)continue;
   const predictions=task.test.map(ex=>{testN++;return independentMask(ex.input,p);});
   if(predictions.some(p=>!shape(p)))continue;
   fitting.push({p,predictions});
  }
 }
 const uniq=new Map(fitting.map(x=>[JSON.stringify(x.predictions),x.predictions]));
 const ambiguous=uniq.size>1;
 const pred=uniq.size===1?[...uniq.values()][0]:null;
 return {
  delta:d,fitting:fitting.map(x=>x.p),pred,trainN,testN,ambiguous,
  reason:pred!==null?'EXACT_TRAIN_AND_UNANIMOUS_TEST':
     ambiguous?'AMBIGUOUS_TEST_PREDICTIONS':'NO_FITTING_MODEL'
 };
}

function audit(arcRoot,p45File,p44File,p43File,p30File){
 const errors=[];
 const read=(file,shaExpected,name)=>{
  const raw=fs.readFileSync(file),actual=sha(raw);
  if(actual!==shaExpected)errors.push('FIRST_IMMUTABLE_SHA_MISMATCH_'+name);
  return {raw,json:JSON.parse(raw),sha:actual};
 };
 const f45=read(p45File,PIN.p45,'P45'),f44=read(p44File,PIN.p44,'P44'),
   f43=read(p43File,PIN.p43,'P43'),f30=read(p30File,PIN.p30,'P30');
 const seed=blob(fs.readFileSync(path.join(ROOT,'experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs')));
 if(seed!==PIN.seed)errors.push('FROZEN_ONE_SEED_CHANGED');
 const original=path.join(arcRoot,'data/training');
 const ids=fs.readdirSync(original).filter(x=>x.endsWith('.json')).sort();
 if(ids.length!==400||[f45,f44,f43,f30].some(x=>x.json.rows?.length!==400))
  throw Error('DENOMINATOR_NOT_400');
 let eligible=0,fits=0,submitted=0,exact=0,wrong=0,newSuccess=0,trainRuns=0,testRuns=0,ambiguous=0;
 const successes=[],failure_reasons={};
 for(let i=0;i<400;i++){
  const id=ids[i],row=f45.json.rows[i];
  if([f45,f44,f43,f30].some(x=>x.json.rows[i].id!==id)){
   errors.push('ROW_IDENTIFIER_MISMATCH_'+id);
   continue;
  }
  const originalTask=JSON.parse(fs.readFileSync(path.join(original,id),'utf8'));
  const p=independentCandidates(originalTask);
  eligible+=Number(p.delta!==null);
  fits+=Number(p.fitting.length>0);
  submitted+=Number(p.pred!==null);
  ambiguous+=Number(p.ambiguous);
  trainRuns+=p.trainN;testRuns+=p.testN;
  const correct=p.pred!==null&&eq(p.pred,originalTask.test.map(x=>x.output));
  const prior=f30.json.rows[i].safe_exact||f43.json.rows[i].teacher_original_exact||
    f44.json.rows[i].p44_correct;
  const additional=correct&&!prior;
  exact+=Number(correct);wrong+=Number(p.pred!==null&&!correct);
  newSuccess+=Number(additional);
  failure_reasons[p.reason]=(failure_reasons[p.reason]||0)+1;
  if(correct)successes.push({id,parameters:p.fitting,new_over_frozen_historical_55:additional});
  const expected={
   prior_original_correct:prior,p45_submitted:p.pred!==null,
   p45_correct:correct,p45_wrong:p.pred!==null&&!correct,
   p45_new_exact:additional,p45_delta:p.delta,
   p45_candidate_programs:p.fitting,p45_reason:p.reason,
   p45_ambiguous:p.ambiguous,
   p45_prediction_sha256:p.pred!==null?sha(Buffer.from(JSON.stringify(p.pred))):null,
   train_program_executions:p.trainN,test_input_program_executions:p.testN
  };
  for(const [k,v] of Object.entries(expected)){
   if(!eq(row[k],v))errors.push('P45_ORIGINAL_SOURCE_ROW_MISMATCH_'+id+'_'+k);
  }
 }
 const s=f45.json.stats;
 const aggregates={
  tasks:400,seed_sources:1,total_generic_programs:1800,
  original_historical_oracle_upper_bound:55,
  p45_submitted:submitted,p45_correct:exact,p45_wrong:wrong,
  p45_new_exact_beyond_prior55:newSuccess,
  p45_ambiguous:ambiguous,
  p45_source_delta_eligible:eligible,
  oracle_union_correct_upper_bound:55+newSuccess,
  total_train_program_executions:trainRuns,
  total_test_input_program_executions:testRuns
 };
 for(const [key,value] of Object.entries(aggregates))
  if(s[key]!==value)errors.push('P45_FIRST_AGGREGATE_MISMATCH_'+key);
 if(f45.json.science_status!=='SCOPED_ONE_SEED_MASK_LIFT_FAIL')
  errors.push('FALSE_SCIENCE_PASS_PROMOTED');
 if(f45.json.Q3_NEUMANN_LEARNED_NEW_STRUCTURE!=='NOT_PROVEN'||
    f45.json.Q6_EXTERNAL_FORMALISM!=='NOT_PROVEN'||
    f45.json.arc_evaluation_IDs_consumed!==0)
  errors.push('GLOBAL_GATE_OVERCLAIM');
 return {
  schema:'neumann.q3.p45.one-seed-mask-first-independent-original400-audit.v1',
  audit_pass:errors.length===0,
  errors:errors.slice(0,25),error_count:errors.length,
  original_P45_sha256:f45.sha,
  prior_sha256:{P44:f44.sha,P43:f43.sha,P30:f30.sha},
  frozen_teacher_program_git_blob:seed,
  independent_400_originals:400,
  mask_adapter_derived_hypotheses:1800,
  unique_original_train_candidate_fits:fits,
  eligible_uniform_delta_originals:eligible,
  independently_scored_original_successes:exact,
  independent_submitted:submitted,independent_wrong:wrong,
  independent_new_exact_beyond_prior55:newSuccess,
  source_400_original_success_rows:successes,
  per_case_breakdown:failure_reasons,
  independent_train_runs:trainRuns,independent_test_runs:testRuns,
  imported_first_generation_runner:false,
  original_arc_evaluation_consumed:0,
  global_Q3:'OPEN',global_Q6:'OPEN'
 };
}
export {independentMask,independentDelta,independentCandidates,audit};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==7){
  console.error('usage: node P45_READONLY.mjs ARC_ROOT P45_FIRST P44_FIRST P43_FIRST P30_FIRST');
  process.exitCode=2;
 }else try{
  const x=audit(...process.argv.slice(2));
  console.log(JSON.stringify(x,null,2));
  if(!x.audit_pass)process.exitCode=1;
 }catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
