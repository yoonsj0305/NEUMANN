/* NEUMANN P2.7 | Independent original-task AST replay audit.
 * Does not trust first scorer's correctness flags; regenerates both predictions.
 * Cannot give a full anti-leakage guarantee for external code, but model API lacks test gold.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import {synthesize,runProgram,eq,allASTs} from "./q3_compositional_schema_learning_p27.mjs";
import {verifyPinnedData} from "./q3_compositional_schema_learning_p27_first.mjs";
const hash=o=>createHash("sha256").update(JSON.stringify(o)).digest("hex");
export function independentAudit(arcRoot,first){
 const v=verifyPinnedData(arcRoot),errors=[],counts={classical:0,learned:0,classical_false:0,learned_false:0};
 if(first.rows.length!==32)throw new Error("ORIGINAL_COUNT_FAIL");
 if(first.meta_training_tasks!==400)throw new Error("META_TRAIN_MISSING");
 if(JSON.stringify(first.rows.map(x=>x.id))!==JSON.stringify(v.cohort.ids.map(x=>x.replace(".json",""))))
  throw new Error("COHORT_REORDERED");
 const stats=new Map(first.rows.map(r=>[r.id,r]));
 for(const file of v.cohort.ids){
  const id=file.replace(".json",""),task=JSON.parse(fs.readFileSync(path.join(v.evalDir,file),"utf8")),row=stats.get(id);
  const inputs=task.test.map(t=>t.input);
  for(const [arm,opts]of [["classical",{selector:"classical",maxCandidates:allASTs.length}],
                           ["learned",{selector:"learned",prior:first.meta_prior,maxCandidates:allASTs.length}]]){
   const attempt=synthesize(task.train,inputs,opts);
   const recorded=row[arm+"_trace"];
   const chosen=attempt.trace.selected_AST;
   if(hash(chosen)!==hash(recorded.selected_AST))errors.push(id+":"+arm+":AST_CHANGED");
   if(attempt.trace.geometry_attempts!==allASTs.length)errors.push(id+":"+arm+":BUDGET_CHANGED");
   if(attempt.prediction!==null){
    for(const p of task.train)if(!eq(runProgram(chosen,p.input),p.output))errors.push(id+":"+arm+":TRAIN_NOT_EXACT");
    for(let i=0;i<inputs.length;i++)if(!eq(runProgram(chosen,inputs[i]),attempt.prediction[i]))
      errors.push(id+":"+arm+":TEST_REPLAY_DISAGREES");
   }
   // Original gold is first touched here after an independently assembled prediction.
   const gold=task.test.map(t=>t.output);
   const exact=attempt.prediction!==null&&attempt.prediction.length===gold.length&&
    attempt.prediction.every((g,i)=>eq(g,gold[i]));
   const wrong=attempt.prediction!==null&&!exact;
   if(exact)counts[arm]++;
   if(wrong)counts[arm+"_false"]++;
   if(exact!==row[arm+"_exact"]||wrong!==row[arm+"_false_accept"])errors.push(id+":"+arm+":ORACLE_SCORE_MISMATCH");
  }
 }
 const good=errors.length===0&&counts.classical===first.stats.classical_exact&&
 counts.learned===first.stats.learned_exact&&
 counts.classical_false===first.stats.classical_false_accept&&
 counts.learned_false===first.stats.learned_false_accept;
 return {schema:"neumann.q3.p27.independent-first-audit.v1",good,
  data_commit:v.cohort.upstream_commit,cohort_sha:first.cohort_sha,
  first_receipt_sha256:hash(first),counts,errors,
  scope:"Original public evaluation, preregistered. Same source language, independently rerun predictions. Not unseen families/10x."};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const [arcRoot,receipt]=process.argv.slice(2);if(!arcRoot||!receipt)throw new Error("Usage: node experiments/q3_p27_independent_audit.mjs ARC_ROOT receipt.json");
  const r=independentAudit(arcRoot,JSON.parse(fs.readFileSync(receipt,"utf8")));
  process.stdout.write(JSON.stringify(r,null,2)+"\n");
  if(!r.good)process.exitCode=1;
 }catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
