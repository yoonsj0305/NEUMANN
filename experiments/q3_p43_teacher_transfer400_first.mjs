/* NEUMANN Q3 P43: opened original 400 teacher-program reuse versus frozen P30.
 * Original immutable teacher source is imported but NOT edited.
 * Program proposals inspect TRAIN pairs and TEST INPUTS; original TEST GOLD
 * is read by a separate scoring phase only after all program outputs frozen.
 * This is NOT learned-policy improvement or unseen ARC eval.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {SOURCE, valid} from './q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const CONTRACT=path.join(ROOT,'docs/experiments/q3_P43_TEACHER_PROGRAM_TRANSFER400_PREREG_2026_11_06.json');
const sha=b=>createHash('sha256').update(b).digest('hex');
function blob(bytes) {
 return createHash('sha1').update(Buffer.concat([Buffer.from('blob '+bytes.length+'\0'),bytes])).digest('hex');
}
function exactGrid(a,b){
 return valid(a)&&valid(b)&&a.length===b.length&&a[0].length===b[0].length
     &&a.every((row,i)=>row.every((v,j)=>v===b[i][j]));
}
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const clone=g=>g.map(row=>row.slice());

/* Task identity is intentionally ABSENT. The frozen program names are for
 * receipt provenance, never selected based on task ID or original TEST gold.
 * TRAIN fit + unanimous predicted TEST outputs is the sole admission gate.
 */
function propose(train,testInputs,candidates){
 const fitting=[],failures=[];
 let trainCalls=0,testCalls=0;
 for(const [name,solver] of candidates){
  let failed=false, preds=[];
  for(const pair of train){
   trainCalls++;
   try{
    const prediction=solver(clone(pair.input));
    if(!exactGrid(prediction,pair.output)){failed=true;break;}
   }catch(error){failed=true;break;}
  }
  if(failed)continue;
  try{
    preds=testInputs.map(g=>{testCalls++;return solver(clone(g));});
    if(!preds.every(valid)){failures.push({name,reason:'BAD_PREDICTION_GRID'});continue;}
  }catch(error){failures.push({name,reason:'EXECUTION_ERROR'});continue;}
  fitting.push({name,preds});
 }
 const unique=Array.from(new Set(fitting.map(f=>JSON.stringify(f.preds))));
 const conflicted=unique.length>1;
 const pred=(unique.length===1?JSON.parse(unique[0]):null);
 return {
   prediction:pred,
   program_ids:fitting.map(f=>f.name),
   fitting_program_count:fitting.length,
   ambiguous:conflicted,
   abstained:pred===null,
   train_calls:trainCalls,
   test_calls:testCalls,
   failures
 };
}

