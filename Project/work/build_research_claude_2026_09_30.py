"""Add Claude's trade model, market values and scouting results to the Week 4 research feed."""
import json
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
r=json.load(open('research-2026-09-30.json'));s=json.load(open('daily-run/snapshot-edition.json'))
L={l['id']:l for l in s['context']['leagues']}
def team(lid,name):return next(t for t in L[lid]['tracking']['teams'] if t['name']==name or any(m.get('name')==name for m in (t.get('members') or [])))
def pid(lid,name,owner=None):
  teams=L[lid]['tracking']['teams'] if owner is None else [team(lid,owner)]
  for t in teams:
    for p in t['players']:
      if p['name']==name:return p['id']
  raise SystemExit(f'not found {name} in {lid}')
now=datetime.now(timezone.utc)
r['updated_at']=now.isoformat();r['valid_until']=(now+timedelta(hours=24)).isoformat()
r['reviewed_at']=now.astimezone(ZoneInfo('America/Detroit')).date().isoformat()
r['scope']+=' Claude model layer added Sep 30 evening: 100,000-season player-level simulations (title, #1 seed, playoff odds), a trade-acceptance model trained on 50 completed trades in these managers\' Sleeper leagues plus FantasyCalc market values and the weekly trade-value chart, and a scan of every Jacked Pine team\'s best trades. Acceptance figures are rough estimates from 7 known outcomes.'
r['sources']['claude_model']={"title":"Claude trade and title-odds model (Jacked Pine Scouting)","url":"https://claude.ai/artifact/FRnJSjPSjGcV72W2WB8fqP","date":now.date().isoformat(),"kind":"Model output","finding":"100k-season player-level simulation with injury risk, history-blended projections, team correlation and real playoff brackets; acceptance model calibrated on Owen's 7 known offer outcomes (6 of 7 correct)."}
r['sources']['fantasycalc']={"title":"FantasyCalc redraft trade values (league-specific)","url":"https://api.fantasycalc.com/values/current?isDynasty=false&ppr=1","date":now.date().isoformat(),"kind":"Market trade values","finding":"Values derived from real trades: superflex 6-team for Jacked Pine, 1QB 10-team for Net Ball, 1QB 16-team for Munchies."}
r['sources']['value_chart']={"title":"Weekly trade-value chart (@fantasy.football.chip)","url":"https://www.tiktok.com/@fantasy.football.chip","date":"2026-09-30","kind":"Rankings opinion","finding":"1QB redraft trade values 0-99; blended at 30% with FantasyCalc in the 1QB leagues."}
SRC=['claude_model','fantasycalc','sleeper']
JP,NB,MSU='1403096266736422912','1385050179488460800','1360286127205912576'
def trade(lid,partner,give,recv,title,why,preason,risk,note,conf):
  t=team(lid,partner);mine=[next(p['id'] for p in L[lid]['roster'] if p['name']==n) for n in give]
  return {"title":title,"give":mine,"receive":[pid(lid,n,partner) for n in recv],"partner_roster_id":t['roster_id'],"why":why,"partner_reason":preason,"risk":risk,"value_note":note,"confidence":conf,"sources":SRC,"partner_roster_ids":sorted(p['id'] for p in t['players'])}
