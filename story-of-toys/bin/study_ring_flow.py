"""Compare the played route with local Ice Rings measurements and the new route."""
import importlib.util,json,math,re,hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import course
out=ROOT/'evidence/route90'
spec=importlib.util.spec_from_file_location('played89',out/'course89.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def angle(a,b):
 return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/math.hypot(*a)/math.hypot(*b)))))
def metrics(c):
 rows=[]
 for s in range(1,8):
  gs=c.stage_gates(s);ps=[c.SPAWNS[s-1]]+[g['center'] for g in gs]+[c.TARGETS[s-1]]
  turns=[angle(c.sub(b,a),c.sub(d,b)) for a,b,d in zip(ps,ps[1:],ps[2:])]
  rows.append({'stage':s,'rings':gs,'path':c.PATHS[s-1] if hasattr(c,'PATHS') else ps,'max_turn_degrees':max(turns),'turns_degrees':turns,'ring_gaps':[math.dist(a,b) for a,b in zip(ps[1:-2],ps[2:-1])]})
 return rows
ref=ROOT.parent/'rl-maps/reference/ice-rings'
rings=json.loads((ref/'ring-transforms.json').read_text());lookup={r['actor']:r for r in rings}
installed=next((Path.home()/'Games/Heroic/Prefixes/default/drive_c/RLTrainingMaps/Ice Rings').glob('*.upk'))
sha=hashlib.sha256(installed.read_bytes()).hexdigest();assert sha==json.loads((ref/'inspection.json').read_text())['sha256']
names=['StaticMeshActor_0','StaticMeshActor_749','StaticMeshActor_750','StaticMeshActor_752','StaticMeshActor_753','StaticMeshActor_754','StaticMeshActor_385'];sample=[]
for name in names:
 r=lookup[name];t=r['transform'];v=lambda s:{k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',s)}
 p=v(t['Location']);rot=v(t['Rotation']);assert rot['Pitch']==rot['Roll']==0
 yaw=rot['Yaw']*math.tau/65536
 sample.append({'actor':name,'center':[p['X'],p['Y'],p['Z']+1929.934692],'normal':[math.sin(yaw),-math.cos(yaw),0],'yaw_degrees':math.degrees(yaw)})
ps=[r['center'] for r in sample]
result={'reference':{'installed_path':str(installed),'sha256':sha,'scope':'Opening spatial run from initial ring; not an inferred ordering of all 1449 instances. Unpitched meshes allow direct local hoop-center correction. No assets copied.','sample':sample,'gaps':[math.dist(a,b) for a,b in zip(ps,ps[1:])],'turns_degrees':[angle(course.sub(b,a),course.sub(c,b)) for a,b,c in zip(ps,ps[1:],ps[2:])]},'before':metrics(old),'after':metrics(course)}
(out/'comparison.json').write_text(json.dumps(result,indent=2))
print('Reference SHA verified; stage max turns before/after:',[(r['stage'],round(r['max_turn_degrees'],1),round(n['max_turn_degrees'],1)) for r,n in zip(result['before'],result['after'])])
