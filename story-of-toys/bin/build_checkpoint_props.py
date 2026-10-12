"""Replace course slabs with thin room props and a golden restart alien."""
import ast,bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'bin')]
from course import DECKS
from checkpoint_props import *
from room_lightmaps import repair_mesh,surface_signature
from room_palette_uv import fit_palette_uv
SOURCE=ROOT/'output/room-final-94c';OUT=ROOT/'output/room-checkpoints-95';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
baseline={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
mat=bpy.data.materials['RoomToyPalette94'];module=ast.parse((ROOT/'bin/build_room_blender.py').read_text())
helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'finish','box','ell','rod','torus'}],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,mat=mat,GROUPS={},group='',CLOUD=1);exec(compile(helpers,'checkpoint-shapes','exec'),ns)
box=ns['box'];rod=ns['rod']
for i in BOOK_CHECKPOINTS:
 ns['group']=f'RoomCheckpointBook{i}';x,y,_=DECKS[i];z=SUPPORT_TOPS[i];color={4:7,5:3,7:10}[i]
 box('Lower cloth cover',(x,y,z+5),(2260,2380,10),color,4)
 box('Cream page edges',(x+12,y,z+35),(2210,2320,50),5,4)
 box('Upper cloth cover',(x,y,z+65),(2260,2380,10),color,4)
 box('Cloth spine',(x-1120,y,z+35),(20,2380,60),color,5)
 for dy in (-840,840):box('Spine gilt band',(x-1132,y+dy,z+35),(5,45,46),11,2)
 # A broad title panel avoids tiny text and fine texture lines.
 box('Cover emblem',(x,y+580,z+72),(230,440,4),11,2)
ns['group']='RoomCheckpointClipboard';x,y,_=DECKS[2];z=SUPPORT_TOPS[2]
box('Clipboard backing',(x,y,z+10),(2240,2380,20),8,10)
box('Paper sheet',(x,y-35,z+24),(2060,2140,8),5,3)
box('Metal clip base',(x,y+1040,z+34),(720,240,16),15,7)
box('Metal clip arch',(x,y+1110,z+53),(570,85,34),15,12)
for dx in (-310,310):box('Clip hinge',(x+dx,y+1020,z+42),(55,150,30),15,8)
# Short marks suggest a checklist without tiny lettering or high-frequency hatching.
for dy in (-650,-310,30,370):
 box('Checklist square',(x-620,y+dy,z+30),(90,90,4),10,2)
 box('Checklist line',(x-160,y+dy,z+30),(620,24,4),15,2)
reports=[];added=[]
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.035);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 reports.append(dict(name=name,lightmap=repair_mesh(o,256)));fit_palette_uv(o.data)
 o['export_material']='RoomToyPalette94';o['export_collision']=True;added.append(name)
# The existing single alien already has repaired UVs and a recognizable face.
sources=[bpy.data.objects[n] for n in ('RoomCheckpointHat','RoomCheckpointHatPart2')]
points=[source.matrix_world@v.co for source in sources for v in source.data.vertices]
lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]));scale=GOLDEN_ALIEN_HEIGHT/(hi[2]-lo[2]);copies=[]
for source in sources:
 o=source.copy();o.data=source.data.copy();bpy.context.scene.collection.objects.link(o)
 for v,original in zip(o.data.vertices,source.data.vertices):v.co=Vector(GOLDEN_ALIEN_BASE)+(source.matrix_world@original.co-center)*scale
 o.matrix_world.identity();copies.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in copies:o.select_set(True)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();o=bpy.context.object;o.name='RoomGoldenAlien'
o.data.update()
uv=o.data.uv_layers[0].data
for face in o.data.polygons:
 mean=sum((uv[i].uv for i in face.loop_indices),Vector((0,0)))/3
 tile=(min(3,int(mean.x*4)),min(3,int(mean.y*4)));index=tile[0]+4*tile[1]
 if index not in (5,9):
  old=Vector(((tile[0]+.5)/4,(tile[1]+.5)/4));new=Vector(((11%4+.5)/4,(11//4+.5)/4))
  for i in face.loop_indices:uv[i].uv+=new-old
added.append(o.name);o['export_collision']=True;o['export_material']='RoomToyPalette94'
for name,sig in baseline.items():assert surface_signature(bpy.data.objects[name])==sig,name
manifest=json.loads((SOURCE/'room-manifest.json').read_text());rows=[]
for name in added:
 o=bpy.data.objects[name];points=[o.matrix_world@v.co for v in o.data.vertices]
 rows.append(dict(name=name,material='RoomToyPalette94',collision=True,triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',512),bounds=[[min(v[k] for v in points),max(v[k] for v in points)] for k in range(3)]))
assert all(r['triangles']*3<65535 for r in rows)
manifest['meshes']+=rows;manifest['triangles']=sum(r['triangles'] for r in manifest['meshes'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'))
manifest['source_sha256']=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest();(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix.update({n:'Room08_' for n in added});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2))
(OUT/'checkpoint-props.json').write_text(json.dumps(dict(added=rows,preserved=list(baseline),lightmaps=reports),indent=2));print(json.dumps(rows))
