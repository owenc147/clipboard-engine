import importlib.util,json,tempfile
from pathlib import Path
from unittest.mock import patch
p=Path('outputs/Binocular.app/Contents/Resources/sleeper_assistant.py')
spec=importlib.util.spec_from_file_location('brief',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.score({'points':99,'custom_points':0})==0
assert m.score({'points':99,'custom_points':None})==99
snapshot=json.loads(Path('work/research/snapshot.json').read_text());players=json.loads(Path('work/live/cache/players.json').read_text())
raw={l['id']:json.loads(Path('work/research',l['id']+'.json').read_text()) for l in snapshot['leagues']}
def get(path):
 _,_,lid,kind=path.split('/')
 return raw[lid][kind] if kind!='matchups' else []
with patch.object(m,'get',get):
 ctx=m.build_context([v['league'] for v in raw.values()],snapshot['user']['user_id'],'coffero',snapshot['state'],2,players)
jp=next(l for l in ctx['leagues'] if l['name']=='Jacked Pine');msu=next(l for l in ctx['leagues'] if l['name']=='MSU Munches v2')
assert next(p for p in jp['market'] if p['name']=='Brock Purdy')['owner'] is None
assert next(p for p in msu['market'] if p['name']=='Devaughn Vele')['owner']=='Bo Dix'
assert abs(msu['scoring']['pass_yd']-1/22.5)<1e-9 and msu['scoring']['pass_cmp']==.1
# A shortened starters array must still flag the missing second slot.
lg={'league_id':'fixture','name':'Fixture','roster_positions':['QB','RB'],'scoring_settings':{},'total_rosters':2}
rosters=[{'owner_id':'me','roster_id':1,'settings':{},'starters':['q'],'players':['q']},{'owner_id':'them','roster_id':2,'settings':{},'starters':['r'],'players':['r']}]
def fake(path):
 if path.endswith('/rosters'):return rosters
 if path.endswith('/users'):return []
 return [{'roster_id':1,'matchup_id':None,'points':0},{'roster_id':2,'matchup_id':None,'points':0}]
with patch.object(m,'get',fake):
 result=m.league_brief(lg,'me',2,[],{'q':{'position':'QB','full_name':'QB','team':'KC'},'r':{'position':'RB','full_name':'RB','team':'SF'}})
assert 'RB slot is EMPTY' in result
assert 'opponent:' not in result
assert '### Scoring details' in result
print('Passed: custom-score zero, ownership checks, custom scoring, missing starters and unmatched bye handling.')
