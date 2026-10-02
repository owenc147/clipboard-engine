"""Personal Binocular desk. Public read-only feeds; private journal stays on disk."""
import csv, io, json, math, os, sys, uuid, copy, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from collections import Counter
VERSION=1
FC='https://api.fantasycalc.com/values/current'
SCHEDULE='https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
STATUSES={'draft','sent','received','accepted','rejected','countered','withdrawn','expired'}
FLEX={'FLEX':{'RB','WR','TE'},'SUPER_FLEX':{'QB','RB','WR','TE'},'REC_FLEX':{'WR','TE'},'WRRB_FLEX':{'RB','WR'}}
def utc(): return datetime.now(timezone.utc)
def stamp(): return utc().isoformat()
def dt(v): return datetime.fromisoformat(v.replace('Z','+00:00'))
def read(p, default):
 if not p.exists():return default
 return json.loads(p.read_text()) # Corrupt journal must never silently reset.
def atomic(p, value):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False));os.replace(tmp,p)
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Binocular personal Mac desk/1.0'})
 with urllib.request.urlopen(req,timeout=20) as f:return f.read()
def get(url):return json.loads(fetch(url))
def mine(c,l):return next((t for t in l.get('tracking',{}).get('teams',[]) if any(m['id']==c.get('user_id') for m in t['members'])),None)
def eligible(p,slot):return bool(set(p.get('positions') or [p.get('position')]) & FLEX.get(slot,{slot}))
def game_for(p,games,week):return next((g for g in games if g['week']==week and p.get('team') in g['teams']),None)
def schedule_complete(games):
 counts=Counter(t for g in games for t in g['teams']);return len(games)==272 and len(counts)==32 and all(n==17 for n in counts.values())
def unavailable(p,games,week,complete):
 if str(p.get('injury') or '').lower() in {'out','doubtful','ir','pup','sus'}:return p['injury']
 if complete and p.get('team') in {t for g in games for t in g['teams']} and not game_for(p,games,week):return 'Bye'
 return None

def cover(players,slots):
 """Maximum bipartite matching prevents counting a flex player twice."""
 assigned={}
 def match(i,seen):
  for p in players:
   pid=p['id']
   if pid in seen or not eligible(p,slots[i]):continue
   seen.add(pid)
   if pid not in assigned or match(assigned[pid],seen):assigned[pid]=i;return True
  return False
 for i in sorted(range(len(slots)),key=lambda i:len(FLEX.get(slots[i],{slots[i]}))):match(i,set())
 return [slots[i] for i in range(len(slots)) if i not in assigned.values()]

def checks(c,games,complete,values,now=None):
 now=now or utc();week=int(c.get('nfl_week') or c.get('week') or 1);out=[]
 for l in c.get('leagues',[]):
  t=mine(c,l)
  if not t:continue
  ps={p['id']:p for p in t['players']};used=set(t['starters'])
  problems=[]
  for slot,pid in zip(t['slots'],t['starters']):
   p=ps.get(pid);reason=unavailable(p,games,week,complete) if p else 'Empty'
   if reason:problems.append((slot,pid,p,reason))
  # Allocate the most constrained positions first; never recommend one bench player twice.
  problems.sort(key=lambda x:len(FLEX.get(x[0],{x[0]})))
  for slot,pid,p,reason in problems:
   game=game_for(p,games,week) if p else None
   locked=bool(game and dt(game['kickoff'])<=now)
   candidates=[x for x in t['players'] if x['id'] not in used and x['role']=='Bench' and eligible(x,slot) and not unavailable(x,games,week,complete) and game_for(x,games,week) and dt(game_for(x,games,week)['kickoff'])>now]
   # Prefer clear status, then market value; this is not a weekly projection.
   candidates.sort(key=lambda x:(bool(x.get('injury')),-(values.get(l['id'],{}).get('players',{}).get(x['id'],{}).get('value') or 0),x['name']))
   replacement=None if locked else next(iter(candidates),None)
   if replacement:used.add(replacement['id'])
   out.append(dict(league_id=l['id'],league=l['name'],id=pid,name=p['name'] if p else 'Empty slot',slot=slot,reason=reason,locked=locked,kickoff=game['kickoff'] if game else None,replacement=replacement,explanation='Position-eligible bench cover, ordered by status then market value; verify final active list. Not a weekly projection.'))
 return out

