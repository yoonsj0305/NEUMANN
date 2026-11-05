/* NEUMANN P1.6: sound exact observational quotient of executable grid-prefixes.
 * A (prefix): cache each syntactic AST prefix and explore every well-typed valid state.
 * Q (quotient): cache each semantic output tuple on original train+test INPUTS
 * and remove redundant successor subtrees.
 * All original TEST outputs are passed ONLY to independent scoreOriginal.
 *
 * Proposition: if p(x)=q(x) for all x in X, then for any deterministic
 * continuation h, h(p(x))=h(q(x)) for every x in X. Formal suffix induction
 * guarantees P/Q identical complete behavior sets on these particular X.
 */
const CONTRACT=Object.freeze({
  schema:"neumann.q3.exact-semantic-quotient.p16.v1",
  maxDepth:3,maxShape:30,
  stopOnFirstTrainFit:false,neuralCalls:0,JEPA:"NOT_RUN",
  verification:"exact full original train outputs, consensus on all test input predictions"
});
function grid(g){
  return Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30
    &&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
}
function sameGrid(a,b){
  return grid(a)&&grid(b)&&a.length===b.length&&a.every((row,r)=>row.length===b[r].length&&row.every((v,c)=>v===b[r][c]));
}
function canonState(outputs){
  // FULL exact serialized output of EVERY original train and test input.
  // No lossy hashes, labels or stochastic embeddings used.
  return JSON.stringify(outputs);
}
function generate(train,testInputs,ops,applyGrid,mode){
  const started=Date.now();
  const trace={arm:mode,depth_limit:CONTRACT.maxDepth,original_input_count:0,operator_names:ops.length,
    operator_evaluations:0,syntactic_candidates:0,valid_candidates:0,invalid_candidates:0,
    behavior_states:0,pruned_equivalent_successors:0,explored_prefixes:0,
    train_consistent_programs:0,distinct_train_consistent_test_predictions:0,
    representative_programs:[],abstention:null,study_wall_ms:null,neural_forwards:0};
  if(!Array.isArray(train)||train.length<1||!Array.isArray(testInputs)||testInputs.length<1||!Array.isArray(ops)||ops.length<1
     ||!train.every(p=>grid(p.input)&&grid(p.output))||!testInputs.every(grid)){
    trace.abstention="INVALID_INPUT";
    trace.study_wall_ms=Date.now()-started;
    return {prediction:null,trace};
  }
  const X=train.map(p=>p.input).concat(testInputs);
  const nTrain=train.length;
  trace.original_input_count=X.length;
  const root={states:X,code:[]};
  let layer=[root],depth=0;
  const known=new Set([canonState(X)]), fittingPredictions=new Map();
  while(layer.length>0&&depth<CONTRACT.maxDepth){
    const upcoming=[];
    for(const node of layer){
      trace.explored_prefixes++;
      for(const op of ops){
        trace.syntactic_candidates++;
        const transformed=[];let valid=true;
        // Fail-closed partial computations; a null intermediate cannot be recovered.
        for(const inp of node.states){
          trace.operator_evaluations++;
          let out=null;
          try{out=applyGrid(inp,op);}catch(error){}
          if(!grid(out)){valid=false;break;}
          transformed.push(out);
        }
        if(!valid){trace.invalid_candidates++;continue;}
        trace.valid_candidates++;
        const code=node.code.concat(op);
        let isFit=true;
        for(let k=0;k<nTrain;k++)if(!sameGrid(transformed[k],train[k].output)){isFit=false;break;}
        if(isFit){
          trace.train_consistent_programs++;
          const testOutputs=transformed.slice(nTrain);
          const signature=canonState(testOutputs);
          if(!fittingPredictions.has(signature)){
            fittingPredictions.set(signature,{outputs:testOutputs,program:code});
          }
        }
        if(depth+1<CONTRACT.maxDepth){
          if(mode==="quotient"){
            const stateSignature=canonState(transformed);
            if(known.has(stateSignature)){trace.pruned_equivalent_successors++;continue;}
            known.add(stateSignature);
          }
          upcoming.push({states:transformed,code});
        }
      }
    }
    depth++;
    layer=upcoming;
  }
  trace.behavior_states=mode==="quotient"?known.size:null;
  trace.distinct_train_consistent_test_predictions=fittingPredictions.size;
  trace.representative_programs=[...fittingPredictions.values()].slice(0,3).map(x=>x.program);
  let prediction=null;
  if(fittingPredictions.size===0)trace.abstention="NO_TRAIN_CONSISTENT_PROGRAM";
  else if(fittingPredictions.size>1)trace.abstention="AMBIGUOUS_TEST_PREDICTIONS";
  else prediction=[...fittingPredictions.values()][0].outputs;
  trace.study_wall_ms=Date.now()-started;
  return {prediction,trace};
}
function independentScore(task,ops,applyGrid){
  // These original gold outputs are not reachable by generate(), which receives
  // only the train pairs and test inputs, never a whole task.
  const testInputs=task.test.map(p=>p.input);
  const P=generate(task.train,testInputs,ops,applyGrid,"prefix");
  const Q=generate(task.train,testInputs,ops,applyGrid,"quotient");
  const identical=(P.prediction===null&&Q.prediction===null)||
    (P.prediction!==null&&Q.prediction!==null&&canonState(P.prediction)===canonState(Q.prediction));
  const matchingReason=P.trace.abstention===Q.trace.abstention;
  // Reach original TEST gold only now.
  const targets=task.test.map(p=>p.output);
  const exact=pred=>pred!==null&&pred.length===targets.length&&pred.every((g,i)=>sameGrid(g,targets[i]));
  const scoreP=exact(P.prediction),scoreQ=exact(Q.prediction);
  return {P_original_exact:scoreP,Q_original_exact:scoreQ,
    semantic_behavior_preserved:identical&&matchingReason,
    P_false_accept:P.prediction!==null&&!scoreP,
    Q_false_accept:Q.prediction!==null&&!scoreQ,
    P:P.trace,Q:Q.trace,
    train_cases:task.train.length,test_cases:task.test.length};
}
function fnv32(text){let h=2166136261;for(let i=0;i<text.length;i++)h=Math.imul(h^text.charCodeAt(i),16777619)>>>0;return h>>>0;}
function selectCohort(names,excluded){
  const blocked=new Set(excluded);
  return names.filter(name=>name.endsWith(".json")&&!blocked.has(name))
    .map(name=>({name,rank:fnv32("neumann-q3-p16-20261105|"+name)}))
    .sort((a,b)=>a.rank-b.rank||a.name.localeCompare(b.name)).slice(0,24).map(x=>x.name);
}
export {CONTRACT,grid,canonState,generate,independentScore,selectCohort};
