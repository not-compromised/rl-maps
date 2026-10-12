"""Finish room furniture around the saved character without rebuilding it."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature,overlapping_faces
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
source=ROOT/'bin/build_room_blender.py';code=source.read_text()
ns={'__file__':str(source),'__name__':'room_finish'}
exec(compile(code[:code.index('# Small plank pieces')],str(source),'exec'),ns)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/room-art-63/AndyDetail-baked.blend'))
scene=bpy.context.scene
mat=bpy.data.objects['RoomFloor'].data.materials[0]
ns.update(scene=scene,mat=mat,GROUPS={})
box,rod,ell,text,torus=[ns[n] for n in ('box','rod','ell','text','torus')]
WOOD,CLOUD,RED,DENIM,SKIN,WHITE,GREEN,PURPLE,HAIR,BLACK,BLUE,YELLOW,ORANGE,DARKGREEN,FACE_SKIN,GLASS=range(16)
protected={n:surface_signature(bpy.data.objects[n]) for n in ('RoomAndy','RoomAndyHead','RoomCheckpointHat')}

def group(name):ns['group']=name

# Deep door panels and a working-height brass knob give the blank wall scale.
group('RoomWalls')
box('Bedroom door',(14000,-18840,11700),(10800,210,23400),WHITE,95)
for x in (8390,19610):box('Door casing',(x,-18580,11800),(420,480,23600),WHITE,45)
box('Door header',(14000,-18580,23600),(11600,480,450),WHITE,45)
for x in (11100,16900):
 for z,h in ((5200,6700),(15800,10200)):
  box('Recessed door panel',(x,-18710,z),(4600,70,h),GLASS,100)
  for xx in (x-2400,x+2400):box('Panel trim',(xx,-18630,z),(140,110,h+250),WHITE,35)
  for zz in (z-h/2,z+h/2):box('Panel trim',(x,-18630,zz),(4900,110,140),WHITE,35)
rod('Door knob plate',(18200,-18700,10900),(18200,-18480,10900),360,YELLOW)
rod('Door knob spindle',(18200,-18480,10900),(18200,-18150,10900),150,YELLOW)
ell('Brass door knob',(18200,-18020,10900),(270,260,270),YELLOW)
# A framed rocket illustration above the bed, facing into the room.
box('Space poster frame',(-22880,6200,17700),(140,10100,10300),WHITE,50)
box('Space poster blue',(-22790,6200,17700),(35,9450,9650),DENIM)
rod('Poster rocket',(-22710,5900,15300),(-22710,5900,19400),420,WHITE)
ell('Poster nose',(-22710,5900,19600),(100,420,750),RED)
box('Poster rocket fin',(-22690,5900,15400),(70,2300,600),RED,80)
ell('Poster rocket window',(-22620,5900,18200),(80,240,240),BLUE)
for y,z in ((2800,21000),(8100,20300),(9200,16200),(3800,14300),(8400,14500)):
 for a in (0,math.pi/2):
  dy,dz=250*math.cos(a),250*math.sin(a)
  rod('Poster star',(-22690,y-dy,z-dz),(-22690,y+dy,z+dz),45,YELLOW,verts=8)
# Thin drawing sheets and pencils sit behind the clear desk landing.
group('RoomDesk')
for j in range(3):box('Drawing paper',(-200,15950,7775+j*12),(2500,1500,12),WHITE,rot=.10+j*.03)
for j,tile in enumerate((RED,BLUE,YELLOW,GREEN)):
 rod('Crayon',(-800+j*520,15400,7870),(0+j*520,15700,7870),65,tile,verts=12)
 rod('Crayon tip',(0+j*520,15700,7870),(160+j*520,15760,7870),65,tile,r2=0,verts=12)
box('Wood ruler',(-3900,16400,7780),(2600,300,45),YELLOW,15)
for j in range(13):box('Ruler tick',(-5100+j*200,16310,7806),(18,110 if j%5 else 200,4),BLACK)
rod('Pencil cup',(-8500,15500,7750),(-8500,15500,8640),360,RED,verts=32)
for j,tile in enumerate((YELLOW,BLUE,GREEN,ORANGE,PURPLE)):
 x=-8700+j*95;y=15500+(j%2)*160
 rod('Colored pencil',(x,y,8240),(x+(j-2)*90,y,9600+j*80),42,tile,verts=8)
 rod('Pencil point',(x+(j-2)*90,y,9600+j*80),(x+(j-2)*90,y,9790+j*80),42,WOOD,r2=0,verts=8)
# The shelf ends coincided with the upright sides, producing dark seams.
shelf=bpy.data.objects['RoomShelves'].data
parents=list(range(len(shelf.vertices)))
def root(i):
 while parents[i]!=i:
  parents[i]=parents[parents[i]];i=parents[i]
 return i
for edge in shelf.edges:
 a,b=map(root,edge.vertices);parents[b]=a
components={}
for vertex in shelf.vertices:components.setdefault(root(vertex.index),[]).append(vertex)
for vertices in components.values():
 if max(v.co.z for v in vertices)-min(v.co.z for v in vertices)>20000:
  center=sum(v.co.x for v in vertices)/len(vertices)
  for vertex in vertices:vertex.co.x=center+(vertex.co.x-center)*1.25
shelf.update()

# Populate the rear of the checkpoint shelves, leaving the front landings clear.
group('RoomShelves')
for z in (10225,20225):
 for j in range(4):
  x=16000+j*420;h=1650+(j%3)*280
  box('Checkpoint shelf book',(x,14200,z+h/2),(350,2000,h),[BLUE,RED,YELLOW,DARKGREEN,PURPLE][j])
  for zz in (z+200,z+h-200):box('Book spine band',(x,13180,zz),(330,25,45),WHITE)
# Toy chest edge strips, latch and a scattered set of flat wooden tracks.
group('RoomToys')
for x in (7300,15900):box('Chest corner trim',(x,-13520,2150),(190,170,4000),BLUE,45)
box('Chest latch',(11600,-13740,4200),(600,130,800),YELLOW,60)
rod('Latch pin',(11250,-13840,4340),(11950,-13840,4340),80,HAIR)
for i in range(4):
 x=10700+i*2100
 for y in (-3100,-900):box('Wooden track rail',(x,y,85),(2100,150,160),WOOD,25)
 for xx in (x-650,x+250):box('Track sleeper',(xx,-2000,35),(160,2600,70),HAIR,15)

# Reuse modeled toys at different checkpoints, with each base on its furniture.
companions=[('RoomCheckpointDesk','RoomWoody',(-1500,15600,7750),.46),
 ('RoomCheckpointLowerShelf','RoomHamm',(20000,12700,10225),.43),
 ('RoomCheckpointUpperShelf','RoomRex',(20100,12700,20225),.40),
 ('RoomCheckpointBed','RoomSlinky',(-18000,900,4165),.55),
 ('RoomCheckpointFinish','RoomBuzz',(-18100,11900,4675),.52)]
for dest,src,pos,scale in companions:
 original=bpy.data.objects[src];old=bpy.data.objects[dest];bpy.data.objects.remove(old,do_unlink=True)
 obj=original.copy();obj.data=original.data.copy();scene.collection.objects.link(obj);obj.name=dest
 world=[obj.matrix_world@v.co for v in obj.data.vertices]
 center=Vector(((min(v.x for v in world)+max(v.x for v in world))/2,(min(v.y for v in world)+max(v.y for v in world))/2,min(v.z for v in world)))
 obj.matrix_world=Matrix.Translation(Vector(pos))@Matrix.Scale(scale,4)@Matrix.Translation(-center)@obj.matrix_world
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 ns['GROUPS'][dest]=[]

# Flatten only the intended hat driving band; keep the side curl elsewhere.
hat=bpy.data.objects['RoomAndyHat']
stitch_vertices=set()
for face in hat.data.polygons:
 uv=hat.data.uv_layers[0].data[face.loop_start].uv
 if int(uv.x*4)+4*int(uv.y*4)==WHITE:stitch_vertices.update(face.vertices)
for vertex in hat.data.vertices:
 x,y=vertex.co.x-1500,vertex.co.y-1000
 distance=abs(y+2400)
 blend=max(0,min(1,(750-distance)/200));blend=blend*blend*(3-2*blend)
 radius=math.sqrt((x/3900)**2+(y/3800)**2)
 edge=max(0,min(1,(radius-.82)/.18));edge=edge*edge*(3-2*edge)
 delta=edge*(1050*(abs(x)/3900)**3-300*max(0,-y/3800)**4+180*max(0,y/3800)**3)
 vertex.co.z-=blend*(delta+(35 if vertex.index in stitch_vertices else 0))
hat.data.update()
ns['GROUPS']['RoomAndyHat']=[]

report=[]
for name,parts in ns['GROUPS'].items():
 obj=bpy.data.objects[name]
 if parts:
  bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
  for p in parts:p.select_set(True)
  bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
  for p in obj.data.polygons:p.material_index=0
  obj.data.materials.clear();obj.data.materials.append(mat)
  while len(obj.data.uv_layers)>1:obj.data.uv_layers.remove(obj.data.uv_layers[-1])
  obj.data.uv_layers.new(name='LightmapUV');obj.data.uv_layers.active_index=1
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
  modifier=obj.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=modifier.name)
 assert len(obj.data.polygons)<60000,(name,len(obj.data.polygons))
 report.append(repair_mesh(obj,max(obj.get('lightmap_resolution',256),512 if name in ('RoomWalls','RoomDesk','RoomShelves','RoomToys') else 256)))
 print('Finished',name,flush=True)
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name not in ns['GROUPS'] and (overlapping_faces(obj) or any(face.area < 1e-6 for face in obj.data.polygons)):
  report.append(repair_mesh(obj,obj.get('lightmap_resolution',256)))
  print('Repaired existing lightmap',obj.name,flush=True)
for n,sig in protected.items():assert surface_signature(bpy.data.objects[n])==sig,n
from room_mesh_parts import split_mesh
split_shelves=split_mesh(bpy.data.objects['RoomShelves'])
report=[row for row in report if row['name']!='RoomShelves']
for obj in split_shelves:
 report.append(dict(name=obj.name,triangles=len(obj.data.polygons),lightmap_resolution=obj['lightmap_resolution'],surface_sha256=surface_signature(obj)))
(out/'finish-manifest.json').write_text(json.dumps({'changed':report,'preserved_character':protected},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
print('Room finish saved',flush=True)