def refresh(root,state,c):
 warnings=[];now=utc()
 try:
  Ppath=root/'players-cache.json';cached=read(Ppath,{})
  if not cached or (now-dt(cached['at'])).total_seconds()>300:
   P=get('https://api.sleeper.app/v1/players/nfl');assert isinstance(P,dict) and len(P)>1000
   cached={'at':stamp(),'players':P};atomic(Ppath,cached)
  P=cached['players'];state['players_at']=cached['at']
  for l in c.get('leagues',[]):
   try:
    meta=get('https://api.sleeper.app/v1/league/'+l['id']);assert isinstance(meta,dict) and isinstance(meta.get('settings'),dict)
    l['settings']=meta['settings'];l['slots']=meta['roster_positions'];l['scoring']=meta['scoring_settings']
    rosters=get('https://api.sleeper.app/v1/league/'+l['id']+'/rosters');assert isinstance(rosters,list)
    byid={str(x['roster_id']):x for x in rosters};before=copy.deepcopy(l.get('tracking',{}).get('teams',[]))
    for t in l.get('tracking',{}).get('teams',[]):
     r=byid.get(t['roster_id']);
     if not r:continue
     t['slots']=[x for x in l['slots'] if x not in ['BN','IR','TAXI']]
     starters=r.get('starters') or [];reserve=r.get('reserve') or [];taxi=r.get('taxi') or []
     t['starters']=starters;t['players']=[]
     for pid in dict.fromkeys((r.get('players') or [])+reserve+taxi+starters):
      if pid=='0' or not pid:continue
      p=P.get(pid,{});slot=t['slots'][starters.index(pid)] if pid in starters and starters.index(pid)<len(t['slots']) else 'Bench'
      t['players'].append(dict(id=pid,name=p.get('full_name') or pid,position=p.get('position') or 'DEF',positions=p.get('fantasy_positions') or [p.get('position') or 'DEF'],team={'LA':'LAR'}.get(p.get('team') or pid,p.get('team') or (pid if pid.isalpha() else None)),injury=p.get('injury_status'),role='Reserve' if pid in reserve else 'Taxi' if pid in taxi else slot))
    # Keep existing history, refresh current-week moves without inventing private offers.
    from league_tracker import normalize_transaction, observe
    l['tracking']['observations']=(observe(before,l['tracking']['teams'],stamp())+l['tracking'].get('observations',[]))[:300]
    old={e['id']:e for e in l['tracking'].get('transactions',[])}
    for w in {int(c['nfl_week']),max(1,int(c['nfl_week'])-1)}:
     for tx in get('https://api.sleeper.app/v1/league/'+l['id']+'/transactions/'+str(w)):
      e=normalize_transaction(tx,l['tracking']['teams'],P,w);old[e['id']]=e
    l['tracking']['transactions']=sorted(old.values(),key=lambda e:e['time'],reverse=True)[:500]
    l['desk_rosters_at']=stamp()
   except Exception as e:warnings.append(l['name']+': roster/activity refresh incomplete: '+str(e))
  state['context']=c
 except Exception as e:warnings.append('Player status refresh failed; showing saved data: '+str(e))
 try:
  season=int(c['season'])
  if state.get('schedule_season')!=season or not state.get('schedule_at') or (now-dt(state['schedule_at'])).total_seconds()>43200:
   rows=csv.DictReader(io.StringIO(fetch(SCHEDULE).decode()));games=[]
   for row in rows:
    if row['season']!=str(season) or row['game_type']!='REG':continue
    when=datetime.fromisoformat(row['gameday']+'T'+row['gametime']).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)
    games.append(dict(id=row['game_id'],week=int(row['week']),teams=[{'LA':'LAR'}.get(row[k],row[k]) for k in ['away_team','home_team']],kickoff=when.isoformat()))
   assert schedule_complete(games),'Season schedule incomplete; no inferred byes'
   state.update(games=games,schedule_at=stamp(),schedule_season=season)
 except Exception as e:warnings.append('Schedule refresh failed: '+str(e))
 markets=state.setdefault('markets',{})
 for l in c.get('leagues',[]):
  try:
   teams=len(l.get('tracking',{}).get('teams',[]));qbs=2 if 'SUPER_FLEX' in l['slots'] or l['slots'].count('QB')>1 else 1;ppr=l['scoring'].get('rec',0)
   assert l.get('settings',{}).get('type') in (0,1,2),'League format unverified'
   dynasty=bool(l['settings']['type']==2)
   fmt=dict(isDynasty=dynasty,numQbs=qbs,numTeams=teams,ppr=ppr)
   old=markets.get(l['id'],{})
   if old.get('format')==fmt and old.get('at') and (now-dt(old['at'])).total_seconds()<21600:continue
   url=FC+'?'+urllib.parse.urlencode({**fmt,'isDynasty':str(dynasty).lower()})
   data=get(url);assert isinstance(data,list) and len(data)>50
   values={}
   for x in data:
    p=x.get('player',{});pid=p.get('sleeperId');v=x.get('value');trend=x.get('trend30Day')
    if pid and isinstance(v,(int,float)) and math.isfinite(v):values[str(pid)]=dict(name=p['name'],position=p.get('position'),team=p.get('maybeTeam'),value=v,trend30=trend if isinstance(trend,(int,float)) and math.isfinite(trend) else None)
   assert values;markets[l['id']]=dict(at=stamp(),format=fmt,players=values,url=url,limits='FantasyCalc market values; do not model custom scoring bonuses, title odds or acceptance. Format from Sleeper. Keeper leagues use redraft values; picks and keeper costs require separate analysis.')
  except Exception as e:warnings.append(l['name']+': values unavailable; retained any saved values: '+str(e))
 try:
  state['trending']=get('https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=30');state['trending_at']=stamp()
  for item in state['trending']:item['name']=locals().get('P',{}).get(item['player_id'],{}).get('full_name') or item['player_id']
 except Exception as e:warnings.append('Trending adds unavailable: '+str(e))
 state['warnings']=warnings;state['checked_at']=stamp();return state

