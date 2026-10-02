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
if failed {exit(1)}
print("PASS: JavaScript syntax, all three lineup manifests, ownership, reserves, injuries, week, expiry and scoring guards")
