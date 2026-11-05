/* NEUMANN P2.7 original-only independent scorer.
 * All proposals computed before accessing ANY official evaluation TEST output.
 * Public training test gold is used only for supervised meta-training, not evaluation.
 */
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import {synthesize,eq,runProgram,allASTs,learnPrior} from "./q3_compositional_schema_learning_p27.mjs";
const exact=(pred,target)=>pred!==null&&pred.length===target.length&&pred.every((g,i)=>eq(g,target[i]));
const signature=x=>JSON.stringify(x);
export function evaluateOriginal(task,prior){
 const started=process.hrtime.bigint(),train=task.train,query=task.test.map(x=>x.input);
 const b=B.propose(train,query,"B");
 const p20=P20.propose(train,query);
 const p24=P24.solve(train,query);
 const p25=P25.solve(train,query);
 const classical=synthesize(train,query,{selector:"classical",maxCandidates:allASTs.length});
 const learned=synthesize(train,query,{selector:"learned",prior,maxCandidates:allASTs.length});
 const models=[b.proposals,p20.prediction,p24.prediction,p25.prediction].filter(p=>p!==null);
 const conflict=models.length>1&&models.some(p=>signature(p)!==signature(models[0]));
 const baseline=conflict?null:models[0]||null;
 // Neither full consensus nor learned tie-break uses any TEST oracle.
 // Existing controls have priority, disagreement degrades safely to ABSTAIN.
 const combine=(additional)=>{
  if(conflict)return null;
  if(baseline!==null&&additional!==null&&signature(additional)!==signature(baseline))return null;
  return baseline??additional;
 };
 const classicalFinal=combine(classical.prediction),learnedFinal=combine(learned.prediction);
 for(const result of [classical,learned]){
  if(result.prediction!==null){
   const p=result.trace.selected_AST;
   if(!p||!train.every(pair=>eq(runProgram(p,pair.input),pair.output))||
       !query.every((g,i)=>eq(runProgram(p,g),result.prediction[i])))
       throw new Error("INDEPENDENT_AST_REPLAY_FAIL");
  }
 }
 const wall_ms=Number(process.hrtime.bigint()-started)/1e6;
 // First read of official evaluation TEST GOLD begins here, after all proposals.
 const target=task.test.map(x=>x.output);
 return {
  B_correct:exact(b.proposals,target),P20_correct:exact(p20.prediction,target),
  P24_correct:exact(p24.prediction,target),P25_correct:exact(p25.prediction,target),
  baseline_conflict:conflict,baseline_exact:exact(baseline,target),
  classical_exact:exact(classical.prediction,target),learned_exact:exact(learned.prediction,target),
  classical_false_accept:classical.prediction!==null&&!exact(classical.prediction,target),
  learned_false_accept:learned.prediction!==null&&!exact(learned.prediction,target),
  classical_combined_exact:exact(classicalFinal,target),
  learned_combined_exact:exact(learnedFinal,target),
  classical_combined_false_accept:classicalFinal!==null&&!exact(classicalFinal,target),
  learned_combined_false_accept:learnedFinal!==null&&!exact(learnedFinal,target),
  baseline_attempts:b.trace.attempted,P20_attempts:p20.trace.candidate_ast_count,
  P25_split_proposals:p25.trace.split_proposals,
  classical_trace:classical.trace,learned_trace:learned.trace,
  train_count:train.length,test_count:query.length,
  study_wall_ms:wall_ms
 };
}
export function aggregate(rows,priorReceipt){
 const sum=k=>rows.filter(x=>x[k]).length;
 const stats={
  task_count:rows.length,
  B_correct:sum("B_correct"),P20_correct:sum("P20_correct"),
  P24_correct:sum("P24_correct"),P25_correct:sum("P25_correct"),
  baseline_exact:sum("baseline_exact"),
  classical_exact:sum("classical_exact"),learned_exact:sum("learned_exact"),
  classical_false_accept:sum("classical_false_accept"),learned_false_accept:sum("learned_false_accept"),
  classical_combined_exact:sum("classical_combined_exact"),
  learned_combined_exact:sum("learned_combined_exact"),
  classical_combined_false_accept:sum("classical_combined_false_accept"),
  learned_combined_false_accept:sum("learned_combined_false_accept"),
  baseline_conflict:sum("baseline_conflict"),
  total_p27_classical_inference_ms:rows.reduce((a,b)=>a+b.classical_trace.wall_ms,0),
  total_p27_learned_inference_ms:rows.reduce((a,b)=>a+b.learned_trace.wall_ms,0),
  total_all_controls_inference_ms:rows.reduce((a,b)=>a+b.study_wall_ms,0),
  meta_training_ms:priorReceipt.stats.wall_ms,
  meta_training_tasks:priorReceipt.trainedTasks,
  total_p27_learned_cost_ms:priorReceipt.stats.wall_ms+rows.reduce((a,b)=>a+b.learned_trace.wall_ms,0)
 };
 stats.learned_new_exact_over_classical=rows.filter(x=>x.learned_exact&&!x.classical_exact).length;
 stats.classical_new_exact_over_learned=rows.filter(x=>x.classical_exact&&!x.learned_exact).length;
 stats.classical_new_correct_vs_baseline=rows.filter(x=>x.classical_combined_exact&&!x.baseline_exact).length;
 stats.learned_new_correct_vs_baseline=rows.filter(x=>x.learned_combined_exact&&!x.baseline_exact).length;
 const gate=stats.learned_new_correct_vs_baseline>=2&&stats.learned_combined_false_accept===0&&
            stats.learned_new_exact_over_classical>=1;
 return {schema:"neumann.q3.p27.first-original-cohort-score.v1",
  original_upstream:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  prior_training:"official public data/training only, supervised on its test labels",
  original_test_predictions_made_without_test_gold:true,teacher_calls:0,neural_calls:0,
  note:"Fixed human primitive grammar, only combinatorial macros and prior learned. Not autonomous new opcode or JEPA.",
  stats,local_gate:gate?"LOCAL_PASS_NOT_GLOBAL_Q3":"FAIL_OR_INCONCLUSIVE",global_Q1_Q7:"OPEN",rows
 };
}
export {learnPrior};
