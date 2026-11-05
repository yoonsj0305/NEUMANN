/* P3.0 first 400 OPENED public ARC training diagnostic with strong 5-TOOL baseline.
 * Same pinned originals used by previous P29 first; no unseen generalization claim.
 * Author-defined operator library and classical synthesis, zero neural/teacher.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import * as B from './q3_object_headroom_p11.mjs';
import * as P20 from './q3_shape_pruned_synthesis_p20.mjs';
import * as P24 from './q3_cached_typed_guard_p24.mjs';
import * as P25 from './q3_generated_decision_trees_p25.mjs';
import * as P27 from './q3_compositional_schema_learning_p27.mjs';
import * as P29 from './q3_p29_induced_coordinate_programs.mjs';
import * as P30 from './q3_p30_object_coordinate_composition.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const hash=b=>createHash('sha256').update(b).digest('hex');
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const exact=(prediction,targets)=>prediction!==null&&eq(prediction,targets);
const P29_FIRST_HASH='d26186c52c2b3f6f7c969476aeeef47ff55dff3c026d220ee6e7a51a3670651a';
export function auditDev(arcRoot,p29First) {
 const firstBytes=fs.readFileSync(p29First);
 if(hash(firstBytes)!==P29_FIRST_HASH)throw Error('ORIGINAL_P29_TRAIN400_RECEIPT_HASH_DRIFT');
 const first=JSON.parse(firstBytes);
 if(first.stats.N!==400||first.rows.length!==400)throw Error('P29_PREVIOUS_400_NOT_COMPLETE');
 const dir=path.join(arcRoot,'data/training');
 const names=fs.readdirSync(dir).filter(x=>x.endsWith('.json')).sort();
 if(names.length!==400)throw Error('REQUIRE_ORIGINAL_400_TRAIN_TASKS');
 const begin=process.hrtime.bigint(),rows=[];
 for(let i=0;i<names.length;i++){
  const id=names[i],task=JSON.parse(fs.readFileSync(path.join(dir,id),'utf8')),goldAfter=()=>task.test.map(t=>t.output);
  if(id!==first.rows[i].id)throw Error('ORIGINAL_TASK_ORDER_DRIFT');
  const train=task.train,testInput=task.test.map(x=>x.input);
  const b=B.propose(train,testInput,'B').proposals,
    p20=P20.propose(train,testInput).prediction,
    p24=P24.solve(train,testInput).prediction,
    p25=P25.solve(train,testInput).prediction,
    p27=P27.synthesize(train,testInput,{selector:'classical',maxCandidates:P27.allASTs.length}).prediction;
  const oldLive=[b,p20,p24,p25,p27].filter(x=>x!==null);
  const oldConflict=oldLive.length>1&&!oldLive.every(x=>eq(x,oldLive[0]));
  const old=oldConflict?null:oldLive[0]??null;
  const p29=P29.synthesize(train,testInput);
  const p30=P30.propose(train,testInput);
  if(first.rows[i].submitted!==(p29.prediction!==null))throw Error('P29_FIRST_SUBMISSION_DRIFT:'+id);
  if(p29.prediction!==null){
   if(p30.prediction===null||!eq(p29.prediction,p30.prediction)||
      p30.trace.source_of_prediction!=='identity_P29_same_source')
    throw Error('P30_REGRESSES_FROZEN_P29_SOURCE:'+id);
  }
  if(p30.prediction!==null){
   const ast=p30.trace.selected_program;
   if(ast===null||!train.every(p=>eq(P30.applyPipeline(ast,p.input),p.output))||
      !testInput.every((x,j)=>eq(P30.applyPipeline(ast,x),p30.prediction[j])))
     throw Error('P30_INDEPENDENT_ORIGINAL_PROGRAM_REPLAY_FAIL:'+id);
  }
  const safe=oldConflict?null:(old!==null&&p30.prediction!==null&&!eq(old,p30.prediction)
   ?null:(old??p30.prediction));
  // Original TEST gold is used only after all three proposals are fixed.
  const gold=goldAfter(),a=exact(old,gold),c=exact(p29.prediction,gold),
       d=exact(p30.prediction,gold),s=exact(safe,gold);
  if(c!==first.rows[i].correct||first.rows[i].false_submit!==(p29.prediction!==null&&!c))
   throw Error('P29_FIRST_ORIGINAL_TEST_CHECKER_DRIFT:'+id);
  rows.push({id,
   old_exact:a,p29_exact:c,p30_exact:d,safe_exact:s,
   old_conflict:oldConflict,p30_submitted:p30.prediction!==null,
   p30_wrong:p30.prediction!==null&&!d,
   safe_submitted:safe!==null,safe_wrong:safe!==null&&!s,
   additional_p30_over_p29:d&&!c,additional_over_old:d&&!a,
   additional_safe:s&&!a,lost_safe:a&&!s,
   source:p30.trace.source_of_prediction,reason:p30.trace.abstention,
   trace:p30.trace,ast:p30.trace.selected_program});
 }
 const n=key=>rows.filter(x=>x[key]).length;
 const result={schema:'neumann.q3.p30.first-public-train400-opened-compound.v1',
  source:'fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34',
  reopened_public_train_not_fresh:true,
  first_P29_sha256:hash(firstBytes),
  P30_operators_human_supplied:true,P30_neural_calls:0,P30_teacher_calls:0,
  independent_full_train_and_test_replay:true,
  original_test_gold_after_all_proposals:true,
  stats:{
   tasks:rows.length,old_baseline_exact:n('old_exact'),
   p29_exact:n('p29_exact'),p30_exact:n('p30_exact'),p30_submitted:n('p30_submitted'),
   p30_wrong_submitted:n('p30_wrong'),
   p30_extra_exact_beyond_p29:n('additional_p30_over_p29'),
   p30_extra_exact_beyond_old:n('additional_over_old'),
   new_safe_combined_exact:n('safe_exact'),new_safe_combined_wrong:n('safe_wrong'),
   new_safe_combined_submitted:n('safe_submitted'),
   additional_safe_exact_over_old:n('additional_safe'),lost_old_exact:n('lost_safe'),
   p30_only_new_crop:rows.filter(x=>x.p30_submitted&&x.source!=='identity_P29_same_source').length,
   global_wall_ms:Number(process.hrtime.bigint()-begin)/1e6
  },rows,
  Q3:'OPEN',Q6:'OPEN',Q7:'OPEN'
 };
 return result;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==4)throw Error('Usage: node experiments/q3_p30_opened_train400_first.mjs ARC_ROOT P29_FIRST400.json');
 try{console.log(JSON.stringify(auditDev(process.argv[2],process.argv[3]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
