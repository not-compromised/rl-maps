"""Rebuild room surface materials and architectural edges around the accepted layout."""
import bpy,sys,math,json,hashlib,ast
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature
out=ROOT/'output/room-environment-91'
assert Path(bpy.data.filepath).resolve()==ROOT/'output/room-wall-89-clear/RoomFinish.blend'
assert not (out/'RoomFinish.blend').exists()
original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
# Linear working colors are encoded to sRGB by Blender's image writer.
colors=[(.35,.215,.115),(.205,.345,.505),(.48,.055,.048),(.035,.12,.29),(.76,.43,.25),(.70,.69,.62),(.21,.43,.09),(.32,.205,.345),(.10,.042,.016),(.017,.023,.03),(.06,.24,.37),(.70,.49,.18),(.60,.21,.065),(.075,.26,.11),(.76,.43,.25),(.42,.63,.78)]
N=2048;T=N//4;yy,xx=np.mgrid[0:T,0:T];u=xx/T;v=yy/T
atlas=np.ones((N,N,4),np.float32)
for i,color in enumerate(colors):
 tile=np.ones((T,T,3))*color
 if i==0:
  grain=.97+.018*np.sin(v*math.tau*33+1.6*np.sin(u*math.tau*1.5))+.01*np.sin(v*math.tau*91+u*3)
  tile*=grain[:,:,None]
 if i in (2,3):tile*=(.99+.006*np.cos(xx*math.pi)+.006*np.cos(yy*math.pi))[:,:,None]
 if i==1:
  for cx,cy,s in [(128,130,1),(380,364,.8)]:
   mask=np.zeros((T,T),bool)
   for dx,dy,r in [(-47,0,27),(-17,20,40),(23,32,49),(61,4,30)]:mask|=(xx-cx-dx*s)**2+(yy-cy-dy*s)**2<(r*s)**2
   mask &= yy>=cy-12*s
   tile[mask]=(.77,.78,.735)
 if i==15:
  tile=np.broadcast_to(np.array([.39,.58,.72])[None,None,:],(T,T,3)).copy()
  tile+=v[:,:,None]*np.array([.09,.075,.035])
  horizon=.105+.018*np.sin(u*17)+.009*np.sin(u*43)
  mask=v<horizon;tile[mask]=(.21,.29,.23)
  # Low, distant houses: gable, siding, framed attic window and shingle courses.
  for cx,width,base,height,col in [(.25,.22,.045,.17,(.28,.30,.32)),(.79,.26,.025,.13,(.31,.29,.26))]:
   ridge=base+height*(1-abs(u-cx)/width)
   roof=(abs(u-cx)<width)&(v>base)&(v<ridge)
   tile[roof]=np.array(col)
   shingle=roof&(np.mod(v*130,1)<.10);tile[shingle]*=.93
   fascia=roof&((ridge-v)<.006);tile[fascia]=(.40,.42,.40)
   wall=(abs(u-cx)<width*.79)&(v<=base);tile[wall]=(.46,.46,.39)
   attic=(abs(u-cx)<.022)&(v>base+.015)&(v<base+.06)
   tile[attic]=(.58,.61,.57)
   pane=(abs(u-cx)<.015)&(v>base+.021)&(v<base+.054);tile[pane]=(.24,.34,.40)
 atlas[(i//4)*T:(i//4+1)*T,(i%4)*T:(i%4+1)*T,:3]=tile

def image_material(name,pixels):
 h,w,_=pixels.shape;im=bpy.data.images.new(name,width=w,height=h,alpha=False);im.pixels.foreach_set(pixels.astype(np.float32).ravel());im.filepath_raw=str(out/(name+'.tga'));im.file_format='TARGA_RAW';im.save();im.pack()
 mat=bpy.data.materials.new(name);mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
 return mat
mat=image_material('RoomEnvironment91',atlas)
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('export_material')=='RoomDecorAtlas':o.data.materials.clear();o.data.materials.append(mat)
# One continuous floor surface; staggered joints and grain live in its diffuse map.
F=4096;y,x=np.mgrid[0:F,0:F];wx=x/F*46080;wy=y/F*38000
rows=np.floor(wy/760).astype(int);shift=(rows%4)*1550
boards=np.floor((wx+shift)/6200).astype(int);local=(wx+shift)%6200;across=wy%760
rng=np.random.default_rng(91);variation=rng.uniform(.92,1.07,(55,10))[rows,boards]
grain=.97+.02*np.sin(across*.13+2*np.sin(local*.0016))+.008*np.sin(across*.7+local*.002)
seams=np.minimum(across,760-across)<10;seams|=np.minimum(local,6200-local)<9
value=variation*grain;value[seams]*=.68
floor=np.ones((F,F,4),np.float32);floor[:,:,:3]=value[:,:,None]*np.array((.32,.185,.095))
floor_mat=image_material('RoomOakFloor91',floor)
for name in ('RoomFloor','RoomCeiling'):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
names={'finish','box'};module=ast.parse((ROOT/'bin/build_room_blender.py').read_text());helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns=dict(bpy=bpy,math=math,mat=mat,GROUPS={},group='RoomFloor',CLOUD=1);exec(compile(helpers,'room-shapes','exec'),ns);box=ns['box']
o=box('Continuous oak floor',(0,0,-100),(46080,38000,200),0)
o.data.materials.clear();o.data.materials.append(floor_mat)
for face in o.data.polygons:
 for li in face.loop_indices:
  p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
  o.data.uv_layers[0].data[li].uv=((p.x+23040)/46080,(p.y+19000)/38000)
ns['group']='RoomCeiling';box('Warm painted ceiling',(0,0,32100),(46480,38400,200),5)
for z,width,height in [(31650,170,650),(31280,290,160),(31180,390,110)]:
 for side in (-1,1):
  box('Side crown',(side*(23040-width/2),0,z),(width,38000,height),5,20)
  box('End crown',(0,side*(19000-width/2),z),(46080-2*width,width,height),5,20)
reports=[]
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 o['export_material']='RoomOakFloor91' if name=='RoomFloor' else 'RoomDecorAtlas'
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 reports.append(repair_mesh(o,2048 if name=='RoomFloor' else 512))
o=bpy.data.objects['RoomToys'];o['export_material']='RoomDecorAtlas';o.data.materials.clear();o.data.materials.append(mat)
# Map both outdoor backing panels across the sky tile instead of sampling its center.
o=bpy.data.objects['RoomWindow'];uv=o.data.uv_layers[0];sky_faces=0
for poly in o.data.polygons:
 if all(int(uv.data[i].uv.x*4)==3 and int(uv.data[i].uv.y*4)==3 for i in poly.loop_indices):
  for li in poly.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
   if p.x < -23000:u=(p.y-2000)/9000;v=(p.z-8100)/13000
   else:u=(p.x+8800)/12000;v=(p.z-8750)/14500
   uv.data[li].uv=((3+.005+.99*u)/4,(3+.005+.99*v)/4)
  sky_faces+=1
assert sky_faces==24,sky_faces
for n,s in original.items():
 if n not in {'RoomFloor','RoomCeiling','RoomWindow'}:assert surface_signature(bpy.data.objects[n])==s,n
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
(out/'environment.json').write_text(json.dumps({'changed_geometry':['RoomFloor','RoomCeiling'],'changed_uv':['RoomWindow'],'palette_objects':[o.name for o in bpy.data.objects if o.type=='MESH' and o.get('export_material')=='RoomDecorAtlas'],'preserved_surfaces':{n:s for n,s in original.items() if n not in {'RoomFloor','RoomCeiling','RoomWindow'}},'lightmap_checks':reports,'floor_surface_z':0,'ring_revision':90},indent=2))
print('Environment91 saved',reports)
