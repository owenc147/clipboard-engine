import unittest, tempfile, json, copy, sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
sys.path.insert(0,str(Path(__file__).parent))
import desk as d
class DeskTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime.now(timezone.utc)
  self.players=[dict(id='1',name='Starter',position='RB',team='BUF',role='RB',injury='Out'),dict(id='2',name='Bench',position='RB',team='NYJ',role='Bench',injury=None)]
  self.team=dict(roster_id='1',members=[{'id':'u'}],players=self.players,starters=['1'],slots=['RB'],name='Mine')
  self.league=dict(id='l',name='Jacked Pine',desk_rosters_at=self.now.isoformat(),tracking={'teams':[self.team,dict(roster_id='2',name='Rival',members=[{'id':'r'}],players=[])]})
  self.c=dict(user='test',user_id='u',season=2026,nfl_week=4,leagues=[self.league])
  self.games=[dict(week=4,teams=['BUF','NYJ'],kickoff=(self.now+timedelta(minutes=30)).isoformat())]
 def test_bench_and_lock(self):
  x=d.checks(self.c,self.games,False,{},self.now);self.assertEqual(x[0]['replacement']['id'],'2')
  x=d.checks(self.c,self.games,False,{},self.now+timedelta(hours=1));self.assertTrue(x[0]['locked']);self.assertIsNone(x[0]['replacement'])
 def test_reserve_and_injured_not_recommended(self):
  self.players[1]['role']='Reserve';self.assertIsNone(d.checks(self.c,self.games,False,{},self.now)[0]['replacement'])
  self.players[1]['role']='Bench';self.players[1]['injury']='Doubtful';self.assertIsNone(d.checks(self.c,self.games,False,{},self.now)[0]['replacement'])
 def test_flex_not_double_counted(self):
  self.assertEqual(len(d.cover([self.players[1]],['RB','FLEX'])),1)
 def test_stale_status_does_not_consume_transition(self):
  state=dict(context=self.c,games=self.games,starter_baseline={'l:1':'Questionable'},players_at=(self.now-timedelta(hours=1)).isoformat())
  self.assertEqual(d.derive(state,self.now),[]);self.assertEqual(state['starter_baseline']['l:1'],'Questionable')
  state['players_at']=self.now.isoformat();self.assertEqual(len(d.derive(state,self.now)),1);self.assertEqual(d.derive(state,self.now),[])
 def test_offer_and_history(self):
  state={};raw=dict(league_id='l',partner='2',direction='sent',outcome='sent',give=['1'],receive=[],receive_other='2027 first')
  x=d.save_offer(None,state,raw,self.c);self.assertEqual(len(state['offers']),1)
  raw.update(id=x['id'],outcome='rejected');x=d.save_offer(None,state,raw,self.c);self.assertEqual(len(x['history']),2);self.assertEqual(x['history'][0]['offer']['outcome'],'sent')
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'journal.json';d.atomic(p,state);self.assertEqual(d.read(p,{})['offers'][0]['outcome'],'rejected');p.write_text('invalid')
   with self.assertRaises(ValueError):d.read(p,{})
 def test_no_fake_byes(self):
  self.assertFalse(d.schedule_complete(self.games));self.assertIsNone(d.unavailable(self.players[1],[],4,False))
 def test_prelock_deduplicates(self):
  from unittest.mock import patch
  state=dict(context=self.c,games=self.games,schedule_season=2026,players_at=self.now.isoformat())
  with patch.object(d,'schedule_complete',return_value=True):
   alerts=d.derive(state,self.now);self.assertEqual(len(alerts),1);self.assertEqual(alerts[0]['kind'],'Pre-lock check');self.assertEqual(d.derive(state,self.now),[])
 def test_export_and_equal_snapshot_preserve_live_data(self):
  import subprocess
  with tempfile.TemporaryDirectory() as folder:
   c=copy.deepcopy(self.c);c['fetched_at']=self.now.isoformat()
   payload=dict(context=c,op='offer',offer=dict(league_id='l',partner='2',direction='sent',outcome='sent',give=['1'],receive=[],receive_other='2027 first'))
   def run(payload):
    result=subprocess.run([sys.executable,str(Path(d.__file__)),folder],input=json.dumps(payload),text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stdout);return json.loads(result.stdout)
   x=run(payload);path=Path(x['export_path']);self.assertTrue(path.exists());export=json.loads(path.read_text());self.assertEqual(len(export['offers']),1);self.assertIsNone(export['model']['acceptance_odds'])
   statepath=path.with_name('desk.json');state=json.loads(statepath.read_text());state['context']['leagues'][0]['desk_rosters_at']=(self.now+timedelta(seconds=1)).isoformat();d.atomic(statepath,state)
   y=run(dict(context=c,op='load'));self.assertEqual(y['state']['context']['leagues'][0]['desk_rosters_at'],(self.now+timedelta(seconds=1)).isoformat())
if __name__=='__main__':unittest.main()
