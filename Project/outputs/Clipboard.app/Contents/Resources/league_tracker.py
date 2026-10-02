"""Public Sleeper activity and roster observations; never writes to Sleeper."""
import json, os
from pathlib import Path

def collect_team(lg, roster, users, players):
    members=[]
    for uid in dict.fromkeys([roster.get('owner_id')]+(roster.get('co_owners') or [])):
        if uid:
            u=users.get(uid,{})
            members.append({'id':uid,'name':u.get('display_name') or u.get('username') or uid})
    u=users.get(roster.get('owner_id'),{})
    team=(u.get('metadata') or {}).get('team_name') or u.get('display_name') or 'Team '+str(roster['roster_id'])
    starters=roster.get('starters') or [];reserve=roster.get('reserve') or [];taxi=roster.get('taxi') or []
    slots=[s for s in lg.get('roster_positions',[]) if s not in ['BN','IR','TAXI']]
    rows=[]
    for pid in dict.fromkeys((roster.get('players') or [])+reserve+taxi+starters):
        if not pid or pid=='0':continue
        p=players.get(pid,{})
        slot=slots[starters.index(pid)] if pid in starters and starters.index(pid)<len(slots) else None
        rows.append({'id':pid,'name':p.get('full_name') or pid,'position':p.get('position') or ('DEF' if pid.isalpha() else '?'),'team':p.get('team'),'injury':p.get('injury_status'),'role':'Reserve' if pid in reserve else 'Taxi' if pid in taxi else slot or 'Bench'})
    s=roster.get('settings') or {}
    return {'roster_id':str(roster['roster_id']),'name':team,'members':members,'owner_id':roster.get('owner_id'),'players':rows,'starters':starters,'slots':slots,'record':str(s.get('wins',0))+'-'+str(s.get('losses',0))+'-'+str(s.get('ties',0))}

def normalize_transaction(t, teams, P, week):
    byid={x['roster_id']:x for x in teams};involved=set(str(x) for x in (t.get('roster_ids') or []));changes=[]
    def team(rid):return byid.get(str(rid),{}).get('name','Team '+str(rid))
    labels = [('adds','Received'),('drops','Sent')] if t.get('type') == 'trade' else [('adds','Added'),('drops','Dropped')]
    if t.get('status') != 'complete': labels = [('adds','Requested add'),('drops','Requested drop')]
    for key,label in labels:
        for pid,rid in (t.get(key) or {}).items():
            involved.add(str(rid));changes.append(label+' '+(P.get(pid,{}).get('full_name') or pid)+' · '+team(rid))
    for p in t.get('draft_picks') or []:
        involved.update([str(p.get('previous_owner_id')),str(p.get('owner_id'))]);changes.append(str(p.get('season'))+' round '+str(p.get('round'))+' pick ('+team(p.get('roster_id'))+' original) · '+team(p.get('previous_owner_id'))+' → '+team(p.get('owner_id')))
    for b in t.get('waiver_budget') or []:
        involved.update([str(b.get('sender')),str(b.get('receiver'))]);changes.append('FAAB '+str(b.get('amount'))+' · '+team(b.get('sender'))+' → '+team(b.get('receiver')))
    bid=(t.get('settings') or {}).get('waiver_bid')
    if bid is not None:changes.append('Reported waiver bid: '+str(bid))
    members=sorted({m['id'] for rid in involved for m in byid.get(rid,{}).get('members',[])})
    return {'id':str(t.get('transaction_id')),'type':t.get('type','unknown'),'status':t.get('status','unknown'),'time':t.get('status_updated') or t.get('created') or 0,'week':t.get('leg',week),'members':members,'teams':[team(rid) for rid in sorted(involved)],'changes':changes,'source':'Sleeper transaction'}

def observe(previous,current,at):
    events=[];old={t['roster_id']:t for t in previous}
    for team in current:
        before=old.get(team['roster_id'])
        if not before or before.get('owner_id')!=team.get('owner_id'):continue
        a={p['id']:p for p in before['players']};b={p['id']:p for p in team['players']};changes=[]
        for pid in sorted(set(a)|set(b)):
            if pid not in a:changes.append('Roster addition: '+b[pid]['name'])
            elif pid not in b:changes.append('Roster removal: '+a[pid]['name'])
            elif a[pid]['role']!=b[pid]['role']:changes.append(b[pid]['name']+': '+a[pid]['role']+' → '+b[pid]['role'])
        if changes:events.append({'id':'observed:'+team['roster_id']+':'+at,'type':'observed','status':'observed','time':at,'members':[m['id'] for m in team['members']],'teams':[team['name']],'changes':changes,'source':'Snapshot comparison'})
    return events

def track_league(lg,rosters,users,P,get,week,at,cache,season,uid):
    teams=[collect_team(lg,r,users,P) for r in rosters]
    path=Path(cache)/('tracking-'+str(uid)+'-'+str(season)+'-'+str(lg['league_id'])+'.json')
    warnings=[]
    try:old=json.loads(path.read_text()) if path.exists() else {}
    except (OSError,ValueError):old={};warnings.append('Saved tracking history could not be read; a new baseline was created.')
    observations=(observe(old.get('teams',[]),teams,at)+old.get('observations',[]))[:300]
    tx={e['id']:e for e in old.get('transactions',[])}
    weeks=list(range(max(0,week-1),week+1));fetched=[]
    for w in weeks:
        try:
            data=get('/league/'+lg['league_id']+'/transactions/'+str(w))
            if not isinstance(data,list):raise ValueError('Unexpected transaction response')
            for t in data:
                if t.get('transaction_id'):tx[str(t['transaction_id'])]=normalize_transaction(t,teams,P,w)
            fetched.append(w)
        except Exception:
            warnings.append('Week '+str(w)+' transactions unavailable; retained prior history where available.')
    transactions=sorted(tx.values(),key=lambda t:t['time'],reverse=True)[:500]
    result={'teams':teams,'transactions':transactions,'observations':observations,'started_at':old.get('started_at',at),'observed_at':at,'weeks_requested':weeks,'weeks_fetched':fetched,'warnings':warnings}
    try:
        path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(result));os.replace(temp,path)
    except OSError:result['warnings'].append('Tracking history could not be saved; this refresh is still visible.')
    return result
