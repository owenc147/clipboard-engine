// Dated editorial choices, checked against the latest roster. Never submits a lineup.
function lineupPlan(research,league,week,now=new Date()) {
 const blocked=[];
 if(!research||!league)return {blocked:['No researched lineup for this league.'],rows:[]};
 if(Number(week)!==RESEARCH.week)blocked.push('These suggestions cover Week '+RESEARCH.week+' only. Select that week to review them.');
 if(now>=new Date(RESEARCH.expires_after+'T00:00:00-04:00'))blocked.push('This lineup edition has expired. New research is needed.');
 if(JSON.stringify(league.slots)!==JSON.stringify(research.slots_baseline))blocked.push('Lineup slots changed. This edition needs review.');
 if(JSON.stringify(Object.entries(league.scoring||{}).sort())!==JSON.stringify(Object.entries(research.scoring_baseline||{}).sort()))blocked.push('Scoring changed. This edition needs review.');
 if(RESEARCH.valid_until&&now>=new Date(RESEARCH.valid_until))blocked.push('Daily lineup research is due. Review updated news before using this edition.');
 const roster=new Map((league.roster||[]).map(p=>[p.id,p])), reserve=new Set([...(league.reserve||[]),...(league.taxi||[])]), seen=new Set();
 const flex={FLEX:['RB','WR','TE'],SUPER_FLEX:['QB','RB','WR','TE'],WRRB_FLEX:['WR','RB'],REC_FLEX:['WR','TE']};
 const rows=(research.lineup||[]).map(p=>{
  const live=roster.get(p.id);let issue='';
  if(!live)issue='No longer on your roster';
  else if(reserve.has(p.id))issue='In reserve · do not start yet';
  else if(/^(out|doubtful|ir|suspended|pup|inactive)$/i.test(live.injury||''))issue='Unavailable: '+live.injury;
  else if(seen.has(p.id))issue='Duplicate player · review required';
  else if(!(flex[p.slot]||[p.slot]).includes(p.position))issue='Position does not fit slot';
  seen.add(p.id);return {...p,issue,injury:live?.injury||''};
 });
 return {blocked,rows};
}
function renderLineup(r,lc){
 const plan=lineupPlan(r,lc,reportWeek);
 if(plan.blocked.length){$('content').innerHTML=plan.blocked.map(s=>'<div class="context-note">'+esc(s)+'</div>').join('');return}
 const current=players((leagues[selected]?.lines.find(s=>s.startsWith('Starters: '))||'').replace('Starters: ',''));
 const changed=plan.rows.filter(p=>!current.some(c=>c.name.replace(' DST','')===p.name)&&!p.issue);
 const rows=plan.rows.map((p,i)=>{const set=current.some(c=>c.name.replace(' DST','')===p.name);return '<div class="lineup-row '+(p.issue?'needs-review':!set?'suggested':'')+'"><span class="slot '+esc(p.slot)+'">'+esc(p.slot==='SUPER_FLEX'?'SFLX':p.slot)+'</span><div class="lineup-player"><strong>'+esc(p.name)+(p.position==='DEF'?' D/ST':'')+'</strong><small>'+esc(p.team||'')+' · '+esc(p.note)+'</small>'+(p.injury?'<small class="flag">Cached status: '+esc(p.injury)+'</small>':'')+'</div><span class="lineup-state">'+esc(p.issue||(set?'IN LINEUP':'START'))+'</span></div>'}).join('');
 const notes=r.lineup_notes.map(n=>'<article class="lineup-note"><h3>'+esc(n.title)+'</h3><p>'+esc(n.body)+'</p><div class="sources-inline">'+n.sources.map(linkSource).join('')+'</div></article>').join('');
 const picks=new Set(plan.rows.map(p=>p.id));const bench=(lc.roster||[]).filter(p=>!picks.has(p.id));
 $('content').innerHTML='<section class="lineup-hero"><div class="kicker">WEEK '+RESEARCH.week+' · RESEARCHED '+esc(RESEARCH.reviewed_at)+'</div><h2>Your starting point.</h2><p>'+esc(lc.name)+' · '+changed.length+' suggested '+(changed.length===1?'starter change':'starter changes')+'</p><span class="lineup-disclaimer">Editorial suggestions. Make changes in Sleeper after checking game status and locks.</span></section>'+researchNotices(r,lc)+'<div class="lineup-grid"><section class="card"><div class="card-header"><h3>Suggested starters</h3><span class="small-label">'+plan.rows.length+' SLOTS</span></div><div class="card-body">'+rows+'<p class="trade-note">Compared with your latest saved starters. “In lineup” means already starting somewhere in your lineup; equivalent FLEX placements can differ.</p></div></section><div class="research-column"><section class="card"><div class="card-header"><h3>The close calls</h3><span class="small-label">WHY THESE PICKS</span></div>'+notes+'</section><section class="card"><div class="card-header"><h3>Suggested bench & reserve</h3></div><div class="card-body">'+bench.map(p=>'<div class="bench-player"><b>'+esc(p.name)+'</b><small>'+((lc.reserve||[]).includes(p.id)?'Reserve':'Suggested bench')+(p.injury?' · '+esc(p.injury):'')+'</small></div>').join('')+'</div></section></div></div>';
}
const renderWithoutLineup=render;
render=function(){renderWithoutLineup();const b=$('lineup-view');b.classList.toggle('active',currentView==='lineup');b.setAttribute('aria-pressed',currentView==='lineup');if(currentView==='lineup')renderLineup(currentResearch(),currentContext());else if(currentView==='overview'&&currentResearch()){
 const r=currentResearch(),plan=lineupPlan(r,currentContext(),reportWeek);if(!plan.blocked.length){const el=document.querySelector('.priority-strip');if(el)el.outerHTML='<div class="priority-strip"><span class="number">XI</span><p><small>WEEK '+RESEARCH.week+' LINEUP DESK · '+esc(RESEARCH.reviewed_at)+'</small>'+esc(r.calls.find(c=>c.kind==='Lineup')?.title||'Review your suggested starters')+'</p><button class="action" onclick="setView(\'lineup\')">View lineup →</button></div>';}
}};
