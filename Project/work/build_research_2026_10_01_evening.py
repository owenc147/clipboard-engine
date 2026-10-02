"""Assemble this researched edition; publishing remains a separate validated step."""
import copy
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
old = json.loads((BASE/'outputs/daily-edition.json').read_text())
r = copy.deepcopy(old['research'])
s = json.loads((BASE/'work/daily-run/snapshot.json').read_text())
c = s['context']
assert c['season'] == '2026' and c['nfl_week'] == 4
assert all(not l['tracking']['warnings'] for l in c['leagues'])
now = datetime.now(timezone.utc)
assert now.astimezone(ZoneInfo('America/Detroit')).date().isoformat() == '2026-10-01'
r.update(name='Clipboard', reviewed_at='2026-10-01', updated_at=now.isoformat(),
         valid_until=(now+timedelta(hours=24)).isoformat(), expires_after='2026-10-06',
         roster_reconciled_at=c['fetched_at'])
r['scope'] = ('October 1 evening Week 4 research: all three live leagues, full rosters, rules, reserves, '
 'matchups and completed Week 3/4 transactions reviewed. Thursday game is locked. Current chosen '
 'lineups remain the baseline. Official practice reports are not final Sunday clearance. '
 'Historical Claude estimates are preserved separately and were not rerun or validated; no claim '
 'is made that these alternatives beat the custom-scoring model. No roster actions performed.')
# Retain the prior model contributions without presenting them as new estimates.
r['historical_model_review'] = {
 'as_of':old['research']['updated_at'], 'status':'Historical only; not rerun or validated on October 1 evening',
 'leagues':{lid:{'trades':copy.deepcopy(l.get('trades',[])),
 'notes':[copy.deepcopy(n) for n in l.get('lineup_notes',[]) if 'Claude' in n['title']]}
 for lid,l in old['research']['leagues'].items()}}
src = r['sources']
def source(key,title,url,date,kind,finding):
 src[key] = dict(title=title,url=url,date=date,kind=kind,finding=finding)
source('sleeper','Fresh Sleeper league data','https://api.sleeper.app/v1/user/coffero',c['fetched_at'],
 'Live league data','All 32 fantasy teams reviewed across three leagues, including reserves, starters, rules, matchups and completed transactions. Pending offers are not exposed by this API.')
for key,title,finding in [
 ('was','Washington Thursday practice report','Daniels and Okonkwo remained limited; Rachaad White did not practice. Friday decisions remain pending.'),
 ('hou','Houston Thursday practice report','Collins remained limited. Use the October 1 Week 4 table; the older updated-date field is inconsistent.'),
 ('lac','Chargers Thursday practice report','McConkey went from limited Wednesday to absent Thursday with a foot injury.'),
 ('pit','Steelers final injury report','Dowdle ruled out; Warren recorded 17 rushes and three receptions last week.')]:
 src[key].update(title=title,date='2026-10-01',finding=finding)
