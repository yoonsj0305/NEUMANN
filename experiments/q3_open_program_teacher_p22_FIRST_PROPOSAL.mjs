/* NEUMANN P2.2 first external GPT-6 executable teacher programs.
 * From original training pairs and test inputs only. Test gold was not used.
 * No task-ID checks inside solvers; research only, not sandboxed production code.
 */
function valid(g){return Array.isArray(g)&&g.length>=1&&g.length<=30&&Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&g.every(r=>Array.isArray(r)&&r.length===g[0].length&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9));}
const copy=g=>g.map(r=>r.slice()),ds=[[1,0],[-1,0],[0,1],[0,-1]],key=(r,c)=>r+","+c;
function components(g,match){
 if(!valid(g))return [];const used=new Set(),out=[],H=g.length,W=g[0].length;
 for(let r=0;r<H;r++)for(let c=0;c<W;c++){
  if(!match(g[r][c])||used.has(key(r,c)))continue;
  const queue=[[r,c]],pts=[];used.add(key(r,c));
  for(let i=0;i<queue.length;i++){const [y,x]=queue[i];pts.push([y,x]);for(const [dy,dx]of ds){const yy=y+dy,xx=x+dx;if(yy<0||xx<0||yy>=H||xx>=W||used.has(key(yy,xx))||!match(g[yy][xx]))continue;used.add(key(yy,xx));queue.push([yy,xx]);}}
  const R=pts.map(z=>z[0]),C=pts.map(z=>z[1]);const r0=Math.min(...R),r1=Math.max(...R),c0=Math.min(...C),c1=Math.max(...C);
  out.push({pts,box:[r0,c0,r1,c1],area:pts.length});
 }return out;
}
function shapeSignature(comp){
 const pts=comp.pts,sites=new Set(pts.map(p=>key(...p))),[r0,c0,r1,c1]=comp.box;
 const degreeCounts=[0,0,0,0,0],junctions=[];
 for(const [r,c]of pts){const n=ds.filter(([dy,dx])=>sites.has(key(r+dy,c+dx))).length;degreeCounts[n]++;if(n===3)junctions.push([r,c]);}
 const flood=new Set();let holes=0;
 for(let r=r0;r<=r1;r++)for(let c=c0;c<=c1;c++){
  if(sites.has(key(r,c))||flood.has(key(r,c)))continue;
  let queue=[[r,c]],exits=false;flood.add(key(r,c));
  for(let i=0;i<queue.length;i++){const [y,x]=queue[i];if(y===r0||y===r1||x===c0||x===c1)exits=true;for(const [dy,dx]of ds){const yy=y+dy,xx=x+dx;if(yy<r0||xx<c0||yy>r1||xx>c1||sites.has(key(yy,xx))||flood.has(key(yy,xx)))continue;flood.add(key(yy,xx));queue.push([yy,xx]);}}
  if(!exits)holes++;
 }
 let hAxis=false;
 if(degreeCounts[1]===4&&degreeCounts[3]===2&&holes===0&&junctions.length===2){
  const [[a,b],[c,d]]=junctions;
  if(a===c){hAxis=[a,b,c,d].every(Number.isInteger)&&sites.has(key(a-1,b))&&sites.has(key(a+1,b))&&sites.has(key(c-1,d))&&sites.has(key(c+1,d));}
  else if(b===d){hAxis=sites.has(key(a,b-1))&&sites.has(key(a,b+1))&&sites.has(key(c,d-1))&&sites.has(key(c,d+1));}
 }
 return [degreeCounts[1],degreeCounts[3],degreeCounts[4],holes,(degreeCounts[1]===4&&degreeCounts[3]===2&&holes===0)?Number(hAxis):0].join("|");
}
function solveTopology(g){
 if(!valid(g))return null;
 const seed=components(g,v=>v===2),others=components(g,v=>v===1);if(seed.length!==1||!others.length)return null;
 const signature=shapeSignature(seed[0]),out=copy(g);
 for(const comp of others)if(shapeSignature(comp)===signature)for(const [r,c]of comp.pts)out[r][c]=2;
 return out;
}
function solveQuadrants(g){
 if(!valid(g))return null;const counts=new Map();for(const row of g)for(const v of row)if(v!==0)counts.set(v,(counts.get(v)||0)+1);
 if(counts.size<2)return null;const sorted=[...counts].sort((a,b)=>b[1]-a[1]);if(sorted[0][1]===sorted[1][1])return null;
 const bg=sorted[0][0],all=[],patches=new Map();for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==0){all.push([r,c]);if(g[r][c]!==bg){if(!patches.has(g[r][c]))patches.set(g[r][c],[]);patches.get(g[r][c]).push([r,c]);}}
 const rs=all.map(v=>v[0]),cs=all.map(v=>v[1]),midR=(Math.min(...rs)+Math.max(...rs))/2,midC=(Math.min(...cs)+Math.max(...cs))/2;
 const out=[[0,0],[0,0]];
 for(const [color,pts]of patches){if(pts.length!==4)return null;const r0=Math.min(...pts.map(v=>v[0])),c0=Math.min(...pts.map(v=>v[1]));if(!pts.every(([r,c])=>r>=r0&&r<=r0+1&&c>=c0&&c<=c0+1))return null;const cr=r0+.5,cc=c0+.5;if(cr===midR||cc===midC)return null;const y=cr<midR?0:1,x=cc<midC?0:1;if(out[y][x]!==0)return null;out[y][x]=color;}
 return out;
}
function solveThreeColors(g){
 if(!valid(g))return null;const comps=components(g,v=>v!==0),eligible=[];
 for(const p of comps){const [r0,c0,r1,c1]=p.box;const colors=new Set(p.pts.map(([r,c])=>g[r][c]));if(p.area===9&&r1-r0===2&&c1-c0===2&&colors.size===3)eligible.push(p);}
 if(eligible.length!==1)return null;
 const [r0,c0]=eligible[0].box;return g.slice(r0,r0+3).map(row=>row.slice(c0,c0+3));
}
function solveCountSnakes(g){
 if(!valid(g)||g.flat().some(v=>v!==0&&v!==5))return null;
 const comps=components(g,v=>v===5);if(!comps.length||comps.length+1>30)return null;
 return Array.from({length:comps.length+1},()=>[0]);
}
function solveHorizontalConnect(g){
 if(!valid(g))return null;const o=copy(g);
 for(let r=0;r<g.length;r++){const at=g[r].map((v,c)=>v===0?-1:c).filter(v=>v>=0);if(at.length>=2)for(let c=at[0]+1;c<at[at.length-1];c++)if(o[r][c]===0)o[r][c]=2;}
 return o;
}
function solveTwinZero(g){
 if(!valid(g)||g[0].length%2!==0)return null;
 const h=g.length,w=g[0].length/2;return Array.from({length:h},(_,r)=>Array.from({length:w},(_,c)=>g[r][c]===0&&g[r][c+w]===0?5:0));
}
function solveShiftBars(g){
 if(!valid(g))return null;const h=g.length,w=g[0].length,out=Array.from({length:h},()=>Array(w).fill(5));
 for(let r=0;r<h;r++)for(let c=1;c<w;c++)if(g[r][c]!==0)out[r][c-1]=g[r][c];
 return out;
}
const SOURCE={
 "bd14c3bf":solveTopology,
 "19bb5feb":solveQuadrants,
 "9a4bb226":solveThreeColors,
 "759f3fd3":null,
 "e872b94a":solveCountSnakes,
 "aa18de87":solveHorizontalConnect,
 "66f2d22f":solveTwinZero,
 "32e9702f":solveShiftBars
};
export {SOURCE,valid,components,shapeSignature};