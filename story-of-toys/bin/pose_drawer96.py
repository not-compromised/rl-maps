import ast,bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'bin'))
from room_lightmaps import repair_mesh
source=root/'output/room-final-96';out=root/'output/room-final-96c';out.mkdir(exist_ok=True);assert not (out/'RoomFinish.blend').exists()
ns={'bpy':bpy,'bmesh':bmesh,'Vector':Vector};m=ast.parse((root/'bin/improve_room96.py').read_text());exec(compile(ast.Module(body=[n for n in m.body if isinstance(n,ast.FunctionDef) and n.name=='components'],type_ignores=[]),'components','exec'),ns)
R=Matrix.Rotation(math.radians(-55),3,'X');center=Vector((-6870,11870,5555));n=0
for o in list(bpy.data.objects):
 if not o.name.startswith('RoomSecretDrawer') or o.type!='MESH':continue
 bm,rows=ns['components'](o)
 for vs,lo,hi in rows:
  if hi.x<-6250:
   for v in vs:v.co=center+R@(v.co-center)+Vector((0,0,-95))
   n+=1
 bm.to_mesh(o.data);bm.free();o.data.update();repair_mesh(o,1024)
# Correct the remaining raised D on the third alphabet block.
o=bpy.data.objects['RoomToys'];bm,rows=ns['components'](o);letters=0
for vs,lo,hi in rows:
 if abs((lo.y+hi.y)/2+7440)<5 and hi.y-lo.y<12:
  for v in vs:v.co.x=-2800-v.co.x
  bmesh.ops.reverse_faces(bm,faces=list({f for v in vs for f in v.link_faces}));letters+=1
for vs,lo,hi in rows:
 if abs((lo.x+hi.x)/2-16475)<5 and hi.x-lo.x<12 and lo.z>2000:
  for v in vs:v.co.y=-23000-v.co.y
  bmesh.ops.reverse_faces(bm,faces=list({f for v in vs for f in v.link_faces}));letters+=1
bm.to_mesh(o.data);bm.free();o.data.update();repair_mesh(o,o.get('lightmap_resolution',512))
manifest=json.loads((source/'room-manifest.json').read_text());detail=json.loads((source/'details96.json').read_text());detail['drawer_pose']='Mike reclines in the open drawer, eye facing the inspection opening';detail['mike_components_rotated']=n
for row in manifest['meshes']:
 ob=bpy.data.objects[row['name']];ps=[ob.matrix_world@v.co for v in ob.data.vertices];row['bounds']=[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)];row['lightmap_resolution']=ob.get('lightmap_resolution',row['lightmap_resolution'])
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'));manifest['source_sha256']=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest();(out/'room-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'details96.json').write_text(json.dumps(detail,indent=2));(out/'asset-prefixes.json').write_text((source/'asset-prefixes.json').read_text());print(n)
