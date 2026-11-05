/* P1.5.1 | Exhaustive 12,719-program finite-grammar audit.
 * Naive N and semantic-train-state DAG M enumerate the SAME ASTs.
 * Train-observation equivalence is used ONLY to share train computation,
 * never as a claim of test-behavior equivalence.
 * No frontier model, neural training, task ID routing, or gold test labels in proposal.
 */
const VERSION="neumann.q3.p151.exhaustive-and-dag.v1";
function validGrid(g){return Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));}
function exactGrid(a,b){return validGrid(a)&&validGrid(b)&&a.length===b.length&&a.every((row,i)=>row.length===b[i].length&&row.every((v,j)=>v===b[i][j]));}
function runProgram(seq,input,applyGrid,trace){
 let g=input;if(!validGrid(g))return null;
 for(const op of seq){
  trace.calls++;
  try{g=applyGrid(g,op);}catch(e){return null;}
  if(!validGrid(g))return null;
 }
 return g;
}
function predictConsistent(sequences,testInputs,applyGrid){
 if(sequences.length===0)return {status:"ABSTAIN_NO_TRAIN_PROGRAM",output:null,interpreter_calls:0};
 const trace={calls:0},outputs=[];
 for(const sequence of sequences){
  const pred=[];
  for(const input of testInputs){const out=runProgram(sequence,input,applyGrid,trace);if(out===null)return {status:"ABSTAIN_TEST_INVALID",output:null,interpreter_calls:trace.calls};pred.push(out);}
  if(outputs.length>0){
   const first=outputs[0];if(first.length!==pred.length||first.some((g,i)=>!exactGrid(g,pred[i])))return {status:"ABSTAIN_DISAGREEMENT",output:null,interpreter_calls:trace.calls};
  }
  outputs.push(pred);
 }
 return {status:"PREDICT_CONSENSUS",output:outputs[0],interpreter_calls:trace.calls};
}
function naive(train,programs,applyGrid){
 const t0=Date.now(),trace={method:"N",ast_checked:0,interpreter_calls:0,invalid_programs:0,exact_training:0,search_ms:null};
 const found=[];
 for(const seq of programs){
  trace.ast_checked++;let valid=true,consistent=true;
  for(const pair of train){
   const out=runProgram(seq,pair.input,applyGrid,{get calls(){return 0;},set calls(v){trace.interpreter_calls++;}});
   if(out===null){valid=false;consistent=false;break;}
   if(!exactGrid(out,pair.output))consistent=false;
  }
  if(!valid)trace.invalid_programs++;
  if(consistent){found.push(seq);trace.exact_training++;}
 }
 trace.search_ms=Date.now()-t0;
 return {found,trace};
}
function dag(train,programs,applyGrid){
 const t0=Date.now();
 const trace={method:"M",ast_checked:0,interpreter_calls:0,invalid_programs:0,exact_training:0,transition_hits:0,transition_misses:0,distinct_train_states:0,signature_code_units:0,search_ms:null};
 const target=JSON.stringify(train.map(e=>e.output));
 const states=[],stateBySignature=new Map(),transitionCache=new Map();
 function intern(views){
  const signature=JSON.stringify(views);
  if(stateBySignature.has(signature))return stateBySignature.get(signature);
  const id=states.length;
  states.push({views,signature});stateBySignature.set(signature,id);
  trace.signature_code_units+=signature.length;
  return id;
 }
 const root=intern(train.map(e=>e.input));
 function next(stateId,op){
  if(stateId===-1)return -1;
  const key=stateId+":"+op;
  if(transitionCache.has(key)){trace.transition_hits++;return transitionCache.get(key);}
  trace.transition_misses++;
  const views=[];
  for(const g of states[stateId].views){
   let result=null;trace.interpreter_calls++;
   try{result=applyGrid(g,op);}catch(e){}
   if(!validGrid(result)){transitionCache.set(key,-1);return -1;}
   views.push(result);
  }
  const resultId=intern(views);
  transitionCache.set(key,resultId);
  return resultId;
 }
 const found=[];
 for(const seq of programs){
  trace.ast_checked++;let current=root;
  for(const op of seq){current=next(current,op);if(current===-1)break;}
  if(current===-1){trace.invalid_programs++;continue;}
  if(states[current].signature===target){found.push(seq);trace.exact_training++;}
 }
 trace.distinct_train_states=states.length;
 trace.search_ms=Date.now()-t0;
 return {found,trace};
}
function compareTask(task,ops,applyGrid,uniformPrograms){
 const train=task.train,testInputs=task.test.map(e=>e.input);
 const Nprograms=uniformPrograms(ops,12719);
 if(Nprograms.length!==12719)throw Error("Not exhaustive");
 const N=naive(train,Nprograms,applyGrid),M=dag(train,Nprograms,applyGrid);
 const canonical=seq=>seq.join("\u001f");
 const identical=N.found.length===M.found.length&&N.found.every((p,i)=>canonical(p)===canonical(M.found[i]));
 const nPred=predictConsistent(N.found,testInputs,applyGrid);
 const mPred=predictConsistent(M.found,testInputs,applyGrid);
 const equalPrediction=JSON.stringify(nPred.output)===JSON.stringify(mPred.output)&&nPred.status===mPred.status;
 // Original test target is read only after both programs and predictions are fixed.
 const original=task.test.map(e=>e.output);
 const isExact=result=>result.output!==null&&result.output.length===original.length&&result.output.every((g,i)=>exactGrid(g,original[i]));
 return {same_exact_ast_sequence:identical,same_test_prediction_and_status:equalPrediction,original_task_N_exact:isExact(nPred),original_task_M_exact:isExact(mPred),
         n_status:nPred.status,m_status:mPred.status,n_exact_ast_count:N.found.length,m_exact_ast_count:M.found.length,
         n_test_calls:nPred.interpreter_calls,m_test_calls:mPred.interpreter_calls,n_trace:N.trace,m_trace:M.trace};
}
export {VERSION,naive,dag,compareTask,runProgram,predictConsistent};
