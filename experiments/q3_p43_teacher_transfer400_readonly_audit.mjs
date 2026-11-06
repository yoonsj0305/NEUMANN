/* P43 independent pinned FIRST audit. Does not import/reuse the P43 proposer
 * or first scoring runner. Runs an alternate direct per-source evaluation on
 * original source and verifies original first JSON hash, all 400 rows, 7 code
 * blob, and separately pinned historic P30 400-task comparator.
 * Not independent neural generation and not an uncontaminated fresh suite.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {SOURCE} from './q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const FIRST_SHA='8b5cb4927133930f6238adb17dbeba5a73d6955a368965b67318cc6aca78a398';
const TEACHER_BLOB='d82f09406b4b3ee4e9651c261013c8ce8aa850c7';
const STRONG_BASELINE_SHA='0fb747b4fd7355649465b8ff3424c0170d6d178f47fd1ea64ca486c416672b79';
const hash=x=>createHash('sha256').update(x).digest('hex');
const gitblob=x=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+x.length+'\0'),x])).digest('hex');
const clone=x=>x.map(row=>row.slice());
const deepEq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function grid(x){
 return Array.isArray(x)&&x.length>0&&x.length<=30&&Array.isArray(x[0])&&x[0].length>0
  &&x[0].length<=30&&x.every(row=>Array.isArray(row)&&row.length===x[0].length
  &&row.every(n=>Number.isInteger(n)&&n>=0&&n<=9));
}
function audit(originalRoot,firstFile,baselineFile){
 const errors=[];
 const f=fs.readFileSync(firstFile),fSha=hash(f),first=JSON.parse(f);
 if(fSha!==FIRST_SHA)errors.push('ORIGINAL_P43_FIRST_RECEIPT_DRIFT');
 const base=fs.readFileSync(baselineFile),baseSha=hash(base),b=JSON.parse(base);
 if(baseSha!==STRONG_BASELINE_SHA)errors.push('ORIGINAL_P30_BASELINE_RECEIPT_DRIFT');
 const teacher=fs.readFileSync(path.join(ROOT,'experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs'));
 if(gitblob(teacher)!==TEACHER_BLOB)errors.push('FROZEN_ORIGINAL_P22_TEACHER_CODE_DRIFT');
 const dir=path.join(originalRoot,'data/training');
 const ids=fs.readdirSync(dir).filter(x=>x.endsWith('.json')).sort();
 if(ids.length!==400||b.rows.length!==400||first.rows.length!==400)throw Error('COHORT_NOT_400');
 const funcs=Object.entries(SOURCE).filter(([,fn])=>typeof fn==='function');
 if(funcs.length!==7)throw Error('NOT_7_ORIGINAL_PROGRAMS');
 let exact=0, submitted=0,wrong=0,extra=0,unanimous=0, ambiguous=0,trainCalls=0,testCalls=0;
 let successes=[];
 for(let i=0;i<400;i++){
   const id=ids[i], task=JSON.parse(fs.readFileSync(path.join(dir,id),'utf8'));
   const old=b.rows[i], recorded=first.rows[i];
   if(id!==old.id||id!==recorded.id){errors.push('HISTORICAL_TASK_ORDER_'+i);continue;}
   const compatible=[];
   const testInputs=task.test.map(t=>t.input);
   for(const [name,fn] of funcs){
     let allFit=true;
     for(const pair of task.train){
       trainCalls++;
       try{
         const output=fn(clone(pair.input));
         if(!grid(output)||!deepEq(output,pair.output)){allFit=false;break;}
       }catch(e){allFit=false;break;}
     }
     if(!allFit)continue;
     let predictions=[];
     try {
       for(const g of testInputs){
         testCalls++;
         const out=fn(clone(g));
         if(!grid(out))throw Error('INVALID_OUTPUT');
         predictions.push(out);
       }
       compatible.push({name,predictions});
     }catch(e){}
   }
   const solutions=new Map(compatible.map(entry=>[JSON.stringify(entry.predictions),entry.predictions]));
   const disputed=solutions.size>1;
   const output=solutions.size===1?[...solutions.values()][0]:null;
   const accept=output!==null;
   const originalGold=task.test.map(t=>t.output);
   const correct=accept&&deepEq(output,originalGold);
   const bad=accept&&!correct;
   const newExact=correct&&!old.safe_exact;
   submitted+=Number(accept);exact+=Number(correct);wrong+=Number(bad);
   extra+=Number(newExact);unanimous+=Number(compatible.length>0&&!disputed);
   ambiguous+=Number(disputed);
   if(correct)successes.push({id,programs:compatible.map(p=>p.name),new_over_classical:newExact});
   const compares={
     baseline_safe_correct:old.safe_exact,
     baseline_safe_submitted:old.safe_submitted,
     teacher_submitted:accept,
     teacher_original_exact:correct,
     teacher_wrong_submitted:bad,
     teacher_extra_exact_over_baseline_safe:newExact,
     teacher_fitting_count:compatible.length,
     teacher_ambiguous:disputed,
     teacher_abstained:!accept
   };
   for(const [key,value] of Object.entries(compares))
     if(recorded[key]!==value)errors.push('ROW_DISAGREEMENT_'+id+'_'+key);
   if(!deepEq(recorded.teacher_fitting_functions,compatible.map(p=>p.name)))
     errors.push('PROGRAM_ID_OR_ORDER_DISAGREEMENT_'+id);
 }
 const stats=first.stats;
 const checks={
  teacher_original_exact:exact,teacher_submitted:submitted,
  teacher_wrong_submitted:wrong,
  teacher_extra_exact_over_strong_classical_safe:extra,
  teacher_unanimous_train_fit:unanimous,
  teacher_ambiguous:ambiguous,
  total_original_train_program_calls:trainCalls,
  total_test_input_program_calls:testCalls,
  classical_safe_union_exact:b.stats.new_safe_combined_exact,
  classical_safe_union_wrong:b.stats.new_safe_combined_wrong
 };
 for(const [key,value] of Object.entries(checks))
   if(stats[key]!==value)errors.push('FIRST_AGGREGATE_MISMATCH_'+key);
 if(first.science_status!=='P43_FROZEN_TEACHER_PROGRAM_TRANSFER_PRESTUDENT_GATE_FAIL')
   errors.push('FIRST_STATUS_NOT_PRESERVED');
 if(extra!==1||wrong!==0||exact!==1||successes.length!==1)
   errors.push('ACTUAL_COUNTEREXAMPLE_TO_EXPECTED_FIRST');
 if(first.Q3_neural_self_discovery!=='NOT_PROVEN'
   ||first.Q6_new_formalism_external_family!=='NOT_PROVEN'
   ||first.original_arc_eval_ids_used!==0)
   errors.push('Q3_Q6_OR_ARC_PROVENANCE_OVERCLAIM');
 return {
  schema:'neumann.q3.p43.teacher7-original400-pinned-readonly-audit.v1',
  audit_pass:errors.length===0,
  errors:errors.slice(0,15),error_count:errors.length,
  original_first_sha256:fSha,original_P30_sha256:baseSha,
  source_original_teacher_blob:gitblob(teacher),
  independent_newly_scored_originals:400,
  independent_reused_program_count:funcs.length,
  independent_teacher_exact:exact,independent_wrong_submitted:wrong,
  independent_extra_exact_over_classical:extra,
  unique_verified_reused_program_successes:successes,
  original_400_test_scored_again_from_source:true,
  imported_original_P43_selector_or_first_runner:false,
  Q3_neural_self_invention:'OPEN',
  G1_student_training_gate:'HOLD'
 };
}
export {audit};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==5){console.error('usage: node independent_q3_p43...mjs ARC_ROOT P43_FIRST P30_FIRST');process.exitCode=2;}
 else try{const result=audit(process.argv[2],process.argv[3],process.argv[4]);console.log(JSON.stringify(result,null,2));if(!result.audit_pass)process.exitCode=1;}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
