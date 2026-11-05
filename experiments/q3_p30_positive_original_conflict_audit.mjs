/* Read-only P3.0 positive original-task diagnostic and safe baseline conflict.
 * Only previously OPENED public ARC training files are evaluated.
 */
import fs from "node:fs";import path from "node:path";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import * as P30 from "./q3_p30_object_relational_recolor.mjs";
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const original=process.argv[2],p=JSON.parse(fs.readFileSync(process.argv[3],"utf8"));
if(p.stats.N!==400||p.stats.P30_correct!==1||p.stats.P30_wrong!==0)throw Error("FIRST_POSITIVE_DRIFT");
for(const first of p.rows.filter(x=>x.P30_submitted)){
 const task=JSON.parse(fs.readFileSync(path.join(original,"data/training",first.id),"utf8"));
 const tr=task.train,inputs=task.test.map(t=>t.input);
 const legacy=[
  B.propose(tr,inputs,"B").proposals,P20.propose(tr,inputs).prediction,
  P24.solve(tr,inputs).prediction,P25.solve(tr,inputs).prediction,
  P27.synthesize(tr,inputs,{selector:"classical",maxCandidates:P27.allASTs.length}).prediction
 ];
 const live=legacy.filter(x=>x!==null);
 const conflict=live.length>1&&live.some(x=>!eq(x,live[0]));
 const old=conflict?null:(live[0]||null);
 const next=P30.synthesize(tr,inputs);
 const newval=next.prediction;
 if(!newval||!next.trace.ast)throw Error("ORIGINAL_P30_NEW_NOT_REPLAYABLE");
 const final=conflict||old!==null&&!eq(old,newval)?null:old||newval;
 // Gold score AFTER complete baseline and P30 proposal.
 const gold=task.test.map(t=>t.output);
 const answer=x=>x!==null&&eq(x,gold);
 const result={id:first.id,old_control_submitted:old!==null,old_control_exact:answer(old),
   new_program_kind:next.trace.ast.kind,new_program_partition:next.trace.ast.partition,
   new_program_predicate:next.trace.ast.predicate,new_program_when:next.trace.ast.when,
   new_program_otherwise:next.trace.ast.otherwise,
   new_program_exact:answer(newval),safe_combined_submitted:final!==null,
   safe_combined_exact:answer(final),new_added_without_conflict:answer(final)&&!answer(old),
   full_source_original_gold_read_only_after_proposal:true};
 console.log(JSON.stringify(result));
}
