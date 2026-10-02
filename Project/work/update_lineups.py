from pathlib import Path
import json,re,struct,plistlib,shutil
R=Path('outputs/Binocular.app/Contents/Resources');d=json.loads((R/'research.json').read_text());snapshot=json.loads((Path.home()/'Library/Application Support/Sleeper Brief/snapshot.json').read_text());P=json.loads((Path.home()/'Library/Application Support/Sleeper Brief/cache/players.json').read_text())
d['reviewed_at']='2026-09-16';d['scope']='Researched September 16 for Week 2. Refresh checks Sleeper rosters; the analysis is a dated editorial edition. Confirm game status and lineup locks before making changes in Sleeper.'
d['sources']['katz']={'title':'Jason Katz · Week 2 quarterback rankings','url':'https://www.profootballnetwork.com/fantasy-football/qb-rankings-week-2-2026-katz/','date':'Sep 14; reviewed Sep 16, 2026','kind':'Independent analyst rankings','finding':'Favors Daniels and Hurts over Purdy, Nix over Mahomes, and Caleb Williams over Mayfield. Not a custom-scoring projection.'}
d['sources']['bowers_update']={'title':'Las Vegas Review-Journal · Bowers update','url':'https://www.reviewjournal.com/sports/raiders/raiders-coach-klint-kubiak-says-brock-bowers-is-day-to-day-3886325/','date':'Updated Sep 15, 2026','kind':'Local beat reporting','finding':'Klint Kubiak described Bowers as day-to-day. This does not establish Week 2 availability; Sleeper still lists him Out in the saved roster.'}
d['sources']['flex']['date']='Sep 16, 2026';d['sources']['flex']['finding']='PPR rankings favor Etienne and Godwin over Reed. The analyst slightly prefers Godwin; the displayed consensus reverses that order. Dobbins versus Croskey-Merritt is close.'
d['sources']['dst']['date']='Rechecked Sep 16, 2026'
ids=list(d['leagues']); jp,nb,ms=[d['leagues'][x] for x in ids]
def call(kind,title,reason,confidence,sources,recheck):return dict(kind=kind,title=title,reason=reason,confidence=confidence,sources=sources,recheck=recheck)
jp['headline']='QB cover secured. Now sharpen the FLEX.';jp['strategy']='Purdy is now on your bench. Keep the two established QB starters and use your available depth to review the FLEX slots.'
jp['calls'][0]=call('Roster','Purdy added; no repeat waiver needed','The September 16 snapshot shows Purdy on your roster and Downs off it. The original add/drop has been completed.','Roster fact',['sleeper'],'Refresh ownership before considering any new move.')
jp['calls'][1]=call('Lineup','Lean Etienne over Reed; Godwin is close','Both PPR alternatives rank ahead of Reed. The analyst and displayed consensus disagree on their order; Etienne is a small preference, not a clear separation.','Lean',['flex'],'McConkey can enter the comparison if cleared without restrictions.')
jp['calls'][3]=call('Trade','Hold your core; no forced consolidation','The QB need is addressed. Review a trade only if it improves a starting slot, rather than responding to roster-count differences.','Hold',['value'],'Reassess after updated roles and injury reports.')
nb['headline']='Adams is in. The remaining call is quarterback.';nb['strategy']='Your roster now has Adams starting and Black on the bench. Focus on the QB comparison and Bowers’ recovery rather than repeating completed moves.'
nb['calls'][0]=call('Lineup','Lean Nix over Mahomes; keep Adams starting','The additional QB review supports Nix. Your passing-yard bonuses leave room for a different outcome; this is a start/sit lean, not a projected-point promise.','Lean',['katz'],'Recheck health and late-week rankings before kickoff.')
nb['calls'][1]=call('Roster','Black added; keep him as depth','The saved roster confirms Black replaced the spare kicker. Do not automatically promote a new waiver addition into the starting lineup.','Roster fact',['sleeper','black'],'Monitor the backfield role before considering him over a current starter.')
nb['calls'][2]=call('Injury','Plan on Goedert; monitor Bowers','Bowers remains in reserve with an Out flag in the snapshot. Local reporting describes him as day-to-day; wait for a Week 2 decision before changing the TE slot.','Conditional',['bowers_update'],'Confirm final status, workload and reserve eligibility.')
ms['calls'][0]=call('Lineup','Keep Caleb and Loveland; RB2 is a close call','The QB review supports Caleb. Dobbins and Croskey-Merritt are close enough that I would retain Croskey-Merritt for now and revisit late-week role news.','Lean',['katz','flex','loveland'],'Check workload updates before replacing the RB2.')
ms['calls'][1]=call('Roster','Douglas added; keep him on the bench','Douglas is now rostered and Tucker is gone. Adding him for depth does not require starting him this week.','Roster fact',['sleeper','douglas'],'Reassess his role after the next game.')
ms['calls'][3]=call('Trade','No urgent TE trade','Hold Loveland. Tucker is no longer on your roster, so the old exploratory package is retired.','Hold',['loveland'],'Any new proposal must use current ownership and improve your team.')
for l in snapshot['context']['leagues']:
 r=d['leagues'][l['id']];r['roster_ids']=sorted(p['id'] for p in l['roster']);r['scoring_baseline']=l['scoring'];r['slots_baseline']=l['slots'];chunk=snapshot['text'].split('## '+l['name']+'\n')[1].split('\n## ')[0];line=next(x for x in chunk.splitlines() if x.startswith('Starters: '))[10:];names={p['name']:p for p in l['roster']}; rows=[]
 for text in re.split(r',\s*(?![^()]*\))',line):
  slot,name=text.split(' ',1); name=re.sub(r'\s*\([^)]*\)|\s*\[[^]]*\]','',name).strip();name=name.replace(' DST','');p=names[name];rows.append({'slot':slot,'id':p['id'],'name':name,'position':P[p['id']]['position'],'team':P[p['id']].get('team'),'note':'Keep current starter'})
 if l['id']==ids[0]:
  row=next(x for x in rows if x['name']=='Jayden Reed');p=names['Travis Etienne'];row.update(id=p['id'],name=p['name'],position='RB',team='NO',note='Lean over Reed · Godwin is a close alternative')
 if l['id']==ids[1]:
  row=rows[0];p=names['Bo Nix'];row.update(id=p['id'],name=p['name'],position='QB',team='DEN',note='Lean over Mahomes · rankings, not a custom projection')
 if l['id']==ids[2]:
  next(x for x in rows if x['slot']=='DEF')['note']='Current-roster fallback · review TB / SF streaming option'
 r['lineup']=rows
 r['lineup_notes']=[{'title':c['title'],'body':c['reason'],'sources':c['sources']} for c in r['calls'] if c['kind'] in ['Lineup','Injury','Defense']]
 r['lineup_notes'].append({'title':'Scoring lens','body':r['scoring_note']+' No custom point projections are available.','sources':['sleeper']})
(R/'research.json').write_text(json.dumps(d,indent=2,ensure_ascii=False));(R/'research.js').write_text('window.RESEARCH = '+json.dumps(d,ensure_ascii=False)+';\n');(R/'initial-snapshot.json').write_text(json.dumps(snapshot))
parts=[]
for code,name in [('icp4','icon_16x16.png'),('icp5','icon_32x32.png'),('icp6','icon_32x32@2x.png'),('ic07','icon_128x128.png'),('ic08','icon_256x256.png'),('ic09','icon_512x512.png'),('ic10','icon_512x512@2x.png')]:
 b=(Path('work/Binocular.iconset')/name).read_bytes();parts.append(code.encode()+struct.pack('>I',len(b)+8)+b)
b=b''.join(parts);(R/'BinocularStadium.icns').write_bytes(b'icns'+struct.pack('>I',len(b)+8)+b)
shutil.copyfile('work/Binocular.iconset/icon_512x512.png','outputs/Binocular Icon.png')
p=R.parent/'Info.plist';info=plistlib.loads(p.read_bytes());info['CFBundleIconFile']='BinocularStadium';info['CFBundleShortVersionString']='1.2';info['CFBundleVersion']='3';p.write_bytes(plistlib.dumps(info))
