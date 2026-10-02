import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
r=json.loads(Path('outputs/daily-edition.json').read_text())['research'];s=json.loads(Path('work/daily-run/snapshot.json').read_text());now=datetime.now(timezone.utc)
r.update(reviewed_at='2026-09-17',updated_at=now.isoformat(),valid_until=(now+timedelta(hours=24)).isoformat(),changes=['Godwin is off the Jacked Pine roster; Likely is now rostered. Retired the Godwin / Kraft trade.','Keep Golden available as Collins cover; pause the Golden-for-Dobbins idea. Monitor Swift and Bowers.','Check Detroit and Buffalo starters before Thursday kickoff; keep later players in FLEX when possible.'])
def source(key,title,url,finding):r['sources'][key]=dict(title=title,url=url,date='Sep 16; checked Sep 17, 2026',kind='Official team report' if key!='swift' else 'Reported team practice update',finding=finding)
source('texans','Texans · Week 2 injury report','https://www.houstontexans.com/news/week-2-injury-report-texans-vs-bengals','Collins was limited Wednesday with a hamstring injury. A final game status is still needed.')
source('saints','Saints · Wednesday injury report','https://www.neworleanssaints.com/news/injury-report-baltimore-ravens-vs-new-orleans-saints-2026-nfl-week-2-wednesday','Juwan Johnson missed Wednesday practice with an illness.')
source('swift','FantasyPros · Swift practice update','https://www.fantasypros.com/nfl/news/608395/dandre-swift-ankleknee-limited-practice-wednesday.php','Swift was limited Wednesday with ankle and knee issues; this is not a final game designation.')
source('bills','Bills · Final Thursday injury report','https://www.buffalobills.com/news/buffalo-bills-injury-report-vs-lions-week-2','The final report lists Cole Bishop, Ty Johnson and T.J. Sanders as questionable. Check the inactive list before kickoff.')
r['sources']['flex']['finding']='The checked PPR list places Etienne ahead of Godwin and Reed. Weekly rankings remain opinions, not custom-scoring projections.'
for key in ['practice','value','flex','katz','pfn']:r['sources'][key]['date']+=' · rechecked Sep 17'
def move(action,pid,title,reason,cost,sources):return dict(action=action,id=pid,title=title,reason=reason,cost=cost,sources=sources,drop_id=None,confidence='Monitor' if action=='Monitor' else 'Hold' if action=='Hold' else 'Lean')
for l in s['context']['leagues']:
 a=r['leagues'][l['id']];a['roster_ids']=sorted(p['id'] for p in l['roster']);a['scoring_baseline']=l['scoring'];a['slots_baseline']=l['slots']
 if l['name']=='Jacked Pine':
  a['trades']=[];a['headline']='Keep Etienne. Recheck the TE depth.';a['strategy']='Godwin is no longer rostered and Likely is on the bench. Keep Kraft starting; the old Godwin trade is retired.'
  a['player_moves'][0].update(reason='Etienne remains the lean over Reed on the checked PPR list. Godwin is no longer a roster alternative.')
  a['player_moves'].append(move('Monitor','7002','Monitor Johnson; keep Kraft starting','Johnson missed Wednesday practice with an illness. Likely is now on your roster.','No urgent TE trade or claim. Wait for updated practice reports.',['saints','sleeper']))
  a['calls']=[dict(kind=m['action'],title=m['title'],reason=m['reason'],confidence=m['confidence'],sources=m['sources'],recheck=m['cost']) for m in a['player_moves']]
  a['calls'][0]['kind']='Lineup'
  a['lineup_notes']=[dict(title=m['title'],body=m['reason']+' '+m['cost'],sources=m['sources']) for m in a['player_moves']]
  for p in a['lineup']:
   if p['id']=='7543':p['note']='Lean over Reed; Godwin is no longer rostered'
 elif l['name']=='Netanyahu Ball':
  a['trades']=[];a['headline']='Keep Golden available while Collins is uncertain.';a['strategy']='Pause the Golden trade. Monitor Collins, Swift and Bowers; preserve healthy alternatives before Sunday.'
  a['player_moves']=[move('Hold','12501','Keep Golden as receiver cover','Collins was limited Wednesday with a hamstring issue. Golden provides an on-roster fallback if Collins cannot play.','Pause Golden for Dobbins until Collins is clarified; do not sell your contingency.',['texans','flex']),move('Monitor','6790','Recheck Swift before locking FLEX','Swift was limited Wednesday with ankle and knee issues.','If unavailable, compare healthy Golden and Reed for FLEX; do not assume a full workload from a Questionable tag.',['swift','flex']),move('Monitor','11604','Keep Goedert ready for Bowers','Wednesday’s report still has Bowers missing practice.','Do not start Bowers without updated availability and workload guidance.',['practice']),move('Start','11563','Keep the Nix lean over Mahomes','The checked QB rankings continue to favor Nix for Week 2.','Weekly opinion, not a calculated custom-scoring projection.',['katz'])]
  a['calls']=[dict(kind=m['action'],title=m['title'],reason=m['reason'],confidence=m['confidence'],sources=m['sources'],recheck=m['cost']) for m in a['player_moves']]
  a['lineup_notes']=[dict(title=m['title'],body=m['reason']+' '+m['cost'],sources=m['sources']) for m in a['player_moves']]
  for p in a['lineup']:
   if p['id']=='7569':p['note']='Conditional: monitor hamstring; Golden is fallback if inactive'
   if p['id']=='6790':p['note']='Conditional: monitor ankle/knee; review healthy FLEX alternatives'
 else:
  a['player_moves'].append(move('Monitor','4983','Check DJ Moore before Thursday kickoff','Buffalo plays Thursday. Keep Moore in a WR slot if starting him, preserving FLEX for a later player.','Check final inactives before kickoff; the published team report does not replace that check.',['bills']))
 for t in a['trades']:
  team=next(x for x in l['tracking']['teams'] if x['roster_id']==t['partner_roster_id']);t['partner_roster_ids']=sorted(p['id'] for p in team['players'])
 a['lineup_notes'].append(dict(title='Thursday lineup locks',body='Review Detroit and Buffalo starters before Thursday kickoff. Use fixed RB/WR slots for early starters when possible to preserve later FLEX choices.',sources=['bills']))
Path('work/research-2026-09-17.json').write_text(json.dumps(r,indent=2))
