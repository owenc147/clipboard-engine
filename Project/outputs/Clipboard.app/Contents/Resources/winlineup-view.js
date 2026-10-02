// "Win-probability lineup" box in Title odds → This week. Runs TitleModel.winLineup (4,000 simulated weeks,
// common random numbers) and compares your current Sleeper lineup, the max-points lineup and the best-P(win) lineup.
(function(){
const cache={};const pc=x=>(100*x).toFixed(1)+'%',e=v=>esc(String(v??''));
function box(lid){const R=modelRuns[lid];if(!R||!R.done||!R.E||!TitleModel.winLineup)return '';
 const key=lid+'|'+modelData.built_at;if(!cache[key]){try{cache[key]=TitleModel.winLineup(R.M,R.E,{N:4000})||{none:1}}catch(err){console.error(err);cache[key]={none:1}}}
 const r=cache[key];if(r.none)return '';const nm=p=>e(mName(p));const b=r.best,m=r.maxPts,c=r.current;
 const role=b.p<.35?'You’re the underdog, so the solver favours upside: higher-variance plays that can steal a win.':b.p>.65?'You’re the favourite, so the solver favours a steady floor and avoids blowup risk.':'Close matchup: maximum points and maximum win chance are nearly the same thing here.';
 const swap=r.ins.length?`<p class="cb-wl-swap"><b>Win-probability swap:</b> start ${r.ins.map(nm).join(', ')} over ${r.outs.map(nm).join(', ')} (win chance ${pc(m.p)} → <b>${pc(b.p)}</b>, projected points ${m.mean.toFixed(1)} → ${b.mean.toFixed(1)}).</p>`:'<p class="cb-wl-swap">The max-points lineup is also the best lineup for winning this matchup. No swap needed.</p>';
 const cur=c&&Math.abs(c.p-b.p)>.004?`<p>Your lineup currently set in Sleeper: <b>${pc(c.p)}</b> to win${c.set.length?'':''}. Best available: ${pc(b.p)}.</p>`:'';
 return `<div class="cb-wl"><h4>Win-probability lineup · vs ${e(r.opp)}</h4><div class="cb-dc-sum"><div><small>Win chance (best)</small><b>${pc(b.p)}</b></div><div><small>Your range (10–90%)</small><b>${b.p10.toFixed(0)}–${b.p90.toFixed(0)}</b></div><div><small>Their range (10–90%)</small><b>${r.oppP10.toFixed(0)}–${r.oppP90.toFixed(0)}</b></div><div><small>Simulated weeks</small><b>${r.N.toLocaleString()}</b></div></div>${swap}${cur}<p class="cb-wl-note">${role} Variance differences come from position (RB vs WR vs TE flex), injury/questionable odds and NFL-team stacking; players at the same position are given the same backtested volatility.</p></div>`}
if(typeof window.mRender==='function'){const before=window.mRender;window.mRender=mRender=function(){before();try{const lid=mLeagueId();if(!lid)return;const html=box(lid);if(!html)return;
 const card=[...document.querySelectorAll('#content .desk-card')].find(c=>/^This week/i.test(c.querySelector('h3')?.textContent||''));if(!card||card.querySelector('.cb-wl'))return;
 const strip=card.querySelector('.pt-weeks');(strip?strip.previousElementSibling||strip:card.lastElementChild).insertAdjacentHTML(strip?'beforebegin':'afterend',html)}catch(err){console.error('winlineup',err)}}}
})();
