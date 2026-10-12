"""Repair exterior winding and the owner's room furniture changes on revision92."""
import bpy,bmesh,sys,json,math,ast,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature
out=ROOT/'output/room-repair-93';source=ROOT/'output/room-finish-92'
assert Path(bpy.data.filepath).resolve()==source/'RoomFinish.blend'
assert not (out/'RoomFinish.blend').exists()
original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
changed={'RoomAndyHat','RoomDesk','RoomBed','RoomWalls','RoomWallsPart2','RoomToys','RoomWagonChest','RoomNurseryCabinet'}
repairs=[]
for name in ('RoomAndyHat','RoomDesk','RoomBed'):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 repairs.append(dict(mesh=name,lightmap=repair_mesh(o,o.get('lightmap_resolution',1024))))
def components(bm):
 left=set(bm.verts)
 while left:
  seed=left.pop();vs={seed};todo=[seed]
  while todo:
   for e in todo.pop().link_edges:
    for v in e.verts:
     if v in left:left.remove(v);vs.add(v);todo.append(v)
  yield vs
removed={}
for name in ('RoomWalls','RoomWallsPart2'):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);delete=[]
 for vs in components(bm):
  lo=[min(v.co[k] for v in vs) for k in range(3)];hi=[max(v.co[k] for v in vs) for k in range(3)]
  if lo[0]>8000 and hi[0]<20000 and hi[1]>-18800 and hi[1]<-17500 and hi[2]<24000:delete.extend(vs)
 removed[name]=len(delete);bmesh.ops.delete(bm,geom=delete,context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update()
o=bpy.data.objects['RoomToys'];bm=bmesh.new();bm.from_mesh(o.data);moved=0
for vs in components(bm):
 lo=[min(v.co[k] for v in vs) for k in range(3)];hi=[max(v.co[k] for v in vs) for k in range(3)]
 if lo[0]>6500 and hi[0]<17000 and hi[1]<-6000 and lo[1]>-14500:
  for v in vs:
   x,y,z=v.co;v.co=(19575+y+10500,-11500-(x-11600),z)
  moved+=1
assert moved==22,moved
bm.to_mesh(o.data);bm.free();o.data.update()
for name in ('RoomNurseryCabinet','RoomWagonChest'):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
mat=bpy.data.materials['RoomEnvironment91'];scene=bpy.context.scene
module=ast.parse((ROOT/'bin/build_room_blender.py').read_text());helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('finish','box','ell','rod')],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,mat=mat,scene=scene,GROUPS={},group='RoomDoor',CLOUD=1);exec(compile(helpers,'room-shapes','exec'),ns)
box,ell,rod=[ns[n] for n in ('box','ell','rod')];WOOD,RED,WHITE,BLUE,YELLOW,GREEN=0,2,5,10,11,13
# Solid six-panel painted door; the shadow recess is physical, not blue glazing.
box('Solid door slab',(14000,-18840,11700),(10800,210,23400),WHITE,60)
for x in (8390,19610):box('Door casing',(x,-18580,11800),(420,480,23600),WHITE,45)
box('Door header',(14000,-18580,23600),(11600,480,450),WHITE,45)
for x in (11200,16800):
 for z,h in ((4400,5900),(11700,6200),(19300,4300)):
  box('Painted recessed panel',(x,-18705,z),(4300,80,h),WHITE,60)
  for dx in (-2300,2300):box('Panel side molding',(x+dx,-18600,z),(160,170,h+320),WHITE,40)
  for dz in (-h/2-80,h/2+80):box('Panel cross molding',(x,-18600,z+dz),(4740,170,160),WHITE,40)
box('Knob backplate',(18150,-18545,10900),(540,100,1000),YELLOW,90)
rod('Knob stem',(18150,-18500,10900),(18150,-18100,10900),110,YELLOW,verts=24)
ell('Brass knob',(18150,-17990,10900),(250,230,250),YELLOW,32,20)
ns['group']='RoomWagonChest';cx,cy=9300,15535
box('Green wagon chest',(cx,cy,1450),(5600,3700,2800),GREEN,75)
box('Blue wagon plinth',(cx,cy,200),(5900,3900,400),BLUE,40)
# Closed barrel lid along the chest's length; hoops span its short dimension.
verts=[];n=48
for x in (cx-2800,cx+2800):
 for j in range(n+1):
  a=j*math.pi/n;verts.append((x,cy+1850*math.cos(a),2850+1550*math.sin(a)))
faces=[tuple(reversed(range(n+1))),tuple(range(n+1,2*(n+1)))];faces += [(j,j+1,n+2+j,n+1+j) for j in range(n)];faces.append((0,n+1,2*n+1,n))
mesh=bpy.data.meshes.new('Brown covered lid');mesh.from_pydata(verts,[],faces);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
o=bpy.data.objects.new('Brown tarp',mesh);scene.collection.objects.link(o);ns['finish'](o,o.name,WOOD,True)
for x in (cx-2350,cx,cx+2350):
 for j in range(n):
  a,b=j*math.pi/n,(j+1)*math.pi/n
  rod('Brown canvas seam',(x,cy+1865*math.cos(a),2850+1565*math.sin(a)),(x,cy+1865*math.cos(b),2850+1565*math.sin(b)),25,WOOD,verts=6)
for x in (cx-1750,cx+1750):
 rod('Painted wheel',(x,cy-1895,1250),(x,cy-1930,1250),1040,RED,verts=48)
 rod('Wheel inset',(x,cy-1935,1250),(x,cy-1950,1250),900,BLUE,verts=48)
 for j in range(12):
  a=j*math.tau/12;rod('Painted spoke',(x,cy-1970,1250),(x+860*math.cos(a),cy-1970,1250+860*math.sin(a)),35,YELLOW,verts=6)
 rod('Wheel hub',(x,cy-1970,1250),(x,cy-2010,1250),180,RED,verts=24)
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for p in o.data.polygons:p.material_index=0
 o.data.materials.clear();o.data.materials.append(mat)
 while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 o['export_material']='RoomDecorAtlas';o['export_collision']=True;repairs.append(dict(mesh=name,lightmap=repair_mesh(o,1024)))
for name,sig in original.items():
 if name not in changed:assert surface_signature(bpy.data.objects[name])==sig,name
manifest=json.loads((source/'room-manifest.json').read_text());manifest['meshes']=[m for m in manifest['meshes'] if m['name']!='RoomNurseryCabinet'];manifest['meshes'].append(dict(name='RoomDoor',material='RoomDecorAtlas',collision=True))
for row in manifest['meshes']:
 o=bpy.data.objects[row['name']];vs=[o.matrix_world@v.co for v in o.data.vertices];row.update(triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',256),bounds=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)])
assert len(manifest['meshes'])==45
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
manifest['source_sha256']=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest();manifest['triangles']=sum(m['triangles'] for m in manifest['meshes']);(out/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'repair.json').write_text(json.dumps(dict(changed=sorted(changed|{'RoomDoor'}),removed=['RoomNurseryCabinet'],preserved=sorted(set(original)-changed),door_removed_vertices=removed,chest_components=moved,chest_wall_gap=40,lightmaps=repairs),indent=2))
print('Saved revision93 furniture and exterior face repairs')
