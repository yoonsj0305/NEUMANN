/* P45 decisive bounded completeness certificate, AFTER original FIRST.
 * Exhausts ALL 1800 human-supplied one-kernel mask/merge programs on
 * each of 400 public ARC TRAIN tasks WITHOUT source-delta prepruning.
 * Never imports P45 first runner, P45 alternate selector, or original P22
 * executable seed, so this is independent direct mathematical semantics.
 * This is a conditional *fixed hypothesis class* bound, NOT general AI.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const FIRST_SHA='38e41ddd312eb451745f2d73194840e98464e9660d14c52c30537fb7e30bfff5';
const SEED_BLOB='d82f09406b4b3ee4e9651c261013c8ce8aa850c7';
const sha=x=>createHash('sha256').update(x).digest('hex');
const blob=x=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+x.length+'\0'),x])).digest('hex');
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
function valid(g){
 return Array.isArray(g)&&g.length>=1&&g.length<=30&&
  Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&
  g.every(r=>Array.isArray(r)&&r.length===g[0].length&&
    r.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
}
function independentMask(g,axis,b,c,marker){
 const out=g.map(r=>r.slice()),H=g.length,W=g[0].length;
 const L=axis==='row'?H:W,P=axis==='row'?W:H;
 for(let line=0;line<L;line++){
  let first=-1,last=-1;
  for(let position=0;position<P;position++){
   const color=axis==='row'?g[line][position]:g[position][line];
   const selected=marker==='ANY'?(color!==b):(color===marker);
   if(selected){if(first===-1)first=position;last=position;}
  }
  if(last<=first)continue;
  for(let j=first+1;j<last;j++){
   const row=axis==='row'?line:j,col=axis==='row'?j:line;
   if(g[row][col]===b)out[row][col]=c;
  }
 }
 return out;
}
function originalDelta(train){
 let first=null,changed=0;
 for(const pair of train){
  if(!valid(pair.input)||!valid(pair.output)||pair.input.length!==pair.output.length||
     pair.input[0].length!==pair.output[0].length)return null;
  for(let y=0;y<pair.input.length;y++)for(let x=0;x<pair.input[0].length;x++){
   const a=pair.input[y][x],b=pair.output[y][x];
   if(a===b)continue;
   changed++;
   if(first===null)first={b:a,c:b};
   else if(first.b!==a||first.c!==b)return null;
  }
 }
 return changed?{...first,changed}:null;
}
function completeTrainEnumeration(train){
 let candidateTuples=0,sourceCalls=0;
 const fit=[];
 const hadChanges=train.some(pair=>!eq(pair.input,pair.output));
 // No inference: every one of 2*10*9*10 possibilities is still visited.
 for(const axis of ['row','column']){
  for(let b=0;b<10;b++)for(let c=0;c<10;c++){
   if(b===c)continue;
   for(const marker of ['ANY',...Array.from({length:10},(_,i)=>i).filter(m=>m!==b)]){
    candidateTuples++;
    let exact=true;
    for(const pair of train){
     sourceCalls++;
     if(!eq(independentMask(pair.input,axis,b,c,marker),pair.output)){
      exact=false;break;
     }
    }
    if(exact&&hadChanges)fit.push({axis,b,c,marker});
   }
  }
 }
 if(candidateTuples!==1800)throw Error('ENTIRE_HYPOTHESIS_SPACE_NOT_VISITED');
 return {candidateTuples,sourceCalls,fit};
}
function audit(arcRoot,p45First){
 const raw=fs.readFileSync(p45First),firstHash=sha(raw);
 if(firstHash!==FIRST_SHA)throw Error('ORIGINAL_IMMUTABLE_P45_FIRST_SHA_DRIFT');
 const original=JSON.parse(raw);
 if(original.science_status!=='SCOPED_ONE_SEED_MASK_LIFT_FAIL'||
    original.stats?.p45_correct!==1||original.stats?.p45_new_exact_beyond_prior55!==0||
    original.stats?.tasks!==400||original.rows?.length!==400)
  throw Error('ORIGINAL_P45_FIRST_SCIENCE_OR_DENOMINATOR_DRIFT');
 const source=fs.readFileSync(path.join(ROOT,'experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs'));
 if(blob(source)!==SEED_BLOB)throw Error('FROZEN_ONE_SOURCE_PROGRAM_BLOB_DRIFT');
 const originalDir=path.join(arcRoot,'data/training');
 const names=fs.readdirSync(originalDir).filter(n=>n.endsWith('.json')).sort();
 if(names.length!==400)throw Error('SOURCE_DENOMINATOR_NOT_400');
 let pairs=0,sourceCalls=0,eligible=0,zeroFitEligible=0,uneligible=0,fullFitTasks=0;
 let matchingTuples=0;
 const originalRows=[];
 const begun=process.hrtime.bigint(),cpu0=process.cpuUsage();
 for(let i=0;i<names.length;i++){
  const task=JSON.parse(fs.readFileSync(path.join(originalDir,names[i]),'utf8'));
  if(!Array.isArray(task.train)||task.train.length<1||
     !task.train.every(p=>valid(p.input)&&valid(p.output)))
   throw Error('BAD_OFFICIAL_ARC_TRAIN_'+names[i]);
  const delta=originalDelta(task.train);
  const result=completeTrainEnumeration(task.train);
  pairs+=result.candidateTuples;
  sourceCalls+=result.sourceCalls;
  eligible+=Number(delta!==null);
  uneligible+=Number(delta===null);
  zeroFitEligible+=Number(delta!==null&&result.fit.length===0);
  fullFitTasks+=Number(result.fit.length>0);
  matchingTuples+=result.fit.length;
  if((result.fit.length>0)!==(original.rows[i].p45_candidate_programs.length>0)||
     !eq(result.fit,original.rows[i].p45_candidate_programs)||
     original.rows[i].id!==names[i]||
     !eq(delta,original.rows[i].p45_delta))
   throw Error('FIRST_VERSUS_FULL_ENUMERATION_ROW_DRIFT_'+names[i]);
  if(result.fit.length>0)originalRows.push({
    id:names[i],all_1800_exhaustive_fit_programs:result.fit,
    previous_scored_correct:original.rows[i].p45_correct,
    new_beyond_prior55:original.rows[i].p45_new_exact
  });
 }
 const cpu=process.cpuUsage(cpu0);
 const testPositive=[{input:[[3,0,4,0,3]],output:[[3,2,4,2,3]]}];
 const testContradictory=[{input:[[3,0,4,0,3]],output:[[3,2,4,5,3]]}];
 const positive=completeTrainEnumeration(testPositive),negative=completeTrainEnumeration(testContradictory);
 const passed=(pairs===720000&&uneligible===337&&eligible===63&&zeroFitEligible===62&&
   fullFitTasks===1&&originalRows.length===1&&
   originalRows[0].id==='a699fb00.json'&&
   originalRows[0].previous_scored_correct&&
   !originalRows[0].new_beyond_prior55&&
   positive.fit.length>0&&negative.fit.length===0);
 return {
  schema:'neumann.q3.p45.complete-1800-fixed-language-bound-audit.v1',
  scientific_status:passed?'FIXED_LANGUAGE_TRAIN_CEILING_CERTIFIED':'FIXED_LANGUAGE_TRAIN_CEILING_NOT_CERTIFIED',
  audit_pass:passed,
  original_P45_first_SHA256:firstHash,
  frozen_original_external_teacher_git_blob:blob(source),
  model_family:'ONE_FROZEN_TEACHER_SOURCE_MASK_MERGE_2_AXES_10_BACKGROUND_9_FILL_10_MARKERS',
  source_scope:'400 PREVIOUSLY OPENED PUBLIC ARC-AGI-1 TRAIN TASKS',
  original_source_commit:'399030444e0ab0cc8b4e199870fb20b863846f34',
  potential_candidate_programs_per_task:1800,
  independent_exhaustive_candidate_task_pairs:pairs,
  total_original_train_program_evaluations:sourceCalls,
  tasks_with_uniform_nontrivial_source_delta:eligible,
  tasks_without_uniform_nontrivial_source_delta:uneligible,
  eligible_tasks_with_zero_exact_train_fit:zeroFitEligible,
  tasks_with_at_least_one_nontrivial_exact_train_program:fullFitTasks,
  total_exact_fit_parameter_tuples:matchingTuples,
  all_fit_original_rows:originalRows,
  positive_synthetic_control_fit:positive.fit.length>0,
  impossible_multi_fill_synthetic_control_rejected:negative.fit.length===0,
  original_test_outputs_read_by_completeness_audit:false,
  original_ARC_evaluation_IDs_consumed:0,
  original_teacher_GPT_generation_cost:'NOT_METERED',
  cpu_ms:(cpu.user+cpu.system)/1000,
  wall_ms:Number(process.hrtime.bigint()-begun)/1e6,
  theorem:"With complete fixed H of 1800 typed-mask variants, if H_D={p∈H : p fits every TRAIN pair and changes at least one TRAIN cell} is empty, no ranking, cached selection, or learned selector restricted to H can produce a nontrivial TRAIN-consistent executable program. The observed 399/400 zero-fit result is conditional on H and this already opened source, not a theorem for all possible program languages.",
  q3_autonomous_structure_discovery:'OPEN',
  q4_equal_rights_lifecycle:'OPEN',
  q6_cross_formalism:'OPEN',
  q7_frontier:'OPEN'
 };
}
export {independentMask,originalDelta,completeTrainEnumeration,audit};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==4){console.error('usage: node P45_FULL_ENUM.mjs ARC_ROOT P45_FIRST');process.exitCode=2;}
 else try{
  const output=audit(process.argv[2],process.argv[3]);
  console.log(JSON.stringify(output,null,2));
  if(!output.audit_pass)process.exitCode=1;
 }catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