function run(originalRoot,baselinePath){
 const pre=JSON.parse(fs.readFileSync(CONTRACT,'utf8'));
 const sourceFile=path.join(ROOT,pre.source_teacher.path);
 const actualBlob=blob(fs.readFileSync(sourceFile));
 if(actualBlob!==pre.source_teacher.git_blob)throw Error('TEACHER_PROGRAM_BLOB_DRIFT');
 const baselineBytes=fs.readFileSync(baselinePath);
 const baselineSha=sha(baselineBytes);
 if(baselineSha!==pre.strong_classical.first_receipt_sha256)
  throw Error('ORIGINAL_P30_FIRST_SHA_DRIFT');
 const prior=JSON.parse(baselineBytes);
 if(prior.rows?.length!==400||prior.stats?.tasks!==400||
   prior.stats.new_safe_combined_exact!==54||
   prior.stats.new_safe_combined_wrong!==8||
   prior.stats.p30_exact!==27)
  throw Error('HISTORICAL_STRONG_CLASSICAL_BASELINE_DRIFT');
 const dataDir=path.join(originalRoot,'data/training');
 const names=fs.readdirSync(dataDir).filter(f=>f.endsWith('.json')).sort();
 if(names.length!==400||prior.rows.some((row,i)=>row.id!==names[i]))
  throw Error('ORIGINAL_OFFICIAL_COHORT_DRIFT');
 const candidates=Object.entries(SOURCE).filter(([,func])=>typeof func==='function');
 if(candidates.length!==7||new Set(candidates.map(([name])=>name)).size!==7)
  throw Error('FROZEN_TEACHER_PROGRAM_COUNT_DRIFT');
 const t0=process.hrtime.bigint(),cpu0=process.cpuUsage();
 const rows=[];
 for(let i=0;i<names.length;i++){
  const filename=names[i];
  const task=JSON.parse(fs.readFileSync(path.join(dataDir,filename),'utf8'));
  if(!Array.isArray(task.train)||task.train.length<1||!Array.isArray(task.test)||task.test.length<1)
   throw Error('BAD_OFFICIAL_TASK:'+filename);
  const train=task.train.map(pair=>({input:pair.input,output:pair.output}));
  const testInputs=task.test.map(t=>t.input);
  // Code generates proposals BEFORE reading task.test[].output.
  const p=propose(train,testInputs,candidates);
  const originalGold=task.test.map(x=>x.output);
  const correct=p.prediction!==null&&
        p.prediction.length===originalGold.length&&
        p.prediction.every((grid,j)=>exactGrid(grid,originalGold[j]));
  const submitted=p.prediction!==null;
  const baselineCorrect=prior.rows[i].safe_exact;
  const baselineSubmitted=prior.rows[i].safe_submitted;
  rows.push({
   id:filename,
   baseline_safe_correct:baselineCorrect,
   baseline_safe_submitted:baselineSubmitted,
   teacher_submitted:submitted,
   teacher_original_exact:correct,
   teacher_wrong_submitted:submitted&&!correct,
   teacher_extra_exact_over_baseline_safe:correct&&!baselineCorrect,
   teacher_misses_baseline_safe:baselineCorrect&&!correct,
   teacher_fitting_functions:p.program_ids,
   teacher_fitting_count:p.fitting_program_count,
   teacher_ambiguous:p.ambiguous,
   teacher_abstained:p.abstained,
   teacher_train_executions:p.train_calls,
   teacher_test_executions:p.test_calls,
   teacher_source_exceptions_or_bad_grids:p.failures
  });
 }
 const cpu=process.cpuUsage(cpu0);
 const total=k=>rows.filter(r=>r[k]).length;
 const teacherUniqueCorrect=new Set(rows.filter(r=>r.teacher_original_exact).flatMap(r=>r.teacher_fitting_functions));
 const stats={
   original_training_tasks:rows.length,
   frozen_teacher_functions:candidates.length,
   classical_safe_union_exact:total('baseline_safe_correct'),
   classical_safe_union_wrong:prior.stats.new_safe_combined_wrong,
   teacher_submitted:total('teacher_submitted'),
   teacher_original_exact:total('teacher_original_exact'),
   teacher_wrong_submitted:total('teacher_wrong_submitted'),
   teacher_extra_exact_over_strong_classical_safe:total('teacher_extra_exact_over_baseline_safe'),
   teacher_baseline_safe_correct_not_solved:total('teacher_misses_baseline_safe'),
   upper_bound_oracle_union_exact:rows.filter(r=>r.teacher_original_exact||r.baseline_safe_correct).length,
   teacher_ambiguous:total('teacher_ambiguous'),
   teacher_unanimous_train_fit:rows.filter(r=>r.teacher_fitting_count>0&&!r.teacher_ambiguous).length,
   distinct_teacher_programs_with_original_success:teacherUniqueCorrect.size,
   total_original_train_program_calls:rows.reduce((a,r)=>a+r.teacher_train_executions,0),
   total_test_input_program_calls:rows.reduce((a,r)=>a+r.teacher_test_executions,0),
   same_process_wall_ms:Number(process.hrtime.bigint()-t0)/1e6,
   same_process_cpu_ms:(cpu.user+cpu.system)/1000
 };
 const go=(stats.teacher_extra_exact_over_strong_classical_safe>=2&&
           stats.teacher_wrong_submitted===0&&
           stats.distinct_teacher_programs_with_original_success>=2);
 return {
   schema:'neumann.q3.p43.teacher7-opened-original-train400-first.v1',
   science_status:go?'P43_FROZEN_TEACHER_PROGRAM_TRANSFER_PRESTUDENT_GATE_PASS':'P43_FROZEN_TEACHER_PROGRAM_TRANSFER_PRESTUDENT_GATE_FAIL',
   teacher_original_git_blob:actualBlob,
   original_P30_first_sha256:baselineSha,
   original_arc_commit:pre.official_original.commit,
   all_400_original_test_golds_only_after_proposal:true,
   all_reused_programs_source_frozen:true,
   original_arc_eval_ids_used:0,
   comparison_to_classical_is_oracle_union_upper_bound_not_deployable:true,
   Q3_neural_self_discovery:'NOT_PROVEN',
   Q4_equal_cost:'NOT_PROVEN',
   Q6_new_formalism_external_family:'NOT_PROVEN',
   Q7_frontier:'NOT_PROVEN',
   stats,rows
 };
}
export {propose,exactGrid,run};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==4){console.error('Usage: node q3_p43_teacher_transfer400_first.mjs ARC_ROOT P30_FIRST_RECEIPT');process.exitCode=2;}
 else try{const result=run(process.argv[2],process.argv[3]);console.log(JSON.stringify(result,null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
