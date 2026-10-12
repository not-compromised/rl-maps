"""Add a wall shelf above the bed and move the finish companion onto it."""
import bpy,sys,ast,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature
out=ROOT/'output/room-finish-92';source=ROOT/'output/room-environment-91'
assert Path(bpy.data.filepath).resolve()==source/'RoomFinish.blend'
assert not (out/'RoomFinish.blend').exists()
protected={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
mat=bpy.data.objects['RoomBed'].data.materials[0]
module=ast.parse((ROOT/'bin/build_room_blender.py').read_text())
helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','box')],type_ignores=[])
ns=dict(bpy=bpy,math=math,mat=mat,GROUPS={},group='RoomFinishShelf',CLOUD=1);exec(compile(helpers,'room-shapes','exec'),ns);box=ns['box']
box('Oak shelf',(-20375,-13300,16800),(4850,8600,400),0,75)
box('Back rail',(-22700,-13300,17300),(170,8500,600),0,40)
box('Front edge',(-17960,-13300,16700),(120,8480,260),0,35)
for y in (-16900,-9700):
 box('Wall bracket',(-22530,y,15400),(320,430,2400),5,50)
 box('Shelf support',(-20700,y,16530),(3780,440,260),5,45)
 brace=box('Diagonal brace',(-20900,y,15520),(3850,340,340),5,45)
 brace.rotation_euler[1]=-math.atan2(1780,3420)
for i,(y,w,h,tile) in enumerate([(-16900,440,1850,3),(-16350,500,2150,2),(-15770,420,1700,6),(-10380,450,2020,10),(-9820,500,1770,7)]):
 x=-22030;z=17000+h/2
 box('Book pages',(x,y,z),(1140,w-100,h-110),5,18)
 for side in (-1,1):box('Book cover',(x,y+side*(w/2-24),z),(1250,48,h),tile,16)
 box('Book spine',(x+600,y,z),(60,w,h),tile,24)
 for dz in (-h*.34,h*.34):box('Spine band',(x+635,y,z+dz),(12,w*.8,44),11,5)
# The gold restart pad is behind the arrival spot; book spines stay farther back.
parts=ns['GROUPS']['RoomFinishShelf'];bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='RoomFinishShelf'
bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for p in o.data.polygons:p.material_index=0
o.data.materials.clear();o.data.materials.append(mat)
while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
o['export_material']='RoomDecorAtlas';o['export_collision']=True
repair=repair_mesh(o,1024)
companion=bpy.data.objects['RoomCheckpointFinish']
for v in companion.data.vertices:v.co.z+=12325
companion.data.update()
for name,sig in protected.items():
 if name!='RoomCheckpointFinish':assert surface_signature(bpy.data.objects[name])==sig,name
manifest=json.loads((source/'room-manifest.json').read_text());manifest['meshes'].append(dict(name=o.name,material='RoomDecorAtlas',collision=True))
for row in manifest['meshes']:
 ob=bpy.data.objects[row['name']];vertices=[ob.matrix_world@v.co for v in ob.data.vertices]
 row.update(triangles=len(ob.data.polygons),lightmap_resolution=ob.get('lightmap_resolution',256),bounds=[[min(v[k] for v in vertices),max(v[k] for v in vertices)] for k in range(3)])
assert len(manifest['meshes'])==45
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
manifest['source_sha256']=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest();manifest['triangles']=sum(m['triangles'] for m in manifest['meshes'])
(out/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'shelf.json').write_text(json.dumps(dict(shelf_top_z=17000,finish_deck_z=17020,books=5,moved_companion='RoomCheckpointFinish',companion_z_shift=12325,unchanged_meshes=sorted(set(protected)-{'RoomCheckpointFinish'}),lightmap=repair),indent=2))
print('Saved shelf and finish companion; all other room surfaces unchanged')
