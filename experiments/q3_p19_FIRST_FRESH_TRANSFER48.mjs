/** P1.9 FIRST unseen original ARC 48 transfer. No model, no tuning to opened set.
 * Historical P1.9 executable expression proposer is imported unchanged.
 * This is a prospective ORIGINAL-task transfer of a human-designed DSL search,
 * not proof of autonomous opcode creation or learned inference superiority.
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
import * as P19 from "./q3_goal_conditioned_induction_p19.mjs";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const fjson=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const sig=x=>JSON.stringify(x);
const blob=p=>{const b=fs.readFileSync(p);return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
const sha256=p=>createHash("sha256").update(fs.readFileSync(p)).digest("hex");
const eq=(a,b)=>sig(a)===sig(b);
const invariant=(p,m)=>{if(!p)throw Error("P19_FRESH48_SOURCE_OR_SCORE_DRIFT:"+m);};
const fnv=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;};
const SEED="neumann-q3-p19-first-fresh-transfer-20261105|";
export function verifyP19OriginalRoot(arcRoot){
 const arc=path.resolve(arcRoot),evalDir=path.join(arc,"data/evaluation");
 const lock=fjson(path.join(ROOT,"docs/experiments/q3_p19_FIRST_FRESH_TRANSFER48_SOURCE_LOCK.json"));
 const cohortPath=path.join(ROOT,"docs/experiments/q3_p19_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json");
 const cohort=fjson(cohortPath);
 invariant(blob(cohortPath)===lock.cohort_blob,"COHORT_MUTATED");
 invariant(cohort.upstream_sha==="399030444e0ab0cc8b4e199870fb20b863846f34","UPSTREAM_DRIFT");
 for(const [file,sha]of Object.entries(lock.source_blobs))
   invariant(blob(path.join(ROOT,file))===sha,"SOURCE_CHANGED:"+file);
 const used=new Set();
 for(const m of cohort.prior_manifests){
   const p=path.join(ROOT,m.path),x=fjson(p);
   invariant(blob(p)===m.blob&&x.ids?.length===m.length,"HISTORIC_MANIFEST_DRIFT:"+m.path);
   for(const name of x.ids)used.add(name);
 }
 invariant(used.size===280&&cohort.excluded===280,"PREVIOUS_EXCLUSION_COUNT");
 const names=fs.readdirSync(evalDir).filter(name=>name.endsWith(".json"));
 invariant(names.length===400,"UPSTREAM_COUNT");
 const unseen=names.filter(x=>!used.has(x));
 invariant(unseen.length===120&&cohort.available===120,"FRESH_COHORT_EXCLUSION");
 const selected=unseen.map(name=>({name,rank:fnv(SEED+name)})).
   sort((a,b)=>a.rank-b.rank||a.name.localeCompare(b.name)).slice(0,48).map(x=>x.name);
 invariant(sig(selected)===sig(cohort.ids)&&cohort.held_back===72,"FILENAME_RESELECTION_MISMATCH");
 return{cohort,lock,evalDir};
}
const accepted=(p,g)=>p!==null&&eq(p,g);
const consensus=xs=>{const valid=xs.filter(x=>x!==null);
  return valid.length&&valid.every(x=>eq(x,valid[0]))?valid[0]:null;};
export function assess(task,id){
 const train=task.train,query=task.test.map(x=>x.input),started=process.hrtime.bigint();
 const pB=B.propose(train,query,"B");
 const p20=P20.propose(train,query);
 const p24=P24.solve(train,query);
 const p25=P25.solve(train,query);
 const p27=P27.synthesize(train,query,{selector:"classical",maxCandidates:P27.allASTs.length});
 const p28=P28.propose(train,query);
 const bs=[pB.proposals,p20.prediction,p24.prediction,p25.prediction,p27.prediction,p28.prediction];
 const active=bs.filter(x=>x!==null);
 const conflict=active.length>1&&!active.every(x=>eq(x,active[0]));
 const baseline=conflict?null:consensus(bs);
 const proposed=P19.propose(train,query);
 if(proposed.prediction!==null){
   const representatives=proposed.trace.representative_ASTs;
   invariant(representatives?.length>0,"NONREPLAYABLE_P19_PROGRAM:"+id);
   const valid=representatives.some(program=>
     train.every(pair=>eq(P19.execute(pair.input,program),pair.output))&&
     query.every((input,i)=>eq(P19.execute(input,program),proposed.prediction[i])));
   invariant(valid,"P19_PROGRAM_ORIGINAL_TRAIN_TEST_REPLAY_FAILED:"+id);
 }
 const combined=conflict?null:
   baseline!==null&&proposed.prediction!==null&&!eq(baseline,proposed.prediction)?null:
   baseline??proposed.prediction;
 const predictorWallMs=Number(process.hrtime.bigint()-started)/1e6;
 // FIRST original TEST output read occurs AFTER all seven actual proposals.
 const testGold=task.test.map(x=>x.output);
 const correct=[...bs,baseline,proposed.prediction,combined].map(x=>accepted(x,testGold));
 return {
  id,train_count:train.length,test_count:query.length,
  base_conflict:conflict,
  B_correct:correct[0],P20_correct:correct[1],P24_correct:correct[2],
  P25_correct:correct[3],P27_correct:correct[4],P28_correct:correct[5],
  base_correct:correct[6],P19_correct:correct[7],combined_correct:correct[8],
  P19_submitted:proposed.prediction!==null,
  P19_wrong:proposed.prediction!==null&&!correct[7],
  combined_submitted:combined!==null,combined_wrong:combined!==null&&!correct[8],
  gained:correct[8]&&!correct[6],lost:correct[6]&&!correct[8],
  P19_training_fit_count:proposed.trace.training_fit_count,
  P19_ambiguous:proposed.trace.ambiguous,
  P19_abstain_reason:proposed.trace.abstention,
  P19_candidate_ASTs:proposed.trace.candidate_ast_count,
  P19_train_replays:proposed.trace.train_sample_evaluations,
  P19_test_replays:proposed.trace.test_sample_evaluations,
  P19_representatives:proposed.trace.representative_ASTs,
  P19_certificate:proposed.prediction===null?null:{
    schema:"neumann.q3.p19.public-execution-certificate.v1",
    train:train.map(x=>({input:x.input,output:x.output})),
    test_inputs:query,predicted_test:proposed.prediction,
    representative_ASTs:proposed.trace.representative_ASTs},
  predictor_wall_ms:predictorWallMs
 };
}
export function runFirst(arcRoot){
 const start=process.hrtime.bigint(),v=verifyP19OriginalRoot(arcRoot),rows=[];
 for(const file of v.cohort.ids){
  const taskFile=path.join(v.evalDir,file),task=fjson(taskFile);
  const r=assess(task,file.replace(".json",""));
  r.original_file_sha256=sha256(taskFile);
  rows.push(r);
 }
 const sum=k=>rows.filter(x=>x[k]).length;
 const totals={
  n:rows.length,B:sum("B_correct"),P20:sum("P20_correct"),P24:sum("P24_correct"),
  P25:sum("P25_correct"),P27:sum("P27_correct"),P28:sum("P28_correct"),
  baseline:sum("base_correct"),P19:sum("P19_correct"),
  combined:sum("combined_correct"),gained:sum("gained"),lost:sum("lost"),
  P19_submitted:sum("P19_submitted"),P19_wrong:sum("P19_wrong"),
  combined_submitted:sum("combined_submitted"),combined_wrong:sum("combined_wrong"),
  baseline_conflicts:sum("base_conflict"),
  P19_train_fits:sum("P19_training_fit_count"),
  P19_ambiguous:sum("P19_ambiguous"),
  P19_total_ASTs:rows.reduce((a,r)=>a+r.P19_candidate_ASTs,0),
  P19_train_pair_checks:rows.reduce((a,r)=>a+r.P19_train_replays,0),
  predictor_wall_ms:rows.reduce((a,r)=>a+r.predictor_wall_ms,0),
  total_wall_ms:Number(process.hrtime.bigint()-start)/1e6,
  energy_joules:null,financial_cost_usd:null
 };
 const gate=v.cohort.local_stop_gate;
 const pass=totals.gained>=gate.added_correct_min&&totals.P19_wrong<=gate.P19_wrong_submissions_max&&
  totals.combined_wrong<=gate.combined_wrong_max&&totals.lost<=gate.prior_exact_lost_max;
 return{schema:"neumann.q3.p19.first-fresh-original-transfer48-score.v1",
  official_upstream:"fchollet/ARC-AGI@"+v.cohort.upstream_sha,
  cohort_blob:v.lock.cohort_blob,
  original_prior_excluded:280,fresh_originals:48,reserved_next_unopened:72,
  scientific_status:pass?"P19_FRESH_TRANSFER_LOCAL_PASS_NOT_Q3":"P19_FRESH_TRANSFER_FAIL_STOP",
  model_or_teacher_calls:0,all_original_test_gold_after_all_proposals:true,
  original_executable_programs_were_human_grammar_bounded:true,
  Q3_autonomous_opcode_invention:"NOT_PROVEN",
  Q6_unseen_semantic_family:"NOT_PROVEN",
  full_10x_cost_or_frontier:"NOT_PROVEN",totals,rows};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3)throw Error("Need official pinned ARC root");
 try{process.stdout.write(JSON.stringify(runFirst(process.argv[2]),null,2)+"\n");}
 catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
