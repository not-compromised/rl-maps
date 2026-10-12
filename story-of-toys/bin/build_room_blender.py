"""Original room scenery. Run with Blender --background --python ... -- OUTPUT."""
import bpy, math, sys, json, hashlib, random
from pathlib import Path
from mathutils import Vector
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from room_lightmaps import repair_mesh
OUT=Path(sys.argv[sys.argv.index('--')+1]); OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'Room.blend').exists(): raise RuntimeError('Choose a new export directory')
random.seed(34)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
# Coordinates are authored in game space. Reflect Y once before FBX export.
COLORS=[(.66,.36,.13),(.22,.52,.79),(.68,.055,.065),(.045,.16,.44),(.87,.55,.35),(.9,.91,.84),(.3,.72,.075),(.34,.09,.59),(.15,.052,.018),(.014,.021,.031),(.07,.3,.66),(.98,.67,.06),(.84,.21,.025),(.10,.4,.16),(.87,.55,.35),(.76,.86,.91)]
WOOD,CLOUD,RED,DENIM,SKIN,WHITE,GREEN,PURPLE,HAIR,BLACK,BLUE,YELLOW,ORANGE,DARKGREEN,FACE_SKIN,GLASS=range(16)
N=1024;T=N//4; yy,xx=np.mgrid[0:T,0:T]; atlas=np.ones((N,N,4),dtype=np.float32)
for i,c in enumerate(COLORS):
 tile=np.ones((T,T,3),np.float32)*c
 if i==WOOD:
  grain=.89+.065*np.sin(xx*.11+np.sin(yy*.022)*2)+.035*np.sin(xx*.9+yy*.023)
  grain*=1-.11*(np.mod(xx,64)<2)
  tile*=grain[:,:,None]
 if i in (RED,DENIM):
  weave=.9+.055*np.sin(xx*math.pi/2)+.04*np.sin(yy*math.pi/2);tile*=weave[:,:,None]
 if i==CLOUD:
  for cx,cy,s in [(64,75,1),(187,188,.9)]:
   mask=np.zeros((T,T),bool)
   for dx,dy,r in [(-29,0,23),(0,8,34),(29,0,25),(0,-12,25)]:mask|=(xx-cx-dx*s)**2+(yy-cy-dy*s)**2<(r*s)**2
   tile[mask]=(.94,.96,.92)
 if i==RED:
  seam=(np.mod(xx,64)<2)|(np.mod(yy,64)<2);tile[seam]*=.65
 if i==FACE_SKIN:
  px=2840*((xx/T-.02)/.96-.5);pz=3200*((yy/T-.02)/.96-.5)
  def pigment(cx,cz,wx,wz):return np.exp(-((px-cx)/wx)**2-((pz-cz)/wz)**2)
  blush=.19*(pigment(-650,-250,380,290)+pigment(650,-250,380,290))+.12*pigment(0,-70,250,190)
  tile=tile*(1-blush[:,:,None])+np.array((.92,.36,.27))*blush[:,:,None]
  rng=np.random.default_rng(34)
  for side in (-1,1):
   for freckle in range(7):
    spot=.20*pigment(side*rng.uniform(420,900),rng.uniform(-70,130),rng.uniform(10,16),rng.uniform(10,16))
    tile=tile*(1-spot[:,:,None])+np.array((.43,.24,.13))*spot[:,:,None]
  # The projected head occupies an ellipse, leaving this corner free for irises.
  radius=np.sqrt((xx-16)**2+(yy-16)**2)/13;angle=np.arctan2(yy-16,xx-16)
  strands=.5+.5*np.sin(angle*37+np.sin(angle*13)*2+radius*12)
  iris=np.ones((T,T,3))*np.array((.035,.22,.31))
  iris+=strands[:,:,None]*np.array((.06,.20,.18))
  rim=np.clip((radius-.76)/.20,0,1)
  iris=iris*(1-rim[:,:,None])+np.array((.018,.055,.075))*rim[:,:,None]
  corner=(xx<32)&(yy<32);tile[corner]=iris[corner]
  tile[(xx>223)&(yy<32)]=(.24,.105,.045)
  t=np.clip(px/440,-1,1);upper=-680+70*t*t+15*t;lower=upper-210*(1-t*t)
  lips=.25*np.exp(-(np.minimum(abs(pz-upper),abs(pz-lower))/24)**2)*(abs(px)<440)*(1-t*t)
  tile=tile*(1-lips[:,:,None])+np.array((.78,.36,.28))*lips[:,:,None]
 atlas[(i//4)*T:(i//4+1)*T,(i%4)*T:(i%4+1)*T,:3]=tile
img=bpy.data.images.new('RoomAtlas',width=N,height=N,alpha=False);img.pixels.foreach_set(atlas.ravel());img.filepath_raw=str(OUT/'RoomAtlas.tga');img.file_format='TARGA_RAW';img.save();img.pack()
mat=bpy.data.materials.new('RoomAtlas');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65
GROUPS={};group='RoomFloor'
def finish(o,name,tile,smooth=False):
 o.name=name;o['tile']=tile;GROUPS.setdefault(group,[]).append(o)
 bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if o.type=='MESH':
  if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
  uv=o.data.uv_layers[0]
  for p in o.data.polygons:
   p.use_smooth=smooth
   for li in p.loop_indices:
    u,v=uv.data[li].uv
    if tile==CLOUD:
     axes=[a for a in range(3) if a!=max(range(3),key=lambda a:abs(p.normal[a]))]
     co=o.data.vertices[o.data.loops[li].vertex_index].co
     u,v=[co[a]/max(o.dimensions[a],1)+.5 for a in axes]
    uv.data[li].uv=((tile%4+.02+.96*u)/4,(tile//4+.02+.96*v)/4)
  o.data.materials.clear();o.data.materials.append(mat)
 return o

def box(name,p,s,tile,bevel=0,rot=0):
 if tile==CLOUD and max(s)>4500:
  axes=[a for a in range(3) if a!=min(range(3),key=lambda a:s[a])]
  counts=[math.ceil(s[a]/3500) for a in axes]
  for i in range(counts[0]):
   for j in range(counts[1]):
    q=list(p);size=list(s)
    for a,n,k in zip(axes,counts,(i,j)):
     size[a]=s[a]/n;q[a]=p[a]-s[a]/2+(k+.5)*size[a]
    box(name,q,size,tile)
  return None
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=s;o.rotation_euler[2]=rot
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name)
 return finish(o,name,tile)

def ell(name,p,s,tile,segments=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=p);o=bpy.context.object;o.scale=s;return finish(o,name,tile,True)

def rod(name,a,b,r,tile,r2=None,verts=24):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(Vector(a)+Vector(b))/2);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,tile,True)

def text(name,body,p,size,tile,rotation=(math.pi/2,0,0),extrude=3):
 bpy.ops.object.text_add(location=p,rotation=rotation);o=bpy.context.object;o.data.body=body;o.data.align_x='CENTER';o.data.size=size;o.data.extrude=extrude;o.data.bevel_depth=1;o.data.resolution_u=4;bpy.ops.object.convert(target='MESH');return finish(bpy.context.object,name,tile)

def torus(name,p,major,minor,tile,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=10,location=p,rotation=rotation,major_radius=major,minor_radius=minor);return finish(bpy.context.object,name,tile,True)

# Small plank pieces keep the grain legible at car height and the floor continuous.
for row,y in enumerate(range(-19000,19000,1000)):
 for x in range(-23040,23040,3840):
  box('Oak plank',(x+1920,y+500,-100),(3840,1000,200),WOOD)
group='RoomWalls'
for side in (-1,1):
 box('Side wall',(side*23140,0,16000),(200,38000,32000),CLOUD)
 box('Side skirting',(side*22980,0,650),(140,38000,1300),WHITE,35)
 box('Side crown',(side*22940,0,30900),(220,38000,350),WHITE,40)
box('Front wall',(0,-19100,16000),(46080,200,32000),CLOUD)
box('Front skirting',(0,-18980,650),(46080,140,1300),WHITE,35)
# Back wall is four solids surrounding the actual window opening.
for p,s in [((-16520,19100,16000),(13040,200,32000)),((15520,19100,16000),(15040,200,32000)),((-1000,19100,4500),(18000,200,9000)),((-1000,19100,28500),(18000,200,7000))]:box('Window wall',p,s,CLOUD)
group='RoomWindow'
for x in (-10150,8150):box('Window casing',(x,18700,17000),(420,650,17000),WHITE,60)
for z in (8750,25250):box('Window casing',(-1000,18700,z),(18800,650,500),WHITE,60)
box('Window mullion',(-1000,18820,17000),(230,200,16000),WHITE,20)
box('Window crossbar',(-1000,18820,17000),(18000,200,230),WHITE,20)
box('Window blue sky',(-1000,19500,17000),(18000,80,16000),GLASS)
box('Deep windowsill',(-1000,18100,8800),(19700,1700,420),WHITE,60)
rod('Curtain pole',(-12000,17800,26000),(10000,17800,26000),130,WOOD)
for x in (-10800,8800):
 for j in range(9):
  ell('Gathered blue curtain',(x+(j-4)*240,17800+(j%2)*160,17000),(210,280,8800),BLUE,16,16)
group='RoomCeiling'
box('Ceiling',(0,0,32100),(46480,38400,200),WHITE)
# Bed frame, rounded posts, red quilt and a separate soft pillow.
group='RoomBed'
for x in (-21000,-10500):
 for y in (-2000,13700):
  rod('Bed post',(x,y,300),(x,y,6800),210,WOOD);ell('Bedpost finial',(x,y,7000),(330,330,360),WOOD)
box('Bed foundation',(-15750,5850,2500),(11200,16400,900),WOOD,120)
box('Mattress',(-15750,5850,3450),(10700,15900,1000),WHITE,380)
box('Red quilt',(-15750,4850,4030),(10700,13900,250),RED,120)
for x in range(-20500,-10499,1000):rod('Quilt stitching',(x,-1950,4165),(x,11700,4165),9,ORANGE,verts=8)
for y in range(-1900,11700,1000):rod('Quilt stitching',(-20900,y,4165),(-10500,y,4165),9,ORANGE,verts=8)
box('Pillow',(-15750,12000,4350),(8000,2600,650),WHITE,300)
box('Headboard',(-15750,13700,4700),(10500,350,3600),WOOD,150)
for x in range(-19750,-10749,1500):rod('Headboard spindle',(x,13700,3200),(x,13700,6200),90,WOOD)
# Desk and chair.
group='RoomDesk'
box('Desk top',(-2800,14300,7450),(13700,5600,600),WOOD,100)
for x in (-8700,3100):
 for y in (12100,16500):box('Desk leg',(x,y,3450),(500,500,6900),WOOD,60)
for z in (5900,4500,3100):
 box('Drawer',(-6800,14000,z),(4000,4600,1250),WOOD,55)
 rod('Drawer handle',(-7300,11600,z),(-6300,11600,z),90,HAIR)
box('Chair seat',(-1000,8900,3600),(4300,4000,450),WOOD,180)
for x in (-2800,800):
 for y in (7300,10500):rod('Chair leg',(x,y,150),(x,y,3450),160,WOOD)
box('Chair back',(-1000,10600,5700),(4200,350,3800),WOOD,220)
# Books and lamp on desk.
for j in range(5):box('Stacked book',(-5900,14300,7900+j*290),(2900-j*90,2200,260),[RED,BLUE,YELLOW,DARKGREEN,PURPLE][j],25,rot=(j-2)*.04)
rod('Lamp base', (2300,14600,7750),(2300,14600,7900),750,BLUE)
rod('Lamp stem',(2300,14600,7900),(2300,14600,11200),150,BLUE)
rod('Lamp shade',(2300,14600,11000),(2300,14600,12300),1500,YELLOW,r2=700)
group='RoomShelves'
for x in (15100,21600):box('Shelf upright',(x,11800,10500),(400,6500,21000),WOOD,70)
for z in (400,5000,10000,15000,20000):box('Shelf plank',(18350,11800,z),(6900,6500,450),WOOD,55)
for level,z in enumerate((630,5230,15230)):
 for j in range(7):
  h=2200+(j%3)*420;tile=[RED,YELLOW,BLUE,DARKGREEN,PURPLE][(j+level)%5]
  box('Book spine',(15700+j*720,13800,z+h/2),(580,2500,h),tile,30)
  text('Book title',['SPACE','STARS','TOYS','ABC','PLANETS','WEST','STORY'][j],(15700+j*720,12535,z+h*.6),190,WHITE)
# Toy chest, alphabet blocks, rug and scattered toys.
group='RoomToys'
box('Toy chest',(11600,-10500,2200),(9000,6000,4400),YELLOW,220)
box('Toy chest lid',(11600,-10500,4570),(9400,6400,420),RED,180)
text('Toy chest label','ANDY',(11600,-13600,2050),1450,RED)
for x in (8000,15200):box('Chest hinge',(x,-13400,4450),(400,180,850),BLUE,30)
for i,(x,y,z) in enumerate([(-10000,-13500,1000),(-7800,-14500,1000),(-8900,-13900,3000),(-12500,-12000,1000)]):
 box('Alphabet block',(x,y,z),(2000,2000,2000),[BLUE,RED,YELLOW,GREEN][i],65)
 box('Alphabet inset',(x,y-1010,z),(1550,25,1550),WHITE,30)
 text('Alphabet letter','ANDY'[i],(x,y-1040,z-580),1600,[BLUE,RED,ORANGE,DARKGREEN][i])
# Rug is thin, colliding furniture rather than a kill floor.
box('Play rug',(0,-10000,22),(14000,9500,44),BLUE,20)
for x in (-6500,6500):box('Rug border',(x,-10000,48),(180,9000,8),YELLOW)
for y in (-14200,-5800):box('Rug border',(0,y,48),(13000,180,8),YELLOW)
for i in range(7):
 x=-5500+i*1800
 box('Rug stripe',(x,-10000,49),(1100,6800,8),[RED,GREEN,YELLOW][i%3])
# Wooden toy train and rubber ball.
box('Train body',(12000,-2000,750),(3600,1400,1100),RED,100)
rod('Train boiler',(10800,-2000,1400),(12500,-2000,1400),550,BLUE)
box('Train cab',(13300,-2000,1800),(1100,1500,1400),YELLOW,75)
for x in (10800,12000,13200):
 for y in (-2800,-1200):rod('Train wheel',(x,y-90,500),(x,y+90,500),480,BLACK)
ell('Rubber ball',(18300,-14500,1500),(1500,1500,1500),YELLOW)
torus('Ball stripe',(18300,-14500,1500),1495,65,BLUE)
# Suspended balsa airplane supports the high-course checkpoint.
group='RoomPlane'
box('Plane wing',(-4000,-3000,21820),(9500,2800,360),YELLOW,140)
ell('Plane fuselage',(-4000,-3000,22050),(620,3600,620),RED)
box('Plane tail',(-4000,-5900,22400),(3900,1100,220),YELLOW,100)
box('Plane fin',(-4000,-6500,22200),(180,1200,500),RED,60)
rod('Propeller',(-4000,610,22400),(-4000,790,22400),140,HAIR)
box('Propeller blade',(-4000,820,22400),(2700,140,170),WOOD,65)
for x in (-6900,-1100):rod('Plane suspension',(x,-3000,22020),(x,-3000,32000),12,WHITE,verts=8)
# Frozen boy: sculpted silhouette, clothing, articulated fingers and face.
group='RoomAndy';origin=Vector((1500,1000,0))
def ap(p):return origin+Vector(p)
def ae(n,p,s,t,**kw):return ell(n,ap(p),s,t,**kw)
def ar(n,a,b,r,t,r2=None):return rod(n,ap(a),ap(b),r,t,r2)
def ab(n,p,s,t,**kw):return box(n,ap(p),s,t,**kw)
from andy_character import build_character
build_character(globals())

# A swept saddle brim curls upward at the sides and dips at the front lip.
# Its broad interior remains level under the existing checkpoint/drive line.
group='RoomAndyHat'
def brim_height(x,y):
 r=math.sqrt((x/3900)**2+(y/3800)**2)
 edge=max(0,min(1,(r-.82)/.18));edge=edge*edge*(3-2*edge)
 side=(abs(x)/3900)**3
 front=max(0,-y/3800)
 return 16340+edge*(1050*side-300*front**4+180*max(0,y/3800)**3)
verts=[];faces=[];segments=128;radial=16
# Two concentric grids create a closed, smoothly curved collision surface.
for bottom in (False,True):
 for ring in range(radial+1):
  radius=.001+(1-.001)*ring/radial
  for i in range(segments):
   a=math.tau*i/segments;x=3900*radius*math.cos(a);y=3800*radius*math.sin(a)
   verts.append(tuple(ap((x,y,brim_height(x,y)-(160 if bottom else 0)))))
layer=(radial+1)*segments
for bottom in (False,True):
 offset=layer if bottom else 0
 for ring in range(radial):
  for i in range(segments):
   j=(i+1)%segments;a=offset+ring*segments+i;b=offset+ring*segments+j
   face=(a,a+segments,b+segments,b)
   faces.append(tuple(reversed(face)) if bottom else face)
 faces.append(tuple(offset+i for i in (reversed(range(segments)) if bottom else range(segments))))
for i in range(segments):
 a=radial*segments+i;b=radial*segments+(i+1)%segments
 faces.append((a,a+layer,b+layer,b))
mesh=bpy.data.meshes.new('Swept cowboy brim');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('Swoosh red hat brim',mesh);scene.collection.objects.link(o);finish(o,o.name,RED,True)
verts=[];faces=[];segments=64
for z,rx,ry in [(16320,1700,1250),(16600,1730,1280),(17650,1470,1050),(17900,1220,820)]:
 for i in range(segments):
  angle=math.tau*i/segments;c=math.cos(angle);v=math.sin(angle)
  x=rx*math.copysign(abs(c)**.7,c);y=450+ry*math.copysign(abs(v)**.7,v)
  verts.append(tuple(ap((x,y,z-(240*(1-abs(c)) if z==17900 else 0)))))
for row in range(3):
 for i in range(segments):
  j=(i+1)%segments;faces.append((row*segments+i,row*segments+j,(row+1)*segments+j,(row+1)*segments+i))
faces.append(tuple(range(3*segments,4*segments)));faces.append(tuple(reversed(range(segments))))
mesh=bpy.data.meshes.new('Pinched cowboy crown');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('Red cowboy crown',mesh);scene.collection.objects.link(o);finish(o,o.name,RED,True)
for i in range(128):
 a=math.tau*i/128;b=math.tau*(i+.68)/128
 def edge(t):
  x=3860*math.cos(t);y=3760*math.sin(t)
  return (x,y,brim_height(x,y)+12)
 ar('Pale brim stitching',edge(a),edge(b),18,WHITE)
# Buzz stands on the floor, separate from Andy and the remote.
group='RoomBuzz';buzzstart=len(GROUPS.get(group,[]))
for side in (-1,1):
 x=side*250
 ell('Buzz boot',(x,-140,240),(250,420,240),WHITE)
 box('Buzz boot green',(x,-230,150),(420,590,170),GREEN,55)
 rod('Buzz shin',(x,0,380),(x,0,900),210,WHITE)
 ell('Buzz knee',(x,-20,910),(225,240,160),PURPLE)
 rod('Buzz thigh',(x,0,1000),(side*240,0,1500),250,WHITE)
box('Buzz hip',(0,0,1500),(950,580,420),WHITE,120)
box('Buzz belt',(0,-25,1700),(1020,650,180),GREEN,65)
ell('Buzz torso',(0,0,2200),(620,390,630),WHITE)
box('Buzz chest',(0,-340,2350),(1050,170,580),GREEN,115)
box('Buzz panel',(-230,-447,2350),(280,70,220),BLUE,30)
for j,t in enumerate((RED,BLUE,YELLOW)):ell('Buzz chest button',(230,-463,2470-j*110),(60,35,45),t,segments=16,rings=10)
text('Buzz name','LIGHTYEAR',(-180,-487,2520),72,BLACK,extrude=1)
# Arms extend forward overhead, silhouette of flight.
for side in (-1,1):
 a=(side*650,0,2450);b=(side*900,-130,1900);c=(side*950,-300,1450)
 ell('Buzz shoulder',a,(270,300,300),GREEN)
 rod('Buzz upper arm',a,b,210,WHITE);ell('Buzz elbow',b,(220,220,190),PURPLE)
 rod('Buzz forearm',b,c,210,WHITE,r2=180)
 ell('Buzz glove',c,(205,190,280),WHITE)
 for f in range(4):rod('Buzz finger',(c[0]+(f-1.5)*75,c[1]-70,c[2]+130),(c[0]+(f-1.5)*75,c[1]-110,c[2]+340),40,WHITE,r2=30)
box('Buzz wing pack',(0,430,2200),(900,340,950),PURPLE,100)
for side in (-1,1):
 box('Buzz wing',(side*1100,440,2270),(1700,150,420),WHITE,40,rot=0)
 box('Buzz wing leading edge',(side*1100,440,2500),(1700,160,85),GREEN,25)
 for j in range(5):box('Buzz red wing stripe',(side*(650+j*250),345,2270),(90,30,405),RED,5)
 ell('Buzz wingtip',(side*1950,440,2290),(130,110,250),[RED,GREEN][side==1])
torus('Buzz collar',(0,0,2790),390,85,PURPLE)
ell('Buzz hood',(0,0,3000),(380,320,450),PURPLE)
ell('Buzz face',(0,-200,3040),(290,205,335),SKIN)
for side in (-1,1):
 ell('Buzz eye',(side*112,-383,3130),(79,28,72),WHITE,segments=20,rings=12)
 ell('Buzz iris',(side*109,-410,3130),(29,15,40),BLUE,segments=16,rings=10)
 rod('Buzz eyebrow',(side*112-80,-383,3230),(side*112+80,-383,3215),25,HAIR)
ell('Buzz chin',(0,-280,2820),(180,150,100),SKIN)
rod('Buzz smile',(-100,-398,2950),(110,-398,2940),17,HAIR)
ell('Buzz nose',(0,-411,3050),(62,60,68),SKIN)
# A narrow clear-blue helmet rim leaves the face visible without an opaque dome.
torus('Buzz helmet rim',(0,0,2860),445,26,GLASS)
from mathutils import Matrix
pose=Matrix.Translation(Vector((6600,-4300,0))) @ Matrix.Rotation(-.35,4,'Z')
for o in GROUPS[group]:o.matrix_world=pose @ o.matrix_world

# Each toy is its own mesh for collision and recognizable close-up detail.
def toy_place(name,position,angle=0):
 transform=Matrix.Translation(Vector(position)) @ Matrix.Rotation(angle,4,'Z')
 for obj in GROUPS[name]:obj.matrix_world=transform @ obj.matrix_world

group='RoomWoody'
for side in (-1,1):
 rod('Woody denim leg',(side*180,0,450),(side*190,0,1750),155,DENIM)
 ell('Woody boot',(side*180,-110,260),(200,360,260),WOOD)
 rod('Woody boot shaft',(side*180,0,270),(side*180,0,650),190,WOOD)
 ell('Woody boot spur',(side*180,240,320),(95,80,95),YELLOW)
ell('Woody shirt',(0,0,2210),(460,250,650),YELLOW)
for x in (-260,0,260):box('Shirt check stripe',(x,-245,2180),(22,15,950),RED)
for z in (1860,2100,2340,2580):box('Shirt check stripe',(0,-251,z),(760,15,22),RED)
for side in (-1,1):
 box('Cowhide vest',(side*310,-255,2300),(230,70,810),WHITE,40)
 for j in range(3):ell('Vest black spot',(side*310,-300,2040+j*220),(70,20,90),BLACK,segments=16,rings=10)
 rod('Woody sleeve',(side*400,0,2490),(side*680,-40,1900),160,YELLOW,r2=120)
 rod('Woody forearm',(side*680,-40,1900),(side*620,-160,1560),110,YELLOW)
 ell('Woody hand',(side*620,-160,1460),(120,100,190),SKIN)
box('Woody belt',(0,-245,1720),(770,90,130),HAIR,25)
ell('Woody belt buckle',(0,-315,1720),(125,35,100),YELLOW)
torus('Red neckerchief',(0,0,2770),210,80,RED)
box('Neckerchief tails',(30,-280,2670),(140,80,260),RED,25)
ell('Woody head',(0,0,3110),(315,260,470),SKIN)
for side in (-1,1):
 ell('Woody ear',(side*310,0,3090),(75,60,130),SKIN)
 ell('Woody eye',(side*115,-245,3180),(80,35,90),WHITE)
 ell('Woody pupil',(side*115,-277,3180),(35,15,48),HAIR)
ell('Woody nose',(0,-290,3080),(75,100,115),SKIN)
rod('Woody smile',(-110,-250,2940),(120,-250,2940),20,HAIR)
ell('Woody hat brim',(0,10,3460),(730,580,80),WOOD)
ell('Woody hat crown',(0,40,3680),(390,310,330),WOOD)
ell('Sheriff badge',(-290,-318,2450),(95,20,95),YELLOW)
toy_place(group,(-5200,-9500,55),-.45)

group='RoomRex'
ell('Rex body',(0,0,1850),(950,950,1550),DARKGREEN)
ell('Rex belly',(0,-790,1750),(650,250,1000),GREEN)
for side in (-1,1):
 ell('Rex thigh',(side*730,0,1000),(550,620,850),DARKGREEN)
 ell('Rex foot',(side*730,-470,240),(570,940,240),DARKGREEN)
 for toe in (-1,0,1):ell('Rex toe',(side*730+toe*270,-1290,170),(100,230,100),WHITE)
 rod('Rex tiny arm',(side*740,-500,2490),(side*960,-1150,2400),145,DARKGREEN,r2=105)
 for f in (-1,1):rod('Rex finger',(side*960,-1150,2400),(side*960+f*100,-1350,2320),55,GREEN)
rod('Rex tail',(0,700,1400),(0,3400,350),620,DARKGREEN,r2=30)
ell('Rex neck',(0,-100,3230),(630,680,900),DARKGREEN)
ell('Rex head',(0,-620,3950),(850,1130,700),DARKGREEN)
ell('Rex muzzle',(0,-1480,3700),(780,660,380),DARKGREEN)
box('Rex mouth',(0,-1930,3620),(1190,90,180),HAIR,65)
for j in range(7):rod('Rex tooth',(-490+j*160,-1980,3700),(-490+j*160,-1980,3540),60,WHITE,r2=3)
for side in (-1,1):
 ell('Rex eye',(side*560,-1310,4260),(250,210,280),WHITE)
 ell('Rex pupil',(side*540,-1500,4240),(85,55,150),BLACK)
 ell('Rex nostril',(side*330,-2060,3860),(65,35,55),BLACK)
toy_place(group,(11900,4700,0),.65)

group='RoomHamm'
ell('Hamm body',(0,0,970),(1300,1650,950),SKIN)
for x in (-720,720):
 for y in (-850,850):rod('Hamm leg',(x,y,130),(x,y,760),260,SKIN);ell('Hamm hoof',(x,y,160),(290,300,150),HAIR)
ell('Hamm head',(0,-1430,1100),(980,780,860),SKIN)
ell('Hamm snout',(0,-2150,950),(590,230,400),SKIN)
for side in (-1,1):
 ell('Hamm nostril',(side*210,-2370,1000),(100,40,120),HAIR)
 ell('Hamm ear',(side*700,-1170,1880),(290,160,490),SKIN)
 ell('Hamm eye',(side*460,-2000,1430),(150,60,160),WHITE)
 ell('Hamm pupil',(side*440,-2050,1430),(65,30,90),BLACK)
box('Piggy bank coin slot',(0,0,1920),(550,110,25),BLACK,20)
torus('Hamm curled tail',(0,1670,1250),260,65,SKIN,rotation=(math.pi/2,0,0))
toy_place(group,(17000,-5400,0),-.6)

group='RoomSlinky'
for y in (-950,950):
 ell('Slinky body end',(0,y,740),(630,530,660),WOOD)
 for side in (-1,1):
  rod('Slinky leg',(side*430,y,650),(side*480,y-50,190),120,YELLOW)
  ell('Slinky paw',(side*480,y-180,170),(220,350,170),YELLOW)
for j in range(13):torus('Slinky metal spring',(0,-850+j*140,800),510,35,GLASS,rotation=(math.pi/2,0,0))
ell('Slinky head',(0,-1260,1490),(570,600,650),WOOD)
ell('Slinky muzzle',(0,-1810,1330),(430,330,330),YELLOW)
ell('Slinky nose',(0,-2100,1450),(220,150,155),BLACK)
for side in (-1,1):
 ell('Slinky floppy ear',(side*570,-1250,1220),(210,270,650),HAIR)
 ell('Slinky eye',(side*200,-1740,1750),(170,80,230),WHITE)
 ell('Slinky pupil',(side*200,-1810,1760),(75,35,120),BLACK)
rod('Slinky tail',(0,1320,900),(0,1810,1590),55,WOOD)
toy_place(group,(-8200,3000,0),-.6)

group='RoomAliens'
for n,(x,y) in enumerate(((7000,10500),(9600,12400),(7200,14500))):
 start=len(GROUPS.get(group,[]))
 ell('Alien suit',(0,0,900),(470,330,560),BLUE)
 for side in (-1,1):
  ell('Alien boot',(side*250,-150,200),(260,380,180),PURPLE)
  rod('Alien arm',(side*410,0,1060),(side*650,-110,800),150,BLUE)
  ell('Alien hand',(side*690,-140,760),(170,150,160),GREEN)
  rod('Alien pointed ear',(side*430,0,1590),(side*800,0,1790),220,GREEN,r2=5)
 ell('Alien head',(0,0,1580),(560,370,420),GREEN)
 for eye in (-1,0,1):
  ell('Alien eye',(eye*275,-330,1680),(140,65,160),WHITE)
  ell('Alien pupil',(eye*275,-390,1680),(55,25,80),BLACK)
 ell('Alien smile',(0,-365,1420),(200,30,75),BLACK)
 rod('Alien antenna',(0,0,1900),(0,0,2250),50,GREEN)
 ell('Alien antenna tip',(0,0,2290),(110,110,110),GREEN)
 transform=Matrix.Translation(Vector((x,y,0))) @ Matrix.Rotation((n-1)*.4,4,'Z')
 for obj in GROUPS[group][start:]:obj.matrix_world=transform @ obj.matrix_world

# Toy companions sit beside the checkpoint driving area, never inside its trigger.
for label,position,scale in [('Desk',(-1600,15700,7750),.65),('Hat',(2900,-2200,brim_height(1400,-3200)),.28),('LowerShelf',(19900,13000,10225),.7),('UpperShelf',(20000,12800,20225),.7),('Bed',(-17500,1200,4165),.7),('Plane',(-6800,-3000,22010),.35),('Finish',(-18000,12000,4675),.7),('Start',(-11100,-11100,0),.7)]:
 group='RoomCheckpoint'+label
 source=GROUPS['RoomAliens']
 # First alien is based at (7000,10500,0) and rotated -0.4 radians.
 for original in source[:len(source)//3]:
  obj=original.copy();obj.data=original.data.copy();scene.collection.objects.link(obj)
  obj.matrix_world=Matrix.Translation(Vector(position)) @ Matrix.Scale(scale,4) @ Matrix.Rotation(.4,4,'Z') @ Matrix.Translation(Vector((-7000,-10500,0))) @ original.matrix_world
  GROUPS.setdefault(group,[]).append(obj)

# Join by furniture/character, never one room-wide collision mesh.
meshes=[];report=[]
for name,parts in GROUPS.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # All atlas slots refer to the same material; consolidate them.
 for poly in o.data.polygons:poly.material_index=0
 o.data.materials.clear();o.data.materials.append(mat)
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 o.data.uv_layers.active_index=0;o.data.uv_layers[0].active_render=True
 tri=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
 if name in ('RoomAndy','RoomAndyHead','RoomAndyHat'):
  repair_mesh(o,512)
 else:o['lightmap_resolution']=512 if name in ('RoomBed','RoomToys') else 256
 print('Prepared',name,len(o.data.polygons),flush=True)
 assert len(o.data.polygons)<=60000,(name,len(o.data.polygons))
 bounds=[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)]
 report.append(dict(name=name,triangles=len(o.data.polygons),bounds=bounds,collision=name!='RoomCeiling',lightmap_resolution=o['lightmap_resolution']))
 meshes.append(o)
# Generated facial texture remains a separate source image until atlas baking.
face_image=bpy.data.images.load(str(Path(__file__).resolve().parents[1]/'assets/andy-face/face-study-01.png'));face_image.pack()
face_mat=mat.copy();face_mat.name='AndyFaceStudy';nodes=face_mat.node_tree.nodes;links=face_mat.node_tree.links
uv=nodes.new('ShaderNodeTexCoord');separate=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],separate.inputs[0])
def math_node(operation,a,b=None):
 n=nodes.new('ShaderNodeMath');n.operation=operation
 if hasattr(a,'is_output'):links.new(a,n.inputs[0])
 else:n.inputs[0].default_value=a
 if b is not None:
  if hasattr(b,'is_output'):links.new(b,n.inputs[1])
  else:n.inputs[1].default_value=b
 return n.outputs[0]
