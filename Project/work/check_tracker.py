import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs/Binocular.app/Contents/Resources').resolve()))
from league_tracker import collect_team,normalize_transaction,observe,track_league
lg={'league_id':'L','roster_positions':['QB','RB','BN']};users={'u':{'display_name':'Same'},'v':{'display_name':'Same'},'c':{'display_name':'Co'}};P={'1':{'full_name':'One','position':'QB'},'2':{'full_name':'Two','position':'RB'},'3':{'full_name':'Three','position':'RB'}}
a={'roster_id':1,'owner_id':'u','co_owners':['c'],'players':['1','2','3'],'starters':['1','2'],'reserve':['3'],'settings':{}}
b={'roster_id':2,'owner_id':'v','players':[],'starters':[],'settings':{}}
teams=[collect_team(lg,r,users,P) for r in [a,b]]
assert teams[0]['players'][2]['role']=='Reserve'
assert teams[0]['members'][1]['id']=='c'
t={'transaction_id':'big-id','type':'trade','status':'complete','adds':{'3':2},'drops':{'3':1},'roster_ids':[1,2],'created':123,'draft_picks':[{'season':2027,'round':1,'roster_id':1,'previous_owner_id':1,'owner_id':2}],'waiver_budget':[{'sender':1,'receiver':2,'amount':5}]}
failed=normalize_transaction(dict(t,status='failed',type='waiver'),teams,P,2);assert failed['changes'][0].startswith('Requested add')
e=normalize_transaction(t,teams,P,2);assert e['members']==['c','u','v'];assert len(e['changes'])==4
assert observe([],teams,'2026-09-16T15:00:00Z')==[]
changed=json.loads(json.dumps(teams));changed[0]['players'][1]['role']='Bench'
assert observe(teams,changed,'2026-09-16T15:00:00Z')[0]['changes']==['Two: RB → Bench']
changed[0]['owner_id']='v';assert observe(teams,changed,'x')==[]
with tempfile.TemporaryDirectory() as cache:
 get=lambda _: [t]
 first=track_league(lg,[a,b],users,P,get,2,'2026-09-16T15:00:00Z',cache,2026,'u')
 assert len(first['transactions'])==1 and not first['observations']
 a['starters']=['1','3'];a['reserve']=[]
 second=track_league(lg,[a,b],users,P,get,2,'2026-09-16T15:05:00Z',cache,2026,'u')
 assert len(second['transactions'])==1 and len(second['observations'])==1
 def fail(_):raise OSError('offline')
 third=track_league(lg,[a,b],users,P,fail,2,'2026-09-16T15:10:00Z',cache,2026,'u')
 assert len(third['warnings'])==2 and len(third['transactions'])==1 and len(third['observations'])==1
 separate=track_league(lg,[a,b],users,P,get,2,'2026-09-16T15:10:00Z',cache,2026,'v')
 assert separate['observations']==[]
print('PASS: distinct IDs, co-managers, reserve roles, pick/FAAB trades, first baseline, role changes, deduplication, persistent history, partial failures and account isolation')
