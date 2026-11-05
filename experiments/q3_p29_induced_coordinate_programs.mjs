/* NEUMANN P2.9 | Example-induced, typed coordinate programs.
 * A deliberately explicit and bounded symbolic metagrammar; source-level
 * relational program search, not autonomous universal opcode invention.
 *
 * Generic operation learned from TRAIN examples:
 *   outputShape = (F(h,w), G(h,w))
 *   view_i[r,c] = input[rowTerm_i(r,c,h,w,H,W)][colTerm_i(...)]
 *   output[r,c] = color-map(view_0) OR table(mask(view_0,view_1))
 *
 * Reuse of the SAME generated program on TEST input sizes and colors is the
 * only generalization. Original TEST target outputs are NEVER read here.
 */
export const CONTRACT=Object.freeze({
 schema:"neumann.q3.p29.example-induced-coordinate-language.v1",
 maxGrid:30,maxTrainPairs:12,maxTestInputs:5,maxViews:100,
 maxGeometryPairs:10000,maxShapes:36,
 newHumanPrimitives:["dimension-expressions","coordinate-terms","palette-or-two-view-mask"],
 labelFeedback:false,teacherCalls:0,neuralCalls:0,training:false,
 degradedMode:"ABSTAIN",fullCost10xClaim:false,autonomousOpcodeClaim:false
});
const copy=x=>JSON.parse(JSON.stringify(x));
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const grid=g=>Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&
 g[0].length>0&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&
 row.every(c=>Number.isInteger(c)&&c>=0&&c<=9));
