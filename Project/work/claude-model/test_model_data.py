import json,tempfile,model_data as m
from pathlib import Path
L='L1'
def fake(self,url,ttl,trim=None):
    if url.endswith('/state/nfl'):v={'season':'2026','week':4}
    elif url.endswith('/players/nfl'):v={'1':{'full_name':'A QB','position':'QB','team':'SF','injury_status':None,'age':26},'2':{'full_name':'B RB','position':'RB','team':'DET'},'3':{'full_name':'C WR','position':'WR','team':'SEA'},'4':{'full_name':'D WR','position':'WR','team':'KC'}}
    elif 'projections' in url:v=[{'player_id':p,'stats':{'pts_ppr':10+int(p),'pass_td':1 if p=='1' else 0}} for p in '1234']
    elif '/stats/nfl/regular/2026/' in url:v={p:{'pts_ppr':12,'pass_td':0,'gp':1} for p in '1234'}
    elif '/stats/nfl/regular/' in url:v={p:{'pts_ppr':200,'gp':16,'pass_td':0} for p in '1234'}
    elif url.endswith(f'/league/{L}'):v={'name':'Jacked Pine','settings':{'playoff_week_start':16,'playoff_teams':4,'playoff_seed_type':1},'roster_positions':['QB','RB','WR','FLEX','BN'],'scoring_settings':{'pass_td':6},'total_rosters':2}
    elif url.endswith('/rosters'):v=[{'roster_id':1,'owner_id':'me','players':['1','2'],'settings':{'wins':3,'losses':0,'fpts':300}},{'roster_id':2,'owner_id':'u2','players':['3','4'],'settings':{'wins':1,'losses':2,'fpts':250}}]
    elif url.endswith('/users'):v=[{'user_id':'me','display_name':'coffero'},{'user_id':'u2','display_name':'rival'}]
    elif '/matchups/' in url:v=[{'roster_id':1,'matchup_id':1},{'roster_id':2,'matchup_id':1}]
    elif '/user/' in url:v=[{'league_id':L}]
    elif '/transactions/' in url:v=[{'type':'trade','status':'complete','roster_ids':[1,2],'transaction_id':'t9','leg':3,'adds':{'3':1,'2':2},'drops':{'2':1,'3':2}}] if url.endswith('/3') else []
    else:raise Exception('unexpected '+url)
    return trim(v) if trim else v
m.Feed.get=fake
d=tempfile.mkdtemp();out=m.build(d,{'leagues':[{'id':L}],'user_id':'me','season':'2026'})
lg=out['leagues'][L];print(lg['me'],lg['repl'],lg['pv'],len(lg['sched']),out['accepted'][-2:],list(out['proj']['1'])[:2],out['s26']['1'],out['hist']['1'])
import json;print(json.dumps(out['scouts'])[:900])
