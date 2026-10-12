"""Prepare mipmapped print assets and limit small-toy lighting allocations."""
import bpy,bmesh,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import surface_signature
from room_palette_uv import fit_palette_uv
SOURCE=ROOT/'output/room-polish-94';OUT=ROOT/'output/room-final-94';assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend';assert not (OUT/'RoomFinish.blend').exists()
manifest=json.loads((SOURCE/'room-manifest.json').read_text());detail=json.loads((SOURCE/'detail.json').read_text());changed=set(detail['changed']);r={x['name']:x for x in manifest['meshes']}
# Preserve every source pixel and pad only the texture container for UE3 mip generation.
o=bpy.data.objects['RoomBedPrint'];node=next(n for n in o.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');old=node.image;w,h=old.size;assert (w,h)==(1444,1080)
p=np.empty(w*h*4,np.float32);old.pixels.foreach_get(p);p=p.reshape(h,w,4);dest=np.pad(p,((0,2048-h),(0,2048-w),(0,0)),mode='edge');assert np.array_equal(dest[:h,:w],p)
im=bpy.data.images.new('RoomBedding94',width=2048,height=2048,alpha=False);im.pixels.foreach_set(dest.ravel());im.filepath_raw=str(OUT/'RoomBedding94.tga');im.file_format='TARGA_RAW';im.save();im.pack();mat=o.data.materials[0].copy();mat.name='RoomBedding94';next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE').image=im;o.data.materials[0]=mat
for loop in o.data.uv_layers[0].data:loop.uv.x*=w/2048;loop.uv.y*=h/2048
o['export_material']='RoomBedding94';changed.add(o.name)
# The airplane shares the clean molded-plastic palette.
o=bpy.data.objects['RoomPlane'];fit_palette_uv(o.data)
o.data.materials.clear();o.data.materials.append(bpy.data.materials['RoomSurface94']);o['export_material']='RoomSurface94';changed.add(o.name)
# Replace all stacked rocket ink/backing with one textured, planar printed sheet.
o=bpy.data.objects['RoomPosters'];bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);drop=[]
while left:
 seed=left.pop();vs={seed};todo=[seed]
 while todo:
  for e in todo.pop().link_edges:
   for v in e.verts:
    if v in left:left.remove(v);vs.add(v);todo.append(v)
 lo=[min(v.co[k] for v in vs) for k in range(3)];hi=[max(v.co[k] for v in vs) for k in range(3)]
 if lo[0]>-18500 and hi[0]<-12800 and lo[1]>18000 and hi[1]<18855:drop.extend(vs)
bmesh.ops.delete(bm,geom=drop,context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update();changed.add(o.name)
im=bpy.data.images.load(str(OUT/'RoomRocketPrint94.tga'));im.pack();mat=bpy.data.materials.new('RoomRocketPrint94');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85
m=bpy.data.meshes.new('Flat rocket print');m.from_pydata([(-18050,18800,12600),(-13350,18800,12600),(-13350,18800,19600),(-18050,18800,19600)],[],[(0,1,2),(0,2,3)]);m.update();o=bpy.data.objects.new('RoomRocketPrint',m);bpy.context.scene.collection.objects.link(o);m.materials.append(mat)
for name,coords in [('UVMap',[(1,0),(0,0),(0,1),(1,1)]),('LightmapUV',[(.01,.01),(.99,.01),(.99,.99),(.01,.99)])]:
 layer=m.uv_layers.new(name=name)
 for f in m.polygons:
  for i in f.loop_indices:layer.data[i].uv=coords[m.loops[i].vertex_index]
o['export_material']='RoomRocketPrint94';o['export_collision']=False;o['lightmap_resolution']=128;changed.add(o.name)
# Only Slinky's dense wire charts need 2048; most toy parts need 512 or 1024.
lighting=[]
for row in detail['toys']['lightmaps']:
 name=row['mesh'];o=bpy.data.objects[name];old_res=o['lightmap_resolution'];new_res=2048 if row['lightmap']['isolated_faces']>500 else (512 if name.startswith(('RoomCheckpointHat','RoomCheckpointPlane','RoomCheckpointStart')) or len(o.data.polygons)<2000 else 1024)
 o['lightmap_resolution']=new_res;lighting.append(dict(mesh=name,before=old_res,after=new_res))
# Check the actual exported cap across every split head piece.
head_points=0
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('RoomAndyHead'):continue
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if p.z>16170:
   assert (abs(p.x-1500)/1650)**(2/.7)+(abs(p.y-1450)/1200)**(2/.7)<.83;head_points+=1
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 vs=[o.matrix_world@v.co for v in o.data.vertices];rows.append(dict(name=o.name,material=o.get('export_material',r.get(o.name,{}).get('material','RoomAtlas')),collision=o.get('export_collision',True),triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',256),bounds=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]))
assert len(rows)==71;assert all(x['triangles']*3<=65535 for x in rows)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(meshes=rows,triangles=sum(r['triangles'] for r in rows),source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest());(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
detail.update(changed=sorted(changed),preserved=sorted(set(detail['preserved'])-changed));detail['final']=dict(bedding_original=[w,h],bedding_padded=[2048,2048],original_pixels_unchanged=True,head_cap_vertices_checked=head_points,lighting_allocations=lighting,requested_room_lightmap_texels=sum(x['lightmap_resolution']**2 for x in rows));(OUT/'detail.json').write_text(json.dumps(detail,indent=2));print(json.dumps(detail['final']))