source('nyj','Jets/Bears Thursday practice report','https://www.newyorkjets.com/news/jets-injury-report-week-4-vs-bears-thursday-10-01-2026','2026-10-01','Official team report','Hall and Caleb Williams missed both practices; Swift newly absent Thursday with knee injury. No final game designations.')
source('phi','Eagles Thursday practice report','https://www.philadelphiaeagles.com/news/rams-vs-eagles-injury-report-2026-nfl-week-4-devonta-smith-puka-nacua','2026-10-01','Official team report','Smith (hamstring) and Goedert (knee) missed Thursday practice after Wednesday nonparticipation. Neither is cleared for Sunday.')
source('smith_news','Smith reportedly unlikely to play','https://aws-prod-web9.rotowire.com/football/headlines/devonta-smith-injury-unlikely-to-play-in-week-4-640205','2026-10-01','Report citing ESPN reporter Tim McManus','Smith reportedly not expected to play Sunday; this is a report, not an official Out designation.')
source('mia','Miami/Minnesota Thursday practice report','https://www.miamidolphins.com/team/injury-report/','2026-10-01; accessed October 1 evening','Official team report','Wright upgraded to full practice with stinger/foot listed. Jefferson missed both practices with ankle injury; final status pending.')
source('no','Saints Thursday practice report','https://www.neworleanssaints.com/news/injury-report-atlanta-falcons-vs-new-orleans-saints-2026-nfl-week-4-thursday','2026-10-01','Official team report','Johnson and Kamara are not listed on the first practice report for Monday. This is not a final inactive list.')
source('etienne','Etienne placed on injured reserve','https://d3nqdp0e3r32g8.cloudfront.net/news/saints-place-running-back-travis-etienne-on-injured-reserve','2026-10-01','WBRZ report of Saints announcement','Etienne placed on injured reserve with hamstring injury. Kamara, Miller and Donaldson remain; split is not established.')
source('tnf','Thursday final inactives','https://fantasy-www.nfl.com/news/week-4-thursday-night-inactives-pittsburgh-steelers-at-cleveland-browns','2026-10-01','NFL inactive report','Warren and Fannin are not inactive. Dowdle and both Cleveland interior linemen Jenkins are inactive. Kickoff was 8:15 p.m. ET.')
source('schedule','Week 4 schedule','https://www.nfl.com/news/nfl-how-to-watch-week-4-schedule-london-game-details-and-more','2026-10-01 accessed','NFL schedule','Week 4 has no byes. Sunday includes early London; Saints play Monday.')
source('london','Colts London kickoff','https://www.colts.com/fans/international/london','2026-10-01 accessed; October 4 game','Official team schedule','Indianapolis and Washington kick off Sunday October 4 at 9:30 a.m. Eastern.')
source('ind','Colts Thursday practice notebook','https://www.colts.com/news/practice-notebook-ashton-dulin-returns-to-field','2026-10-01','Official team report','Dulin returned fully. Keenan Allen limited with groin injury. Linked Wednesday report had Shrader full despite groin issue; no final clearance inferred.')
src['ranks'].update(date='2026-09-30; updated 2026-10-01',finding='Half-PPR opinions, not league projections. Hurts over Stroud; Jones over Herbert; Mahomes over Nix. Outdated injury assumptions must yield to official reports.')
src['second'].update(date='QB September 30; RB October 1; TE September 29; checked October 1',finding='Independent weekly rankings corroborate QB comparisons but disagree on Fannin. Not custom-scoring projections.')
src['value'].update(date='2026-09-29; checked 2026-10-01',finding='Separate one-QB and two-QB values; market opinion does not measure acceptance or starter impact. Injury news can supersede chart values.')
for key in ['claude_model','fantasycalc','value_chart']:
 src[key]['kind'] = 'Historical input — not refreshed in this edition'
 src[key]['finding'] = 'Preserved from the prior edition. Not fetched, rerun or independently validated during this review.'

# Extend the candidate ownership shortlist from the same complete fresh roster set.
# Cached identity/status are metadata only, never a source for current medical clearance.
p = json.loads((BASE/'work/daily-cache/players.json').read_text())
for pid in ['4035','11566']:
 name=p[pid]['full_name']
 if not any(x['name']==name for x in r['candidates']):
  r['candidates'].append({'name':name,'role':'Ownership and opportunity review','sources':['sleeper']})
 for l in c['leagues']:
  owners=[t['name'] for t in l['tracking']['teams'] if any(x['id']==pid for x in t['players'])]
  assert len(owners)<=1
  if not any(x['id']==pid for x in l['market']):
   l['market'].append(dict(id=pid,name=name,position=p[pid]['position'],team=p[pid]['team'],owner=owners[0] if owners else None,injury=p[pid].get('injury_status')))
s['candidate_ownership_note']='Added Kamara/Daniels shortlist entries using complete rosters retrieved at context.fetched_at; cached player identity/status only. Original snapshot retained in daily-run.'

def move(action,pid,title,reason,cost,sources,confidence='Conditional',drop=None):
 return dict(action=action,id=pid,title=title,reason=reason,cost=cost,sources=sources,confidence=confidence,drop_id=drop)
def note(title,body,sources): return dict(title=title,body=body,sources=sources)
for l in c['leagues']:
 a=r['leagues'][l['id']]
 a.update(roster_ids=sorted(x['id'] for x in l['roster']),scoring_baseline=l['scoring'],slots_baseline=l['slots'])
 own=next(t for t in l['tracking']['teams'] if t['owner_id']==c['user_id'])
 assert [x['id'] for x in a['lineup']]==own['starters'], 'Chosen lineup changed; review required'
 for row in a['lineup']:
  row['note']='Chosen baseline preserved; no change submitted. '+('Thursday game locked.' if row['team'] in ['PIT','CLE'] else 'Subject to final availability; alternatives are not validated model improvements.')
 a['strategy']='Preserve chosen lineup; prioritize confirmed availability and flexible bench depth.'
 a['trades']=[]
 a['lineup_notes']=[note('Historical model outputs','Prior Claude model results and proposed offers are retained in historical_model_review with their original timestamp. No new title odds or acceptance probabilities were produced.',['claude_model'])]

