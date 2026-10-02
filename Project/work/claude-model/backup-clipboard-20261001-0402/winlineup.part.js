// Win-probability lineup solver: picks the starting lineup that maximises P(beat this week's opponent),
// not projected points. Uses the same player draws as the season simulator (compound Poisson-lognormal,
// talent and shared NFL-team factors, injury/Q miss chances) with common random numbers, so every
// candidate lineup is compared on identical simulated weeks. Hill-climbs over one-player swaps.
function winLineup(M,E,opts={}){
 const me=M.L.me,N=opts.N||4000,wk=M.data.week,sl=M.slots;
 const g0=(M.L.sched[wk]||[]).find(x=>x.includes(me));if(!g0)return null;const op=g0[0]===me?g0[1]:g0[0];
 const T=M.L.teams[me],O=M.L.teams[op],res=T.reserve||[];
 const bad=p=>['Out','Doubtful','IR','PUP','Sus','NA'].includes(M.st(p));
 const pool=T.players.filter(p=>!res.includes(p)&&!bad(p)&&E.ix[p]!=null);
 const cur=(T.starters||[]).filter(p=>E.ix[p]!=null);
 const oStart=((O.starters&&O.starters.length)?O.starters:lineupWeek(M,O.players.filter(p=>!(O.reserve||[]).includes(p)),0).out).filter(p=>E.ix[p]!=null);
 const ids=[...new Set([...pool,...cur,...oStart])];const D={};for(const p of ids)D[p]=new Float64Array(N);
 const R=rng(opts.seed||20261004);const g=()=>{let u=0;while(!u)u=R();return Math.sqrt(-2*Math.log(u))*Math.cos(6.283185307*R())};
 for(let n=0;n<N;n++){const tf={};for(const p of ids){const pl=E.pl[E.ix[p]];if(pl.miss&&R()<pl.miss){D[p][n]=0;continue}
   let f=1;if(pl.sTeam>0&&pl.nfl!=null){if(tf[pl.nfl]==null)tf[pl.nfl]=Math.exp(.15*g()-.01125);f=tf[pl.nfl]}
   const tal=Math.exp(pl.sTal*g()-pl.sTal*pl.sTal/2);D[p][n]=drawP(pl,0,tal,f,g,R)}}
 const opp=new Float64Array(N);for(const p of oStart)for(let n=0;n<N;n++)opp[n]+=D[p][n];
 const fits=set=>{const used=new Array(sl.length).fill(null);const ps=[...set].sort((a,b)=>sl.filter(s=>s.includes(M.pos(a))).length-sl.filter(s=>s.includes(M.pos(b))).length);
  const go=i=>{if(i===ps.length)return true;for(let k=0;k<sl.length;k++){if(used[k]===null&&sl[k].includes(M.pos(ps[i]))){used[k]=ps[i];if(go(i+1))return true;used[k]=null}}return false};return set.length<=sl.length&&go(0)};
 const ev=set=>{let w=0,s=0;const t=new Float64Array(N);for(const p of set){const d=D[p];for(let n=0;n<N;n++)t[n]+=d[n]}for(let n=0;n<N;n++){s+=t[n];if(t[n]>opp[n])w++;else if(t[n]===opp[n])w+=.5}
  const q=Array.from(t).sort((a,b)=>a-b);return {set:[...set],p:w/N,mean:s/N,p10:q[Math.floor(N*.1)],p50:q[Math.floor(N*.5)],p90:q[Math.floor(N*.9)]}};
 const maxPts=lineupWeek(M,pool,0).out;let best=ev(maxPts);const base=best;
 for(let round=0;round<4;round++){let imp=null;const bench=pool.filter(p=>!best.set.includes(p));
  for(const out of best.set)for(const inn of bench){const cand=best.set.filter(p=>p!==out).concat(inn);if(!fits(cand))continue;const r=ev(cand);if(r.p>(imp?imp.p:best.p)+0.004)imp=r}
  if(!imp)break;best=imp}
 const oppQ=Array.from(opp).sort((a,b)=>a-b);
 return {opp:O.name,N,oppMean:opp.reduce((a,b)=>a+b,0)/N,oppP10:oppQ[Math.floor(N*.1)],oppP90:oppQ[Math.floor(N*.9)],
  current:cur.length?ev(cur):null,maxPts:base,best,
  ins:best.set.filter(p=>!base.set.includes(p)),outs:base.set.filter(p=>!best.set.includes(p))}}
