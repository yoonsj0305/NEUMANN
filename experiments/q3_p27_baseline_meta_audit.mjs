/* NEUMANN P2.7 BASELINE independent audit, read-only after original first.
 * Recomputes ORIGINAL baseline outputs from TRAIN and TEST INPUT only.
 * Verifies first cohort result's baseline flags, 31 no-fit P2.7 cases, and meta prior data.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import {learnPrior,eq} from "./q3_compositional_schema_learning_p27.mjs";
import {verifyPinnedData} from "./q3_compositional_schema_learning_p27_first.mjs";
const hash=o=>createHash("sha256").update(JSON.stringify(o)).digest("hex");
export function auditBaseline(arcRoot,receipt){
 const v=verifyPinnedData(arcRoot),errors=[],winners=[],noFit=[];
 const known=new Map(receipt.rows.map(r=>[r.id,r]));
 let Bcorrect=0,P20correct=0,P24correct=0,P25correct=0,baseline=0,conflicts=0;
 for(const filename of v.cohort.ids){
  const id=filename.replace(".json",""),task=JSON.parse(fs.readFileSync(path.join(v.evalDir,filename),"utf8")),row=known.get(id);
  const q=task.test.map(t=>t.input),tr=task.train;
  const pb=B.propose(tr,q,"B").proposals,pp20=P20.propose(tr,q).prediction,pp24=P24.solve(tr,q).prediction,pp25=P25.solve(tr,q).prediction;
  const accepted=[pb,pp20,pp24,pp25].filter(x=>x!==null);
  const conflict=accepted.length>1&&accepted.some(p=>JSON.stringify(p)!==JSON.stringify(accepted[0]));
  const pbase=conflict?null:accepted[0]||null;
  // The original gold is accessed ONLY AFTER all baseline proposals have been built.
  const gold=task.test.map(x=>x.output);
  const exact=p=>p!==null&&p.length===gold.length&&p.every((g,i)=>eq(g,gold[i]));
  const flags={B_correct:exact(pb),P20_correct:exact(pp20),P24_correct:exact(pp24),
   P25_correct:exact(pp25),baseline_exact:exact(pbase),baseline_conflict:conflict};
  for(const [k,v]of Object.entries(flags))if(v!==row[k])errors.push(id+":"+k+":FIRST_MISMATCH");
  if(flags.B_correct)Bcorrect++;if(flags.P20_correct)P20correct++;if(flags.P24_correct)P24correct++;if(flags.P25_correct)P25correct++;
  if(flags.baseline_exact){baseline++;winners.push(id);}
  if(conflict)conflicts++;
  if(row.classical_trace.train_fit_count===0&&row.learned_trace.train_fit_count===0)noFit.push(id);
 }
 const training=v.trainNames.map(name=>JSON.parse(fs.readFileSync(path.join(v.trainDir,name),"utf8")));
 const learned=learnPrior(training);
 if(hash(learned.prior)!==receipt.meta_prior_sha256)errors.push("META_PRIOR_SHA_DRIFT");
 if(learned.trainedTasks!==400)errors.push("META_TRAIN_COUNT_DRIFT");
 const positive=Object.values(learned.prior).reduce((total,x)=>total+Object.values(x).reduce((a,b)=>a+b,0),0);
 if(positive!==9)errors.push("META_POSITIVE_COUNT_DRIFT");
 if(winners.length!==2||noFit.length!==31)errors.push("FIRST_EXACT_OR_TRAIN_CEILING_CHANGED");
 const verified=errors.length===0&&Bcorrect===receipt.stats.B_correct&&P20correct===receipt.stats.P20_correct&&
  P24correct===receipt.stats.P24_correct&&P25correct===receipt.stats.P25_correct&&baseline===receipt.stats.baseline_exact;
 return {schema:"neumann.q3.p27.independent-baseline-and-meta-audit.v1",verified,
  first_result_sha256:receipt.__original_raw_sha256||null,
  source_commit:v.cohort.upstream_commit,
  original_tasks:v.cohort.ids.length,
  baseline_correct:baseline,baseline_winners:winners,baseline_conflicts:conflicts,
  P11_B:Bcorrect,P20:P20correct,P24:P24correct,P25:P25correct,
  meta_training_tasks:learned.trainedTasks,meta_prior_positive:positive,
  no_train_consistent_P27_program_count:noFit.length,
  errors,global_Q1_Q7:"OPEN",
  interpretation:"Original first archived baseline and meta-policy checks only; no learned invention or new original solve."};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{
  const [arc,first]=process.argv.slice(2);
  if(!arc||!first)throw new Error("Usage: node experiments/q3_p27_baseline_meta_audit.mjs ARC_ROOT FIRST_JSON");
  const b=fs.readFileSync(first),r=JSON.parse(b);
  r.__original_raw_sha256=createHash("sha256").update(b).digest("hex");
  const out=auditBaseline(arc,r);
  process.stdout.write(JSON.stringify(out,null,2)+"\n");
  if(!out.verified)process.exitCode=1;
 }catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
