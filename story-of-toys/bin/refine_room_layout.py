"""Place bedside furniture and reference props without rebuilding accepted meshes."""
import bpy, math, sys, json, ast, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import surface_signature, repair_mesh
source=ROOT/'output/room-reference-87/RoomFinish.blend'
assert Path(bpy.data.filepath).resolve()==source.resolve(), 'Open the accepted revision87 source before applying this pass'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='ff4d4af72494f9a2566a307ad381eed3de91cd6d4d22c3e6aac0df34431aa477'
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
scene=bpy.context.scene
original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
# Reuse the existing shape helpers and packed palette without regenerating textures.
names={'finish','box','ell','rod','text','torus'}
module=ast.parse((ROOT/'bin/build_room_blender.py').read_text())
helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,scene=scene,mat=bpy.data.materials['RoomDecorAtlas'],GROUPS={},group='RoomDresser',CLOUD=1)
exec(compile(helpers,'room-shapes','exec'),ns)
box,ell,rod,text=[ns[n] for n in ('box','ell','rod','text')]
WOOD,CLOUD,RED,DENIM,SKIN,WHITE,GREEN,PURPLE,HAIR,BLACK,BLUE,YELLOW,ORANGE,DARKGREEN,FACE_SKIN,GLASS=range(16)

def move(name,offset):
 for v in bpy.data.objects[name].data.vertices:v.co+=Vector(offset)
 bpy.data.objects[name].data.update()

# The nightstand faces the room, alongside the pillow end of the bed.
o=bpy.data.objects['RoomNightstand'];old=Vector((-11000,17100,0));new=Vector((-8150,9500,0))
for v in o.data.vertices:
 p=v.co-old;v.co=new+Vector((-p.y,p.x,p.z))
o.data.update()
move('RoomSlinky',(2100,-3600,0))
move('RoomWagonChest',(1700,31500,0))
for v in bpy.data.objects['RoomWagonChest'].data.vertices:
 v.co.x=18600-v.co.x;v.co.y=31200-v.co.y
bpy.data.objects['RoomWagonChest'].data.update()
move('RoomAliens',(0,-4600,0))
# Tall cream dresser with two small drawers above three full-width drawers.
# Its front faces positive X, matching the adjacent nightstand.
def B(label,p,s,tile,bevel=0):
 x,y,z=p;sx,sy,sz=s
 return box(label,(-8100-y,4200+x,z),(sy,sx,sz),tile,bevel)
def E(label,p,s,tile):
 x,y,z=p;sx,sy,sz=s
 return ell(label,(-8100-y,4200+x,z),(sy,sx,sz),tile,24,16)
B('Cream dresser case',(0,0,3050),(5600,2800,5700),WHITE,120)
B('Rounded dresser top',(0,0,6030),(5900,3100,360),WHITE,120)
B('Dresser toe plinth',(0,0,230),(5580,2750,460),WOOD,50)
for z in (1300,2700,4100):
 B('Wide raised drawer',(0,-1470,z),(5180,180,1180),WHITE,85)
 for x in (-1500,1500):E('Round cream knob',(x,-1650,z),(155,145,155),WHITE)
for x in (-1380,1380):
 B('Small top drawer',(x,-1470,5320),(2400,180,960),WHITE,75)
 E('Round upper knob',(x,-1650,5320),(155,145,155),WHITE)
# A tilted classroom globe, separate ocean sphere, raised land and brass meridian.
ns['group']='RoomGlobe'
center=Vector((-8100,4200,8220));radius=1550
ell('Globe domed base',(-8100,4200,6300),(1100,1100,210),YELLOW,32,16)
rod('Globe support',(-8100,4200,6400),(-8100,4200,6860),300,YELLOW,r2=190,verts=24)
from mathutils import Matrix
rotation=Matrix.Rotation(math.radians(23),3,'Y')
ell('Blue globe ocean',center,(radius,radius,radius),BLUE,48,32)
def globe_point(lon,lat,r=radius+12):
 a,b=math.radians(lon),math.radians(lat)
 return center+rotation@Vector((r*math.cos(b)*math.cos(a),r*math.cos(b)*math.sin(a),r*math.sin(b)))
