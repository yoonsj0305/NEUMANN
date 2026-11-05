/* NEUMANN P2.9 | Strongest prior CLASSICAL coverage audit of P29 19
 * previously scored public training positives. No new evaluation task opened.
 * Fair reference-set audit, not a blind-test architecture selection result.
 * All older code paths are used as frozen in git. Score each first-run
 * P29 success against P11B/P19/P20/P21/P211/P23/P24/P25/P27/P28.
 * Do NOT report oracle union as a deployable policy: it sees gold.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import * as P19 from "./q3_goal_conditioned_induction_p19.mjs";
import * as P21 from "./q3_object_rule_induction_p21.mjs";
import * as P211 from "./q3_object_rule_induction_p211.mjs";
import * as P23 from "./q3_typed_guard_ast_p23.mjs";
import * as P28 from "./q3_p28_factorized_operator.mjs";
import * as P29 from "./q3_p29_induced_coordinate_programs.mjs";

const FROZEN_P29_RECEIPT_SHA="d26186c52c2b3f6f7c969476aeeef47ff55dff3c026d220ee6e7a51a";
const CORE_GIT_BLOB="ca6f76504be5cf2fc00709b6479f0e8436c6fa18";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const sha=b=>createHash("sha256").update(b).digest("hex");
const blob=p=>{const b=fs.readFileSync(p);return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const expectedExact=(pred,gold)=>pred!==null&&eq(pred,gold);
const incoming=(t)=>Array.isArray(t?.train)&&t.train.length>0&&Array.isArray(t?.test)&&t.test.length>0;

export function audit(arcRoot,p29FirstFile,priorFiveFile) {
 const p29bytes=fs.readFileSync(p29FirstFile),priorbytes=fs.readFileSync(priorFiveFile);
 if(sha(p29bytes)!==FROZEN_P29_RECEIPT_SHA)throw Error("FIRST_P29_RECEIPT_SHA_DRIFT");
 if(blob(path.join(ROOT,"experiments/q3_p29_induced_coordinate_programs.mjs"))!==CORE_GIT_BLOB)
   throw Error("P29_FIRST_SOURCE_CHANGED");
 const first=JSON.parse(p29bytes),old=JSON.parse(priorbytes);
 if(first.stats.N!==400||first.stats.correct!==19||first.stats.false_submit!==1||
    old.counts.N!==400||old.counts.old_consensus_correct!==39||
    old.P29_first_receipt_sha256!==FROZEN_P29_RECEIPT_SHA)
   throw Error("RECEIPT_OR_STRONG_BASELINE_COUNTS_DRIFT");
 const positive=first.rows.filter(x=>x.correct);
 if(positive.length!==19)throw Error("NOT_NINETEEN_ORIGINAL_POSITIVES");
 const oldById=new Map(old.rows.map(x=>[x.id,x]));
 const t0=process.hrtime.bigint(),rows=[];
 for(const originalRow of positive) {
   const id=originalRow.id,prior=oldById.get(id),file=path.join(arcRoot,"data/training",id);
   if(!prior||!fs.existsSync(file))throw Error("MISSING_ORIGINAL:"+id);
   const task=JSON.parse(fs.readFileSync(file,"utf8"));
   if(!incoming(task))throw Error("INVALID_ORIGINAL:"+id);
   const tr=task.train,inputs=task.test.map(x=>x.input);
   const begin=process.hrtime.bigint(),extras=[
     {name:"P19",prediction:P19.propose(tr,inputs).prediction},
     {name:"P21",prediction:P21.propose(tr,inputs).prediction},
     {name:"P211",prediction:P211.propose(tr,inputs).prediction},
     {name:"P23",prediction:P23.solve(tr,inputs).prediction},
     {name:"P28",prediction:P28.propose(tr,inputs).prediction},
   ];
   // The very first P29 AST is executed independently of any new synthesis.
   const p29exec=originalRow.program?inputs.map(g=>P29.interpret(originalRow.program,g)):null;
   if(p29exec===null||p29exec.some(x=>x===null)||
      !tr.every(x=>eq(P29.interpret(originalRow.program,x.input),x.output)))
     throw Error("P29_FIRST_AST_ORIGINAL_REPLAY_FAILED:"+id);
   // Only score after every original prior proposer has returned.
   const gold=task.test.map(x=>x.output);
   if(!expectedExact(p29exec,gold))throw Error("ORIGINAL_P29_FIRST_SCORE_MISMATCH:"+id);
   const priorFive=prior.old_flags.map(Boolean);
   if(priorFive.length!==5)throw Error("MISSING_5_STRONG_BASELINES:"+id);
   const extrasResults=extras.map(x=>({
      name:x.name,submitted:x.prediction!==null,exact:expectedExact(x.prediction,gold),
      wrong:x.prediction!==null&&!expectedExact(x.prediction,gold),
   }));
   const covered=priorFive.some(Boolean)||extrasResults.some(x=>x.exact);
   const allAccepted=extras.map(x=>x.prediction).filter(x=>x!==null);
   const conflict=allAccepted.length>1&&!allAccepted.every(x=>eq(x,allAccepted[0]));
   rows.push({
      id,first_p29_correct:true,prior_strong_five_any_exact:priorFive.some(Boolean),
      prior_strong_five_flags:priorFive,
      extra_previous_classical:extrasResults,
      prior_all_10_oracle_union_exact:covered,
      first_p29_correct_not_in_any_prior_10:!covered,
      prior_extra_disagreement:conflict,
      counterfactual_selector_preregistered:false,
      baseline_experiment_wall_ms:Number(process.hrtime.bigint()-begin)/1e6,
   });
 }
 const total=k=>rows.filter(x=>x[k]).length;
 const extras=Object.fromEntries(["P19","P21","P211","P23","P28"].map(name=>[
    name,rows.filter(r=>r.extra_previous_classical.some(x=>x.name===name&&x.exact)).length]));
 return {
  schema:"neumann.q3.p29.maximal-prior-classical-coverage-on-first-positive19.v1",
  author_scope:"POST_HOC_OPENED_19_ONLY__NO_NEW_EVALUATION_OR_UNSEEN_TRANSFER",
  original_p29_census_sha256:sha(p29bytes),
  first_prior_five_full400_receipt_sha256:sha(priorbytes),
  first_p29_source_git_blob:CORE_GIT_BLOB,
  old_arm_names:["P11 B","P20","P24","P25","P27 classical","P19","P21","P211","P23","P28"],
  omitted_neural_controls:"None relevant; all matched arms here are classical fixed-language synthesis.",
  zero_new_heldout_consumed:true,
  zero_neural_calls:true,
  first_p29_correct_19_from_original_receipt:true,
  independent_first_p29_ast_replay:true,
  gold_only_for_diagnostic_score:true,
  posthoc_oracle_union_is_deployable:false,
  Q3_spontaneous_new_primitive:"NOT_PROVEN",
  Q6_unseen_semantic_family:"NOT_PROVEN",
  stats:{
    already_opened_p29_first_correct:19,
    covered_by_previously_compared_five:total("prior_strong_five_any_exact"),
    additional_coverage_from_five_older_omitted_arms:total("prior_all_10_oracle_union_exact")-total("prior_strong_five_any_exact"),
    total_covered_by_any_prior_10:total("prior_all_10_oracle_union_exact"),
    p29_not_solved_by_ANY_frozen_prior_10:total("first_p29_correct_not_in_any_prior_10"),
    per_missing_classical_arm_correct_among_19:extras,
    diagnostic_wall_ms:Number(process.hrtime.bigint()-t0)/1e6
  },
  rows
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
 if(process.argv.length!==5)throw Error("node experiments/q3_p29_maximal_prior_audit.mjs ARC_ROOT P29_FIRST400_JSON PREVIOUS5_400_JSON");
 try{process.stdout.write(JSON.stringify(audit(process.argv[2],process.argv[3],process.argv[4]),null,2)+"\n");}
 catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
