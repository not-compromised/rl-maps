"""Geometry/UV diagnostics for distance artifacts and the exposed forehead."""
import bpy,json,sys,collections,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'bin')]
from build_map import gray_scene
from course import DECKS
out={}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 m=o.data;uv=m.uv_layers[0].data;seen=collections.Counter();near_edge=0;tiles=collections.Counter()
 for f in m.polygons:
  p=[tuple(round(x,3) for x in o.matrix_world@m.vertices[i].co) for i in f.vertices];seen[tuple(sorted(p))]+=1
  center=sum((uv[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
  tiles[str((int(center.x*4),int(center.y*4)))]+=1
  if any(min((v*4)%1,1-(v*4)%1)<.021 for i in f.loop_indices for v in uv[i].uv):near_edge+=1
 out[o.name]=dict(triangles=len(m.polygons),raw_corners=len(m.loops),duplicate_faces=sum(n-1 for n in seen.values() if n>1),atlas_edge_faces=near_edge,tiles=tiles,materials=[x.name for x in m.materials],properties=dict(o.items()))
# Any head point above the brim must fit well inside the crown's lower footprint.
h=bpy.data.objects['RoomAndyHead'];outside=[]
for v in h.data.vertices:
 p=h.matrix_world@v.co
 if p.z<16170:continue
 # Crown base centered (1500,1450), rounded rectangle exponent 2/.7.
 value=(abs(p.x-1500)/1650)**(2/.7)+(abs(p.y-1450)/1200)**(2/.7)
 if value>1:outside.append(list(p))
# Course pads sampled against authoring-space mesh top surfaces.
pads=[]
for i,p in enumerate(DECKS):
 hits=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  inv=o.matrix_world.inverted();origin=inv@Vector((p[0],p[1],p[2]+200));direction=(inv.to_3x3()@Vector((0,0,-1))).normalized()
  ok,point,normal,index=o.ray_cast(origin,direction,distance=1000)
  if ok:
   world=o.matrix_world@point
   if abs(world.z-p[2])<40:hits.append(dict(mesh=o.name,z=world.z,pad_clearance=p[2]-world.z))
 pads.append(dict(index=i,hits=hits))
result=dict(meshes=out,head_outside_crown_above_brim=outside,head_outside_count=len(outside),pad_contacts=pads)
p=ROOT/'evidence/detail94/surface-baseline.json';p.write_text(json.dumps(result,indent=2,default=str));print(json.dumps(dict(oversized=[(n,r['triangles']) for n,r in out.items() if r['raw_corners']>65535],duplicates=[(n,r['duplicate_faces']) for n,r in out.items() if r['duplicate_faces']],head_outside_count=len(outside),pads=pads),indent=2))
