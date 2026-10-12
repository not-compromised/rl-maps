"""Repair exposed head cap, atlas edge sampling and coincident scenery faces."""
import bpy,bmesh,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin')]
from room_mesh_parts import split_mesh
from room_palette_uv import fit_palette_uv
from room_lightmaps import surface_signature,repair_mesh
SOURCE=ROOT/'output/room-toys-94b';OUT=ROOT/'output/room-polish-94';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
changed={'RoomAndy','RoomAndyHat','RoomAndyHead','RoomDesk','RoomWagonChest'}
# Solid colors on cloth/plastic avoid sampling atlas borders and minuscule weave lines.
colors=[(.52,.27,.095),(.22,.52,.79),(.57,.045,.03),(.045,.115,.29),(.87,.55,.35),(.9,.91,.84),(.30,.66,.07),(.34,.09,.59),(.15,.052,.018),(.014,.021,.031),(.07,.3,.66),(.98,.67,.06),(.84,.21,.025),(.08,.30,.11),(.87,.55,.35),(.76,.86,.91)]
N=256;pixels=np.ones((N,N,4),np.float32)
for i,c in enumerate(colors):pixels[(i//4)*64:(i//4+1)*64,(i%4)*64:(i%4+1)*64,:3]=c
im=bpy.data.images.new('RoomSurface94',width=N,height=N,alpha=False);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(OUT/'RoomSurface94.tga');im.file_format='TARGA_RAW';im.save();im.pack()
mat=bpy.data.materials.new('RoomSurface94');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
for name in ('RoomAndy','RoomAndyHat'):
 o=bpy.data.objects[name];fit_palette_uv(o.data)
 o.data.materials.clear();o.data.materials.append(mat);o['export_material']='RoomSurface94'
head=bpy.data.objects['RoomAndyHead'];moved=0
for v in head.data.vertices:
 p=head.matrix_world@v.co
 if p.z<15900:continue
 q=(abs(p.x-1500)/1650)**(2/.7)+(abs(p.y-1450)/1200)**(2/.7)
 if q>.82:
  factor=(.82/q)**(.7/2);weight=min(1,max(0,(p.z-15900)/250));factor=1+(factor-1)*weight
  p.x=1500+(p.x-1500)*factor;p.y=1450+(p.y-1450)*factor;v.co=head.matrix_world.inverted()@p;moved+=1
head.data.update()
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
removed={}
for name in ('RoomDesk','RoomWagonChest'):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);seen=set();drop=[]
 for f in bm.faces:
  key=tuple(sorted(tuple(round(x,3) for x in v.co) for v in f.verts))
  if key in seen:drop.append(f)
  else:seen.add(key)
 removed[name]=len(drop);bmesh.ops.delete(bm,geom=drop,context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update()
parts=[];lighting=[]
for name in sorted(changed):
 o=bpy.data.objects[name]
 for piece in split_mesh(o,triangle_limit=20000):
  # Existing padded charts remain valid after component partitioning.
  lighting.append(repair_mesh(piece,piece.get('lightmap_resolution',1024)));parts.append(piece.name)
for n,sig in original.items():
 if n not in changed:assert surface_signature(bpy.data.objects[n])==sig,n
manifest=json.loads((SOURCE/'room-manifest.json').read_text());rows=[r for r in manifest['meshes'] if r['name'] not in changed]
for name in parts:
 o=bpy.data.objects[name];vs=[o.matrix_world@v.co for v in o.data.vertices];rows.append(dict(name=name,material=o.get('export_material','RoomAtlas'),collision=o.get('export_collision',True),triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',1024),bounds=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]))
assert all(len(o.data.loops)<=65535 for o in bpy.data.objects if o.type=='MESH')
for v in head.data.vertices:
 p=head.matrix_world@v.co
 if p.z>16170:assert (abs(p.x-1500)/1650)**(2/.7)+(abs(p.y-1450)/1200)**(2/.7)<.83
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(meshes=rows,triangles=sum(r['triangles'] for r in rows),source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest());(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
r=json.loads((SOURCE/'detail.json').read_text());r['changed']=sorted(set(r['changed'])|set(parts));r['preserved']=sorted(set(r['preserved'])-changed);r['surfaces']=dict(head_vertices_adjusted=moved,removed_duplicate_faces=removed,parts=parts,lightmaps=lighting);(OUT/'detail.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(parts=parts,removed=removed,head=moved,total_meshes=len(rows))))