def validate_offer(raw,c):
 l=next((x for x in c['leagues'] if x['id']==raw.get('league_id')),None);assert l,'Choose a league'
 t=mine(c,l);partner=next((x for x in l['tracking']['teams'] if x['roster_id']==raw.get('partner')),None);assert partner and partner!=t,'Choose another manager'
 assert raw.get('direction') in {'sent','received'},'Choose sent or received'
 assert raw.get('outcome') in STATUSES,'Invalid outcome'
 for side,team in [('give',t),('receive',partner)]:
  ids=raw.get(side,[]);assert isinstance(ids,list) and len(ids)==len(set(ids)) and all(isinstance(x,str) for x in ids),'Invalid assets'
  # Past offers may include players no longer owned: saved names remain historical evidence.
  assert len(ids)<=30,'Too many assets'
 assert raw.get('give') or raw.get('give_other','').strip(),'Enter what you give'
 assert raw.get('receive') or raw.get('receive_other','').strip(),'Enter what you receive'
 for field in ['notes','give_other','receive_other','offered_at']:
  assert isinstance(raw.get(field,''),str) and len(raw.get(field,''))<=4000,'Text too long'
 if raw.get('offered_at'):dt(raw['offered_at'])
 return l,t,partner

def save_offer(root,state,raw,c):
 l,t,p=validate_offer(raw,c);items=state.setdefault('offers',[]);old=next((x for x in items if x['id']==raw.get('id')),None)
 assert not raw.get('id') or old,'Offer not found'
 names={x['id']:x['name'] for team in l['tracking']['teams'] for x in team['players']}
 item={k:raw.get(k,[] if k in ['give','receive'] else '') for k in ['league_id','partner','direction','outcome','give','receive','give_other','receive_other','notes','offered_at']}
 item.update(id=old['id'] if old else str(uuid.uuid4()),created_at=old['created_at'] if old else stamp(),updated_at=stamp(),league=l['name'],partner_name=p['name'],names={**(old or {}).get('names',{}),**names},history=(old or {}).get('history',[])+[dict(at=stamp(),offer=dict(item))],market_at_creation=(old or {}).get('market_at_creation') or state.get('markets',{}).get(l['id'],{}))
 if old:items[items.index(old)]=item
 else:items.insert(0,item)
 return item

