/* NEUMANN Q3 P44: ONE source program -> orbit closure under D4 × S10.
 * A source-preserving CLASSICAL program generator, not learned new semantics.
 * Original GPT-6 teacher function SOURCE['aa18de87'] is byte-frozen and
 * applied by conjugation; no new handcrafted gap-filling operation here.
 * Gold labels remain unavailable until after all proposals are frozen.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {SOURCE,valid} from './q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const PRE=path.join(ROOT,'docs/experiments/q3_P44_ONE_SEED_D4_S10_ORBIT_FIRST_PREREG_2026_11_06.json');
const FIRST_HASH=b=>createHash('sha256').update(b).digest('hex');
const gitBlob=b=>createHash('sha1').update(Buffer.concat([
 Buffer.from('blob '+b.length+'\0'),b])).digest('hex');
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const copy=g=>g.map(r=>r.slice());
const transpose=g=>g[0].map((_,c)=>g.map(r=>r[c]));

function palette(b,c){
 if(!Number.isInteger(b)||!Number.isInteger(c)||b<0||c<0||b>9||c>9||b===c)
  throw Error('INVALID_INVERTIBLE_PALETTE');
 const forward=Array(10).fill(-1), inverse=Array(10).fill(-1);
 forward[b]=0;forward[c]=2;
 const freeSource=Array.from({length:10},(_,i)=>i).filter(v=>v!==b&&v!==c);
 const freeTarget=Array.from({length:10},(_,i)=>i).filter(v=>v!==0&&v!==2);
 for(let j=0;j<8;j++)forward[freeSource[j]]=freeTarget[j];
 for(let i=0;i<10;i++)inverse[forward[i]]=i;
 if(new Set(forward).size!==10||inverse.some(x=>x<0)||
    forward[b]!==0||forward[c]!==2)
  throw Error('NONBIJECTIVE_PALETTE');
 return {forward,inverse};
}
function conjugateSeed(axis,b,c,seed=SOURCE['aa18de87']){
 if(!['row','column'].includes(axis)||typeof seed!=='function')
  throw Error('BAD_SEED_OR_ORIENTATION');
 const {forward,inverse}=palette(b,c);
 return g=>{
  if(!valid(g))return null;
  const canonical=axis==='column'?transpose(g):copy(g);
  const normalized=canonical.map(row=>row.map(v=>forward[v]));
  const transformed=seed(normalized);
  if(!valid(transformed)||transformed.length!==normalized.length||
    transformed[0].length!==normalized[0].length)return null;
  const decoded=transformed.map(row=>row.map(v=>inverse[v]));
  return axis==='column'?transpose(decoded):decoded;
 };
}
function makeFamily(seed=SOURCE['aa18de87']){
 const result=[];
 for(const axis of ['row','column'])
  for(let b=0;b<=9;b++)
   for(let c=0;c<=9;c++)if(b!==c)
    result.push({axis,b,c,
      key:axis+'/background:'+b+'/fill:'+c,
      program:conjugateSeed(axis,b,c,seed)});
 if(result.length!==180)throw Error('EXPECTED_180_ORBIT_QUOTIENT_PROGRAMS');
 return result;
}

function proposer(train,testInputs,variants){
 const admitted=[],failures=[];
 let trainExecutions=0,testExecutions=0,matchedAfterTrain=0;
 // No TEST gold available in this function. One score for all exact-TRAIN
 // sources; conflicting distinct predictions => explicit ABSTAIN.
 for(const variant of variants){
  let fit=true,anyNontrivial=false;
  for(const pair of train){
   trainExecutions++;
   let predicted;
   try{predicted=variant.program(copy(pair.input));}
   catch(e){fit=false;break;}
   if(!valid(predicted)||!eq(predicted,pair.output)){fit=false;break;}
   if(!eq(predicted,pair.input))anyNontrivial=true;
  }
  if(!fit||!anyNontrivial)continue;
  matchedAfterTrain++;
  const preds=[];
  let good=true;
  for(const input of testInputs){
   testExecutions++;
   try{
    const predicted=variant.program(copy(input));
    if(!valid(predicted)){good=false;break;}
    preds.push(predicted);
   }catch(e){good=false;break;}
  }
  if(!good){failures.push(variant.key);continue;}
  admitted.push({
   key:variant.key,axis:variant.axis,b:variant.b,c:variant.c,
   preds
  });
 }
 const unique=new Map(admitted.map(x=>[JSON.stringify(x.preds),x.preds]));
 const ambiguous=unique.size>1;
 const prediction=unique.size===1?[...unique.values()][0]:null;
 return {
  prediction,
  accepted_programs:admitted.map(({key,axis,b,c})=>({key,axis,b,c})),
  ambiguous,
  train_semantic_fits:matchedAfterTrain,
  submitted:prediction!==null,
  train_executions:trainExecutions,
  test_executions:testExecutions,
  invalid_source_outputs:failures
 };
}

function run(arcRoot,p30Path,p43Path){
 const pre=JSON.parse(fs.readFileSync(PRE,'utf8'));
 const teacherFile=path.join(ROOT,pre.single_seed.path);
 const teacherSHA=gitBlob(fs.readFileSync(teacherFile));
 if(teacherSHA!==pre.single_seed.git_blob)throw Error('P22_SEED_SOURCE_SHA_DRIFT');
 const firstP30=fs.readFileSync(p30Path),firstP43=fs.readFileSync(p43Path);
 const hash30=FIRST_HASH(firstP30),hash43=FIRST_HASH(firstP43);
 if(hash30!==pre.originals.baseline_original_p30_sha256)
  throw Error('STRONG_CLASSICAL_FIRST_SHA_DRIFT');
 if(hash43!==pre.originals.baseline_original_p43_sha256)
  throw Error('P43_SINGLE_SEED_FIRST_SHA_DRIFT');
 const old30=JSON.parse(firstP30),old43=JSON.parse(firstP43);
 if(old30.rows?.length!==400||old43.rows?.length!==400||
    old30.stats.new_safe_combined_exact!==54||
    old43.stats.teacher_original_exact!==1||
    old43.stats.teacher_wrong_submitted!==0)
  throw Error('REFERENCE_CASES_NOT_AS_FROZEN');
 if(typeof SOURCE[pre.single_seed.name]!=='function')
  throw Error('SINGLE_SEED_ABSENT');
 const family=makeFamily(SOURCE[pre.single_seed.name]);
 const dir=path.join(arcRoot,pre.originals.scope);
 const names=fs.readdirSync(dir).filter(n=>n.endsWith('.json')).sort();
 if(names.length!==400||names.some((name,i)=>old30.rows[i].id!==name||old43.rows[i].id!==name))
  throw Error('ORIGINAL_PUBLIC_400_TASK_SET_CHANGED');
 const begin=process.hrtime.bigint(),beginCpu=process.cpuUsage();
 const rows=[];
 for(let i=0;i<names.length;i++){
  const task=JSON.parse(fs.readFileSync(path.join(dir,names[i]),'utf8'));
  if(!Array.isArray(task.train)||task.train.length<1||!Array.isArray(task.test)||
    task.test.length<1)throw Error('INVALID_OFFICIAL_ORIGINAL');
  const train=task.train.map(p=>({input:p.input,output:p.output}));
  const inputs=task.test.map(p=>p.input);
  const proposal=proposer(train,inputs,family);
  // Original TEST gold can be accessed ONLY after the fixed source program
  // has completed all training selections and TEST predictions.
  const gold=task.test.map(p=>p.output);
  const correct=proposal.submitted&&proposal.prediction.length===gold.length&&
    proposal.prediction.every((g,j)=>eq(g,gold[j]));
  const prior30correct=old30.rows[i].safe_exact;
  const prior43correct=old43.rows[i].teacher_original_exact;
  const previouslyCorrect=prior30correct||prior43correct;
  rows.push({
   id:names[i],
   p30_correct:prior30correct,p43_correct:prior43correct,
   prior_correct_oracle_set:previouslyCorrect,
   p44_submitted:proposal.submitted,
   p44_correct:correct,
   p44_wrong:proposal.submitted&&!correct,
   p44_new_exact_over_both:correct&&!previouslyCorrect,
   p44_ambiguous:proposal.ambiguous,
   p44_train_semantic_fits:proposal.train_semantic_fits,
   p44_candidate_programs:proposal.accepted_programs,
   p44_prediction_sha256:proposal.submitted?FIRST_HASH(Buffer.from(JSON.stringify(proposal.prediction))):null,
   train_program_executions:proposal.train_executions,
   test_input_program_executions:proposal.test_executions,
   invalid_source_outputs:proposal.invalid_source_outputs
  });
 }
 const cpu=process.cpuUsage(beginCpu);
 const count=k=>rows.filter(r=>r[k]).length;
 const newly=rows.filter(r=>r.p44_new_exact_over_both);
 const newNonidentity=newly.some(r=>r.p44_candidate_programs.some(p=>
    p.axis==='column'||p.b!==0||p.c!==2));
 const stats={
  original_tasks:rows.length,
  teacher_seed_programs:1,
  group_orbit_distinct_candidate_programs:family.length,
  historical_p30_correct:count('p30_correct'),
  historical_p43_correct:count('p43_correct'),
  historical_oracle_union_correct:count('prior_correct_oracle_set'),
  p44_submitted:count('p44_submitted'),
  p44_exact:count('p44_correct'),
  p44_wrong:count('p44_wrong'),
  p44_new_original_exact_vs_p30_and_p43:count('p44_new_exact_over_both'),
  p44_ambiguous:count('p44_ambiguous'),
  new_nonidentity_axis_or_palette_used:newNonidentity,
  total_train_program_executions:rows.reduce((s,r)=>s+r.train_program_executions,0),
  total_test_input_program_executions:rows.reduce((s,r)=>s+r.test_input_program_executions,0),
  cpu_ms:(cpu.user+cpu.system)/1000,
  wall_ms:Number(process.hrtime.bigint()-begin)/1e6,
  oracle_union_correct_upper_bound:rows.filter(r=>r.prior_correct_oracle_set||r.p44_correct).length
 };
 const passed=stats.p44_new_original_exact_vs_p30_and_p43>=2&&
   stats.p44_wrong===0&&stats.new_nonidentity_axis_or_palette_used;
 return {
  schema:'neumann.q3.p44.single-seed-D4-S10-orbit-first.v1',
  science_status:passed?'SCOPED_ONE_SEED_ORBIT_REUSE_PASS':'SCOPED_ONE_SEED_ORBIT_REUSE_FAIL',
  source_original_seed_git_blob:teacherSHA,
  original_p30_first_sha256:hash30,
  original_p43_first_sha256:hash43,
  original_arc_commit:pre.originals.commit,
  previous_seed_case:pre.single_seed.origin_first_verified_transfer_task,
  generated_from_original_seed_only:true,
  separate_generated_new_handwritten_operators:0,
  classical_conjugation_search_equal_rights:true,
  original_test_gold_processed_only_after_proposals:true,
  arc_evaluation_IDs_consumed:0,
  real_independent_external_formalism:false,
  neural_program_synthesis_calls:0,
  teacher_training_costs:'NOT_METERED',
  Q3_NEUMANN_AUTONOMOUS_INVENTION:'NOT_PROVEN',
  Q4_10X_LIFECYCLE:'NOT_PROVEN',
  Q6_CROSS_FORMALISM:'NOT_PROVEN',
  Q7_FRONTIER:'NOT_PROVEN',
  stats,rows
 };
}
export {palette,transpose,conjugateSeed,makeFamily,proposer,run};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==5){
  console.error('usage: node q3_p44_one_seed_orbit_FIRST.mjs ARC_ROOT P30_FIRST P43_FIRST');
  process.exitCode=2;
 }else try{
  const result=run(process.argv[2],process.argv[3],process.argv[4]);
  console.log(JSON.stringify(result,null,2));
 }catch(error){console.error(String(error.stack||error));process.exitCode=1;}
}
