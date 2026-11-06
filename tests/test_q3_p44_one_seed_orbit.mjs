import test from 'node:test';
import assert from 'node:assert/strict';
import {palette,transpose,conjugateSeed,makeFamily,proposer} from '../experiments/q3_p44_one_seed_orbit_FIRST.mjs';
import {SOURCE} from '../experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs';
const seed=SOURCE['aa18de87'];
const eq=(a,b)=>assert.deepEqual(a,b);

function independentReference(g,axis,b,c){
 const out=g.map(r=>r.slice()),H=g.length,W=g[0].length;
 const channels=(axis==='row')?H:W,positions=(axis==='row')?W:H;
 for(let line=0;line<channels;line++){
  const sites=[];
  for(let j=0;j<positions;j++){
   const cell=axis==='row'?g[line][j]:g[j][line];
   if(cell!==b)sites.push(j);
  }
  if(sites.length>=2){
   for(let j=sites[0]+1;j<sites[sites.length-1];j++){
    if(axis==='row'&&out[line][j]===b)out[line][j]=c;
    else if(axis==='column'&&out[j][line]===b)out[j][line]=c;
   }
  }
 }
 return out;
}

test('exact seed preserved, not rewritten',()=>{
 const f=conjugateSeed('row',0,2,seed);
 for(const g of [
  [[0,1,0,4],[7,0,0,3]],
  [[5]],[[2,0,3],[0,0,0]],
  [[0,0],[0,0],[1,0],[0,5]]
 ])eq(f(g),seed(g));
});

test('180 unique quotient parameter sets, bijective color map and rectangular transpose',()=>{
 const family=makeFamily();
 assert.equal(family.length,180);
 assert.equal(new Set(family.map(x=>x.key)).size,180);
 for(let b=0;b<10;b++)for(let c=0;c<10;c++)if(b!==c){
  const p=palette(b,c);
  assert.equal(p.forward[b],0);assert.equal(p.forward[c],2);
  assert.deepEqual(Array.from({length:10},(_,x)=>p.inverse[p.forward[x]]),
    Array.from({length:10},(_,x)=>x));
 }
 const g=[[0,2,0],[3,4,5]];
 eq(transpose(transpose(g)),g);
});

test('independent direct reference matches conjugated source on 3000 deterministic multishape cases',()=>{
 let n=0;
 for(let H=1;H<=5;H++)for(let W=1;W<=5;W++)
  for(let b=0;b<10;b++)for(let c=0;c<10;c++)if(b!==c){
   const g=Array.from({length:H},(_,r)=>Array.from({length:W},(_,col)=>
      ((r*7+col*3+H*W+b+c)%5<2)?b:(r*3+col*7+c)%10));
   for(const axis of ['row','column']){
    eq(conjugateSeed(axis,b,c)(g),independentReference(g,axis,b,c));
    n++;
   }
  }
 assert.equal(n,4500);
});

test('exhaustive 3x3 3-palette source-conjugation equivalence',()=>{
 const colors=[0,2,7],total=3**9;
 for(let code=0;code<total;code++){
  let v=code;
  const g=Array.from({length:3},()=>Array(3).fill(0));
  for(let r=0;r<3;r++)for(let c=0;c<3;c++){g[r][c]=colors[v%3];v=Math.floor(v/3);}
  for(const axis of ['row','column']){
   const b=0,c=2;
   eq(conjugateSeed(axis,b,c)(g),independentReference(g,axis,b,c));
  }
 }
 assert.equal(total,19683);
});

test('TRAIN nontrivial causal effect, disallow all-identity matches',()=>{
 const family=makeFamily();
 const train=[{input:[[1,0,3]],output:[[1,0,3]]}];
 const p=proposer(train,[[1,0,3]],family);
 assert.equal(p.submitted,false);
 assert.equal(p.accepted_programs.length,0);
});

test('TRAIN exact match + source ID independence + disagreement abstention',()=>{
 const a={axis:'row',b:0,c:2,key:'a',program:g=>[[1,2,3]]};
 const b={axis:'row',b:0,c:3,key:'b',program:g=>g[0][0]===1?[[1,2,3]]:[[1,3,3]]};
 const train=[{input:[[1,0,3]],output:[[1,2,3]]}];
 const p=proposer(train,[[4,0,3]],[a,b]);
 assert.equal(p.ambiguous,true);
 assert.equal(p.submitted,false);
 const q=proposer(train,[[4,0,3]],[a]);
 assert.equal(q.submitted,true);
});

test('malformed source, invalid params, altered user input fail closed',()=>{
 assert.throws(()=>palette(1,1),/INVALID/);
 assert.throws(()=>conjugateSeed('nondihedral',0,2),/BAD_SEED/);
 const f=conjugateSeed('column',7,1);
 assert.equal(f([[10]]),null);
 const g=[[7,1,7],[3,7,4]],copy=g.map(r=>r.slice());
 f(g);eq(g,copy);
});
