/* NEUMANN P2.2 | FIRST external GPT-6 teacher proposal, strictly TRAIN + TEST INPUT.
 * Programs intentionally remain specific to their separately assigned public tasks.
 * A dispatcher is bookkeeping outside each solver, not evidence of NEUMANN policy learning.
 * No original test answers, exact test input table, task ID checks inside solve(), IO or model calls.
 */
const valid=g=>Array.isArray(g)&&g.length>=1&&g.length<=30&&Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&g.every(r=>Array.isArray(r)&&r.length===g[0].length&&r.every(x=>Number.isInteger(x)&&x>=0&&x<=9));
const clone=g=>g.map(r=>r.slice());
const neigh=[[1,0],[-1,0],[0,1],[0,-1]];
function componentsOf(g,color){if(!valid(g))return [];const h=g.length,w=g[0].length,seen=new Set(),result=[];const key=(r,c)=>r+','+c;
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){
  if(g[r][c]!==color||seen.has(key(r,c)))continue;
  const queue=[[r,c]];seen.add(key(r,c));
  for(let k=0;k<queue.length;k++){const [a,b]=queue[k];for(const[d,e]of neigh){const x=a+d,y=b+e;if(x<0||y<0||x>=h||y>=w||g[x][y]!==color||seen.has(key(x,y)))continue;seen.add(key(x,y));queue.push([x,y]);}}
  result.push(queue);
 }return result;
}
function box(points){return {r0:Math.min(...points.map(p=>p[0])),r1:Math.max(...points.map(p=>p[0])),c0:Math.min(...points.map(p=>p[1])),c1:Math.max(...points.map(p=>p[1]))};}
function glyphType(points){if(!points?.length)return null;
 const b=box(points),h=b.r1-b.r0+1,w=b.c1-b.c0+1,set=new Set(points.map(([r,c])=>(r-b.r0)+','+(c-b.c0)));
 if(h<3||w<3)return null;
 const has=(r,c)=>set.has(r+','+c),top=Array.from({length:w},(_,c)=>has(0,c)).every(Boolean),bottom=Array.from({length:w},(_,c)=>has(h-1,c)).every(Boolean),left=Array.from({length:h},(_,r)=>has(r,0)).every(Boolean),right=Array.from({length:h},(_,r)=>has(r,w-1)).every(Boolean);
 const fullSides=[top,bottom,left,right].filter(Boolean).length;
 if(fullSides===4){
  // Count enclosed background regions within a closed boundary, permitting
  // 1-hole frames and 2+-hole multi-frame figures at different dimensions.
  const seen=new Set();let holes=0;
  for(let r=1;r<h-1;r++)for(let c=1;c<w-1;c++){
   const start=r+','+c;if(has(r,c)||seen.has(start))continue;
   const queue=[[r,c]];seen.add(start);let touchesEdge=false;
   for(let k=0;k<queue.length;k++){const [rr,cc]=queue[k];
    if(rr===0||rr===h-1||cc===0||cc===w-1)touchesEdge=true;
    for(const[dr,dc]of neigh){const nr=rr+dr,nc=cc+dc,id=nr+','+nc;
     if(nr<0||nc<0||nr>=h||nc>=w||has(nr,nc)||seen.has(id))continue;
     seen.add(id);queue.push([nr,nc]);
    }
   }
   if(!touchesEdge)holes++;
  }
  return holes>=1?'closed_'+holes:null;
 }
 // Three straight sides, missing fourth has exactly the two corners: C or U with variable aspect ratio.
 if(fullSides===3){if(!top&&Array.from({length:w-2},(_,c)=>has(0,c+1)).some(Boolean))return null;
  if(!bottom&&Array.from({length:w-2},(_,c)=>has(h-1,c+1)).some(Boolean))return null;
  if(!left&&Array.from({length:h-2},(_,r)=>has(r+1,0)).some(Boolean))return null;
  if(!right&&Array.from({length:h-2},(_,r)=>has(r+1,w-1)).some(Boolean))return null;
  for(let r=1;r<h-1;r++)for(let c=1;c<w-1;c++)if(has(r,c))return null;return 'c_shape';}
 // H: two opposite full rails and a single straight connector, not an E-shaped zig-zag.
 if(left&&right&&!top&&!bottom){const bridges=[];for(let r=1;r<h-1;r++)if(Array.from({length:w},(_,c)=>has(r,c)).every(Boolean))bridges.push(r);
  if(bridges.length===1){const target=bridges[0];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(has(r,c)!==(c===0||c===w-1||r===target))return null;return 'h_shape';}}
 if(top&&bottom&&!left&&!right){const bridges=[];for(let c=1;c<w-1;c++)if(Array.from({length:h},(_,r)=>has(r,c)).every(Boolean))bridges.push(c);
  if(bridges.length===1){const target=bridges[0];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(has(r,c)!==(r===0||r===h-1||c===target))return null;return 'h_shape';}}
 return null;
}
function shapeAnalogRecolor(input){if(!valid(input))return null;
 const reference=componentsOf(input,2);if(reference.length!==1)return null;const type=glyphType(reference[0]);if(type===null)return null;
 const result=clone(input);
 for(const obj of componentsOf(input,1))if(glyphType(obj)===type)for(const [r,c]of obj)result[r][c]=2;
 return result;
}
function patchQuadrants(input){if(!valid(input))return null;
 const all=[];for(let r=0;r<input.length;r++)for(let c=0;c<input[0].length;c++)if(input[r][c]===8)all.push([r,c]);if(all.length<8)return null;
 const b=box(all),midR=(b.r0+b.r1)/2,midC=(b.c0+b.c1)/2;
 const patches=[];
 for(let color=1;color<=9;color++){if(color===8)continue;
  const groups=componentsOf(input,color);for(const pts of groups){const obj=box(pts);if(pts.length!==4||obj.r1-obj.r0!==1||obj.c1-obj.c0!==1)return null;
   patches.push({color,r:(obj.r0+obj.r1)/2,c:(obj.c0+obj.c1)/2});
  }
 }
 if(!patches.length)return null;
 const out=[[0,0],[0,0]];for(const p of patches){if(p.r===midR||p.c===midC)return null;const r=p.r<midR?0:1,c=p.c<midC?0:1;if(out[r][c]!==0)return null;out[r][c]=p.color;}
 return out;
}
function uniqueThreeColorTile(input){if(!valid(input))return null;const hits=[];for(let r=0;r<=input.length-3;r++)for(let c=0;c<=input[0].length-3;c++){
 const tile=input.slice(r,r+3).map(row=>row.slice(c,c+3));if(tile.flat().every(v=>v!==0)&&new Set(tile.flat()).size===3){
  // Reject subwindows of larger adjoining components: 3x3 must be isolated by background.
  let isolated=true;for(let rr=r-1;rr<=r+3;rr++)for(let cc=c-1;cc<=c+3;cc++){
   if(rr<0||cc<0||rr>=input.length||cc>=input[0].length||rr>=r&&rr<r+3&&cc>=c&&cc<c+3)continue;
   if(input[rr][cc]!==0 && ((rr===r-1||rr===r+3)&&(cc>=c&&cc<c+3)||(cc===c-1||cc===c+3)&&(rr>=r&&rr<r+3)))isolated=false;
  }
  if(isolated)hits.push(tile);
 }
 }return hits.length===1?hits[0]:null;
}
function countComponentsPlusOne(input){if(!valid(input))return null;
 // General count of independent 4-neighbor connected components of the observed foreground color 5.
 const parts=componentsOf(input,5);if(parts.length===0||parts.length+1>30)return null;
 return Array.from({length:parts.length+1},()=>[0]);
}
function betweenRowBoundaries(input){if(!valid(input))return null;const g=clone(input);for(let r=0;r<g.length;r++){
 const active=[];for(let c=0;c<g[r].length;c++)if(g[r][c]!==0)active.push(c);
 if(active.length>=2)for(let c=active[0]+1;c<active[active.length-1];c++)if(g[r][c]===0)g[r][c]=2;
 }return g;
}
function explicitlyAbstain(_input){return null;}
const FIRST_PROPOSALS=Object.freeze({
 'bd14c3bf':shapeAnalogRecolor,
 '19bb5feb':patchQuadrants,
 '9a4bb226':uniqueThreeColorTile,
 '759f3fd3':explicitlyAbstain,
 'e872b94a':countComponentsPlusOne,
 'aa18de87':betweenRowBoundaries
});
export {FIRST_PROPOSALS,valid,componentsOf,glyphType};
