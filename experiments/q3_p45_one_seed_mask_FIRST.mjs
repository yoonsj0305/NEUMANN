/* Q3 P45 ONE frozen program, new type adapter: mask projection + merge.
 * The only problem-solving kernel is original source SOURCE['aa18de87'].
 * Generic mask/merge code is HUMAN-AUTHORED classical structure synthesis.
 * Source-preregistered 400 ORIGINAL PUBLIC ARC TRAIN, not fresh unseen ARC eval.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {SOURCE,valid} from './q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const PRE=path.join(ROOT,'docs/experiments/q3_P45_ONE_SEED_MASK_LIFT_FIRST_PREREG_2026_11_06.json');
const sha=x=>createHash('sha256').update(x).digest('hex');
const gitblob=x=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+x.length+'\0'),x])).digest('hex');
const clone=g=>g.map(r=>r.slice());
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const transpose=g=>g[0].map((_,col)=>g.map(r=>r[col]));

function applyMaskLifting(input,{axis,b,c,marker},kernel=SOURCE['aa18de87']){
 if(!valid(input)||!['row','column'].includes(axis)||!Number.isInteger(b)||
    !Number.isInteger(c)||b===c||b<0||b>9||c<0||c>9||
    (marker!=='ANY'&&(!Number.isInteger(marker)||marker<0||marker>9||marker===b))||
    typeof kernel!=='function')return null;
 const raw=axis==='column'?transpose(input):clone(input);
 // SOURCE receives normalized binary mask, not a new geometric operator.
 const mask=raw.map(row=>row.map(v=>(marker==='ANY'?v!==b:v===marker)?1:0));
 const changed=kernel(mask);
 if(!valid(changed)||changed.length!==mask.length||
     changed[0].length!==mask[0].length)return null;
 const out=raw.map((row,i)=>row.map((old,j)=>
   old===b&&mask[i][j]===0&&changed[i][j]===2?c:old));
 return axis==='column'?transpose(out):out;
}

function inferSourceDelta(train){
 let b=null,c=null,changed=0;
 for(const pair of train){
  if(!valid(pair.input)||!valid(pair.output)||pair.input.length!==pair.output.length||
     pair.input[0].length!==pair.output[0].length)return null;
  for(let i=0;i<pair.input.length;i++)for(let j=0;j<pair.input[0].length;j++){
   const x=pair.input[i][j],y=pair.output[i][j];
   if(x===y)continue;
   changed++;
   if(b===null){b=x;c=y;}
   else if(b!==x||c!==y)return null;
  }
 }
 if(changed===0||b===c)return null;
 return {b,c,changed};
}

function propose(train,testInputs,kernel=SOURCE['aa18de87']){
 const delta=inferSourceDelta(train);
 if(delta===null)return {
  submitted:false,prediction:null,reason:'NO_UNIFORM_NONTRIVIAL_SOURCE_DELTA',
  fitting:[],ambiguous:false,trainRuns:0,testRuns:0,sourceDelta:null
 };
 const {b,c}=delta;
 const markers=['ANY',...Array.from({length:10},(_,i)=>i).filter(m=>m!==b)];
 const candidates=[],errors=[];
 let trainRuns=0,testRuns=0;
 for(const axis of ['row','column'])for(const marker of markers){
  const p={axis,b,c,marker};
  let trainFit=true;
  for(const pair of train){
   trainRuns++;
   let pred=null;
   try{pred=applyMaskLifting(clone(pair.input),p,kernel);}
   catch(e){trainFit=false;break;}
   if(pred===null||!eq(pred,pair.output)){trainFit=false;break;}
  }
  if(!trainFit)continue;
  const preds=[];
  let good=true;
  for(const grid of testInputs){
   testRuns++;
   try{
    const pred=applyMaskLifting(clone(grid),p,kernel);
    if(!valid(pred)){good=false;break;}
    preds.push(pred);
   }catch(e){good=false;break;}
  }
  if(!good){errors.push(p);continue;}
  candidates.push({axis,b,c,marker,predictions:preds});
 }
 const different=new Map(candidates.map(x=>[JSON.stringify(x.predictions),x.predictions]));
 const prediction=different.size===1?[...different.values()][0]:null;
 return {
  submitted:prediction!==null,prediction,
  reason:prediction!==null?'EXACT_TRAIN_AND_UNANIMOUS_TEST':(
    different.size>1?'AMBIGUOUS_TEST_PREDICTIONS':'NO_FITTING_MODEL'),
  fitting:candidates.map(({axis,b,c,marker})=>({axis,b,c,marker})),
  ambiguous:different.size>1,trainRuns,testRuns,sourceDelta:delta,
  failures:errors
 };
}

function run(arcRoot,p30Path,p43Path,p44Path){
 const pre=JSON.parse(fs.readFileSync(PRE,'utf8'));
 const seedSha=gitblob(fs.readFileSync(path.join(ROOT,pre.provenance.seed_file)));
 if(seedSha!==pre.provenance.seed_git_blob)throw Error('FROZEN_P22_SEED_GIT_BLOB_DRIFT');
 const bytes30=fs.readFileSync(p30Path),bytes43=fs.readFileSync(p43Path),bytes44=fs.readFileSync(p44Path);
 const h30=sha(bytes30),h43=sha(bytes43),h44=sha(bytes44);
 if(h30!==pre.provenance.historical_P30_first_sha256||
    h43!==pre.provenance.historical_P43_first_sha256||
    h44!==pre.provenance.historical_P44_first_sha256)
  throw Error('HISTORICAL_IMMUTABLE_FIRST_SHA_DRIFT');
 const old30=JSON.parse(bytes30),old43=JSON.parse(bytes43),old44=JSON.parse(bytes44);
 if(old30.rows?.length!==400||old43.rows?.length!==400||old44.rows?.length!==400||
     old30.stats.new_safe_combined_exact!==54||
     old43.stats.teacher_original_exact!==1||
     old44.stats.p44_exact!==1||
     old44.stats.p44_new_original_exact_vs_p30_and_p43!==0)
  throw Error('HISTORICAL_PRIOR_COHORT_OR_SCIENCE_DRIFT');
 const originals=path.join(arcRoot,'data/training');
 const ids=fs.readdirSync(originals).filter(x=>x.endsWith('.json')).sort();
 if(ids.length!==400||ids.some((id,i)=>old30.rows[i].id!==id||
     old43.rows[i].id!==id||old44.rows[i].id!==id))
  throw Error('SOURCE_400_TASK_ORDER_CHANGED');
 if(typeof SOURCE[pre.provenance.seed_function]!=='function')
  throw Error('MISSING_FROZEN_SEED_PROGRAM');
 const kernel=SOURCE[pre.provenance.seed_function];
 const rows=[],begin=process.hrtime.bigint(),cpu0=process.cpuUsage();
 for(let i=0;i<ids.length;i++){
  const task=JSON.parse(fs.readFileSync(path.join(originals,ids[i]),'utf8'));
  if(!Array.isArray(task.train)||task.train.length===0||
     !Array.isArray(task.test)||task.test.length===0)
   throw Error('INVALID_OFFICIAL_ARC_TASK');
  const train=task.train.map(({input,output})=>({input,output}));
  const testInputs=task.test.map(({input})=>input);
  const p=propose(train,testInputs,kernel);
  // This is the only original TEST gold touch: proposals all already frozen.
  const gold=task.test.map(({output})=>output);
  const correct=p.submitted&&p.prediction.length===gold.length&&
    p.prediction.every((v,j)=>eq(v,gold[j]));
  const previous=old30.rows[i].safe_exact||old43.rows[i].teacher_original_exact||
    old44.rows[i].p44_correct;
  rows.push({
    id:ids[i],prior_original_correct:previous,
    p45_submitted:p.submitted,p45_correct:correct,
    p45_wrong:p.submitted&&!correct,p45_new_exact:correct&&!previous,
    p45_delta:p.sourceDelta,p45_candidate_programs:p.fitting,
    p45_reason:p.reason,p45_ambiguous:p.ambiguous,
    p45_prediction_sha256:p.submitted?sha(Buffer.from(JSON.stringify(p.prediction))):null,
    train_program_executions:p.trainRuns,test_input_program_executions:p.testRuns
  });
 }
 const cpu=process.cpuUsage(cpu0),count=k=>rows.filter(r=>r[k]).length;
 const newRows=rows.filter(r=>r.p45_new_exact);
 const eligibleSpecific=newRows.some(r=>r.p45_candidate_programs.some(p=>p.marker!=='ANY'));
 const stats={
  tasks:rows.length,seed_sources:1,
  total_generic_programs:1800,
  original_historical_oracle_upper_bound:55,
  p45_submitted:count('p45_submitted'),p45_correct:count('p45_correct'),
  p45_wrong:count('p45_wrong'),p45_new_exact_beyond_prior55:count('p45_new_exact'),
  p45_ambiguous:count('p45_ambiguous'),
  p45_source_delta_eligible:rows.filter(r=>r.p45_delta!==null).length,
  new_correct_uses_selective_marker:eligibleSpecific,
  oracle_union_correct_upper_bound:rows.filter(r=>r.prior_original_correct||r.p45_correct).length,
  total_train_program_executions:rows.reduce((a,r)=>a+r.train_program_executions,0),
  total_test_input_program_executions:rows.reduce((a,r)=>a+r.test_input_program_executions,0),
  cpu_ms:(cpu.user+cpu.system)/1000,
  wall_ms:Number(process.hrtime.bigint()-begin)/1e6
 };
 const passed=stats.p45_new_exact_beyond_prior55>=2&&
     stats.p45_wrong===0&&eligibleSpecific;
 return {
  schema:'neumann.q3.p45.single-seed-mask-project-merge-first.v1',
  science_status:passed?'SCOPED_ONE_SEED_MASK_LIFT_PASS':'SCOPED_ONE_SEED_MASK_LIFT_FAIL',
  original_frozen_seed_git_blob:seedSha,
  original_P30_first_sha256:h30,original_P43_first_sha256:h43,
  original_P44_first_sha256:h44,
  source_original:'fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34/data/training',
  original_400_public_already_opened:true,
  original_gold_not_available_to_generator:true,
  learned_neural_semantic_policies_called:0,
  new_human_typed_adapters:1,
  historical_external_teacher_token_cost:'NOT_METERED',
  arc_evaluation_IDs_consumed:0,
  Q3_NEUMANN_LEARNED_NEW_STRUCTURE:'NOT_PROVEN',
  Q4_10X_ALL_IN:'NOT_PROVEN',
  Q6_EXTERNAL_FORMALISM:'NOT_PROVEN',
  Q7_FRONTIER:'NOT_PROVEN',
  stats,rows
 };
}
export {applyMaskLifting,inferSourceDelta,propose,run};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==6){
  console.error('usage: node q3_p45_one_seed_mask_FIRST.mjs ARC_ROOT P30_FIRST P43_FIRST P44_FIRST');
  process.exitCode=2;
 }else try{console.log(JSON.stringify(run(...process.argv.slice(2)),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
