from pathlib import Path
p=Path(__file__).parent/'stage/model_data.py';s=p.read_text();s=s.replace("model-cache-v2.json", "model-cache-v3.json")
s=s.replace("def vec(s):\n    return [round(s.get('pts_ppr') or 0, 2)] + [round(s.get(k) or 0, 2) for k in KEYS]", "def vec(s):\n    return [round(s.get('pts_ppr') or 0, 4)] + [None if k in BONUS and k not in s else round(s.get(k) or 0, 4) for k in KEYS]")
s=s.replace("if s.get('pts_ppr'):", "if s and ('pts_ppr' in s or s.get('gp')):")
s=s.replace("score = {k: ss[k] for k in KEYS if ss.get(k)}", "score = {k: ss[k] for k in KEYS if ss.get(k) and k not in BONUS}")
s=s.replace("def build(root, context):", "def build(root, context):\n    # Persist every configured scoring column, including K/DST and zero/negative totals.\n    global KEYS\n    KEYS = list(dict.fromkeys(KEYS + sorted({k for l in context.get('leagues', []) for k in l.get('scoring', {})}) + list(BONUS)))")
# Since cache contains positional vectors, use a schema-dependent cache identity.
s=s.replace("feed = Feed(Path(root) / 'model-cache-v3.json')", "import hashlib\n    schema = hashlib.sha256('|'.join(KEYS).encode()).hexdigest()[:12]\n    feed = Feed(Path(root) / ('model-cache-v3-' + schema + '.json'))")
# Need bonus-key info for exact actual flags and count histories.
s=s.replace("'keys': KEYS", "'bonus_keys': BONUS, 'keys': KEYS")
p.write_text(s)
p=Path(__file__).parent/'stage/model-engine.js';s=p.read_text();start=s.index(' const fp=(v,p,mean,d=1)=>');end=s.index('\n const pts=',start)
s=s[:start]+''' const fp=(v,p,mean,d=1)=>{
  if(!v)return 0;
  let t=0;for(const k in SC){const i=KI[k];if(i)t+=SC[k]*(v[i]||0)/d}
  for(const stat in BON){const y=(v[KI[stat]]||0)/d;
   for(const [th,b] of BON[stat]){
    const key=Object.keys(data.bonus_keys||{}).find(k=>data.bonus_keys[k][0]===stat&&data.bonus_keys[k][1]===th);
    const i=key&&KI[key],count=i?v[i]:null;
    // Actual weekly/season totals use recorded bonus counts when present.
    // Forecasts and aggregate histories without counts retain an explicit yardage approximation.
    t+=b*(!mean?(y>=th?1:0):(d>1&&count!=null?count/d:pOver(y,th,stat)));
   }
  }
  return t; // A legitimate zero/negative league score must never revert to generic PPR.
 };''' +s[end:]
s=s.replace("root.TitleModel={prepare,", "root.TitleModel={prepare,")
p.write_text(s)
