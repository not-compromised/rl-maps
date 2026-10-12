"""Bake the facial material into a portable room atlas for the existing UDK material."""
import bpy,sys,json,hashlib
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);scene=bpy.context.scene
if (out/'BakedRoomAtlas.tga').exists() or (out/'AndyDetail-baked.blend').exists():raise RuntimeError('Choose a new atlas output directory')
out.mkdir(parents=True,exist_ok=True)
head=bpy.data.objects['RoomAndyHead'];source=head.data.materials[0];assert source.name.startswith('AndyFaceStudy')
material=source.copy();material.name='FaceAtlasBakeSource';nodes=material.node_tree.nodes;links=material.node_tree.links
mix=next(n for n in nodes if n.type=='MIX_RGB');emission=nodes.new('ShaderNodeEmission');links.new(mix.outputs[0],emission.inputs['Color']);links.new(emission.outputs[0],nodes.get('Material Output').inputs['Surface'])
target=bpy.data.images.new('RoomAtlasWithFace',width=4096,height=4096,alpha=False);target.colorspace_settings.name='sRGB'
node=nodes.new('ShaderNodeTexImage');node.image=target;nodes.active=node
bpy.ops.object.select_all(action='DESELECT');bpy.ops.mesh.primitive_plane_add(size=2);plane=bpy.context.object;plane.name='Temporary atlas baking plane';plane.data.materials.append(material)
scene.render.engine='CYCLES';scene.cycles.samples=1;bpy.ops.object.bake(type='EMIT',margin=0,use_clear=True)
target.filepath_raw=str(out/'BakedRoomAtlas.tga');target.file_format='TARGA_RAW';target.save();target.pack()
# Check that baking retained flat colors outside the face tile.
original=next(n.image for n in source.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.name.startswith('RoomAtlas'))
checks=[]
for tile in range(16):
 if tile==14:continue
 x=(tile%4)*256+128;y=(tile//4)*256+128
 a=original.pixels[(y*1024+x)*4:(y*1024+x)*4+3]
 b=target.pixels[((y*4+2)*4096+x*4+2)*4:((y*4+2)*4096+x*4+2)*4+3]
 error=max(abs(v-w) for v,w in zip(a,b));checks.append({'tile':tile,'max_channel_error':error})
# Patterned tiles interpolate slightly at the larger sampling grid.
assert all(c['max_channel_error']<.08 for c in checks),checks
bpy.data.objects.remove(plane,do_unlink=True)
baked=bpy.data.materials.new('RoomAtlasBaked');baked.use_nodes=True;tex=baked.node_tree.nodes.new('ShaderNodeTexImage');tex.image=target;baked.node_tree.links.new(tex.outputs['Color'],baked.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);baked.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65
head.data.materials[0]=baked
bpy.ops.wm.save_as_mainfile(filepath=str(out/'AndyDetail-baked.blend'))
(out/'atlas-bake.json').write_text(json.dumps({'size':[4096,4096],'source_material':source.name,'checks':checks,'tga_sha256':hashlib.sha256((out/'BakedRoomAtlas.tga').read_bytes()).hexdigest()},indent=2));print('Baked portable face atlas',flush=True)