def derive(state,now=None):
 now=now or utc();c=state['context'];games=state.get('games',[]);complete=schedule_complete(games) and state.get('schedule_season')==int(c['season']);markets=state.get('markets',{})
 state['checks']=checks(c,games,complete,markets,now);state['schedule_complete']=complete
 grid={};new=[];prior=state.get('starter_baseline',{});baseline=dict(prior);alerts=state.setdefault('alerts',[]);known={a['key'] for a in alerts}
 for l in c['leagues']:
  t=mine(c,l)
  if not t:continue
  ps={p['id']:p for p in t['players']};grid[l['id']]=[]
  for w in range(1,19):
   active=[p for p in t['players'] if p['role'] not in ['Reserve','Taxi'] and (game_for(p,games,w) or not complete)]
   grid[l['id']].append(dict(week=w,bye=[p['id'] for p in t['players'] if complete and p.get('team') in {t for g in games for t in g['teams']} and not game_for(p,games,w)],missing=cover(active,t['slots']) if complete else None))
  fresh=l.get('desk_rosters_at') and state.get('players_at') and (now-dt(l['desk_rosters_at'])).total_seconds()<900 and (now-dt(state['players_at'])).total_seconds()<900
  for slot,pid in zip(t['slots'],t['starters']):
   if pid not in ps:continue
   p=ps[pid];key=l['id']+':'+pid;status=p.get('injury') or 'No injury designation'
   if fresh:baseline[key]=status
   if fresh and key in prior and prior[key]!=status:
    issue=next((x for x in state['checks'] if x['league_id']==l['id'] and x['id']==pid),{})
    repl=issue.get('replacement')
    if not repl and status.lower() in ['questionable','doubtful','out']:
     trial=copy.deepcopy(c)
     for tl in trial['leagues']:
      if tl['id']==l['id']:
       for player in mine(trial,tl)['players']:
        if player['id']==pid:player['injury']='Out'
     repl=next((x.get('replacement') for x in checks(trial,games,complete,markets,now) if x['league_id']==l['id'] and x['id']==pid),None)
    msg=p['name']+': '+prior[key]+' → '+status+('. Consider '+repl['name'] if repl else '. Review lineup before kickoff.')
    new.append(dict(key=key+':status:'+status+':'+state['players_at'],league=l['name'],message=msg,at=stamp(),kind='Status change'))
  if fresh and complete:
   soon=[g for g in games if g['week']==int(c['nfl_week']) and 0<(dt(g['kickoff'])-now).total_seconds()<=3600]
   for game in soon:
    issues=[x for x in state['checks'] if x['league_id']==l['id'] and (x['kickoff']==game['kickoff'] or x['reason'] in ['Bye','Empty']) and not x['locked']]
    for x in issues:
     repl=x['replacement'];new.append(dict(key=l['id']+':lock:'+game['kickoff']+':'+x['slot']+':'+x['id'],league=l['name'],message=x['name']+' · '+x['reason']+('. Consider '+repl['name'] if repl else '. No eligible unlocked bench cover found.'),kind='Pre-lock check',at=stamp()))
 # Failed refreshes must not consume status transitions.
 state['starter_baseline']=baseline
 new=[a for a in new if a['key'] not in known];state['alerts']=(new+alerts)[:1000];state['bye_grid']=grid
 return new

def main():
 root=Path(sys.argv[1]);payload=json.load(sys.stdin);c=payload['context'];user=c['user'].lower();assert user and all(x.isalnum() or x in '_-' for x in user)
 root=root/'profiles'/user/'desk';root.mkdir(parents=True,exist_ok=True);path=root/'desk.json';state=read(path,{'schema_version':VERSION,'offers':[],'alerts':[]})
 prev=state.get('context',{});state['context']=c if not prev or c.get('fetched_at','')>prev.get('fetched_at','') else prev;c=state['context'];op=payload.get('op','load');status=''
 if op=='refresh':
  # Refresh season/week too; do not silently monitor a historical selected week.
  nfl=get('https://api.sleeper.app/v1/state/nfl');assert str(nfl.get('season'))==str(c['season']),'Saved leagues belong to another season. Refresh league data first.'
  c['nfl_week']=nfl.get('week') or nfl.get('display_week') or 1
  state=refresh(root,state,c)
 elif op=='offer':save_offer(root,state,payload['offer'],c);status='Offer saved on this Mac.'
 elif op=='outcome':
  item=next(x for x in state['offers'] if x['id']==payload['id']);assert payload['outcome'] in STATUSES
  item['outcome']=payload['outcome'];item['updated_at']=stamp();item['history'].append(dict(at=stamp(),outcome=payload['outcome'])) ;status='Outcome recorded.'
 new=derive(state);atomic(path,state)
 export={**state,'exported_at':stamp(),'privacy':'Personal Mac data. Manual offers are not automatically verified by Sleeper. No credentials included.','model':{'status':'not_connected','title_odds':None,'acceptance_odds':None}}
 target=root/'binocular-export.json';atomic(target,export)
 print(json.dumps(dict(ok=True,state=state,new_alerts=new,status=status,export_path=str(target))))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'status':'Desk operation failed; existing saved data retained. '+str(e)}));sys.exit(1)
