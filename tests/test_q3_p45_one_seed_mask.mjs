import test from 'node:test';
import assert from 'node:assert/strict';
import {applyMaskLifting,inferSourceDelta,propose} from '../experiments/q3_p45_one_seed_mask_FIRST.mjs';
import {SOURCE} from '../experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';

function directReference(grid,{axis,b,c,marker}){
 const o=grid.map(row=>row.slice());
 const H=grid.length,W=grid[0].length;
 for(let line=0;line<(axis==='row'?H:W);line++){
  const indices=[];
  for(let position=0;position<(axis==='row'?W:H);position++){
   const color=axis==='row'?grid[line][position]:grid[position][line];
   if(marker==='ANY'?color!==b:color===marker)indices.push(position);
  }
  if(indices.length<2)continue;
  for(let j=indices[0]+1;j<indices[indices.length-1];j++){
   const y=axis==='row'?line:j,x=axis==='row'?j:line;
   if(o[y][x]===b)o[y][x]=c;
  }
 }
 return o;
}

test('single original kernel P22 unchanged (identity mask row background0,fill2)',()=>{
 const old=SOURCE['aa18de87'];
 const inputs=[[[1,0,0,3]],[[0,0,0]],[[1,0,3],[8,0,5]]];
 for(const input of inputs){
  const expected=old(input.map(r=>r.slice()));
  const actual=applyMaskLifting(input,{axis:'row',b:0,c:2,marker:'ANY'});
  assert.deepEqual(actual,expected);
 }
});

test('selective color markers bridge around unrelated colors without erasing them',()=>{
 const input=[[3,0,4,0,3]];
 assert.deepEqual(applyMaskLifting(input,{axis:'row',b:0,c:2,marker:3}),
                    [[3,2,4,2,3]]);
 assert.deepEqual(input,[[3,0,4,0,3]]);
});

test('axis column, arbitrary background and output color',()=>{
 const input=[[1],[0],[2],[0],[1]];
 assert.deepEqual(applyMaskLifting(input,{axis:'column',b:0,c:3,marker:1}),
                    [[1],[3],[2],[3],[1]]);
});

test('varying marker/background/output palettes and rectangular grids match independent rule',()=>{
 let count=0;
 for(let H=1;H<=5;H++)for(let W=1;W<=5;W++)
 for(let b=0;b<=9;b++)for(let c=0;c<=9;c++)if(c!==b)
 for(const marker of ['ANY',(b+1)%10]){
  const grid=Array.from({length:H},(_,r)=>Array.from({length:W},(_,col)=>
   (r*31+col*13+b*7+c*3)%10));
  for(const axis of ['row','column']){
   const params={axis,b,c,marker};
   assert.deepEqual(applyMaskLifting(grid,params),directReference(grid,params));
   count++;
  }
 }
 assert.equal(count,9000);
});

test('all three-color 3x3 grids agree with independent reference for both orientations',()=>{
 const colors=[0,2,7];
 for(let index=0;index<3**9;index++){
  let n=index;const grid=Array.from({length:3},()=>Array(3));
  for(let r=0;r<3;r++)for(let c=0;c<3;c++){
   grid[r][c]=colors[n%3];n=Math.floor(n/3);
  }
  for(const axis of ['row','column'])for(const marker of ['ANY',2]){
   const params={axis,b:0,c:7,marker};
   assert.deepEqual(applyMaskLifting(grid,params),directReference(grid,params));
  }
 }
});

test('infer source-only changed pixels from TRAIN, reject incompatible changes',()=>{
 const training=[{input:[[3,0,4,0,3]],output:[[3,2,4,2,3]]}];
 assert.deepEqual(inferSourceDelta(training),{b:0,c:2,changed:2});
 assert.equal(inferSourceDelta([{input:[[1,0]],output:[[1,0]]}]),null);
 assert.equal(inferSourceDelta([{input:[[1,0]],output:[[2,3]]}]),null);
 assert.equal(inferSourceDelta([{input:[[1,0]],output:[[3],[4]]}]),null);
});

test('choose a single correct selective marker without original TEST gold',()=>{
 const train=[{input:[[3,0,4,0,3]],output:[[3,2,4,2,3]]}];
 const p=propose(train,[[[3,0,8,0,3]]]);
 assert.equal(p.submitted,true);
 assert.deepEqual(p.prediction,[[[3,2,8,2,3]]]);
 assert.ok(p.fitting.some(x=>x.marker===3));
});

test('two TRAIN-consistent marker predicates with divergent TEST => ABSTAIN',()=>{
 const train=[{input:[[1,2,0,2,1]],output:[[1,2,5,2,1]]}];
 const p=propose(train,[[[1,0,2,0,1]]]);
 assert.equal(p.submitted,false);
 assert.equal(p.ambiguous,true);
 assert.equal(p.prediction,null);
 assert.ok(p.fitting.some(x=>x.marker===1));
 assert.ok(p.fitting.some(x=>x.marker===2));
});

test('invalid source and kernel failure do not produce a prediction',()=>{
 assert.equal(applyMaskLifting([[1,0,2]],{axis:'row',b:0,c:0,marker:1}),null);
 assert.equal(applyMaskLifting([[1,0,2]],{axis:'z',b:0,c:2,marker:1}),null);
 assert.equal(applyMaskLifting([[1,0,2]],{axis:'row',b:0,c:2,marker:1},
  ()=>null),null);
 const p=propose([{input:[[1,0,1]],output:[[1,2,1]]}],[[[1,0,1]]],
  ()=>{throw Error('broken seed');});
 assert.equal(p.submitted,false);
});
