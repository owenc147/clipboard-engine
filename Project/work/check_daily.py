import copy,json,unittest
from pathlib import Path
from datetime import datetime
from publish_research import validate
BASE=Path(__file__).resolve().parents[1]
e=json.loads((BASE/'outputs/daily-edition.json').read_text())
class PublicationTests(unittest.TestCase):
 def test_valid(self):validate(e['research'],e['snapshot'])
 def test_stale(self):
  s=copy.deepcopy(e['snapshot']);s['context']['fetched_at']='2025-01-01T00:00:00+00:00'
  with self.assertRaises(AssertionError):validate(e['research'],s)
 def test_target_traded(self):
  s=copy.deepcopy(e['snapshot']);l=s['context']['leagues'][0];t=e['research']['leagues'][l['id']]['trades'][0]
  team=next(x for x in l['tracking']['teams'] if x['roster_id']==t['partner_roster_id']);team['players']=[p for p in team['players'] if p['id'] not in t['receive']]
  with self.assertRaises(AssertionError):validate(e['research'],s)
 def test_rule_change(self):
  s=copy.deepcopy(e['snapshot']);s['context']['leagues'][0]['scoring']['rec']=0
  with self.assertRaises(AssertionError):validate(e['research'],s)
 def test_claim_taken(self):
  r=copy.deepcopy(e['research']);l=e['snapshot']['context']['leagues'][0];r['leagues'][l['id']]['player_moves'][0].update(action='Add',id='TB')
  with self.assertRaises(AssertionError):validate(r,e['snapshot'])
if __name__=='__main__':unittest.main()
