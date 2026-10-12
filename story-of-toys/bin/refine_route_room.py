"""Flatten the quilt and place the saved bookcase against the back wall."""
import bpy,bmesh,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature,overlapping_faces
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True);assert not (out/'RoomFinish.blend').exists()
source=ROOT/'output/room-finish-73'
assert Path(bpy.data.filepath).resolve()==(source/'RoomFinish.blend').resolve()
protected={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
bed=bpy.data.objects['RoomBed'];bm=bmesh.new();bm.from_mesh(bed.data);uv=bm.loops.layers.uv[0]
stitches=[f for f in bm.faces if all(int(l[uv].uv.x*4)+4*int(l[uv].uv.y*4)==12 for l in f.loops)]
assert stitches, 'Expected raised orange quilt stitches'
removed=len(stitches);bmesh.ops.delete(bm,geom=stitches,context='FACES')
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(bed.data);bm.free();bed.data.update()
repair=repair_mesh(bed,512)
shifted=['RoomShelves','RoomShelvesPart2','RoomShelvesPart3','RoomCheckpointLowerShelf','RoomCheckpointUpperShelf']
for name in shifted:
 obj=bpy.data.objects[name]
 for v in obj.data.vertices:v.co.y+=3800
 obj.data.update()
# A solid back closes the remaining inset between the planks and wall.
base=bpy.data.objects['RoomShelves']
bpy.ops.mesh.primitive_cube_add(size=1,location=(18350,18925,10500))
back=bpy.context.object;back.name='Bookcase back';back.dimensions=(6900,150,21000)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for layer in list(back.data.uv_layers):back.data.uv_layers.remove(layer)
u=back.data.uv_layers.new(name='UVMap')
for f in back.data.polygons:
 for li,xy in zip(f.loop_indices,((.02,.02),(.23,.02),(.23,.23),(.02,.23))):u.data[li].uv=xy
back.data.uv_layers.new(name='LightmapUV')
back.data.materials.append(base.data.materials[0])
bpy.ops.object.select_all(action='DESELECT');base.select_set(True);back.select_set(True);bpy.context.view_layer.objects.active=base;bpy.ops.object.join()
mod=base.modifiers.new('Back triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
repair_mesh(base,base.get('lightmap_resolution',512))
changed={'RoomBed',*shifted}
for name,sig in protected.items():
 if name not in changed:assert surface_signature(bpy.data.objects[name])==sig,name
for name in changed:assert not overlapping_faces(bpy.data.objects[name]),name
manifest=json.loads((source/'room-manifest.json').read_text())
for row in manifest['meshes']:
 o=bpy.data.objects[row['name']];world=[o.matrix_world@v.co for v in o.data.vertices]
 row['triangles']=len(o.data.polygons)
 row['bounds']=[[min(v[i] for v in world),max(v[i] for v in world)] for i in range(3)]
 row['lightmap_resolution']=o.get('lightmap_resolution',256)
shelf_max=max((bpy.data.objects[n].matrix_world@v.co).y for n in shifted[:3] for v in bpy.data.objects[n].data.vertices)
assert abs(shelf_max-19000)<1e-3,shelf_max
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()/'RoomFinish.blend'))
manifest['triangles']=sum(m['triangles'] for m in manifest['meshes'])
manifest['source_sha256']=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest()
(out/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'refinement.json').write_text(json.dumps({'removed_stitch_faces':removed,'bed_lightmap':repair,'bookcase_back_y':shelf_max,'wall_inside_y':19000,'shifted_meshes':shifted,'unchanged_meshes':sorted(set(protected)-changed)},indent=2))
print('Removed quilt stitch faces:',removed,'; bookcase back:',shelf_max,flush=True)
