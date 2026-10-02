"""Prospective evidence capture; never infers private rejections from public inactivity."""
from datetime import datetime,timezone

def capture(state):
 now=datetime.now(timezone.utc).isoformat()
 for o in state.get('offers',[]):
  if o.get('learning_snapshot') or o.get('outcome') not in ['sent','received']:continue
  market=state.get('markets',{}).get(o['league_id'],{});values=market.get('players',{})
  give=o.get('give',[]);receive=o.get('receive',[])
  l=next((x for x in state.get('context',{}).get('leagues',[]) if x['id']==o['league_id']),{})
  team=next((x for x in l.get('tracking',{}).get('teams',[]) if x['roster_id']==o['partner']),{})
  users={x['id'] for x in team.get('members',[])};tx=[x for x in l.get('tracking',{}).get('transactions',[]) if users.intersection(x.get('members',[])) and x.get('status')=='complete']
  complete=bool(give and receive and not o.get('give_other') and not o.get('receive_other') and all(x in values for x in give+receive))
  o['learning_snapshot']={'captured_at':now,'outcome_at_capture':o['outcome'],'give':list(give),'receive':list(receive),'market_at':market.get('at'),'market_values':{p:values[p]['value'] for p in give+receive if p in values},'complete_assets':complete,'partner_roster_id':o['partner'],'observed_completed_trades':sum(x.get('type')=='trade' for x in tx),'observed_completed_moves':len(tx),'activity_note':'Counts cover retained history, not all offers or responses.'}

def summary(offers):
 eligible=[];excluded=0
 for o in offers:
  if o.get('direction')!='sent' or o.get('outcome') not in ['accepted','rejected']:continue
  s=o.get('learning_snapshot',{});valid=s.get('complete_assets') and s.get('outcome_at_capture')=='sent' and s.get('give')==o.get('give') and s.get('receive')==o.get('receive')
  try:
   ct=datetime.fromisoformat(s['captured_at']);mt=datetime.fromisoformat(s['market_at']);ut=datetime.fromisoformat(o['updated_at']);valid=valid and 0<=(ct-mt).total_seconds()<=86400 and ut>ct
  except (KeyError,TypeError,ValueError):valid=False
  if valid:eligible.append(o)
  else:excluded+=1
 return {'eligible':len(eligible),'accepted':sum(o['outcome']=='accepted' for o in eligible),'rejected':sum(o['outcome']=='rejected' for o in eligible),'excluded_completed':excluded,'status':'collecting evidence; no calibrated manager probability','note':'Silent, expired, countered and withdrawn offers are not rejection labels. Seeded historical outcomes are not prospective validation.'}
