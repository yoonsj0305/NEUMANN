/* P2.9 exact-source original public training 400 classical headroom audit.
 * Retains P2.9 original FIRST JSON from prior artifact unchanged.
 * Strong old five-family TOOL engines replayed against original public inputs.
 * No pretrained model, no teacher, no test-label visibility at proposal.
 * Not a new sealed or blind evaluation; 400 ARC public TRAIN originals.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import {interpret as replayP29} from "./q3_p29_induced_coordinate_programs.mjs";

const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(p,g)=>p!==null&&eq(p,g);
const hash=(b)=>createHash("sha256").update(b).digest("hex");
const fileGitBlob=(p)=>{const d=fs.readFileSync(p);return createHash("sha1").update("blob "+d.length+"\0").update(d).digest("hex");};
const FIRST_CORE_SHA="ca6f76504be5cf2fc00709b6479f0e8436c6fa18";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export function audit(arc,reportFile) {
 if(fileGitBlob(path.join(ROOT,"experiments/q3_p29_induced_coordinate_programs.mjs"))!==FIRST_CORE_SHA)
  throw Error("ORIGINAL_P29_EXECUTOR_SOURCE_DRIFT");
 const receiptBytes=fs.readFileSync(reportFile),r=JSON.parse(receiptBytes);
 if(r.stats.N!==400||r.task_set!=="data/training; OPENED DEVELOPMENT, NOT UNSEEN EVALUATION"||r.rows.length!==400)
  throw Error("ORIGINAL_FIRST_P29_400_NOT_FOUND");
 const corpus=path.join(arc,"data/training");
 const ids=fs.readdirSync(corpus).filter(x=>x.endsWith(".json")).sort();
 if(ids.length!==400||ids.some((id,i)=>id!==r.rows[i].id))throw Error("TASK_COHORT_DRIFT");
 const began=process.hrtime.bigint(),rows=[];
 for(let i=0;i<ids.length;i++) {
   const id=ids[i],task=JSON.parse(fs.readFileSync(path.join(corpus,id),"utf8"));
   const tr=task.train,tests=task.test.map(x=>x.input),p29r=r.rows[i];
   const b=B.propose(tr,tests,"B").proposals;
   const p20=P20.propose(tr,tests).prediction;
   const p24=P24.solve(tr,tests).prediction;
   const p25=P25.solve(tr,tests).prediction;
   const p27=P27.synthesize(tr,tests,{selector:"classical",maxCandidates:P27.allASTs.length}).prediction;
   const old=[b,p20,p24,p25,p27];
   const live=old.filter(x=>x!==null),conflict=live.length>1&&live.some(x=>!eq(x,live[0]));
   const consensus=conflict?null:live[0]||null;
   const p29=p29r.program?tests.map(x=>replayP29(p29r.program,x)):null;
   if(p29r.submitted!==(p29!==null))throw Error("P29_FIRST_SUBMISSION_MISMATCH:"+id);
   if(p29!==null) {
     if(p29.some(x=>x===null)||!tr.every(x=>eq(replayP29(p29r.program,x.input),x.output)))
      throw Error("P29_ORIGINAL_TRAIN_SOURCE_REPLAY_FAIL:"+id);
   }
   const combined=conflict?null:(consensus!==null&&p29!==null&&!eq(consensus,p29)?null:(consensus??p29));
   // Gold accessed after generating all 5 strong controls and replaying P29.
   const original=task.test.map(x=>x.output);
   const correctP29=exact(p29,original);
   if(correctP29!==p29r.correct||p29r.false_submit===(p29r.correct))
       throw Error("FIRST_P29_ORIGINAL_GOLD_FLAG_MISMATCH:"+id);
   rows.push({
     id,old_flags:old.map(x=>exact(x,original)),old_conflict:conflict,
     old_exact:exact(consensus,original),p29_exact:correctP29,p29_wrong:p29!==null&&!correctP29,
     p29_new_exact:correctP29&&!exact(consensus,original),
     combined_exact:exact(combined,original),combined_wrong:combined!==null&&!exact(combined,original),
     gained:exact(combined,original)&&!exact(consensus,original),
     lost:exact(consensus,original)&&!exact(combined,original)
   });
 }
 const count=pred=>rows.filter(pred).length;
 const counts={
  N:rows.length,
  individual_old:["B","P20","P24","P25","P27"].map((name,k)=>({name,correct:count(x=>x.old_flags[k])})),
  union_of_individual_old:count(x=>x.old_flags.some(Boolean)),
  old_consensus_correct:count(x=>x.old_exact),
  old_conflicts:count(x=>x.old_conflict),
  p29_first_correct:count(x=>x.p29_exact),
  p29_false_submitted:count(x=>x.p29_wrong),
  p29_additional_over_old_consensus:count(x=>x.p29_new_exact),
  combined_exact:count(x=>x.combined_exact),
  combined_wrong:count(x=>x.combined_wrong),
  combined_gained:count(x=>x.gained),
  combined_lost:count(x=>x.lost)
 };
 if(counts.p29_first_correct!==r.stats.correct||
    counts.p29_false_submitted!==r.stats.false_submit)
    throw Error("ORIGINAL_P29_FIRST_AGGREGATE_DRIFT");
 return {
  schema:"neumann.q3.p29.opened-400-matched-classical-audit.v1",
  upstream:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  P29_first_receipt_sha256:hash(receiptBytes),
  P29_original_core_git_blob:FIRST_CORE_SHA,
  independent_same_source_replay:true,
  source:"ORIGINAL_PUBLIC_TRAINING_400_NOT_BLIND",
  no_model_calls:true,no_training:true,all_baselines_are_classical:true,
  original_gold_read_after_proposals:true,
  verdict:"DIAGNOSTIC_ONLY_NO_GENERALIZATION_CLAIM",
  counts,rows,elapsed_ms:Number(process.hrtime.bigint()-began)/1e6
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==4)throw Error("Usage: node experiments/q3_p29_training400_matched_controls.mjs ARC_ROOT FIRST_JSON");
 try{console.log(JSON.stringify(audit(process.argv[2],process.argv[3]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
