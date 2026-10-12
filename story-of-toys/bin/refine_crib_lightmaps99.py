"""Give the crib arches continuous planar charts in unused lightmap space."""
import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from polish_room99 import crib_parts,digest
from room_lightmaps import overlapping_faces
source=ROOT/'output/room-finish-99b';out=ROOT/'output/room-finish-99c'
assert Path(bpy.data.filepath).resolve()==source/'RoomFinish.blend'
assert not out.exists();out.mkdir()
original={o.name:digest(o) for o in bpy.data.objects if o.type=='MESH'}
# These four empty rectangles were measured against every retained triangle.
# The overlap check below guards against using them with a different baseline.
regions=[(2,2,32,20),(2,22,32,20),(57,72,32,20),(2,42,28,18)]
report=[];i=0
for obj,faces in crib_parts()[0]:
 uv=obj.data.uv_layers[1].data
 for side in (-1,1):
  front=[f for f in faces if f.normal.x*side>.99]
  assert len(front)==96
  x,y,w,h=regions[i];i+=1
  before=[];after=[]
  for face in front:
   a,b,c=[uv[j].uv.copy() for j in face.loop_indices];before.append(abs((b-a).cross(c-a))*.5*1024**2)
   for li in face.loop_indices:
    p=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
    uv[li].uv=((x+1+(w-2)*(p.y+17050)/5100)/128,(y+1+(h-2)*(p.z-5200)/2800)/128)
   a,b,c=[uv[j].uv for j in face.loop_indices];after.append(abs((b-a).cross(c-a))*.5*1024**2)
  report.append(dict(side=side,region=(x,y,w,h),faces=len(front),texels_before=sum(before),texels_after=sum(after)))
assert not overlapping_faces(bpy.data.objects['RoomCribPart2'])
for name,value in original.items():
 if name!='RoomCribPart2':assert digest(bpy.data.objects[name])==value,name
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
sha=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest()
for name in ('room-manifest.json','room99.json'):
 data=json.loads((source/name).read_text());data.update(source=str(out/'RoomFinish.blend'),source_sha256=sha)
 if name=='room99.json':data['arch_lightmaps']=report
 (out/name).write_text(json.dumps(data,indent=2))
(out/'asset-prefixes.json').write_bytes((source/'asset-prefixes.json').read_bytes())
print(json.dumps(report,indent=2));print('Source SHA256',sha)
