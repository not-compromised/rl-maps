"""Map the owner's unmodified reference frame onto the flat quilt surface."""
import bpy,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/room-reference-78/RoomFinish.blend'))
protected={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
img=bpy.data.images.load(str(ROOT/'assets/room-reference/buzz-bedding.png'))
assert img.pixels[0]>=0
# Container conversion only. Pixels and source dimensions are retained.
img.filepath_raw=str(out.resolve()/'RoomBuzzBedding.tga');img.file_format='TARGA_RAW';img.save();img.pack()
mat=bpy.data.materials.new('RoomBuzzBedding');mat.use_nodes=True
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.95
# Source quadrilateral lies wholly on the blue quilt. No frame pixels are edited.
width,height=img.size
corners=[(925,755),(1420,800),(1420,1070),(255,1070)]
# Build a grid so perspective mapping is continuous across the sheet.
import numpy as np
rows=[];rhs=[]
for (u,v),(x,y) in zip(((0,0),(1,0),(1,1),(0,1)),corners):
 rows += [[u,v,1,0,0,0,-x*u,-x*v],[0,0,0,u,v,1,-y*u,-y*v]];rhs += [x,y]
h=np.linalg.solve(np.array(rows),np.array(rhs))
def photo(u,v):
 d=h[6]*u+h[7]*v+1
 return ((h[0]*u+h[1]*v+h[2])/d/width,1-(h[3]*u+h[4]*v+h[5])/d/height)
n=20;verts=[];coords=[];faces=[]
for j in range(n+1):
 for i in range(n+1):
  u,v=i/n,j/n;verts.append((-20900+10300*u,11700-13700*v,4155));coords.append(photo(1-u,v))
for j in range(n):
 for i in range(n):
  a=j*(n+1)+i;faces.extend([(a,a+n+1,a+1),(a+1,a+n+1,a+n+2)])
mesh=bpy.data.meshes.new('Flat printed quilt');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('RoomBedPrint',mesh);bpy.context.scene.collection.objects.link(o);mesh.materials.append(mat)
o['export_material']='RoomBuzzBedding';o['export_collision']=True
uv=mesh.uv_layers.new(name='UVMap')
for f in mesh.polygons:
 for li in f.loop_indices:uv.data[li].uv=coords[mesh.loops[li].vertex_index]
lm=mesh.uv_layers.new(name='LightmapUV')
for f in mesh.polygons:
 for li in f.loop_indices:
  co=verts[mesh.loops[li].vertex_index];lm.data[li].uv=(.01+.98*(co[0]+20900)/10300,.01+.98*(co[1]+2000)/13700)
repair_mesh(o,512)
for name,sig in protected.items():assert surface_signature(bpy.data.objects[name])==sig,name
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()/'RoomFinish.blend'))
(out/'bedding.json').write_text(json.dumps({'source':'assets/room-reference/buzz-bedding.png','dimensions':list(img.size),'source_quad':corners,'mesh':o.name,'collision':True,'surface_z':4155,'limitations':'Screenshot resolution and baked-in shading; no invented artwork'},indent=2))