column=math_node('FLOOR',math_node('MULTIPLY',separate.outputs['X'],4));row=math_node('FLOOR',math_node('MULTIPLY',separate.outputs['Y'],4))
mask=math_node('COMPARE',math_node('ADD',column,math_node('MULTIPLY',row,4)),14)
scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';links.new(uv.outputs['UV'],scale.inputs[0]);scale.inputs[3].default_value=4
shift=nodes.new('ShaderNodeVectorMath');shift.operation='SUBTRACT';links.new(scale.outputs[0],shift.inputs[0]);shift.inputs[1].default_value=(2,3,0)
face_tex=nodes.new('ShaderNodeTexImage');face_tex.image=face_image;face_tex.extension='EXTEND';links.new(shift.outputs[0],face_tex.inputs['Vector'])
original=next(n for n in nodes if n.type=='TEX_IMAGE' and n!=face_tex)
mix=nodes.new('ShaderNodeMixRGB');links.new(mask,mix.inputs[0]);links.new(original.outputs['Color'],mix.inputs[1]);links.new(face_tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
bpy.data.objects['RoomAndyHead'].data.materials[0]=face_mat
# Preview scene stays in authored game coordinates.
world=bpy.data.worlds.new('Afternoon');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.48,.7,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
for name,pos,power,size in [('Window light',(-1000,16500,22000),4e10,12000),('Soft fill',(0,-12000,18000),1.4e10,14000)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,6000))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Room overview');cam=bpy.data.objects.new('Room overview',data);scene.collection.objects.link(cam);cam.location=(21000,-18300,18500);cam.rotation_euler=(Vector((-2500,3000,8500))-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=20;data.clip_end=150000;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'overview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Room.blend'))
# FBX stores a Y-reflected mesh so UDK imports the authored game-space positions.
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
 o.select_set(True);o.scale.y=-1
 bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Applying negative object scale flips winding; recalculate outward normals.
 import bmesh
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
bpy.ops.export_scene.fbx(filepath=str(OUT/'Room.fbx'),use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,bake_anim=False,add_leaf_bones=False,path_mode='STRIP',embed_textures=False)
(OUT/'room-manifest.json').write_text(json.dumps({'blender':bpy.app.version_string,'dimensions':[46080,38000,32000],'meshes':report,'triangles':sum(m['triangles'] for m in report),'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ('.fbx','.tga','.blend')}},indent=2))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Room.blend'));bpy.ops.render.render(write_still=True)
