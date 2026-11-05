/* P2.5: bounded exact TRAIN-induced executable decision trees.
 * Classical per-task synthesis. NOT a neural student or autonomous opcode invention.
 */
import {inGrid,modeOutput,source,primitiveFacts} from "./q3_cached_typed_guard_p24.mjs";
const CONTRACT=Object.freeze({schema:"neumann.q3.p25.generated-tree.v1",maxDepth:3,splitBeam:12,maxPlans:8,maxRowsPerMode:1400,nodeBudgetPerMode:12000,neuralCalls:0,teacherCalls:0});
const MODES=["same","half_lr","half_tb","shift_0_-1","shift_0_1","shift_-1_0","shift_1_0"];
const exact=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.length>0&&a.every((r,i)=>Array.isArray(r)&&Array.isArray(b[i])&&r.length===b[i].length&&r.every((v,j)=>v===b[i][j]));
const value=(action,s)=>action==="a"?s.ctx.a:action==="b"?s.ctx.b:Number(action.slice(1));
const leafCost=x=>x==="a"?0.1:x==="b"?0.3:0.7;
function createExamples(train,mode){
 const rows=[];for(const p of train){
  const shape=modeOutput(mode,p.input);if(!shape||p.output.length!==shape.H||p.output[0]?.length!==shape.W)return null;
  for(let r=0;r<shape.H;r++)for(let c=0;c<shape.W;c++){
   const ctx=source(mode,p.input,r,c);rows.push({ctx,facts:primitiveFacts(ctx),target:p.output[r][c]});
   if(rows.length>CONTRACT.maxRowsPerMode)return null;
  }
 }return rows;
}
function testFeature(key,s){
 if(key.startsWith("flag:"))return !!s.facts[key.slice(5)];
 if(key.startsWith("aEq:"))return s.ctx.a===Number(key.slice(4));
 if(key.startsWith("bEq:"))return s.ctx.b===Number(key.slice(4));
 return false;
}
function featureSet(samples,train){
 const keys=Object.keys(samples[0].facts).map(x=>"flag:"+x);
 for(const k of [...new Set(train.flatMap(p=>p.input.flat()))].sort((a,b)=>a-b)){keys.push("aEq:"+k);keys.push("bEq:"+k);}
 return {keys,values:keys.map(k=>samples.map(s=>testFeature(k,s)))};
}
function gini(indices,samples){
 const n=indices.length;if(!n)return 0;const counts=new Map();for(const i of indices)counts.set(samples[i].target,(counts.get(samples[i].target)||0)+1);
 let score=1;for(const count of counts.values())score-=Math.pow(count/n,2);return score;
}
function splits(indices,samples,f){
 const base=gini(indices,samples),out=[];
 for(let j=0;j<f.keys.length;j++){
  const a=[],b=[];for(const i of indices)(f.values[j][i]?a:b).push(i);
  if(a.length===0||b.length===0)continue;
  const gain=base-(a.length*gini(a,samples)+b.length*gini(b,samples))/indices.length;
  out.push({name:f.keys[j],yes:a,no:b,gain});
 }
 out.sort((a,b)=>b.gain-a.gain||a.name.localeCompare(b.name));
 return out.slice(0,CONTRACT.splitBeam);
}
function top(plans){
 plans.sort((a,b)=>a.cost-b.cost||JSON.stringify(a.tree).localeCompare(JSON.stringify(b.tree)));
 const seen=new Set(),result=[];for(const p of plans){const str=JSON.stringify(p.tree);if(!seen.has(str)){result.push(p);seen.add(str);}if(result.length>=CONTRACT.maxPlans)break;}
 return result;
}
function trainTree(rows,f,actions,trace,mode){
 const memo=new Map();let nodes=0;
 function recurse(indices,depth){
  const key=depth+"|"+indices.join(",");if(memo.has(key))return memo.get(key);
  nodes++;trace.subproblems++;
  if(nodes>CONTRACT.nodeBudgetPerMode){trace.budget_exhaustions++;memo.set(key,[]);return [];}
  const leaves=[];
  for(const action of actions){trace.leaf_action_checks++;let ok=true;for(const i of indices)if(value(action,rows[i])!==rows[i].target){ok=false;break;}
   if(ok)leaves.push({tree:{kind:"action",action},cost:leafCost(action)});
  }
  if(leaves.length){const r=top(leaves);memo.set(key,r);return r;}
  if(depth===0||indices.length<2){memo.set(key,[]);return [];}
  let candidates=[];
  for(const split of splits(indices,rows,f)){
   trace.split_proposals++;const yes=recurse(split.yes,depth-1),no=recurse(split.no,depth-1);
   if(!yes.length||!no.length)continue;
   for(const a of yes.slice(0,3))for(const b of no.slice(0,3)){
    candidates.push({tree:{kind:"if",test:split.name,yes:a.tree,no:b.tree},cost:1+a.cost+b.cost});
   }
   candidates=top(candidates);
  }
  const r=top(candidates);memo.set(key,r);return r;
 }
 const plans=recurse(rows.map((_,i)=>i),CONTRACT.maxDepth);trace.unique_subproblems+=nodes;
 return plans.map(p=>({mode,tree:p.tree,score:p.cost}));
}
function execTree(tree,s){
 if(tree.kind==="action")return value(tree.action,s);
 return execTree(testFeature(tree.test,s)?tree.yes:tree.no,s);
}
function run(ast,g){
 if(!inGrid(g))return null;const sh=modeOutput(ast.mode,g);if(!sh)return null;
 const out=[];for(let r=0;r<sh.H;r++){const row=[];for(let c=0;c<sh.W;c++){
  const ctx=source(ast.mode,g,r,c),v=execTree(ast.tree,{ctx,facts:primitiveFacts(ctx)});
  if(!Number.isInteger(v)||v<0||v>9)return null;row.push(v);
 }out.push(row);}return out;
}
function solve(train,testInputs){
 const start=Date.now(),trace={schema:CONTRACT.schema,train_pairs:train?.length||0,modes:0,train_cell_samples:0,
   split_proposals:0,leaf_action_checks:0,subproblems:0,unique_subproblems:0,budget_exhaustions:0,
   tree_candidates:0,train_exact_candidates:0,original_test_program_evals:0,selected_AST:null,abstention:null,wall_ms:null,neural_calls:0,teacher_calls:0};
 const done=(prediction,reason)=>{trace.abstention=reason;trace.wall_ms=Date.now()-start;return {prediction,trace};};
 if(!Array.isArray(train)||!train.length||!train.every(p=>inGrid(p.input)&&inGrid(p.output))||!Array.isArray(testInputs)||!testInputs.length||!testInputs.every(inGrid))return done(null,"INVALID_INPUT");
 const palette=[...new Set(train.flatMap(p=>p.output.flat()))].sort((a,b)=>a-b),all=[];
 for(const mode of MODES){
  const rows=createExamples(train,mode);if(!rows||!rows.length)continue;
  trace.modes++;trace.train_cell_samples+=rows.length;
  const actions=["a",...(mode==="half_lr"||mode==="half_tb"?["b"]:[]),...palette.map(k=>"c"+k)];
  const plans=trainTree(rows,featureSet(rows,train),actions,trace,mode);
  for(const ast of plans){
   trace.tree_candidates++;let ok=true;
   for(const p of train)if(!exact(run(ast,p.input),p.output)){ok=false;break;}
   if(ok){trace.train_exact_candidates++;all.push(ast);}
  }
 }
 if(!all.length)return done(null,"NO_TRAIN_CONSISTENT_TREE");
 all.sort((a,b)=>a.score-b.score||JSON.stringify(a).localeCompare(JSON.stringify(b)));
 const best=all[0].score,tied=all.filter(x=>Math.abs(x.score-best)<1e-9);
 if(tied.length>CONTRACT.maxPlans)return done(null,"INCOMPLETE_MINIMUM_COST_CONSENSUS");
 const distinct=new Map();
 for(const ast of tied){
  const out=[];for(const g of testInputs){trace.original_test_program_evals++;out.push(run(ast,g));}
  if(out.some(g=>g===null))continue;
  distinct.set(JSON.stringify(out),{out,ast});
 }
 if(!distinct.size)return done(null,"UNSUPPORTED_TEST_EXECUTION");
 if(distinct.size>1)return done(null,"AMBIGUOUS_MINIMUM_COST_TREES");
 const item=distinct.values().next().value;trace.selected_AST=item.ast;
 return done(item.out,null);
}
export {CONTRACT,createExamples,featureSet,trainTree,run,solve};
