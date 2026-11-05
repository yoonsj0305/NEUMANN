/* P3.0 posthoc strongest-prior coverage audit on 9 ORIGINAL 400 TRAIN successes.
 * Uses only already opened public tasks. No new evaluation/generalization claim.
 * Check every successful P30 original AST against 10 pre-existing classical arms
 * AND P29 original first output. Report oracle UNION only as offline upper bound.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P19 from "./q3_goal_conditioned_induction_p19.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P21 from "./q3_object_rule_induction_p21.mjs";
import * as P211 from "./q3_object_rule_induction_p211.mjs";
import * as P23 from "./q3_typed_guard_ast_p23.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import * as P28 from "./q3_p28_factorized_operator.mjs";
import * as P29 from "./q3_p29_induced_coordinate_programs.mjs";
import * as P30 from "./q3_p30_object_rewrite_language.mjs";
const ORIGINAL_P30_SHA="9f7415d9ee0cd633fd67a0a87e4518f473c2d7124ce92773b13cd8412a6b8452";
const ORIGINAL_P29_SHA="d26186c52c2b3f6f7c969476aeeef47ff55dff3c026d220ee6e7a51a3670651a";
const P30_CORE_BLOB="398b9bb869b1f53c6f90c6f5fc47fa78a7167954";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sha=b=>createHash("sha256").update(b).digest("hex");
const blob=p=>{const b=fs.readFileSync(p);return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
const exact=(guess,gold)=>guess!==null&&eq(guess,gold);
export function audit(arcRoot,p30FirstFile,p29FirstFile) {
 const p30raw=fs.readFileSync(p30FirstFile),p29raw=fs.readFileSync(p29FirstFile);
 if(sha(p30raw)!==ORIGINAL_P30_SHA||sha(p29raw)!==ORIGINAL_P29_SHA)
   throw Error("ORIGINAL_RECEIPT_MISMATCH");
 if(blob(path.join(ROOT,"experiments/q3_p30_object_rewrite_language.mjs"))!==P30_CORE_BLOB)
   throw Error("P30_SOURCE_DRIFT");
 const p30=JSON.parse(p30raw),p29=JSON.parse(p29raw);
 if(p30.stats.N!==400||p30.stats.correct!==9||p30.stats.false_submit!==1||
    p29.stats.N!==400||p29.stats.correct!==19)throw Error("FIRST_AGGREGATE_CHANGED");
 const p30pos=p30.rows.filter(x=>x.correct),map29=new Map(p29.rows.map(x=>[x.id,x]));
 if(p30pos.length!==9)throw Error("POSITIVE_NOT_NINE");
 const rows=[],started=process.hrtime.bigint();
 for(const entry of p30pos){
  const task=JSON.parse(fs.readFileSync(path.join(arcRoot,"data/training",entry.id),"utf8"));
  const tr=task.train,q=task.test.map(x=>x.input),p29entry=map29.get(entry.id);
  if(!p29entry)throw Error("MISSING_P29_ROW");
  const candidates={
   "P11 B":B.propose(tr,q,"B").proposals,
   "P19":P19.propose(tr,q).prediction,
   "P20":P20.propose(tr,q).prediction,
   "P21":P21.propose(tr,q).prediction,
   "P211":P211.propose(tr,q).prediction,
   "P23":P23.solve(tr,q).prediction,
   "P24":P24.solve(tr,q).prediction,
   "P25":P25.solve(tr,q).prediction,
   "P27":P27.synthesize(tr,q,{selector:"classical",maxCandidates:P27.allASTs.length}).prediction,
   "P28":P28.propose(tr,q).prediction,
   "P29":p29entry.program?q.map(g=>P29.interpret(p29entry.program,g)):null,
  };
  const p30cand=q.map(g=>P30.interpret(entry.program,g));
  if(!entry.program||p30cand.some(x=>x===null)||
    !tr.every(x=>eq(P30.interpret(entry.program,x.input),x.output)))
    throw Error("FIRST_P30_AST_INVALID:"+entry.id);
  // Only after ALL 11 older proposers + P30 original AST execute.
  const gold=task.test.map(x=>x.output);
  if(!exact(p30cand,gold))throw Error("P30_ORIGINAL_CORRECTNESS_DRIFT:"+entry.id);
  if(exact(candidates.P29,gold)!==p29entry.correct)throw Error("P29_FIRST_CORRECTNESS_DRIFT");
  const correct=Object.fromEntries(Object.entries(candidates).map(([name,p])=>[name,exact(p,gold)]));
  rows.push({id:entry.id,prior_correct:correct,
   any_prior_10:Object.entries(correct).some(([name,x])=>name!=="P29"&&x),
   prior_p29:correct.P29,
   p30_uncovered_by_ALL_PRIOR_11:!Object.values(correct).some(Boolean)});
 }
 const k=f=>rows.filter(f).length;
 const stats={
  p30_FIRST_public_training_original_exact:9,
  p30_already_covered_by_p29:k(x=>x.prior_p29),
  p30_already_covered_by_any_prior10:k(x=>x.any_prior_10),
  p30_uncovered_by_all_11_prior_classical:k(x=>x.p30_uncovered_by_ALL_PRIOR_11),
  remaining_novel_positive_ids:rows.filter(x=>x.p30_uncovered_by_ALL_PRIOR_11).map(x=>x.id),
  p30_FIRST_false_submit_count:1,
  elapsed_ms:Number(process.hrtime.bigint()-started)/1e6
 };
 return {
  schema:"neumann.q3.p30.prior11-original-positive9-audit.v1",
  original_FIRST_P30_sha256:sha(p30raw),original_FIRST_P29_sha256:sha(p29raw),
  task_scope:"OPENED_SELECTED_AFTER_FIRST_P30_GOLD__NOT_UNSEEN",
  original_upstream:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  strongest_comparison:"Frozen P11B,P19,P20,P21,P211,P23,P24,P25,P27,P28,P29, equal public TRAIN/TEST-input access",
  posthoc_oracle_union_not_deployable:true,
  all_control_proposals_before_gold_read:true,
  zero_new_evaluation_tasks_used:true,
  source_family:"human-authored object metagrammar, no neural training",
  STOP_GATE:"P30 first retains one false submission, so full scientific gate FAIL independent of positive novelty. New untouched ARC72 must NOT be consumed.",
  Q3:"OPEN",Q6:"OPEN",Q7:"OPEN",stats,rows
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==5)throw Error("node experiments/q3_p30_prior11_audit.mjs ARC_ROOT P30_FIRST P29_FIRST");
 try{console.log(JSON.stringify(audit(...process.argv.slice(2)),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
