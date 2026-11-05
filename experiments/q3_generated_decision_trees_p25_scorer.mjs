/* P2.5 independent scorer contract, source frozen before new ARC body fetch.
 * scoreOriginal accesses original TEST outputs only after all proposals exist.
 * No test gold passed to a proposer or used in AST ranking. Research-only.
 */
function gridEq(a,b){
 return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.length>0&&a.every((row,r)=>Array.isArray(row)&&Array.isArray(b[r])&&row.length===b[r].length&&row.every((x,c)=>x===b[r][c]));
}
function scoreOriginal(task,B,Q,P20,C211,P24,P25){
 const train=task.train,testInputs=task.test.map(t=>t.input);
 const b=B.propose(train,testInputs,"B");
 const q=Q.generate(train,testInputs,B.GRIDOPS,B.applyGrid,"quotient");
 const p20=P20.propose(train,testInputs);
 const p24=P24.solve(train,testInputs);
 const programs=[b.proposals,q.prediction,p20.prediction,p24.prediction].filter(x=>x!==null);
 const conflict=programs.length>1&&programs.some(x=>JSON.stringify(x)!==JSON.stringify(programs[0]));
 let c=null,student=null;
 if(!conflict&&programs.length===0){
  c=C211.propose(train,testInputs);
  if(c.prediction===null)student=P25.solve(train,testInputs);
 }
 const baseline=conflict?null:programs[0]||c?.prediction||null;
 const predicted=baseline||student?.prediction||null;
 // Scorer now, for the FIRST time, accesses original test outputs.
 const originals=task.test.map(t=>t.output);
 const exact=proposals=>proposals!==null&&proposals.length===originals.length&&proposals.every((grid,i)=>gridEq(grid,originals[i]));
 const baseExact=exact(baseline),studentExact=student!==null&&exact(student.prediction);
 return {train_examples:train.length,test_examples:testInputs.length,
  B_exact:exact(b.proposals),Q_exact:exact(q.prediction),P20_exact:exact(p20.prediction),
  C211_exact:c!==null&&exact(c.prediction),P24_exact:exact(p24.prediction),
  baseline_exact:baseExact,combined_exact:exact(predicted),
  P25_additional_exact:studentExact&&!baseExact,
  P25_false_accept:student!==null&&student.prediction!==null&&!studentExact,
  combined_false_accept:predicted!==null&&!exact(predicted),
  baseline_conflict:conflict,
  B_attempts:b.trace.attempted,Q_operator_evals:q.trace.operator_evaluations,
  P20_AST_attempts:p20.trace.candidate_ast_count,C211_AST_attempts:c?.trace?.candidate_programs||0,
  P24_trace:p24.trace,P25_trace:student?.trace||null};
}
export {gridEq,scoreOriginal};