j=r['leagues']['1403096266736422912']
j['headline']='Pause the Smith trade; consider Kamara for bench depth'
j['player_moves']=[
 move('Monitor','11635','Keep Burden ahead of injured McConkey for now','McConkey missed Thursday practice.','No claim required. Decide before Burden locks; do not wait for the later Chargers game.',['lac','sleeper']),
 move('Hold','9758','Keep chosen Stroud baseline','Hurts is an analyst alternative, not a verified improvement; Philadelphia also has receiving injuries.','Six-point passing TDs matter. Retain Purdy/Stroud unless the custom model is reassessed; keep Daniels as recovery cover.',['ranks','phi','sleeper']),
 move('Add','4035','Consider Kamara instead of a second defense','Etienne’s IR move creates additional opportunity, although the Saints split remains uncertain.','Drop bench LAR, not locked PIT. No chosen starter changes. Use a low-cost claim if needed; do not spend heavily in this shallow league. Gives up a defensive stash.',['etienne','no','sleeper'],'Moderate','LAR'),
 move('Hold','8228','Warren is already locked','Warren was active for Thursday; the start can no longer be revised.','No action. Retain Sunday FLEX options.',['tnf','sleeper'],'Confirmed')]
j['lineup_notes'] += [
 note('Smith proposal on hold','Do not act on Purdy + Montgomery for Lawrence + Kyren + Smith at the old valuation. Smith missed practice and is reportedly unlikely Sunday. It would also cost one roster spot. Zavier has Goff/Shough, numerous RB alternatives and multiple established WRs; no current mutual starter gain is established.',['phi','smith_news','sleeper']),
 note('Chris backup is not an automatic next offer','St. Brown + Daniels + Barkley for Flowers + Watson + Hubbard remains historical, not endorsed now. Chris already has Murray, Love and Maye; an injured Daniels is not immediate QB cover. Preserve your established starters rather than infer a benefit from the old simulation.',['sleeper','was','value']),
 note('TE, kicker and weekly opponent','Keep Johnson as chosen TE with Kraft cover. Saints first report lists no Johnson injury; if that changes, decide on Kraft before Sunday afternoon. Shrader remains selected, with the early London deadline. This week’s rival Christopher currently starts Swift, whose Thursday absence creates uncertainty; it is not a reason to force your own changes.',['no','ind','london','nyj','sleeper']),
 note('Ownership and trade scan','LAR replaced Croskey-Merritt; Phil acquired Gordon and released Judkins. Zavier owns Allen; John owns Fannin. All rivals have QB/TE alternatives, so a one-for-one reserve QB/TE swap for a premium receiver is unsupported. Jones is surplus QB depth here; Judkins is already playing Thursday. Miller/Wright are alternatives to Kamara, not guaranteed lead backs.',['sleeper','value','mia','etienne'])]

n=r['leagues']['1385050179488460800']
n['headline']='Allen remains conditional; consider Kamara for redundant TE depth'
n['player_moves']=[
 move('Hold','11576','Keep Allen provisionally in FLEX','Hall missed both practices; Allen’s opportunity still depends on Hall’s final availability.','Already owned. If Hall returns, compare Kincaid or receiver alternatives before the Jets game.',['nyj','waiver','sleeper']),
 move('Monitor','7569','Keep an owned replacement ready for Collins','Collins stayed limited Thursday; he is not yet cleared.','Egbuka is the first alternative to review, with Odunze another option. Check final availability before their Sunday afternoon games. No claim needed.',['hou','second','sleeper']),
 move('Add','4035','Consider Kamara for Goedert’s bench spot','Additional Saints opportunity is more useful than a third TE behind McBride/Kincaid; Goedert missed practice.','Drop Goedert only if acquiring Kamara. A modest claim, not an all-in bid; shared workload and recent knee history limit certainty. Keep current starters.',['etienne','phi','sleeper'],'Moderate','5022'),
 move('Hold','8130','Preserve McBride and Kincaid cover','The completed Bowers/Irving trade is already reflected; no redundant TE claim needed.','McBride remains TE; Kincaid covers injury/bye and conditional FLEX needs.',['sleeper','second'],'Strong')]
