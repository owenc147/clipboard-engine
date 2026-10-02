import Foundation
import JavaScriptCore
let ctx=JSContext()!
var failed=false
ctx.exceptionHandler={_,e in print("FAIL: \(e!)");failed=true}
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath).appendingPathComponent("outputs/Binocular.app/Contents/Resources")
for name in ["binocular.js","lineup.js","research.js","radar.js","suggestions.js","moves.js","profiles.js"] {
 let source=try String(contentsOf:root.appendingPathComponent(name),encoding:.utf8)
 let literal=String(data:try JSONSerialization.data(withJSONObject:[source]),encoding:.utf8)!
 ctx.evaluateScript("new Function(\(literal)[0]);")
}
ctx.evaluateScript(try String(contentsOf:root.appendingPathComponent("research.js"),encoding:.utf8).replacingOccurrences(of:"window.RESEARCH",with:"var RESEARCH"))
let line=try String(contentsOf:root.appendingPathComponent("lineup.js"),encoding:.utf8)
ctx.evaluateScript(line.components(separatedBy:"function renderLineup")[0])
let data=try String(contentsOf:root.appendingPathComponent("initial-snapshot.json"),encoding:.utf8)
ctx.evaluateScript("var snapshot = \(data);")
ctx.evaluateScript("""
function assert(c,m){if(!c)throw Error(m)}
const now=new Date('2026-09-16T14:00:00Z');
for(const l of snapshot.context.leagues){const r=RESEARCH.leagues[l.id],p=lineupPlan(r,l,2,now);assert(!p.blocked.length,'valid league blocked');assert(p.rows.every(x=>!x.issue),'invalid suggested starter');assert(p.rows.length===l.slots.filter(x=>!['BN','IR','TAXI'].includes(x)).length,'wrong slot count');assert(lineupPlan(r,l,1,now).blocked.length,'past week allowed');assert(lineupPlan(r,l,2,new Date('2026-09-23')).blocked.length,'expired allowed');}
let l=JSON.parse(JSON.stringify(snapshot.context.leagues[0])),r=RESEARCH.leagues[l.id],id=r.lineup[0].id;
l.roster=l.roster.filter(p=>p.id!==id);assert(lineupPlan(r,l,2,now).rows[0].issue,'absent starter allowed');
l=JSON.parse(JSON.stringify(snapshot.context.leagues[0]));l.reserve=[id];assert(lineupPlan(r,l,2,now).rows[0].issue,'reserve allowed');
l.reserve=[];l.roster.find(p=>p.id===id).injury='Out';assert(lineupPlan(r,l,2,now).rows[0].issue,'out allowed');
l.scoring.rec=0;assert(lineupPlan(r,l,2,now).blocked.length,'changed scoring allowed');
""")
ctx.evaluateScript("var window={},context=snapshot.context,reportWeek=2;")
let moves=try String(contentsOf:root.appendingPathComponent("moves.js"),encoding:.utf8)
ctx.evaluateScript(moves.components(separatedBy:"function renderMoves")[0])
ctx.evaluateScript("""
for(const l of snapshot.context.leagues){const r=RESEARCH.leagues[l.id];assert(!movesIssues(r,l,now).length,'valid daily edition blocked');for(const m of r.player_moves)assert(!moveCheck(m,l),'invalid player move');for(const t of r.trades)assert(!tradeCheck(t,r,l).issues.length,'invalid trade');assert(movesIssues(r,l,new Date('2026-09-20')).length,'expired daily moves allowed');}
let ml=JSON.parse(JSON.stringify(snapshot.context.leagues[0])),mr=RESEARCH.leagues[ml.id],mt=mr.trades[0];
ml.tracking.teams.find(t=>t.roster_id===mt.partner_roster_id).players=[];assert(tradeCheck(mt,mr,ml).issues.length,'lost target allowed');
ml=JSON.parse(JSON.stringify(snapshot.context.leagues[0]));ml.roster=ml.roster.filter(p=>!mt.give.includes(p.id));assert(tradeCheck(mt,mr,ml).issues.length,'lost outgoing allowed');
assert(moveCheck({action:'Add',id:'TB'},snapshot.context.leagues[0]),'rostered waiver target allowed');
""")
if failed {exit(1)}
print("PASS: lineup guards, daily expiry, trade ownership changes, unavailable waiver targets, all JavaScript syntax")
