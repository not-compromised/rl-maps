"""Dispatch through the shared editor claim and retain full responses privately."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from editor_transport import dispatch
handle=sys.argv[1];action=sys.argv[2]
r=dispatch(handle,action)
p=ROOT/'evidence'/'editor';p.mkdir(parents=True,exist_ok=True)
f=p/(str(time.time_ns())+'.json');f.write_text(json.dumps(r))
print(json.dumps({'ok':r.get('ok'),'evidence':str(f),'visible_fields':[x for x in r.get('fields',[]) if x.get('visible')]}))
