from pathlib import Path
p=Path(__file__).parent/'stage/model-engine.js';s=p.read_text()
insert='''
// Shared factor weights are allocated from the target variance, not added on top.
function variancePlan(cv,talent=0,team=0,bringback=0,opponent=0){
 const total=Math.log1p(cv*cv), b=Math.max(0,bringback)*total,o=Math.max(0,opponent)*total;
 const rem=total-talent*talent-team*team-b-o;
 if(rem < -1e-10)throw new Error('Variance budget exceeded');
 return {total,independent:Math.sqrt(Math.max(0,rem)),bringback:Math.sqrt(b),opponent:Math.sqrt(o)};
}
function empiricalQuantile(errors,z){return errors[Math.min(errors.length-1,Math.max(0,Math.floor(Phi(z)*errors.length)))];}
function sameScoring(a,b){return JSON.stringify(Object.entries(a||{}).sort())===JSON.stringify(Object.entries(b||{}).sort())}
'''
s=s.replace('function rng(seed)',insert+'\nfunction rng(seed)')
s=s.replace("const cv=CV[ps]||.6,sT=Math.sqrt(Math.log(1+cv*cv)),sTeam", "const cv=CV[ps]||.6,sT=Math.sqrt(Math.log(1+cv*cv)),sTeam")
s=s.replace("team=(M.data.players[p]||[])[2];", "team=({'LA':'LAR'}[(M.data.players[p]||[])[2]]||(M.data.players[p]||[])[2]);")
s=s.replace("return {p,pos:ps,mean:M.val[p]||[],hz", "const cal=M.data.calibration||{},entry=cal.residuals?.[M.lid]?.[ps],residuals=entry?.enabled&&sameScoring(cal.scoring?.[M.lid],M.L.raw_scoring)?entry.centered_errors:null;\n  return {p,pos:ps,team,cv,residuals,mean:M.val[p]||[],hz")
s=s.replace("sTal:y?.12:.18", "sTal:residuals?0:(y?.12:.18)")
s=s.replace("return {ids,ix,pl,nt}", "// Include opponents without a fantasy-rostered player so factor IDs stay stable.\n for(const byTeam of Object.values(M.data.research_inputs?.games||{}))for(const team of Object.keys(byTeam))if(nfl[team]==null)nfl[team]=nt++;\n return {ids,ix,pl,nt,nfl}")
s=s.replace("let spare=null;const g=()=>{if(spare!==null){const s=spare;spare=null;return s}", "const g=()=>{if(acc.gaussianSpare!=null){const s=acc.gaussianSpare;acc.gaussianSpare=null;return s}")
s=s.replace("spare=r*Math.sin(6.283185307*v)", "acc.gaussianSpare=r*Math.sin(6.283185307*v)")
s=s.replace("acc.stamp=0}", "acc.factorValues=new Float64Array(3*64*NW);acc.factorStamps=new Int32Array(3*64*NW);acc.stamp=0}")
a=s.index(' const draw=(i,w)=>');b=s.index('\n const score=',a)
s=s[:a]+''' const factor=(kind,idx,w)=>{const k=(kind*64+idx)*NW+w;if(acc.factorStamps[k]!==acc.stamp){acc.factorStamps[k]=acc.stamp;acc.factorValues[k]=g()}return acc.factorValues[k]};
 const draw=(i,w)=>{
  const x=i*NW+w;if(dst[x]===acc.stamp)return dr[x];dst[x]=acc.stamp;const p=pl[i],mean=p.mean[w]||0;
  const projected=M.data.proj[p.p]?.[w];
  if(!projected||(mean===0&&(M.raw[p.p]?.[w]||0)!==0))return dr[x]=0;
  const opp=M.data.research_inputs?.games?.[M.W[w]]?.[p.team]?.opponent,oi=E.nfl[opp],ti=E.nfl[p.team];
  const cc=M.data.calibration?.correlations||{},hasGame=oi!=null&&ti!=null;
  const rb=hasGame&&['QB','WR','TE'].includes(p.pos)&&cc.bringback?.enabled?Math.max(0,cc.bringback.rho):0;
  const rd=hasGame&&['QB','DEF'].includes(p.pos)&&cc.qb_dst?.enabled?Math.abs(cc.qb_dst.rho):0;
  const gameZ=rb?factor(1,Math.min(ti,oi),w):0,duelZ=rd?factor(2,p.pos==='DEF'?oi:ti,w):0;
  if(p.residuals){
   const z=Math.sqrt(1-rd)*g()-(p.pos==='DEF'?Math.sqrt(rd)*duelZ:0);
   return dr[x]=mean+empiricalQuantile(p.residuals,z);
  }
  const ts=p.sTeam&&ti!=null?p.sTeam:0,v=variancePlan(p.cv,p.sTal,ts,rb,rd);
  const noise=v.independent*g()+(ts?ts*factor(0,ti,w):0)+v.bringback*gameZ+v.opponent*duelZ;
  return dr[x]=mean*tal[i]*Math.exp(noise-.5*(v.total-p.sTal*p.sTal));
 };''' +s[b:]
s=s.replace("root.TitleModel={prepare,", "root.TitleModel={variancePlan,empiricalQuantile,prepare,")
p.write_text(s)