n['lineup_notes'] += [
 note('QB and waiver review','Keep chosen Mahomes over Nix. Daniels was dropped by Kyle’s Clash Team and is unrostered, but remains limited and would be a third QB in a one-QB league. Do not drop useful injury cover just to chase a name. BabyMamaPayment added White, who is still absent from practice.',['sleeper','was','second']),
 note('Previously reported pending offer','Mahomes/Kyren/Kincaid for Lawrence/Jeanty/McMillan was reported sent in the prior edition; pending status is not visible through Sleeper. Do not resend or assume acceptance. Kyle has Ferguson and has since dropped Daniels. The roster-neutral package trades TE insurance for WR depth but requires a fresh custom-scoring comparison; no current odds asserted.',['sleeper','value','claude_model']),
 note('Opponent and locked defense','PIT is locked. Keep Gibbs/Kyren, Montgomery, Adams and Bates as chosen. Opponent JP’s Baby Momma starts Jefferson, who missed Thursday practice; do not assume he is out. Hall’s manager MagicMax5 already has several TEs, reducing the case for a simple Kincaid swap.',['sleeper','mia','tnf'])]

m=r['leagues']['1360286127205912576']
m['headline']='Keep Gordon as depth with Wright back at full practice'
m['player_moves']=[
 move('Hold','12495','Do not promote Gordon automatically','Wright returned to full practice; last week’s lead workload does not establish Gordon’s future share.','Keep Love/Croskey-Merritt as chosen. Preserve Gordon as depth, not a guaranteed starter or permanent bye solution.',['mia','waiver','sleeper']),
 move('Hold','5870','Keep chosen Jones pending final reports','Independent QB rankings lean Jones over Herbert; neither reflects the exact completion and yardage bonuses here.','Check before London’s early kickoff. Preserve Herbert as cover; Caleb missed both practices.',['second','nyj','london','sleeper']),
 move('Hold','12506','Fannin’s Thursday start is locked','Fannin was not on Cleveland’s inactive list.','No TE substitution now. Okonkwo remains injury-dependent future cover.',['tnf','was','sleeper'],'Confirmed'),
 move('Hold','5927','Keep McLaurin with Washington availability on watch','Daniels remains limited; the quarterback situation is not settled.','No forced move. Malik Washington is owned cover. Finalize Washington players before London kickoff.',['was','london','sleeper'])]
m['lineup_notes'] += [
 note('Transactions and available players','JDMOONZ added Dobbins and dropped Ekeler, reducing his immediate need for Croskey-Merritt. Bateman and Vele were claimed by rivals. Bo Dix owns Wright/Miller, and JDMOONZ owns Kamara: none is a waiver target here. No supported drop from the current thin RB/WR depth for another QB or speculative receiver.',['sleeper','value']),
 note('Previously reported CMC offer','Caleb plus Croskey-Merritt for McCaffrey remains historical, with current pending status unknown. The counterparty has Brissett, Kamara and now Dobbins, and Caleb is not cleared. A blank QB slot is not proof he needs to surrender McCaffrey. No acceptance probability or new offer recommended; Herbert-for-RB swaps also need a genuine mutual starter benefit.',['sleeper','nyj','value']),
 note('Opponent and remaining lineup','Diddy’s Basement currently has an empty kicker slot and Achane still selected; that can change. Preserve Lamb/Wilson, Love/Croskey-Merritt, MIN and Shrader rather than chase a live projected margin. This league rewards completions and passing yardage differently; the chosen lineup is not being replaced by generic rankings.',['sleeper','ind','mia'])]

for a in r['leagues'].values():
 a['calls']=[dict(kind=x['action'],id=x['id'],title=x['title'],reason=x['reason'],confidence=x['confidence'],sources=x['sources'],recheck=x['cost']) for x in a['player_moves']]
 a['lineup_notes'].append(note('Timing and uncertainty','Thursday players are locked. Sunday and Monday final inactive lists are still pending. No bye-driven move is needed this week. An injury tag or blank cached status is not medical clearance.',['tnf','schedule']))
r['changes']=[
 'Verified Smith hamstring practice absence: old Zavier trade recommendation is on hold; historical model estimates are not refreshed.',
 'Kamara is available in Jacked Pine and Netanyahu Ball; consider LAR or redundant Goedert as the respective drop after Etienne’s IR move.',
 'Wright full practice lowers confidence in Gordon’s workload; preserve the chosen MSU RB starters.',
 'Thursday Warren/PIT/Fannin locked; McConkey, Collins, Hall, Daniels and Caleb reviewed against official Thursday reports.',
 'All three chosen lineups preserved; completed rival transactions and ownership reconciled. No actions submitted.'
]
out=BASE/'work/research-2026-10-01-evening.json'
snap=BASE/'work/snapshot-2026-10-01-evening.json'
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
snap.write_text(json.dumps(s,ensure_ascii=False)+'\n')
print(out)
print(snap)
