"""Public research inputs. xFP is observed opportunity, never a future projection."""
import csv,io,json,time,urllib.request
from pathlib import Path
URL_X='https://github.com/ffverse/ffopportunity/releases/download/latest-data/ep_weekly_{}.csv'
URL_IDS='https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv'
URL_GAMES='https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
MAP={'pass_yd':'pass_yards_gained_exp','pass_td':'pass_touchdown_exp','pass_int':'pass_interception_exp','pass_cmp':'pass_completions_exp','pass_2pt':'pass_two_point_conv_exp','rush_yd':'rush_yards_gained_exp','rush_td':'rush_touchdown_exp','rush_2pt':'rush_two_point_conv_exp','rec':'receptions_exp','rec_yd':'rec_yards_gained_exp','rec_td':'rec_touchdown_exp','rec_2pt':'rec_two_point_conv_exp'}
def load(root,season,week):
 root=Path(root);p=root/'research-inputs.json';old={}
 try:old=json.loads(p.read_text())
 except (OSError,ValueError):pass
 if old.get('season')==season and old.get('week')==week and time.time()-old.get('fetched',0)<21600:return old
 def csvrows(url):
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Clipboard personal research inputs'}),timeout=15) as f:return list(csv.DictReader(io.StringIO(f.read().decode())))
 out={'season':season,'week':week,'fetched':time.time(),'xfp':{},'games':{},'warnings':[]}
 try:
  ids={r['gsis_id']:r['sleeper_id'] for r in csvrows(URL_IDS) if r.get('sleeper_id') not in [None,'','NA']}
  for r in csvrows(URL_X.format(season)):
   w=int(r['week']);pid=ids.get(r.get('player_id'))
   if not pid or not 1<=w<week:continue
   row={'week':w}
   for k,col in MAP.items():
    try:row[k]=float(r.get(col) or 0)
    except ValueError:row[k]=0
   out['xfp'].setdefault(pid,[]).append(row)
  for pid,rs in out['xfp'].items():out['xfp'][pid]=sorted(rs,key=lambda x:x['week'])[-3:]
 except Exception as e:out['warnings'].append('xFP unavailable: '+str(e))
 try:
  norm=lambda t:{'LA':'LAR','OAK':'LV','SD':'LAC'}.get(t,t)
  for r in csvrows(URL_GAMES):
   if r['season']!=str(season) or r['game_type']!='REG':continue
   w=r['week'];h,a=norm(r['home_team']),norm(r['away_team']);out['games'].setdefault(w,{})
   for team,opp in [(h,a),(a,h)]:out['games'][w][team]={'opponent':opp,'game_id':r['game_id']}
 except Exception as e:out['warnings'].append('Opponent schedule unavailable; using independent opponents: '+str(e))
 # Retain old same-season data with its original timestamp only, never label it fresh.
 if out['warnings'] and old.get('season')==season:
  for k in ['xfp','games']:
   if not out[k] and old.get(k):out[k]=old[k];out['warnings'].append(k+' is cached from '+time.strftime('%Y-%m-%d',time.gmtime(old['fetched'])))
 tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(out));tmp.replace(p);return out
