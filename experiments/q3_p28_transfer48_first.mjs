/** P2.8 first FRESH original public ARC transfer48.
 * Source and cohort are frozen before opening any of these 48 evaluation bodies.
 * Original TEST output is read only AFTER all proposals use TRAIN + TEST INPUT.
 * A frozen human-authored factorization grammar is not an autonomous new opcode.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import * as P28 from "./q3_p28_factorized_operator.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const fjson=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const sig=o=>JSON.stringify(o);
const blob=p=>{const b=fs.readFileSync(p);return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
const digest=b=>createHash("sha256").update(b).digest("hex");
const eq=(a,b)=>sig(a)===sig(b);
const assert=(b,m)=>{if(!b)throw Error("P28_FIRST_TRANSFER_CONTRACT:"+m);};
const fnv=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;};
const SEED="neumann-q3-p28-FIRST-FRESH-TRANSFER-20261105|";

export function verifyOriginalRoot(arc) {
 const root=path.resolve(arc),evalDir=path.join(root,"data/evaluation");
 const manifestPath=path.join(ROOT,"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json");
 const lock=fjson(path.join(ROOT,"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_SOURCE_LOCK.json"));
 const cohort=fjson(manifestPath);
 assert(blob(manifestPath)===lock.cohort_blob,"CHANGED_COHORT_BLOB");
 assert(cohort.upstream_sha==="399030444e0ab0cc8b4e199870fb20b863846f34","UPSTREAM_COMMIT");
 for(const [file,expected] of Object.entries(lock.source_blobs))assert(blob(path.join(ROOT,file))===expected,"SOURCE_BLOB:"+file);
 const used=new Set();
 for(const m of cohort.historic_previous_manifests){
    assert(blob(path.join(ROOT,m.path))===m.blob,"PREV_MANIFEST_CHANGED:"+m.path);
    const historic=fjson(path.join(ROOT,m.path));
    assert(historic.ids?.length===m.count,"PREV_MANIFEST_LENGTH:"+m.path);
    for(const id of historic.ids)used.add(id);
 }
 assert(used.size===232&&cohort.prior_unique_excluded===used.size,"PREVIOUS_EXCLUSION_DRIFT");
 const names=fs.readdirSync(evalDir).filter(x=>x.endsWith(".json"));
 assert(names.length===400&&cohort.official_filename_count===400,"OFFICIAL_FILE_COUNT_DRIFT");
 const rest=names.filter(name=>!used.has(name));
 assert(rest.length===168&&cohort.remaining_before_select===168,"UNOPENED_REMAINDER_DRIFT");
 const selected=rest.map(name=>({name,priority:fnv(SEED+name)})).
   sort((a,b)=>a.priority-b.priority||a.name.localeCompare(b.name)).
   slice(0,48).map(x=>x.name);
 assert(sig(selected)===sig(cohort.ids)&&new Set(selected).size===48,"BLIND_SELECTION_DRIFT");
 assert(cohort.next_unopened_eval_reserve===120,"REMAINING_RESERVE_DRIFT");
 return {root,evalDir,cohort,lock};
}
const exact=(a,b)=>a!==null&&eq(a,b);
const consensus=programs=>{
 const active=programs.filter(x=>x!==null);
 if(!active.length)return null;
 return active.every(p=>eq(p,active[0]))?active[0]:null;
};
const join=(base,next)=>{
 if(base!==null&&next!==null&&!eq(base,next))return null;
 return base??next;
};
export function assess(task,id) {
 const train=task.train,testInputs=task.test.map(x=>x.input);
 const t=process.hrtime.bigint();
 const b=B.propose(train,testInputs,"B");
 const p20=P20.propose(train,testInputs);
 const p24=P24.solve(train,testInputs);
 const p25=P25.solve(train,testInputs);
 const p27=P27.synthesize(train,testInputs,{selector:"classical",maxCandidates:P27.allASTs.length});
 const old=[b.proposals,p20.prediction,p24.prediction,p25.prediction,p27.prediction];
 const activeOld=old.filter(x=>x!==null);
 const oldWinner=consensus(old);
 const oldConflict=activeOld.length>1&&!activeOld.every(p=>eq(p,activeOld[0]));
 const p28=P28.propose(train,testInputs);
 const p28Winner=p28.prediction;
 if(p28Winner!==null){
   const a=p28.trace.generated_AST;
   assert(a!==null&&train.every(x=>eq(P28.interpret(a,x.input),x.output)),"P28_TRAIN_REPLAY:"+id);
   assert(testInputs.every((x,i)=>eq(P28.interpret(a,x),p28Winner[i])),"P28_TEST_REPLAY:"+id);
 }
 const joined=oldConflict?null:join(oldWinner,p28Winner);
 const predWallMs=Number(process.hrtime.bigint()-t)/1e6;
 // Gold accessed strictly AFTER all 5 baseline and new P28 proposals.
 const gold=task.test.map(x=>x.output);
 const modes=[...old,p28Winner,oldWinner,joined];
 const correct=modes.map(p=>exact(p,gold));
 const submitted=modes.map(p=>p!==null);
 return {id,train_pairs:train.length,test_items:testInputs.length,
   old_baseline_conflict:oldConflict,
   B_correct:correct[0],P20_correct:correct[1],P24_correct:correct[2],P25_correct:correct[3],P27_correct:correct[4],
   P28_correct:correct[5],old_consensus_correct:correct[6],new_consensus_correct:correct[7],
   P28_submitted:submitted[5],P28_wrong:submitted[5]&&!correct[5],
   old_consensus_submitted:submitted[6],new_consensus_submitted:submitted[7],
   new_consensus_wrong:submitted[7]&&!correct[7],
   new_consensus_additional_correct:!correct[6]&&correct[7],
   new_consensus_correct_lost:correct[6]&&!correct[7],
   P28_train_fits:p28.trace.exact_train_programs,
   P28_abstained:p28.trace.abstention,
   P28_enumerated:p28.trace.enumerated,
   P28_pair_evaluations:p28.trace.train_pair_evaluations,
   P27_attempts:p27.trace.geometry_attempts,
   P28_ast:p28.trace.generated_AST,
   P28_certificate:p28Winner===null?null:{schema:"neumann.q3.p28.proof-certificate.v1",
      ast:p28.trace.generated_AST,train:train.map(x=>({input:x.input,output:x.output})),
      test_inputs:testInputs,predicted_test:p28Winner},
   predictor_wall_ms:predWallMs
 };
}
export function runFirst(arc) {
 const started=process.hrtime.bigint(),v=verifyOriginalRoot(arc);
 const rows=[];
 for(const filename of v.cohort.ids){
   const filenamePath=path.join(v.evalDir,filename);
   const task=fjson(filenamePath);
   const row=assess(task,filename.slice(0,-5));
   row.original_file_sha256=digest(fs.readFileSync(filenamePath));
   rows.push(row);
 }
 const sum=k=>rows.filter(x=>x[k]).length;
 const stats={
  n:rows.length,B:sum("B_correct"),P20:sum("P20_correct"),P24:sum("P24_correct"),
  P25:sum("P25_correct"),P27:sum("P27_correct"),P28:sum("P28_correct"),
  old_consensus_correct:sum("old_consensus_correct"),
  new_consensus_correct:sum("new_consensus_correct"),
  added_exact:sum("new_consensus_additional_correct"),
  lost_exact:sum("new_consensus_correct_lost"),
  original_baseline_conflicts:sum("old_baseline_conflict"),
  P28_train_fit_count:rows.filter(x=>x.P28_train_fits>0).length,
  P28_submitted:sum("P28_submitted"),P28_false_submits:sum("P28_wrong"),
  P28_abstentions:rows.filter(x=>!x.P28_submitted).length,
  combined_wrong:sum("new_consensus_wrong"),
  combined_submitted:sum("new_consensus_submitted"),
  P28_candidate_enumerations:rows.reduce((a,b)=>a+b.P28_enumerated,0),
  P28_train_pair_evaluations:rows.reduce((a,b)=>a+b.P28_pair_evaluations,0),
  P27_total_geometry_attempts:rows.reduce((a,b)=>a+b.P27_attempts,0),
  total_predictor_wall_ms:rows.reduce((a,b)=>a+b.predictor_wall_ms,0),
  total_wall_ms:Number(process.hrtime.bigint()-started)/1e6,
  energy_joules:null,financial_cost_usd:null
 };
 const passed=stats.added_exact>=2&&stats.P28_false_submits===0&&stats.lost_exact===0&&stats.combined_wrong===0;
 return {schema:"neumann.q3.p28.first-fresh-original-transfer48.v1",
  upstream:v.cohort.upstream+"@"+v.cohort.upstream_sha,
  transfer_cohort_source_blob:v.lock.cohort_blob,
  source_lock_file:"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_SOURCE_LOCK.json",
  original_file_count:400,previous_used_file_count:232,reserved_unopened_file_count:120,
  gold_used_only_after_all_proposals:true,selected_AFTER_file_names_ONLY:true,
  scoring_original_TEST_exact:true,neural_model_calls:0,teacher_calls:0,
  science_status:passed?"LOCAL_TRANSFER_PASS_NOT_GLOBAL_Q3":"P28_FRESH_TRANSFER_FAIL_STOP",
  legacy_matched_TOOL_includes_P28_same_81_hypothesis_class:true,
  meaning:"Any P28 advantage over P27/older is a newly human-supplied grammar; same-language 81-program classical TOOL has identical solution access. Not autonomous semantic opcode invention.",
  q3_autonomous_invention:"NOT_PROVEN",q6_unseen_semantic_family:"NOT_PROVEN",
  frontier:"NOT_PROVEN",full_cost_10x:"NOT_PROVEN",stats,rows
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3)throw Error("Usage: node experiments/q3_p28_transfer48_first.mjs <official-pinned-ARC-root>");
 try{process.stdout.write(JSON.stringify(runFirst(process.argv[2]),null,2)+"\n");}
 catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