function dimOps(axis) {
 const normal=axis==="row"?"h":"w",other=axis==="row"?"w":"h";
 const d=[
  {id:normal,cost:0,run:(h,w)=>axis==="row"?h:w},
  {id:other,cost:4,run:(h,w)=>axis==="row"?w:h},
  {id:"h*w",cost:6,run:(h,w)=>h*w},
  {id:"h*h",cost:7,run:(h,w)=>h*h},
  {id:"w*w",cost:7,run:(h,w)=>w*w}
 ];
 for(let k=2;k<=5;k++){
  d.push({id:k+"*"+normal,cost:3+k,run:(h,w)=>k*(axis==="row"?h:w)});
  d.push({id:k+"*"+other,cost:7+k,run:(h,w)=>k*(axis==="row"?w:h)});
 }
 d.push({id:normal+"+1",cost:9,run:(h,w)=>(axis==="row"?h:w)+1});
 return d;
}
const ROW_DIMS=dimOps("row"),COL_DIMS=dimOps("col");
function size(g,what) { return what==="h"?g.length:g[0].length; }
function evalDim(op,g) {return op.run(g.length,g[0].length);}
function coordTerms(targetAxis) {
 const n=targetAxis==="row"?"h":"w",primary=targetAxis==="row"?"r":"c";
 const terms=[];
 for(const axis of ["r","c"])for(const kind of ["raw","mod","block","stretch"])
 for(const reverse of [false,true]) {
   const id=axis+":"+kind+(reverse?":reverse":"");
   const cost=(axis===primary?0:5)+
     ({raw:0,mod:3,block:4,stretch:2}[kind])+(reverse?2:0);
   terms.push({id,cost,axis,kind,reverse,n});
 }
 return terms;
}
const ROW_TERMS=coordTerms("row"),COL_TERMS=coordTerms("col");
function idx(term,r,c,h,w,H,W) {
 const n=term.n==="h"?h:w;
 const q=term.axis==="r"?r:c;
 const L=term.axis==="r"?H:W;
 let out;
 if(term.kind==="raw")out=q;
 else if(term.kind==="mod")out=q%n;
 else if(term.kind==="block")out=Math.floor(q/n);
 else {
   if(L%n!==0)return null;
   out=Math.floor(q/(L/n));
 }
 if(term.reverse)out=n-1-out;
 return Number.isInteger(out)&&out>=0&&out<n?out:null;
}
function dims(p) {return [p.input.length,p.input[0].length,p.output.length,p.output[0].length];}
function validTask(train,tests) {
 return Array.isArray(train)&&train.length>0&&train.length<=CONTRACT.maxTrainPairs&&
 train.every(p=>p&&grid(p.input)&&grid(p.output))&&Array.isArray(tests)&&tests.length>0&&
 tests.length<=CONTRACT.maxTestInputs&&tests.every(grid);
}
export function shapeCandidates(train,tests) {
 if(!validTask(train,tests))return [];
 const out=[];
 for(const R of ROW_DIMS)for(const C of COL_DIMS) {
   if(!train.every(p=>evalDim(R,p.input)===p.output.length&&evalDim(C,p.input)===p.output[0].length))continue;
   const target=tests.map(g=>[evalDim(R,g),evalDim(C,g)]);
   if(target.some(([h,w])=>h<1||w<1||h>30||w>30))continue;
   out.push({row:R.id,col:C.id,cost:R.cost+C.cost,target,
             rowOp:R,colOp:C});
 }
 return out.sort((a,b)=>a.cost-b.cost||a.row.localeCompare(b.row)||a.col.localeCompare(b.col)).
   slice(0,CONTRACT.maxShapes);
}
function projected(termRow,termCol,input,H,W) {
 const h=input.length,w=input[0].length,flat=[];
 for(let r=0;r<H;r++)for(let c=0;c<W;c++){
   const rr=idx(termRow,r,c,h,w,H,W),cc=idx(termCol,r,c,h,w,H,W);
   if(rr===null||cc===null)return null;
   flat.push(input[rr][cc]);
 }
 return flat;
}
function viewsFor(shape,train,tests) {
 const inputs=train.map(p=>p.input).concat(tests);
 const targetSizes=train.map(p=>[p.output.length,p.output[0].length]).concat(shape.target);
 const seen=new Map();
 for(const rr of ROW_TERMS)for(const cc of COL_TERMS) {
   const values=[];
   let ok=true;
   for(let t=0;t<inputs.length;t++){
     const x=projected(rr,cc,inputs[t],targetSizes[t][0],targetSizes[t][1]);
     if(x===null){ok=false;break;}
     values.push(x);
   }
   if(!ok)continue;
   const key=JSON.stringify(values);
   const val={row:rr.id,col:cc.id,values,cost:rr.cost+cc.cost,
      syntax:{row:rr.id,col:cc.id}};
   if(!seen.has(key)||val.cost<seen.get(key).cost||
      (val.cost===seen.get(key).cost&&val.row+" "+val.col<seen.get(key).row+" "+seen.get(key).col))
     seen.set(key,val);
 }
 return [...seen.values()].sort((a,b)=>a.cost-b.cost||a.row.localeCompare(b.row)||a.col.localeCompare(b.col)).
   slice(0,CONTRACT.maxViews);
}
function unflatten(flat,H,W) {
 const y=[];for(let r=0;r<H;r++)y.push(flat.slice(r*W,(r+1)*W));return y;
}
function evaluateUnary(view,train,tests,shape) {
 const palette=new Map();
 for(let t=0;t<train.length;t++){
   const vals=view.values[t],gold=train[t].output.flat();
   for(let j=0;j<vals.length;j++){
     if(palette.has(vals[j])&&palette.get(vals[j])!==gold[j])return null;
     palette.set(vals[j],gold[j]);
   }
 }
 const predicted=[];
 for(let i=0;i<tests.length;i++){
   const flat=view.values[train.length+i].map(v=>palette.get(v));
   if(flat.some(x=>x===undefined))return null;
   predicted.push(unflatten(flat,shape.target[i][0],shape.target[i][1]));
 }
 const remap=[...palette].sort((a,b)=>a[0]-b[0]);
 const cost=shape.cost+view.cost+remap.filter(([a,b])=>a!==b).length*3;
 return {cost,prediction:predicted,
  ast:{kind:"coordinate-unary-palette",outputShape:[shape.row,shape.col],view:view.syntax,palette:remap}};
}
function binaryProgram(a,b,train,tests,shape,trace) {
 // A four-row table keyed only by zero/nonzero of two independently
 // input-indexed cells. The output can be 0 or either actual source value.
 const mask=[7,7,7,7];
 let checks=0;
 for(let t=0;t<train.length;t++){
   const x=a.values[t],z=b.values[t],gold=train[t].output.flat();
   for(let j=0;j<gold.length;j++) {
     checks++;
     const u=x[j],v=z[j],w=gold[j],bucket=(u===0?2:0)+(v===0?1:0);
     mask[bucket]&=(w===0?1:0)|(w===u?2:0)|(w===v?4:0);
     if(mask[bucket]===0){trace.trainPixelChecks+=checks;return null;}
   }
 }
 trace.trainPixelChecks+=checks;
 // Each bucket's minimum-cost choice is zero if admissible, else source0
 // or source1. Source choices tie when both admissible and zero impossible.
 const choices=[];
 const kinds=["zero","outer","inner"];
 let baseCost=0;
 for(const m of mask){
   if(m&1)choices.push([0]);
   else if((m&2)&&(m&4)){choices.push([1,2]);baseCost+=2;}
   else if(m&2){choices.push([1]);baseCost+=2;}
   else if(m&4){choices.push([2]);baseCost+=2;}
   else return null;
 }
 // A tied equal-MDL program with a different TEST output must abstain.
 const variants=[];
 const walk=(i,s)=>{
   if(i===4){variants.push(s.slice());return;}
   for(const v of choices[i]){s.push(v);walk(i+1,s);s.pop();}
 };
 walk(0,[]);
 let predictionKey=null,result=null,selector=null;
 for(const selected of variants){
   const outputs=[];
   for(let i=0;i<tests.length;i++) {
     const x=a.values[train.length+i],z=b.values[train.length+i],flat=[];
     for(let j=0;j<x.length;j++){
       const p=x[j],q=z[j],key=(p===0?2:0)+(q===0?1:0);
       flat.push(selected[key]===0?0:selected[key]===1?p:q);
     }
     outputs.push(unflatten(flat,shape.target[i][0],shape.target[i][1]));
   }
   const key=JSON.stringify(outputs);
   if(predictionKey!==null&&key!==predictionKey)return {ambiguous:true};
   predictionKey=key;result=outputs;selector=selected;
 }
 if(result===null)return null;
 return {ambiguous:false,cost:shape.cost+a.cost+b.cost+8+baseCost,
  prediction:result,
  ast:{kind:"coordinate-two-view-zero-mask",outputShape:[shape.row,shape.col],
       outer:a.syntax,inner:b.syntax,selector:selector.map(x=>kinds[x])}};
}
function termFromCode(code,termList) {return termList.find(t=>t.id===code);}
function shapeOpFromCode(code,ops){return ops.find(t=>t.id===code);}
export function interpret(ast,input) {
 if(!grid(input)||!ast||!Array.isArray(ast.outputShape)||ast.outputShape.length!==2)return null;
 const R=shapeOpFromCode(ast.outputShape[0],ROW_DIMS),
       C=shapeOpFromCode(ast.outputShape[1],COL_DIMS);
 if(!R||!C)return null;
 const H=evalDim(R,input),W=evalDim(C,input);
 if(H<1||W<1||H>30||W>30)return null;
 const view=(code)=>{
   if(!code||!code.row||!code.col)return null;
   const rr=termFromCode(code.row,ROW_TERMS),cc=termFromCode(code.col,COL_TERMS);
   return rr&&cc?projected(rr,cc,input,H,W):null;
 };
 if(ast.kind==="coordinate-unary-palette"){
   const vals=view(ast.view);
   if(vals===null||!Array.isArray(ast.palette))return null;
   const m=new Map(ast.palette);
   if(vals.some(x=>!m.has(x)))return null;
   return unflatten(vals.map(x=>m.get(x)),H,W);
 }
 if(ast.kind==="coordinate-two-view-zero-mask"){
   const a=view(ast.outer),b=view(ast.inner),s=ast.selector;
   if(a===null||b===null||!Array.isArray(s)||s.length!==4||
      s.some(x=>!["zero","outer","inner"].includes(x)))return null;
   return unflatten(a.map((p,i)=>{
     const q=b[i],rule=s[(p===0?2:0)+(q===0?1:0)];
     return rule==="zero"?0:rule==="outer"?p:q;
   }),H,W);
 }
 return null;
}
export function synthesize(train,tests,{allowBinary=true,maxViews=CONTRACT.maxViews}={}) {
 const start=process.hrtime.bigint();
 const trace={schema:CONTRACT.schema,shapePrograms:0,coordinateViews:0,
  unaryFits:0,binaryFits:0,geometryPairs:0,trainPixelChecks:0,
  minCost:null,minCostTies:0,distinctBestPredictions:0,
  abstained:null,ast:null,wallMs:0};
 const finish=(prediction,reason)=>{
   trace.abstained=reason;
   trace.wallMs=Number(process.hrtime.bigint()-start)/1e6;
   return {prediction,trace};
 };
 if(!validTask(train,tests))return finish(null,"BAD_INPUT");
 const shapes=shapeCandidates(train,tests);
 trace.shapePrograms=shapes.length;
 if(!shapes.length)return finish(null,"NO_SHAPE_RULE");
 let best=Infinity,winners=new Map(),tied=0;
 const admit=candidate=>{
   if(!candidate||candidate.ambiguous)return;
   if(!candidate.ast||!train.every(p=>eq(interpret(candidate.ast,p.input),p.output)))throw Error("TRAIN_REPLAY_FAILURE");
   if(!tests.every((x,i)=>eq(interpret(candidate.ast,x),candidate.prediction[i])))throw Error("TEST_REPLAY_FAILURE");
   if(candidate.cost<best){best=candidate.cost;winners=new Map();tied=0;}
   if(candidate.cost===best){
     const key=JSON.stringify(candidate.prediction);
     if(!winners.has(key))winners.set(key,candidate);
     tied++;
   }
 };
 for(const shape of shapes){
   if(shape.cost>best)break;
   const views=viewsFor(shape,train,tests).slice(0,maxViews);
   trace.coordinateViews+=views.length;
   for(const v of views){
     if(shape.cost+v.cost>best)break;
     const u=evaluateUnary(v,train,tests,shape);
     if(u){trace.unaryFits++;admit(u);}
   }
   if(!allowBinary||shape.cost+8>best)continue;
   for(const a of views) {
     if(shape.cost+a.cost+8>best)break;
     for(const b of views) {
       if(shape.cost+a.cost+b.cost+8>best)break;
       trace.geometryPairs++;
       if(trace.geometryPairs>CONTRACT.maxGeometryPairs)return finish(null,"PAIR_BUDGET_EXCEEDED");
       const candidate=binaryProgram(a,b,train,tests,shape,trace);
       if(candidate?.ambiguous)continue;
       if(candidate){trace.binaryFits++;admit(candidate);}
     }
   }
 }
 trace.minCost=Number.isFinite(best)?best:null;
 trace.minCostTies=tied;
 trace.distinctBestPredictions=winners.size;
 if(winners.size===0)return finish(null,"NO_EXECUTABLE_TRAIN_FIT");
 if(winners.size>1)return finish(null,"AMBIGUOUS_MIN_COST_PROGRAMS");
 const chosen=winners.values().next().value;
 trace.ast=copy(chosen.ast);
 return finish(copy(chosen.prediction),null);
}
