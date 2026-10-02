import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
root=Path('outputs/Binocular.app/Contents/Resources')
r=json.loads((root/'research.json').read_text());s=json.loads(Path('work/latest-snapshot.json').read_text())
now=datetime.now(timezone.utc);r['updated_at']=now.isoformat();r['valid_until']=(now+timedelta(hours=24)).isoformat()
r['scope']='Daily scouting edition. Recommendations are analyst judgments checked against saved ownership; confirm injuries and game locks in Sleeper before acting.'
r['changes']=['Retired TB / SF waiver calls: both defenses are rostered in all three leagues.','Added Wednesday practice updates for McConkey and Bowers.','Added three exploratory trades with ownership checks and reasons for each side.']
r['sources']['practice']={'title':'Raiders · Wednesday Week 2 injury report','url':'https://www.raiders.com/news/las-vegas-raiders-los-angeles-chargers-nfl-week-2-injury-report-2026-season','date':'Sep 16, 2026','kind':'Official team report','finding':'Bowers (knee) and McConkey (rib) did not practice Wednesday. Neither has a final Week 2 game designation on this report.'}
r['sources']['value']['date']='Rechecked Sep 16, 2026'
def move(action,pid,title,reason,cost,sources,drop=None):return dict(action=action,id=pid,title=title,reason=reason,cost=cost,sources=sources,drop_id=drop,confidence='Lean' if action in ['Start','Add'] else 'Monitor' if action=='Monitor' else 'Hold')
def trade(title,give,receive,partner,why,other,risk,value):return dict(title=title,give=give,receive=receive,partner_roster_id=partner,why=why,partner_reason=other,risk=risk,value_note=value,confidence='Exploratory · no offer sent',sources=['value'],partner_roster_ids=[])
for l in s['context']['leagues']:
 a=r['leagues'][l['id']];a['roster_ids']=sorted(p['id'] for p in l['roster']);a['scoring_baseline']=l['scoring'];a['slots_baseline']=l['slots']
 if l['name']=='Jacked Pine':
  a['player_moves']=[move('Start','7543','Keep Etienne in FLEX','The current lineup already reflects the earlier lean over Reed. Godwin remains an alternative.','No waiver or trade needed. Revisit late-week role news.',['flex']),move('Monitor','11635','Keep a healthy option ahead of McConkey','Wednesday’s official report lists him as DNP with a rib injury.','Keep him rostered; wait for later practice reports and final status.',['practice']),move('Hold','8183','Keep Purdy as Superflex cover','You have Hurts and Daniels starting, with Purdy available for injury or bye cover.','A third quarterback has a real opportunity cost in a Superflex trade.',['value'])]
  a['trades']=[trade('Explore a McBride upgrade',['4037','9484'],['8130'],'1','Consolidates a bench receiver and your starting TE into one TE upgrade in a shallow six-team league.','nicbarbz40 can replace McBride with Kraft and consider Godwin for a FLEX spot; Kittle is also on that roster.','They must free a roster spot and may prefer the best player. You lose Godwin depth while McConkey is uncertain. Walk away if asked for a core starter.','Chart reference: Godwin 22.7 + Kraft 15.2 versus McBride 28.0. This is an intentional consolidation premium, not proof of fairness.')]
  for c in a['calls']:
   if c['kind']=='Injury':c.update(reason='McConkey did not practice Wednesday (rib). Keep a healthy alternative ready; final Week 2 status is still pending.',sources=['practice'])
 elif l['name']=='Netanyahu Ball':
  a['player_moves']=[move('Start','11563','Keep Nix; Adams over Reed','The current starters match the researched Week 2 lean. Golden remains an upside bench option.','This is a ranking-based lean, not a custom-scoring point projection.',['qb','wr']),move('Monitor','11604','Goedert remains Bowers cover','Bowers did not practice Wednesday with a knee injury. No final Week 2 designation is published in that report.','Hold Bowers; do not activate solely because a cached status changes.',['practice']),move('Hold','13414','Hold Black as RB depth','Black is already on your roster, so the previous add is complete.','Do not force him into a starting slot based on one game.',['black'])]
  a['trades']=[trade('Explore Golden for Dobbins',['12501'],['6806'],'4','Turns bench WR upside into RB cover behind Gibbs, Hall and Swift.','MagicMax5 has Dobbins on the bench plus Irving, Croskey-Merritt and Jacobs; Golden offers a different WR upside profile.','You surrender Golden’s breakout upside. Dobbins is depth, not a clear new starter; do not add another useful player to force it.','Chart reference: Golden 15.8 versus Dobbins 18.9. A conversation starter; the other manager can reasonably decline.')]
  for c in a['calls']:
   if 'Bowers' in c['reason'] or 'Bowers' in c['title']:c.update(reason='Bowers missed Wednesday practice (knee). Keep Goedert ready while awaiting the final Week 2 report.',sources=['practice'])
 else:
  a['player_moves']=[move('Hold','12517','Hold Loveland after the empty box score','Reported route participation supports patience rather than buying another TE after one game.','Monitor targets and routes in Week 2; keep your WR depth.',['loveland']),move('Hold','13296','Keep Douglas on the bench','Douglas is already rostered. Let his role develop before moving him ahead of established starters.','Do not drop Malik Washington just because Douglas had a productive debut.',['douglas']),move('Monitor','MIN','Retire the TB / SF pickup plan','Both recommended defenses now belong to other teams in this league.','Keep MIN for now; no researched, available replacement is established in this edition.',['sleeper','dst'])]
  a['trades']=[trade('Explore Wilson for Pollard',['10232'],['5967'],'4','Adds a different RB2 option alongside Love, Croskey-Merritt and Dobbins.','bwyck21 has Pollard benched behind Walker and Henderson; Wilson could compete with Doubs for FLEX.','This is optional: you would remove your current FLEX and need Douglas or Dobbins to replace him. Hold if that loss outweighs RB depth.','Chart reference: Wilson 14.4 versus Pollard 16.6. Similar range does not establish equal weekly value.')]
  for c in a['calls']:
   if c['kind']=='Defense':c.update(title='TB and SF are taken; keep MIN pending a new review',reason='The refreshed roster check shows both targets on other teams. The old streaming move is retired.',recheck='A replacement must be available in this league before recommending a claim.',sources=['sleeper','dst'])
  for n in a['lineup_notes']:
   if 'Stream Tampa' in n['title']:n.update(title='Previous defense targets are no longer available',body='TB and SF now belong to other teams. Keep MIN pending research on an available alternative.',sources=['sleeper','dst'])
  for p in a['lineup']:
   if p['id']=='MIN':p['note']='Keep pending research on an available replacement'
 for t in a['trades']:
  partner=next(x for x in l['tracking']['teams'] if x['roster_id']==t['partner_roster_id']);t['partner_roster_ids']=sorted(p['id'] for p in partner['players'])
Path('work/research-draft.json').write_text(json.dumps(r,indent=2))
