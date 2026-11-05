import test from "node:test";
import assert from "node:assert/strict";
import * as S from "../experiments/q3_p29_induced_coordinate_programs.mjs";
import {propose as oldP28} from "../experiments/q3_p28_factorized_operator.mjs";

const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const mk=(h,w,offset=0)=>Array.from({length:h},(_,r)=>Array.from({length:w},(_,c)=>
 ((r*2+c*3+offset)%5===0?0:1+(r*3+c+offset)%8)));
const scale=(x,k)=>x.flatMap(row=>Array.from({length:k},()=>row.flatMap(v=>Array(k).fill(v))));
const tile=(x,ky,kx)=>Array.from({length:x.length*ky},(_,r)=>Array.from({length:x[0].length*kx},(_,c)=>x[r%x.length][c%x[0].length]));
const squareFactor=(x)=>{
 const h=x.length,w=x[0].length;
 return Array.from({length:h*h},(_,r)=>Array.from({length:w*w},(_,c)=>{
  const a=x[Math.floor(r/h)][Math.floor(c/w)],b=x[r%h][c%w];
  if(a!==0&&b!==0)return a;
  if(a===0&&b!==0)return b;
  return 0;
 }));
};
const solve=(pairs,testInputs)=>S.synthesize(pairs.map(([input,output])=>({input,output})),testInputs);
test("identity and arbitrary palette rewrite are induced, not frozen named macros",()=>{
 const a=mk(2,3,1),b=mk(3,2,3),c=mk(2,2,1);
 const remap=x=>x.map(row=>row.map(v=>v===0?0:(v+1)%10));
 const z=solve([[a,remap(a)],[b,remap(b)]],[c]);
 assert.equal(z.trace.abstained,null,JSON.stringify(z.trace));
 assert.ok(eq(z.prediction,[remap(c)]));
 assert.equal(z.trace.ast.kind,"coordinate-unary-palette");
 assert.ok(eq(S.interpret(z.trace.ast,c),remap(c)));
});
test("extracts scale-3 geometry from diverse heights and widths",()=>{
 const a=mk(2,3,1),b=mk(3,2,2),c=mk(3,4,3);
 const z=solve([[a,scale(a,3)],[b,scale(b,3)]],[c]);
 assert.equal(z.trace.abstained,null,JSON.stringify(z.trace));
 assert.ok(eq(z.prediction,[scale(c,3)]));
 assert.ok(eq(S.interpret(z.trace.ast,c),scale(c,3)));
});
test("extracts periodic 3x2 tile coordinates from examples with different shapes",()=>{
 const a=mk(2,3,0),b=mk(3,2,3),c=mk(3,4,4);
 const z=solve([[a,tile(a,3,2)],[b,tile(b,3,2)]],[c]);
 assert.equal(z.trace.abstained,null,JSON.stringify(z.trace));
 assert.ok(eq(z.prediction,[tile(c,3,2)]));
});
test("learns h^2 x w^2 two-source coordinate interaction across rectangles",()=>{
 const a=mk(2,3,0),b=mk(3,2,3),c=mk(2,2,7);
 const tr=[{input:a,output:squareFactor(a)},{input:b,output:squareFactor(b)}];
 const z=S.synthesize(tr,[c]);
 assert.equal(z.trace.abstained,null,JSON.stringify(z.trace));
 assert.ok(eq(z.prediction,[squareFactor(c)]),JSON.stringify({trace:z.trace,prediction:z.prediction}));
 assert.equal(z.trace.ast.kind,"coordinate-two-view-zero-mask");
 assert.ok(eq(S.interpret(z.trace.ast,c),squareFactor(c)));
 const old=oldP28(tr,[c]);
 assert.ok(eq(old.prediction,[squareFactor(c)]));
});
test("first-pass failures abstain without hidden oracle",()=>{
 const a=mk(2,3,0);
 assert.equal(S.synthesize([{input:a,output:[[7]]}],[a]).prediction,null);
 assert.equal(S.synthesize([{input:a,output:scale(a,6)}],[a]).prediction,null);
 assert.equal(S.interpret({kind:"coordinate-unary-palette",outputShape:["bad","w"]},a),null);
});
test("a public input cannot influence output through any secret expected test label",()=>{
 const a=mk(2,3,1),b=mk(3,2,2),c=mk(3,4,3);
 const t=[{input:a,output:scale(a,3)},{input:b,output:scale(b,3)}];
 const r=S.synthesize(t,[c]);
 const r2=S.synthesize(t,[JSON.parse(JSON.stringify(c))]);
 assert.ok(eq(r.prediction,r2.prediction));
 assert.ok(eq(r.trace.ast,r2.trace.ast));
 assert.equal(S.CONTRACT.teacherCalls,0);
 assert.equal(S.CONTRACT.neuralCalls,0);
});
