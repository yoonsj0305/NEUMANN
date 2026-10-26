/* First source-only, pre-gold deterministic temporal concept. Invented by GPT6 chat assistant, NOT NEUMANN learned model. */
export const inferTemporalRuns=function inferTemporalRuns(g){
 const h=g.length,w=g[0].length;if(g.some(row=>row.length!==w))throw Error("shape");
 const sep=[];for(let r=0;r<h;r++)if(g[r].every(v=>v===5))sep.push(r);
 if(sep.length!==3)throw Error("three separators required");
 const bounds=[-1,...sep,h],blocks=[];
 for(let j=0;j<bounds.length-1;j++){const z=g.slice(bounds[j]+1,bounds[j+1]);if(z.length!==3)throw Error("three row temporal panel required");blocks.push(z)}
 if(blocks.length!==4)throw Error("four panels");const mask=Array.from({length:3},()=>Array(w).fill(0));
 const colors=[...new Set(g.flat())].filter(x=>x!==0&&x!==5).sort((a,b)=>a-b);
 const traces=[];
 for(let r=0;r<3;r++)for(const color of colors){
  const series=blocks.map(b=>b[r].map((v,c)=>v===color?c:-1).filter(c=>c!==-1));
  const last=series[3];if(!last.length)continue;
  let project=null,confidence=0;
  if(series[2].length&&series[2].length===series[2].at(-1)-series[2][0]+1&&last.length===last.at(-1)-last[0]+1){
   const ds=last[0]-series[2][0],de=last.at(-1)-series[2].at(-1);
   const previous=series[1].length && series[1].length===series[1].at(-1)-series[1][0]+1;
   const sameTrend=previous&&(series[2][0]-series[1][0]===ds)&&(series[2].at(-1)-series[1].at(-1)===de);
   const early=series[0].length&&series[0].length===series[0].at(-1)-series[0][0]+1;
   const earlierSame=!early || (series[1].length&&series[1][0]-series[0][0]===ds&&series[1].at(-1)-series[0].at(-1)===de);
   if(sameTrend&&earlierSame){let l=last[0]+ds,u=last.at(-1)+de;if(l>=0&&u<w&&l<=u){project=Array.from({length:u-l+1},(_,k)=>l+k);confidence=1;}}
  }
  if(!project)project=last;
  traces.push({r,color,indices:project,confidence,changed:JSON.stringify(project)!==JSON.stringify(last)});
 }
 // In a collision, a growing or shifting range inferred from ≥3 frames prevails over preserved uncertain pixels.
 traces.sort((a,b)=>a.confidence-b.confidence||a.color-b.color);
 for(const t of traces)for(const c of t.indices)mask[t.r][c]=t.color;
 return mask
};
