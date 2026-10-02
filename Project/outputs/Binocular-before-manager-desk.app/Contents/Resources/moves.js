// The daily edition is data only. The native app watches its companion JSON file.
window.receiveEdition=data=>{
 if(!data.research?.leagues||!data.research?.sources)return;
 if((data.research.user||'').toLowerCase()!==(context.user||'').toLowerCase())return;
 window.RESEARCH=data.research;
 const snap=data.snapshot;
 if(snap?.context&&Date.parse(snap.context.fetched_at)>Date.parse(context.fetched_at||'1970-01-01'))window.receive({...snap,status:'Daily research and league snapshot loaded'});
 else {render();updateFreshness()}
};
function movesIssues(r,lc,now=new Date()){
 const issues=[];
 if(!r||!lc)return ['No researched moves for this league.'];
 if(Number(reportWeek)!==Number(RESEARCH.week)||String(context.season)!==String(RESEARCH.season))issues.push('Different week or season. These moves need a new review.');
 if(!RESEARCH.valid_until||!Number.isFinite(Date.parse(RESEARCH.valid_until))||now>=new Date(RESEARCH.valid_until))issues.push('Daily research is due. These ideas are archived until the next successful update.');
 if(!Number.isFinite(Date.parse(context.fetched_at))||now-new Date(context.fetched_at)>86400000)issues.push('Ownership is over 24 hours old. Refresh league data before evaluating these moves.');
 if(JSON.stringify(Object.entries(lc.scoring||{}).sort())!==JSON.stringify(Object.entries(r.scoring_baseline||{}).sort())||JSON.stringify(lc.slots)!==JSON.stringify(r.slots_baseline))issues.push('League rules changed. These ideas need review.');
 return issues;
}
function tradeCheck(t,r,lc){
 const own=new Set((lc.roster||[]).map(p=>p.id)),team=(lc.tracking?.teams||[]).find(x=>x.roster_id===t.partner_roster_id);
 const issues=[];
 if(!t.give.every(id=>own.has(id)))issues.push('A player offered is no longer on your roster.');
 if(!team||!t.receive.every(id=>team.players.some(p=>p.id===id)))issues.push('Target ownership changed.');
 if(t.receive.some(id=>own.has(id)))issues.push('You already roster the target.');
 if(JSON.stringify([...own].sort())!==JSON.stringify(r.roster_ids))issues.push('Your roster changed since this analysis.');
 if(team&&JSON.stringify(team.players.map(p=>p.id).sort())!==JSON.stringify(t.partner_roster_ids))issues.push('The other roster changed; reassess the fit.');
 return {team,issues};
}
function moveCheck(m,lc){
 const own=new Set((lc.roster||[]).map(p=>p.id));
 if(m.action==='Add'){
  const market=(lc.market||[]).find(p=>p.id===m.id),owner=(lc.tracking?.teams||[]).find(t=>t.players.some(p=>p.id===m.id));
  if(!market||market.owner||owner)return 'Target is rostered or availability is unverified.';
  if(m.drop_id&&!own.has(m.drop_id))return 'Drop candidate is no longer on your roster.';
 }else if(!own.has(m.id))return 'Player is no longer on your roster.';
 if(m.action==='Start'){
  const p=(lc.roster||[]).find(p=>p.id===m.id);
  if((lc.reserve||[]).includes(m.id)||/^(out|doubtful|ir|suspended|pup|inactive)$/i.test(p?.injury||''))return 'Player unavailable or in reserve; review required.';
 }
 return '';
}
function movePlayer(id,lc){return (lc.tracking?.teams||[]).flatMap(t=>t.players).find(p=>p.id===id)||(lc.roster||[]).find(p=>p.id===id)||(lc.market||[]).find(p=>p.id===id)||{name:id};}
function renderMoves(){
 const lc=currentContext(),r=currentResearch();
 if(!r||!lc){$('content').innerHTML='<div class="context-note">No daily research matched this league and account.</div>';return}
 const issues=movesIssues(r,lc),refs=ids=>(ids||[]).map(linkSource).join('');
 const playerCards=(r.player_moves||[]).map(m=>{const issue=moveCheck(m,lc);return '<article class="move-card"><div class="call-top"><span class="call-kind">'+esc(m.action.toUpperCase())+'</span><span class="confidence">'+esc(m.confidence)+'</span></div><h3>'+esc(m.title)+'</h3><p>'+esc(m.reason)+'</p><div class="move-cost">'+esc(m.cost)+'</div>'+(issue?'<div class="context-note">'+esc(issue)+'</div>':'')+'<div class="sources-inline">'+refs(m.sources)+'</div></article>'}).join('');
 const tradeCards=(r.trades||[]).map(t=>{const check=tradeCheck(t,r,lc),problems=[...issues,...check.issues];const names=ids=>ids.map(id=>'<strong>'+esc(movePlayer(id,lc).name)+'</strong>').join('<span> + </span>');return '<article class="trade-proposal"><div class="call-top"><span class="call-kind">'+(problems.length?'NEEDS REVIEW':'EXPLORE')+'</span><span class="confidence">'+esc(check.team?.name||'Ownership changed')+'</span></div><h3>'+esc(t.title)+'</h3><div class="trade-sides"><div><small>YOU SEND</small>'+names(t.give)+'</div><div class="trade-arrow">⇄</div><div><small>YOU RECEIVE</small>'+names(t.receive)+'</div></div><div class="trade-reasons"><p><b>Your reason</b>'+esc(t.why)+'</p><p><b>Their possible reason</b>'+esc(t.partner_reason)+'</p></div><p class="move-cost"><b>Trade-off:</b> '+esc(t.risk)+'</p><details><summary>Value check & evidence</summary><p>'+esc(t.value_note)+'</p><p>Analyst judgment using a general redraft chart, not custom-scoring projections or an acceptance prediction. Confirm trade deadline and game locks in Sleeper.</p><div class="sources-inline">'+refs(t.sources)+'</div></details>'+(check.issues.length?'<div class="context-note">'+check.issues.map(esc).join(' ')+'</div>':'')+'</article>'}).join('');
 $('content').innerHTML='<section class="lineup-hero"><div class="kicker">DAILY SCOUTING · WEEK '+esc(RESEARCH.week)+'</div><h2>Make your next move.</h2><p>'+esc(lc.name)+' · Player calls and possible trades</p><span class="lineup-disclaimer">Reviewed '+esc(dateLabel(RESEARCH.updated_at))+' · Daily research catches up through Codex; checks every 15 minutes.</span></section>'+issues.map(x=>'<div class="context-note">'+esc(x)+'</div>').join('')+'<section class="daily-changes"><b>What changed</b><ul>'+(RESEARCH.changes||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul><small>When your Mac and Codex are running, checks publish research once per day. Binocular can be closed.</small></section><div class="moves-grid">'+(playerCards||'<p>No supported player move today. Hold your roster.</p>')+'</div><div class="moves-heading"><span class="kicker">TRADE DESK</span><h2>Start a conversation.</h2><p>Exploratory ideas. No trade offers are sent by Binocular.</p></div>'+(tradeCards||'<div class="context-note">No supported trade today. Holding is a valid choice.</div>');
}
const renderBeforeMoves=render;
render=function(){renderBeforeMoves();const b=$('moves-view');b.classList.toggle('active',currentView==='moves');b.setAttribute('aria-pressed',currentView==='moves');if(currentView==='moves')renderMoves()};
