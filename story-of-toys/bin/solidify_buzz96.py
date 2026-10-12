"""Close Buzz's one-sided wing stripes so they survive engine backface culling."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh
from room_palette_uv import fit_palette_uv
SOURCE=ROOT/'output/room-release-96';OUT=ROOT/'output/room-release-96b';OUT.mkdir(exist_ok=True);assert not (OUT/'RoomFinish.blend').exists()
changed=[];total=0
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('RoomBuzz'):continue
 bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);targets=[]
 while left:
  seed=left.pop();vs={seed};todo=[seed]
  while todo:
   for edge in todo.pop().link_edges:
    for v in edge.verts:
     if v in left:left.remove(v);vs.add(v);todo.append(v)
  fs={f for v in vs for f in v.link_faces}
  if len(vs)==4 and len(fs)==2 and max(v.co.z for v in vs)<18450 and sum(v.co.z for v in vs)/4<18370:targets.append(fs)
 if targets:
  for fs in targets:bmesh.ops.solidify(bm,geom=list(fs),thickness=10)
  bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);o.data.update();repair_mesh(o,1024);fit_palette_uv(o.data);changed.append(o.name);total+=len(targets)
 bm.free()
assert total==10,(total,changed)
manifest=json.loads((SOURCE/'room-manifest.json').read_text())
for row in manifest['meshes']:
 o=bpy.data.objects[row['name']]
 if row['name'] in changed:
  ps=[o.matrix_world@v.co for v in o.data.vertices];row.update(triangles=len(o.data.polygons),bounds=[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest(),triangles=sum(r['triangles'] for r in manifest['meshes']));(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'asset-prefixes.json').write_text(json.dumps({n:v for n,v in json.loads((SOURCE/'asset-prefixes.json').read_text()).items() if n in {m['name'] for m in manifest['meshes']}},indent=2));detail=json.loads((SOURCE/'details96.json').read_text());detail['solid_wing_stripes']=dict(count=total,meshes=changed);(OUT/'details96.json').write_text(json.dumps(detail,indent=2));print('Closed wing stripes',total,changed)
