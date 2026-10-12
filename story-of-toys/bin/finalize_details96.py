"""Repair Andy's remaining collapsed texture coordinates without changing facial artwork."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin')]
from room_lightmaps import repair_mesh
SOURCE=ROOT/'output/room-models-96';OUT=ROOT/'output/room-final-96';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
fixed={};before_total=0
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('RoomAndyHead'):continue
 uv=o.data.uv_layers[0].data;lm=o.data.uv_layers[1].data;count=0;preserved=[]
 for face in o.data.polygons:
  coords=[uv[i].uv.copy() for i in face.loop_indices];a,b,c=coords
  if abs((b-a).cross(c-a))>=1e-12:preserved.append((list(face.loop_indices),coords));continue
  center=sum(coords,Vector((0,0)))/3;tile=(max(0,min(3,int(center.x*4))),max(0,min(3,int(center.y*4))))
  for i in face.loop_indices:uv[i].uv=Vector(((tile[0]+.5)/4,(tile[1]+.5)/4))+(lm[i].uv-Vector((.5,.5)))*.06
  a,b,c=[uv[i].uv for i in face.loop_indices]
  if abs((b-a).cross(c-a))<1e-12:
   # A padded local triangle keeps a valid diffuse basis for very small charts.
   for i,p in zip(face.loop_indices,((-.01,-.01),(.01,-.01),(-.01,.01))):uv[i].uv=Vector(((tile[0]+.5)/4,(tile[1]+.5)/4))+Vector(p)
  count+=1
 for ids,coords in preserved:assert all(uv[i].uv==c for i,c in zip(ids,coords))
 remaining=sum(abs((uv[f.loop_indices[1]].uv-uv[f.loop_indices[0]].uv).cross(uv[f.loop_indices[2]].uv-uv[f.loop_indices[0]].uv))<1e-12 for f in o.data.polygons)
 assert not remaining
 fixed[o.name]=dict(repaired=count,preserved_artwork_triangles=len(preserved),remaining_invalid_uvs=remaining);before_total+=count
assert before_total>1000
manifest=json.loads((SOURCE/'room-manifest.json').read_text());detail=json.loads((SOURCE/'details96.json').read_text());detail['changed']=sorted(set(detail['changed'])|set(fixed));detail['head_uv']=fixed
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest['source_sha256']=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest();(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'details96.json').write_text(json.dumps(detail,indent=2));prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix.update({n:'Room09_' for n in fixed});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2));print(json.dumps(fixed))
