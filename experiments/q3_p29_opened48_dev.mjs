/* P2.9 original ARC 48 OPENED DEVELOPMENT (not blind heldout).
 * Original first P2.8 cohort is already publicly scored in this project.
 * This is ONLY a mechanism/program/coverage diagnostic, not first unseen transfer.
 * Strong legacy classical controls are re-executed on exactly same data.
 * P29 is itself classical enumeration of a human-defined coordinate grammar.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import * as P29 from "./q3_p29_induced_coordinate_programs.mjs";

const ROOT=new URL("../",import.meta.url).pathname;
const json=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const sha256=data=>createHash("sha256").update(data).digest("hex");
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(guess,gold)=>guess!==null&&eq(guess,gold);
const baseline=(task)=>{
 const tr=task.train,inputs=task.test.map(p=>p.input);
 const b=B.propose(tr,inputs,"B").proposals;
 const p20=P20.propose(tr,inputs).prediction;
 const p24=P24.solve(tr,inputs).prediction;
 const p25=P25.solve(tr,inputs).prediction;
 const p27=P27.synthesize(tr,inputs,{selector:"classical",maxCandidates:P27.allASTs.length}).prediction;
 const active=[b,p20,p24,p25,p27].filter(x=>x!==null);
 const conflict=active.length>1&&!active.every(p=>eq(p,active[0]));
 return {prediction:conflict?null:(active[0]??null),conflict};
};
export function assess(task,id,expectedOld) {
 // Re-run all controls from same frozen exact public TRAIN and TEST INPUTS.
 const base=baseline(task);
 const input=task.test.map(p=>p.input);
 const result=P29.synthesize(task.train,input);
 const newCandidate=result.prediction;
 if(newCandidate!==null){
   if(result.trace.ast===null)throw Error("NO_EXECUTABLE_AST:"+id);
   for(const p of task.train)if(!eq(P29.interpret(result.trace.ast,p.input),p.output))throw Error("TRAIN_DRIFT:"+id);
   for(let i=0;i<input.length;i++)if(!eq(P29.interpret(result.trace.ast,input[i]),newCandidate[i]))throw Error("EXECUTION_DRIFT:"+id);
 }
 // If old systems disagree, do NOT use new P29 to circumvent old conflict.
 const safe=base.conflict?null:(base.prediction!==null&&newCandidate!==null&&!eq(base.prediction,newCandidate)
     ?null:(base.prediction??newCandidate));
 // TEST gold is read after both baseline and new proposals.
 const gold=task.test.map(p=>p.output);
 const bc=exact(base.prediction,gold),pc=exact(newCandidate,gold),cc=exact(safe,gold);
 if(expectedOld){
  if(bc!==expectedOld.old_consensus_correct||base.conflict!==expectedOld.old_baseline_conflict)
   throw Error("PRIOR_FIRST_BASELINE_MISMATCH:"+id);
 }
 return {id,
  old_correct:bc,old_submitted:base.prediction!==null,old_conflict:base.conflict,
  p29_correct:pc,p29_submitted:newCandidate!==null,p29_wrong:newCandidate!==null&&!pc,
  safe_correct:cc,safe_submitted:safe!==null,safe_wrong:safe!==null&&!cc,
  gained:cc&&!bc,lost:bc&&!cc,raw_additional:pc&&!bc,
  trace:result.trace,
  ast:result.trace.ast
 };
}
export function openedRun(arc,firstFile) {
 const started=process.hrtime.bigint();
 const raw=fs.readFileSync(firstFile);
 if(sha256(raw)!=="1b708e7ccb3686637ee8a8cefcbdba1e03b1aa4abfaebe48d3eba8e51f84bd78")
   throw Error("ORIGINAL_FIRST_P28_RECEIPT_SHA_DRIFT");
 const first=JSON.parse(raw);
 const manifest=json(path.join(ROOT,"docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json"));
 if(first.rows.length!==48||manifest.ids.length!==48)throw Error("UNEXPECTED_REUSED_COUNT");
 const rows=[];
 for(let i=0;i<48;i++){
   const filename=manifest.ids[i],taskBytes=fs.readFileSync(path.join(arc,"data/evaluation",filename));
   if(sha256(taskBytes)!==first.rows[i].original_file_sha256)
      throw Error("ORIGINAL_FILE_SHA_DRIFT:"+filename);
   const task=JSON.parse(taskBytes);
   rows.push(assess(task,filename.slice(0,-5),first.rows[i]));
 }
 const count=key=>rows.filter(r=>r[key]).length;
 return {
  schema:"neumann.q3.p29.opened-prior-eval48-development.v1",
  scope:"REUSED_PREVIOUSLY_SCORED_48_ORIGINALS_NOT_FRESH_HOLDOUT",
  original_first_P28_sha256:sha256(raw),
  P29_is_human_specified_symbolic_grammar:true,
  P29_learned_model_calls:0,P29_teacher_calls:0,
  Q3_autonomous_opcode_invention:"NOT_PROVEN",
  Q6_unseen_semantic_family:"NOT_PROVEN",
  stats:{
    n:rows.length,old_correct:count("old_correct"),p29_correct:count("p29_correct"),
    p29_submitted:count("p29_submitted"),p29_wrong:count("p29_wrong"),
    safe_correct:count("safe_correct"),safe_wrong:count("safe_wrong"),safe_submitted:count("safe_submitted"),
    gained:count("gained"),lost:count("lost"),raw_additional:count("raw_additional"),
    p29_train_fit:rows.filter(r=>r.trace.ast!==null).length,
    p29_shape_rule_found:rows.filter(r=>r.trace.shapePrograms>0).length,
    time_ms:Number(process.hrtime.bigint()-started)/1e6
  },rows
 };
}
if(process.argv[1]&&process.argv[1].endsWith("q3_p29_opened48_dev.mjs")){
 if(process.argv.length!==4)throw Error("node experiments/q3_p29_opened48_dev.mjs ARC_ROOT FIRST_P28_RECEIPT");
 try{console.log(JSON.stringify(openedRun(process.argv[2],process.argv[3]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
