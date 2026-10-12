"""Orient disconnected font caps using welded complete mesh groups."""
import bpy,bmesh,json,hashlib,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh
SOURCE=ROOT/'output/room-release-96b';OUT=ROOT/'output/room-release-96d';OUT.mkdir(exist_ok=True);assert not (OUT/'RoomFinish.blend').exists()
groups={}
for o in bpy.data.objects:
 if o.type=='MESH':groups.setdefault(re.sub(r'Part\d+$','',o.name),[]).append(o)
changes=[]
def key(vs):return tuple(sorted(tuple(round(x,3) for x in v) for v in vs))
for name,objects in groups.items():
 if name not in {'RoomBookLettering96','RoomBuzz','RoomCheckpointBook4','RoomCheckpointBook5','RoomCheckpointBook7','RoomClaw96','RoomClawLettering96','RoomMoonLettering96','RoomPosterLetters96','RoomSecretDrawer','RoomToys'}:continue
 # All groups are checked: font caps also occur in toys, badges and secret props.
 bm=bmesh.new();verts=[];faces=[]
 for o in objects:
  start=len(verts);verts.extend(tuple(v.co) for v in o.data.vertices);faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
 tmp=bpy.data.meshes.new('NormalAudit');tmp.from_pydata(verts,[],faces);bm.from_mesh(tmp);bpy.data.meshes.remove(tmp)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.025);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 normals={key([v.co for v in f.verts]):f.normal.copy() for f in bm.faces if len(f.verts)==3}
 bm.free()
 for o in objects:
  edit=bmesh.new();edit.from_mesh(o.data);flip=[]
  for f in edit.faces:
   target=normals.get(key([v.co for v in f.verts]))
   if name=='RoomRug96' and all(abs(v.co.z-48)<.1 for v in f.verts):
    if f.normal.z<0:flip.append(f)
   elif target is not None and f.normal.dot(target)<-.5:flip.append(f)
  if flip:
   bmesh.ops.reverse_faces(edit,faces=flip);edit.to_mesh(o.data);o.data.update();repair_mesh(o,o.get('lightmap_resolution',512));changes.append({'name':o.name,'faces_reoriented':len(flip)})
  edit.free()
manifest=json.loads((SOURCE/'room-manifest.json').read_text())
for row in manifest['meshes']:
 o=bpy.data.objects[row['name']];assert len(o.data.polygons)==row['triangles'];row['lightmap_resolution']=o.get('lightmap_resolution',row['lightmap_resolution'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest['source_sha256']=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest();(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2));prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix.update({r['name']:'Room09_' for r in changes});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2));detail=json.loads((SOURCE/'details96.json').read_text());detail['normal_repairs']=changes;detail['changed']=sorted(set(detail['changed'])|{r['name'] for r in changes});(OUT/'details96.json').write_text(json.dumps(detail,indent=2));print(json.dumps(changes))