r['leagues'][JP]['trades']=[
 trade(JP,'realzavierR',['Brock Purdy','David Montgomery'],['Trevor Lawrence','Kyren Williams','DeVonta Smith'],
  'Send Zavier: Purdy + Montgomery for Lawrence + Kyren + D. Smith',
  'Best move available to any Jacked Pine team: title odds about 18.8% to 24.3%, #1 seed 28% to 37.5%. Adds a QB plus RB and WR depth for byes.',
  'Zavier gets the best QB in the deal (Purdy) and consolidates his RB surplus; the market sees it as close to even for him.',
  'You need one roster spot (3 for 2). johnlucamigaldi\'s best trade targets the same Lawrence and D. Smith, so send this first. Walk away if he asks for Jaxon Smith-Njigba or St. Brown.',
  'Claude model: acceptance about 78% (rough tier). Zavier\'s title odds drop from about 22% to 16%.','Recommended · send tonight'),
 trade(JP,'ChristopherW16',['Amon-Ra St. Brown','Jayden Daniels','Saquon Barkley'],['Zay Flowers','Christian Watson','Chuba Hubbard'],
  'Backup if Zavier declines: St. Brown + Daniels + Barkley for Flowers + Watson + Hubbard',
  'Title odds about 18.8% to 20.5% and lowers Chris, the favorite, from about 24% to 22%.',
  'Chris gets St. Brown, the best player in the deal, and a QB while Caleb Williams is out.',
  'Costs St. Brown. Flowers is Questionable (hamstring). Only send if the Zavier deal fails.',
  'Claude model: acceptance very high (rough tier).','Backup · do not send with Zavier offer open')]
r['leagues'][NB]['trades']=[
 trade(NB,'Jacoblandess',['Patrick Mahomes','Kyren Williams','Dalton Kincaid'],['Trevor Lawrence','Ashton Jeanty','Tetairoa McMillan'],
  'Offer sent: Mahomes + Kyren + Kincaid for Lawrence + Jeanty + McMillan',
  'Title odds about 26.4% to 32.9%. Jeanty fills RB2; Lawrence projects about even with Mahomes rest of season.',
  'Jacoblandess (0-3) gets Mahomes, the best player in the deal.',
  'Lose about 3 points at QB this week. Keep Nix for Lawrence\'s Week 7 bye. If declined, ask for a fresh scan; the Gianni backup is now unlikely.',
  'Claude model: acceptance about 66%. Pending as of Sep 30 evening.','Sent · pending')]
r['leagues'][MSU]['trades']=[
 trade(MSU,'JDMOONZ',['Caleb Williams','Jacory Croskey-Merritt'],['Christian McCaffrey'],
  'Offer sent: Caleb Williams + Croskey-Merritt for McCaffrey',
  'Playoff odds about 27% to 35%, title 3.5% to 6%.',
  'JDMOONZ would add a starting QB when healthy and RB depth.',
  'Very unlikely: McCaffrey\'s market value far exceeds the package. Do not sweeten; every acceptable version lowers your odds.',
  'Claude model: acceptance about 0-2%. Leave it open; a decline costs nothing.','Sent · long shot')]
notes={JP:('Claude title odds and rival scan','100k simulations: Chris 24.0%, Zavier 22.1%, Nic 21.0%, you 18.8%, John 8.1%, Rob 6.0% (your playoffs 84%, #1 seed 28%). Each rival\'s best trade: Nic and Rob both target Chris (each lowers Chris about 3 points); John targets Zavier for Lawrence + J. Love + D. Smith; Chris and Zavier target John for Bowers/Walker. None of their moves changes your odds beyond noise except John beating you to Zavier.'),
 NB:('Claude title odds','100k simulations: you are the title favorite at about 26% (Eric about 24%). The Jacoblandess offer is the best available move; Eric declined Kyren + Kincaid for Henry, as the model expected.'),
 MSU:('Claude title odds','100k simulations: playoffs about 27%, title about 3.5%. No acceptable trade improves the odds besides the CMC long shot; waivers and streaming (DEF Week 6, K Week 13, RB depth before Week 7) matter more.')}
for lid,(t,b) in notes.items():r['leagues'][lid].setdefault('lineup_notes',[]).insert(0,{"title":t,"body":b,"sources":SRC})
r['changes']=['Added Claude model layer: 100k-season title odds, acceptance model with FantasyCalc and trade-value chart, and rival trade scan.','Jacked Pine: recommend Zavier offer (Purdy + Montgomery for Lawrence + Kyren + D. Smith); Chris backup.','Net Ball: Jacoblandess offer pending; Eric declined Henry offer.','Munchies: CMC offer pending, long shot.']+r['changes']
json.dump(r,open('research-2026-09-30-claude.json','w'),indent=1,ensure_ascii=False)
print('draft written')
