"""Validate researched data and atomically publish it beside Binocular.app."""
import json,sys,os
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parents[1]
def timestamp(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def validate(r,s,now=None):
 now=now or datetime.now(timezone.utc)
 c=s['context'];assert isinstance(s['text'],str) and s['text'],'Missing brief'
 assert r['user']==c['user']=='coffero','Account mismatch'
 assert str(r['season'])==str(c['season']) and int(r['week'])==int(c['nfl_week']),'Week/season mismatch'
 assert 0 <= (now-timestamp(c['fetched_at'])).total_seconds() < 86400,'Snapshot is stale or future dated'
 assert 0 <= (now-timestamp(r['updated_at'])).total_seconds() < 86400,'Research must have an actual recent review'
 assert 0 < (timestamp(r['valid_until'])-now).total_seconds() <= 36*3600,'Invalid research expiry'
 assert isinstance(r.get('candidates'),list),'Candidates must be a list of records'
 for candidate in r['candidates']:
  assert isinstance(candidate,dict) and isinstance(candidate.get('name'),str) and candidate['name'].strip(),'Candidate must contain a player name'
 for source in r['sources'].values():assert source['url'].startswith('https://') and source['date'],'Missing dated HTTPS source'
 for l in c['leagues']:
  a=r['leagues'][l['id']];own={p['id'] for p in l['roster']}
  assert sorted(own)==a['roster_ids'],'Research roster baseline mismatch'
  assert a['scoring_baseline']==l['scoring'] and a['slots_baseline']==l['slots'],'Rules mismatch'
  assert a['player_moves'],'Missing player analysis'
  for m in a['player_moves']:
   assert m['reason'] and m['cost'] and m['sources'],'Incomplete player reasoning'
   if m['action']=='Add':
    market=next((p for p in l['market'] if p['id']==m['id']),None)
    assert market and not market['owner'] and not any(m['id']==p['id'] for t in l['tracking']['teams'] for p in t['players']),'Add target not available'
    assert not m.get('drop_id') or m['drop_id'] in own,'Drop not owned'
   else:assert m['id'] in own,'Player not owned'
  for t in a.get('trades',[]):
   assert t['give'] and t['receive'] and set(t['give'])<=own,'Offer not owned'
   team=next(x for x in l['tracking']['teams'] if x['roster_id']==t['partner_roster_id'])
   theirs={p['id'] for p in team['players']}
   assert set(t['receive'])<=theirs and not (set(t['receive'])&own),'Target ownership mismatch'
   assert sorted(theirs)==t['partner_roster_ids'],'Partner baseline mismatch'
   assert all(t[k] for k in ['why','partner_reason','risk','value_note','sources']),'Incomplete trade analysis'
  for item in a['calls']+a.get('lineup_notes',[])+a['player_moves']+a.get('trades',[]):
   assert all(key in r['sources'] for key in item['sources']),'Unknown source'
 return {'research':r,'snapshot':s}
def publish(research,snapshot):
 r=json.loads(Path(research).read_text());s=json.loads(Path(snapshot).read_text());edition=validate(r,s)
 dest=BASE/'outputs/daily-edition.json';temp=dest.with_suffix('.pending.json')
 temp.write_text(json.dumps(edition,ensure_ascii=False));os.replace(temp,dest)
 print('Published validated daily edition:',dest)
if __name__=='__main__':
 assert len(sys.argv)==3,'Usage: python3 work/publish_research.py RESEARCH_JSON SNAPSHOT_JSON'
 publish(*sys.argv[1:])
