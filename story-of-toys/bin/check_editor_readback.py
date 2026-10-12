"""Check a saved room's fresh engine rows against course and Blender exports."""
import argparse,hashlib,json,re,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from audit_editor import QUERIES,validate,parsed_rows,check_exact,vector
p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('--asset-prefixes',type=Path);p.add_argument('--kill-z',type=float,default=-2400);p.add_argument('--build',type=Path,default=ROOT/'output/room-course-03b');p.add_argument('--art',type=Path,default=ROOT/'output/room-art-05');a=p.parse_args()
report=json.loads((a.build/'build.json').read_text());package=report['package'];prefix=package+'.TheWorld:PersistentLevel.'
for file,key in [('course.t3d','source_sha256'),('scene.json','scene_sha256'),('Voyage.kismet.txt','kismet_sha256')]:
 assert hashlib.sha256((a.build/file).read_bytes()).hexdigest()==report[key],file
scene=json.loads((a.build/'scene.json').read_text());graph=(a.build/'Voyage.kismet.txt').read_text();room=json.loads((a.art/'room-manifest.json').read_text())['meshes']
asset_prefixes=json.loads(a.asset_prefixes.read_text()) if a.asset_prefixes else {}
def asset(m):return package+'.'+asset_prefixes.get(m['name'],'Room05_')+m['name']
text=a.log.read_text();lines=text.splitlines()
def result(query):
 cls,prop=query.split();matches=[l for l in lines if re.search(r'Log: \d+\) '+cls+r' \S+\.'+prop+r' = ',l)]
 return {'rows':matches}
results={q:result(q) for q in QUERIES}
room_actors={prefix+m['name']+'_Actor' for m in room};room_components={prefix+m['name']+'_Actor.'+m['name']+'_Component':m for m in room}
filtered={}
for q,r in results.items():
 filtered[q]={'rows':[l for l in r['rows'] if not any((' '+k+'.').lower() in l.lower() for k in room_actors)]}
# This UDK build pads imported static-mesh extents by one unit on each axis.
# The shared course validator compares unpadded source geometry.
filtered['StaticMeshComponent Bounds']['rows']=[re.sub(
 r'BoxExtent=\(X=([^,]+),Y=([^,]+),Z=([^)]+)\)',
 lambda m:'BoxExtent=(X=%f,Y=%f,Z=%f)'%tuple(float(x)-1 for x in m.groups()),line)
 for line in filtered['StaticMeshComponent Bounds']['rows']]
checks=validate(report,scene,graph,filtered)
def rows(q):return parsed_rows(result(q),package)
mesh_rows=rows('StaticMeshComponent StaticMesh')
check_exact({k:v for k,v in mesh_rows.items() if k in {x.lower() for x in room_components}}, {k:f"StaticMesh'{asset(m)}'" for k,m in room_components.items()},'Blender mesh references')
for prop in ('bDisableAllRigidBody','BlockRigidBody','CollideActors'):
 r=rows('StaticMeshComponent '+prop)
 for k,m in room_components.items():
  expected='False' if prop=='bDisableAllRigidBody' else str(m.get('collision',True))
  assert r[k.lower()]==expected,(k,prop,r.get(k.lower()))
r=rows('StaticMeshComponent Bounds')
for k,m in room_components.items():
 bounds=m['bounds']
 for field,expected in [('Origin',[(lo+hi)/2 for lo,hi in bounds]),('BoxExtent',[(hi-lo)/2+1 for lo,hi in bounds])]:
  assert all(abs(x-y)<.2 for x,y in zip(vector(r[k.lower()],field),expected)),(k,field)
for prop,expected in [('Location',[0,0,0]),('Rotation',[0,0,0]),('DrawScale',[1]),('DrawScale3D',[1,1,1])]:
 r=rows('StaticMeshActor '+prop)
 for k in room_actors:assert [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',r[k.lower()])]==expected,(k,prop)
for prop in ['UseSimpleRigidBodyCollision','UseSimpleBoxCollision','UseSimpleLineCollision']:
 r=rows('StaticMesh '+prop)
 for m in room:assert r[asset(m).lower()]=='False',(m['name'],prop)
for prop,expected in [('UseFullPrecisionUVs','True'),('LightMapCoordinateIndex','1')]:
 r=rows('StaticMesh '+prop)
 for m in room:assert r[asset(m).lower()]==expected,(m['name'],prop)
# Actor overrides must not silently replace the authored mesh resolution.
lightmap_overrides=rows('StaticMeshComponent bOverrideLightMapRes')
resolutions=rows('StaticMesh LightMapResolution')
for k,m in room_components.items():
 assert lightmap_overrides[k.lower()]=='False',(k,'stale lightmap override')
 assert int(resolutions[asset(m).lower()])==m['lightmap_resolution'],(k,'lightmap resolution')
assert list(rows('WorldInfo KillZ').values())==[f'{a.kill_z:.6f}']
assert list(rows('Pylon_Soccar_TA FieldExtent').values())==['(X=40000.000000,Y=40000.000000,Z=40000.000000)']
spawn=report['stages'][0]['spawn'];gate=report['gates'][0]['center']
initial_yaw=round(math.atan2(gate[1]-spawn[1],gate[0]-spawn[0])*32768/math.pi)
assert list(rows('PlayerStart_TA Rotation').values())==[f'(Pitch=0,Yaw={initial_yaw},Roll=0)']
checks.update(room_meshes=len(room),total_meshes=checks['meshes']+len(room),kill_z=a.kill_z)
print(json.dumps(checks,indent=2))
