import test from "node:test";
import assert from "node:assert/strict";
import * as P from "../experiments/q3_p30_object_relational_recolor.mjs";
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function make(rows,cols,objects) {
 const grid=Array.from({length:rows},()=>Array(cols).fill(0));
 for(const {r,c,h,w,color} of objects)for(let i=0;i<h;i++)for(let j=0;j<w;j++){
   if(grid[r+i][c+j]!==0)throw Error("OVERLAP");
   grid[r+i][c+j]=color;
 }
 return grid;
}
function recolorLargest(objects,rows,cols,target=7){
 const max=Math.max(...objects.map(x=>x.h*x.w));
 return make(rows,cols,objects.map(x=>({...x,color:x.h*x.w===max?target:x.color})));
}
const cases=[
 {rows:8,cols:8,objects:[{r:1,c:1,h:2,w:2,color:1},{r:5,c:6,h:1,w:1,color:2}]},
 {rows:8,cols:8,objects:[{r:4,c:3,h:1,w:4,color:3},{r:0,c:1,h:2,w:1,color:4}]},
 {rows:8,cols:8,objects:[{r:1,c:4,h:3,w:1,color:1},{r:6,c:0,h:1,w:2,color:2}]},
 {rows:9,cols:9,objects:[{r:3,c:1,h:2,w:3,color:5},{r:0,c:7,h:1,w:1,color:6}]}
];
function train(){
 return cases.slice(0,3).map(x=>({input:make(x.rows,x.cols,x.objects),
   output:recolorLargest(x.objects,x.rows,x.cols)}));
}
test("induce general multi-object role recoloring from three differently arranged examples",()=>{
 const x=cases[3],q=make(x.rows,x.cols,x.objects);
 const r=P.synthesize(train(),[q]);
 assert.ok(r.prediction,JSON.stringify(r.trace));
 assert.ok(eq(r.prediction,[recolorLargest(x.objects,x.rows,x.cols)]),JSON.stringify(r.trace));
 assert.ok(eq(P.execute(r.trace.ast,q),r.prediction[0]));
});
test("frozen invented program replays all training examples independently",()=>{
 const q=make(cases[3].rows,cases[3].cols,cases[3].objects);
 const result=P.synthesize(train(),[q]);
 if(result.prediction!==null){
   for(const p of train())assert.ok(eq(P.execute(result.trace.ast,p.input),p.output));
 }
 assert.equal(P.CONTRACT.teacherCalls,0);
 assert.equal(P.CONTRACT.neuralCalls,0);
});
test("unsupported changed backgrounds or changed object masks safely abstain",()=>{
 const p=train(),altered=p.map(x=>({...x,output:x.output.map(row=>row.slice())}));
 altered[0].output[7][7]=9;
 const r=P.synthesize(altered,[make(cases[3].rows,cases[3].cols,cases[3].objects)]);
 assert.equal(r.prediction,null);
});
test("fail-closed on empty invalid source instead of inventing output",()=>{
 assert.equal(P.synthesize([],[make(cases[3].rows,cases[3].cols,cases[3].objects)]).prediction,null);
 assert.equal(P.execute({kind:"not-existing-operator"},make(3,3,[])),null);
});
