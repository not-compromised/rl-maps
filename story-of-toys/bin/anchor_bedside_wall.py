"""Seat the headboard and adjacent cabinets against the left wall."""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import surface_signature
source=ROOT/'output/room-layout-88-globe/RoomFinish.blend'
assert Path(bpy.data.filepath).resolve()==source
assert hashlib.sha256(source.read_bytes()).hexdigest()=='dadec7a12d98b71d6b7821d3e62132d80f0b77f31646042283e0bc1b0d0395f8'
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
bed={'RoomBed','RoomBedPrint','RoomCheckpointBed','RoomCheckpointFinish'}
offsets={'RoomNightstand':(-12925,-15015,0),'RoomDresser':(-13125,-4415,0),
         'RoomGlobe':(-12775,-4415,0),'RoomGlobePart2':(-12775,-4415,0), 'RoomCheckpointStart':(7500,7500,0), 'RoomNurseryCabinet':(26900,-365,0)}
for name in bed:
 o=bpy.data.objects[name]
 for v in o.data.vertices:
  x,y,z=v.co;v.co=(-8725-y,x+2635,z)
 o.data.update()
for name,delta in offsets.items():
 o=bpy.data.objects[name]
 for v in o.data.vertices:v.co+=Vector(delta)
 o.data.update()
# Only the alphabet-block cluster occupied the newly claimed bed corner.
o=bpy.data.objects['RoomToys'];moved=0
adj={v.index:set() for v in o.data.vertices}
for edge in o.data.edges:
 a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
remaining=set(adj)
while remaining:
 seed=remaining.pop();component={seed};pending=[seed]
 while pending:
  for i in adj[pending.pop()]:
   if i in remaining:remaining.remove(i);component.add(i);pending.append(i)
 vs=[o.data.vertices[i] for i in component]
 if max(v.co.x for v in vs)<-6700 and max(v.co.y for v in vs)<-10000 and max(v.co.z for v in vs)>100:
  for v in vs:v.co.x+=7500;v.co.y+=7500;moved+=1
 elif min(v.co.x for v in vs)>16000 and max(v.co.y for v in vs)<-12000:
  for v in vs:v.co.x+=2700;v.co.y+=4500
assert moved>0
o.data.update()
o=bpy.data.objects['RoomCheckpointBed']
for v in o.data.vertices:v.co.x-=7000
o.data.update()
for name,sig in original.items():
 if name not in bed|offsets.keys()|{'RoomToys'}:assert surface_signature(bpy.data.objects[name])==sig,name
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
(out/'placement.json').write_text(json.dumps({'bed_transform':'(-8725-y, x+2635, z)','translations':offsets,'alphabet_block_translation':[7500,7500,0],'rubber_ball_translation':[2700,4500,0],'wall_molding_inner_x':-22815,'corner_molding_inner_y':-18755,'back_x':-22775,'wall_gap':40,'preserved':sorted(original.keys()-bed-offsets.keys()-{'RoomToys'})},indent=2))
print('Saved wall-aligned furniture',out)