land=[('North America',[(-168,67),(-125,72),(-100,58),(-60,50),(-80,24),(-100,16),(-117,32),(-145,58)],GREEN),('South America',[(-81,11),(-50,0),(-35,-8),(-53,-34),(-70,-55),(-77,-12)],YELLOW),('Africa',[(-17,35),(10,37),(35,28),(50,10),(36,-24),(18,-35),(2,-5),(-17,16)],ORANGE),('Eurasia',[(-10,36),(-10,58),(30,70),(95,76),(175,60),(140,35),(105,6),(75,10),(45,35)],GREEN),('Australia',[(112,-12),(139,-10),(154,-27),(143,-40),(116,-34)],RED),('Greenland',[(-53,60),(-22,74),(-42,83),(-62,75)],WHITE)]
for label,outline,tile in land:
 lon=sum(p[0] for p in outline)/len(outline);lat=sum(p[1] for p in outline)/len(outline)
 verts=[globe_point(lon,lat)]+[globe_point(a,b) for a,b in outline]
 faces=[(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))]
 faces=[tuple(reversed(f)) if (verts[f[1]]-verts[f[0]]).cross(verts[f[2]]-verts[f[0]]).dot(verts[f[0]]-center)<0 else f for f in faces]
 mesh=bpy.data.meshes.new(label);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(label,mesh);scene.collection.objects.link(obj)
 # Subdivide and project so broad continents follow the globe instead of sinking into it.
 bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 mod=obj.modifiers.new('Curved land','SUBSURF');mod.subdivision_type='SIMPLE';mod.levels=3
 bpy.ops.object.modifier_apply(modifier=mod.name)
 for v in obj.data.vertices:v.co=center+(v.co-center).normalized()*(radius+16)
 ns['finish'](obj,label,tile,True);obj.select_set(False)
for lat in (-60,-30,0,30,60):
 for j in range(72):rod('Globe latitude',globe_point(j*5,lat, radius+22),globe_point((j+1)*5,lat,radius+22),6,GLASS,verts=4)
for lon in range(0,360,30):
 for j in range(36):rod('Globe longitude',globe_point(lon,-90+j*5,radius+22),globe_point(lon,-85+j*5,radius+22),6,GLASS,verts=4)
for j in range(96):
 a,b=j*math.tau/96,(j+1)*math.tau/96
 p=center+rotation@Vector((1750*math.cos(a),0,1750*math.sin(a)))
 q=center+rotation@Vector((1750*math.cos(b),0,1750*math.sin(b)))
 rod('Brass meridian',p,q,55,YELLOW,verts=8)
# Clear the right side of the lowest shelf for the reference basket.
import bmesh
shelf_changes=[]
for obj in list(bpy.data.objects):
 if not obj.name.startswith('RoomShelves'):continue
 bm=bmesh.new();bm.from_mesh(obj.data);remaining=set(bm.verts);remove=[]
 while remaining:
  seed=remaining.pop();component={seed};pending=[seed]
  while pending:
   for edge in pending.pop().link_edges:
    for v in edge.verts:
     if v in remaining:remaining.remove(v);component.add(v);pending.append(v)
  lo=[min(v.co[i] for v in component) for i in range(3)]
  hi=[max(v.co[i] for v in component) for i in range(3)]
  if lo[2]>500 and hi[2]<4000 and (lo[0]+hi[0])/2>17400 and lo[1]>=15300:
   remove.extend(component)
 if remove:
  bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(obj.data);obj.data.update();shelf_changes.append(obj.name)
 bm.free()
# Basket sits at the back of the low shelf, below the lower landing.
ns['group']='RoomShelfBasket'
box('Blue basket base',(18000,17300,960),(3100,1900,160),BLUE,55)
for z in (1100,1530,1960,2390):
 for y in (16350,18250):box('Basket horizontal rail',(18000,y,z),(3100,75,65),BLUE,15)
 for x in (16450,19550):box('Basket side rail',(x,17300,z),(75,1900,65),BLUE,15)
for x in range(16450,19551,310):
 for y in (16350,18250):box('Basket upright',(x,y,1745),(65,75,1420),BLUE,15)
for y in range(16350,18251,380):
 for x in (16450,19550):box('Basket side upright',(x,y,1745),(75,65,1420),BLUE,15)
for i,tile in enumerate((GREEN,RED,YELLOW)):
 box('Basket toy block',(17300+i*650,17300,1470),(550,850,850),tile,50,rot=.1*(i-1))
changed=[]
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for obj in parts:obj.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 obj['export_material']='RoomDecorAtlas'
 obj.data.uv_layers.new(name='LightmapUV');obj.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 mod=obj.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 changed.append(repair_mesh(obj,512))
 if name=='RoomShelfBasket':move(name,(1300,0,-250))
modified={'RoomNightstand','RoomSlinky','RoomWagonChest','RoomAliens',*shelf_changes}
for name,sig in original.items():
 if name not in modified:assert surface_signature(bpy.data.objects[name])==sig,name
from room_mesh_parts import split_mesh
for name in list(ns['GROUPS']):
 obj=bpy.data.objects[name]
 if len(obj.data.polygons)>20000:split_mesh(obj)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
(out/'layout.json').write_text(json.dumps({'moved':sorted(modified),'new':list(ns['GROUPS']),'preserved':{n:s for n,s in original.items() if n not in modified},'new_mesh_checks':changed},indent=2))
print('Layout saved',out,flush=True)
