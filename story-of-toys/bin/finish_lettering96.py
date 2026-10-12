"""Replace coincident zero-depth sign lettering with closed raised glyphs."""
import ast,bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin')]
from room_lightmaps import repair_mesh
from room_mesh_parts import split_mesh
from room_palette_uv import fit_palette_uv
SOURCE=ROOT/'output/room-final-96c';OUT=ROOT/'output/room-release-96';OUT.mkdir(exist_ok=True);assert not (OUT/'RoomFinish.blend').exists()
ns=dict(bpy=bpy,bmesh=bmesh,math=math,Vector=Vector,mat=bpy.data.materials['RoomToyPalette94'],GROUPS={},group='RoomPosterLetters96',CLOUD=1,changed=set(),labels=[])
mod=ast.parse((ROOT/'bin/build_room_blender.py').read_text());exec(compile(ast.Module(body=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name in ('text','finish')],type_ignores=[]),'letter-base','exec'),ns)
mod=ast.parse((ROOT/'bin/improve_room96.py').read_text().replace('rotation=rotation,extrude=2','rotation=rotation,extrude=8'));ns['ns']=ns;exec(compile(ast.Module(body=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name in ('components','drop_components','label')],type_ignores=[]),'letters','exec'),ns)
assert ns['drop_components']('RoomPosters',lambda lo,hi:abs(lo.x+22835)<2 and abs(hi.x+22835)<2)>0
for body,z,size,tile in [('LIGHTYEAR',16500,520,5),('DEEP SPACE',11700,470,5),('CODE',10900,760,2)]:ns['label'](body,(-22815,14000,z),size,tile,rotation=(math.pi/2,0,math.pi/2))
assert ns['drop_components']('RoomSecretUnderBed',lambda lo,hi:abs((lo.y+hi.y)/2+10068)<3 and hi.y-lo.y<4)>0
ns['group']='RoomClawLettering96';ns['label']('THE CLAW CLUB',(-14400,-10040,1180),175,5,rotation=(math.pi/2,0,math.pi))
assert ns['drop_components']('RoomSecretShelf',lambda lo,hi:abs((lo.y+hi.y)/2-17381)<3 and hi.y-lo.y<4)>0
ns['group']='RoomMoonLettering96';ns['label']('42',(17040,17360,1990),180,5)
changed=set(ns['changed']);reports=[]
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
 m=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();o['export_material']='RoomToyPalette94';o['export_collision']=False
 for o in split_mesh(o,18000):reports.append(repair_mesh(o,512));fit_palette_uv(o.data);changed.add(o.name)
for n in ns['changed']:
 o=bpy.data.objects[n];reports.append(repair_mesh(o,o.get('lightmap_resolution',512)))
manifest=json.loads((SOURCE/'room-manifest.json').read_text());base={r['name']:r for r in manifest['meshes']};rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 ps=[o.matrix_world@v.co for v in o.data.vertices];rows.append(dict(name=o.name,material=o.get('export_material',base.get(o.name,{}).get('material','RoomAtlas')),collision=o.get('export_collision',True),triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',256),bounds=[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)]))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(meshes=rows,triangles=sum(r['triangles'] for r in rows),source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest());(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2));detail=json.loads((SOURCE/'details96.json').read_text());detail['changed']=sorted((set(detail['changed'])|changed)-set(detail['removed']));detail['closed_lettering']=ns['labels'];(OUT/'details96.json').write_text(json.dumps(detail,indent=2));prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix.update({n:'Room09_' for n in changed});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2));print('Closed sign lettering saved',len(rows),'meshes')
