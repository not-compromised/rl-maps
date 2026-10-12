"""Rework the bedroom around the preserved character from the supplied references."""
import bpy,bmesh,sys,json,math,hashlib,runpy
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh,surface_signature
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
source=ROOT/'bin/build_room_blender.py';code=source.read_text()
# Give the rebuilt furniture its own procedural palette. Character textures stay intact.
code=code.replace('(.22,.52,.79)','(.30,.43,.62)').replace('(.34,.09,.59)','(.52,.32,.53)').replace('(.07,.3,.66)','(.055,.38,.43)')
code=code.replace("if i==RED:\n  seam=", "if False:\n  seam=")
code=code.replace('max(s)>4500','max(s)>6500').replace('s[a]/3500','s[a]/6000')
code=code.replace("str(OUT/'RoomAtlas.tga')","str(OUT/'RoomDecorAtlas.tga')")
code=code.replace("[(-29,0,23),(0,8,34),(29,0,25),(0,-12,25)]","[(-28,0,21),(-5,20,31),(25,5,23)]")
code=code.replace("tile[mask]=(.94,.96,.92)","mask &= yy >= cy-16*s; tile[mask]=(.94,.91,.78)")
ns={'__file__':str(source),'__name__':'room_reference'}
exec(compile(code[:code.index('# Small plank pieces')],str(source),'exec'),ns)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/room-finish-75/RoomFinish.blend'))
scene=bpy.context.scene
mat=bpy.data.materials.new('RoomDecorAtlas');mat.use_nodes=True
image=bpy.data.images.load(str(out.resolve()/'RoomDecorAtlas.tga'));image.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65
ns.update(scene=scene,mat=mat,GROUPS={})
box,rod,ell,text,torus,finish=[ns[n] for n in ('box','rod','ell','text','torus','finish')]
def small_torus(name,p,major,minor,tile):
 bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=6,location=p,major_radius=major,minor_radius=minor)
 return finish(bpy.context.object,name,tile,True)
WOOD,CLOUD,RED,DENIM,SKIN,WHITE,GREEN,PURPLE,HAIR,BLACK,BLUE,YELLOW,ORANGE,DARKGREEN,FACE_SKIN,GLASS=range(16)
protected={n:surface_signature(bpy.data.objects[n]) for n in ('RoomAndy','RoomAndyHead','RoomAndyHat','RoomBuzz','RoomWoody','RoomSlinky','RoomRex','RoomHamm')}
for name in ('RoomBed','RoomDesk','RoomWalls','RoomWindow','RoomShelves','RoomShelvesPart2','RoomShelvesPart3'):
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def group(name):ns['group']=name

def mesh(name,verts,faces,tile):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);return finish(o,name,tile)

def turned(name,p,height,radius,tile):
 profile=[(0,.65),(.07,.72),(.12,.48),(.26,.30),(.37,.42),(.44,.70),(.5,1),(.56,.70),(.64,.4),(.77,.3),(.9,.48),(.96,.72),(1,.65)]
 verts=[(p[0]+radius*r*math.cos(a*math.tau/16),p[1]+radius*r*math.sin(a*math.tau/16),p[2]+height*t) for t,r in profile for a in range(16)]
 faces=[]
 for j in range(len(profile)-1):
  for k in range(16):faces.append((j*16+k,j*16+(k+1)%16,(j+1)*16+(k+1)%16,(j+1)*16+k))
 faces.extend([tuple(reversed(range(16))),tuple((len(profile)-1)*16+k for k in range(16))]);return mesh(name,verts,faces,tile)

def arch_board(name,cx,y,width,base,crest,ends,thickness,tile,band):
 verts=[];n=48
 for yy in (y-thickness/2,y+thickness/2):
  for lower in (False,True):
   for i in range(n+1):
    t=2*i/n-1;z=ends+(crest-ends)*(math.cos(t*math.pi/2)**1.4)
    if lower:z=max(base,z-band)
    verts.append((cx+t*width/2,yy,z))
 faces=[];stride=n+1
 for i in range(n):
  faces.extend([(i,i+1,stride+i+1,stride+i),(2*stride+i,3*stride+i,3*stride+i+1,2*stride+i+1),(i,2*stride+i,2*stride+i+1,i+1),(stride+i,stride+i+1,3*stride+i+1,3*stride+i)])
 faces.extend([(0,stride,3*stride,2*stride),(n,2*stride+n,3*stride+n,stride+n)])
 return mesh(name,verts,faces,tile)

def crescent_cut(board,cx,y,z):
 R,r,d=480,445,195;ix=(R*R-r*r+d*d)/(2*d);iz=math.sqrt(R*R-ix*ix);a=math.atan2(iz,ix);b=math.atan2(iz,ix-d)
 points=[(R*math.cos(a+(math.tau-2*a)*i/40),R*math.sin(a+(math.tau-2*a)*i/40)) for i in range(41)]
 points += [(d+r*math.cos(-b-(math.tau-2*b)*i/40),r*math.sin(-b-(math.tau-2*b)*i/40)) for i in range(1,40)]
 v=[(cx+x,y+yy,z+zz) for yy in (-600,600) for x,zz in points];n=len(points)
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 m=bpy.data.meshes.new('Crescent cutter');m.from_pydata(v,[],faces);m.update();bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();o=bpy.data.objects.new('Crescent cutter',m);scene.collection.objects.link(o)
 bpy.context.view_layer.objects.active=board;mod=board.modifiers.new('Crescent opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(o,do_unlink=True)

# Cream paneling below a quieter cloud wallpaper, with two real window openings.
group('RoomWalls')
for x in (-23140,23140):
 if x>0:box('Cloud side wall',(x,0,16000),(200,38000,32000),CLOUD)
 else:
  for p,s in [((x,-8500,16000),(200,21000,32000)),((x,15000,16000),(200,8000,32000)),((x,6500,4050),(200,9000,8100)),((x,6500,26550),(200,9000,10900))]:box('Bed window wall',p,s,CLOUD)
box('Cloud front wall',(0,-19100,16000),(46080,200,32000),CLOUD)
for p,s in [((-15920,19100,16000),(14240,200,32000)),((13120,19100,16000),(19840,200,32000)),((-2800,19100,4375),(12000,200,8750)),((-2800,19100,27625),(12000,200,8750))]:box('Desk window wall',p,s,CLOUD)
for side in (-1,1):
 x=side*22990
 box('Side wainscot',(x,0,2700),(100,38000,5400),WHITE)
 for y in range(-18000,19000,2100):box('Panel stile',(x-side*70,y,2700),(70,140,5000),WHITE,15)
 for z,h in ((160,320),(5200,220),(5460,180)):box('Side molding',(x-side*100,0,z),(150,38000,h),WHITE,30)
 y=side*18930
 box('End wainscot',(0,y,2700),(46080,100,5400),WHITE)
 for x in range(-22000,23000,2100):box('Panel stile',(x,y-side*70,2700),(140,70,5000),WHITE,15)
 for z,h in ((160,320),(5200,220),(5460,180)):box('End molding',(0,y-side*100,z),(46080,150,h),WHITE,30)
# Retain the room's door, rebuilding its recessed panels.
box('Bedroom door',(14000,-18840,11700),(10800,210,23400),WHITE,95)
for x in (8390,19610):box('Door casing',(x,-18580,11800),(420,480,23600),WHITE,45)
box('Door header',(14000,-18580,23600),(11600,480,450),WHITE,45)
for x in (11100,16900):
 for z,h in ((5200,6700),(15800,10200)):
  box('Door inset',(x,-18710,z),(4600,70,h),GLASS,70)
  for xx in (x-2400,x+2400):box('Door panel trim',(xx,-18630,z),(140,110,h+250),WHITE,25)
  for zz in (z-h/2,z+h/2):box('Door panel trim',(x,-18630,zz),(4900,110,140),WHITE,25)
ell('Brass door knob',(18200,-18020,10900),(270,260,270),YELLOW)

group('RoomWindow')
def window(center,width,height,side=False):
 cx,cy,cz=center
 def B(name,p,s,tile,bevel=0):
  x,y,z=p;sx,sy,sz=s
  if side:return box(name,(cx-y,cy+x,cz+z),(sy,sx,sz),tile,bevel)
  return box(name,(cx+x,cy+y,cz+z),(sx,sy,sz),tile,bevel)
 for x in (-width/2,width/2):B('White sash jamb',(x,-100,0),(420,550,height+450),WHITE,45)
 for z in (-height/2,0,height/2):B('White sash rail',(0,-140,z),(width,350,280),WHITE,25)
 B('Sill',(0,-450,-height/2),(width+700,1200,350),WHITE,50)
 B('Blue outdoors',(0,380,0),(width,60,height),GLASS)
 for x in (-width/6,width/6):B('Sash muntin',(x,-180,0),(95,190,height),WHITE,10)
 for j in range(12):B('Blind slat',(0,-330,height/2-150-j*300),(width-500,270,100),WHITE,15)
 for x in (-width*.32,width*.32):B('Blind tape',(x,-490,height*.23),(55,35,height*.48),WHITE)
window((-2800,19000,16000),12000,14500)
window((-23040,6500,14600),9000,13000,True)

# Curved maple head and foot boards with separately turned spindles.
group('RoomBed')
box('Bed base',(-15750,5850,2350),(10800,16400,600),WOOD,100)
box('Mattress',(-15750,5850,3450),(10700,15900,1000),WHITE,330)
for y,crest,ends in ((13700,9900,6200),(-2100,6900,5000)):
 for x in (-21000,-10500):
  turned('Bedpost',(x,y,0),ends-150,230,WOOD);ell('Bedpost globe',(x,y,ends+170),(350,350,350),WOOD)
 board=arch_board('Curved bed crown',-15750,y,10500,4600,crest,ends,340,WOOD,2100 if y>0 else 850)
 if y>0:crescent_cut(board,-15750,y,crest-1050)
 for j in range(1,10):
  t=2*j/10-1;top=ends+(crest-ends)*math.cos(t*math.pi/2)**1.4-(2100 if y>0 else 850)
  turned('Bed spindle',(-21000+j*1050,y,2700),max(1000,top-2700),170,WOOD)
box('Pillow',(-15750,12000,4440),(8100,2600,620),WHITE,290)
# Flat blue fabric; printed Buzz artwork is a separately tracked texture task.
box('Smooth bedspread',(-15750,4850,4000),(10700,13900,250),DENIM,100)

# Purple drawer pedestals and a shaped chair replace the brown block desk.
group('RoomDesk')
box('Cream desktop edge',(-2800,14300,7390),(13700,5600,640),WHITE,140)
box('Warm yellow desktop',(-2800,14300,7730),(13650,5550,40),YELLOW,60)
for x in (-6800,2300):
 box('Desk pedestal',(x,14700,3650),(3900 if x<0 else 2600,4600,7200),WHITE,80)
 for z in (1400,3700,6000):
  box('Purple drawer',(x,12345,z),(3500 if x<0 else 2300,180,2000),PURPLE,70)
  points=[(x+500*math.cos(math.pi+t*math.pi/16),12125,z+180*math.sin(math.pi+t*math.pi/16)) for t in range(17)]
  for a,b in zip(points,points[1:]):rod('Curved drawer pull',a,b,65,RED,verts=12)
box('Chair seat',(-1000,8900,3550),(4000,3500,450),YELLOW,180)
for x in (-2600,600):
 for y in (7500,10150):turned('Chair leg',(x,y,100),3250,140,WOOD)
arch_board('Chair scalloped back',-1000,10400,4000,4800,7800,7000,300,YELLOW,2500)
for x in (-2600,600):rod('Chair back post',(x,10400,3350),(x,10400,7000),130,WOOD)
# Red articulated lamp with paired arms, pivot joints and open bell shade.
lamp_start=len(ns['GROUPS']['RoomDesk'])
base=Vector((2500,16400,7800));a=base+Vector((0,0,280));b=base+Vector((-700,0,1500));c=base+Vector((0,-300,2800))
ell('Lamp base',base,(750,650,120),RED)
for p,q in ((a,b),(b,c)):
 for offset in (-100,100):rod('Lamp parallel arm',p+Vector((0,offset,0)),q+Vector((0,offset,0)),55,RED,verts=12)
 for k in range(12):
  f=k/12;u=p.lerp(q,f);v=p.lerp(q,f+.06)
  rod('Lamp spring',u+Vector((120,100*math.cos(k*math.pi),0)),v+Vector((120,-100*math.cos(k*math.pi),0)),25,WHITE,verts=8)
for p in (a,b,c):rod('Lamp hinge',p+Vector((0,-200,0)),p+Vector((0,200,0)),145,HAIR)
direction=Vector((-1,-.7,-.65)).normalized();n=direction;u=n.cross(Vector((0,0,1))).normalized();v=n.cross(u)
verts=[]
for depth,r in ((0,190),(850,780),(850,720),(50,140)):
 for j in range(40):verts.append(tuple(c+n*depth+(u*math.cos(j*math.tau/40)+v*math.sin(j*math.tau/40))*r))
faces=[]
for k in range(4):
 for j in range(40):faces.append((k*40+j,k*40+(j+1)%40,((k+1)%4)*40+(j+1)%40,((k+1)%4)*40+j))
mesh('Open red lamp shade',verts,faces,RED);ell('Lamp bulb',c+n*450,(180,180,180),WHITE)
for lamp_part in ns['GROUPS']['RoomDesk'][lamp_start:]:
 lamp_part.location=base+(lamp_part.location-base)*1.65
 lamp_part.scale*=1.65
for j,tile in enumerate((RED,BLUE,GREEN)):
 box('Desk book',(-6700,16000,7900+j*270),(3200,1700,250),tile,25)
for j in range(3):box('Drawing paper',(-1800,15500,7780+j*10),(2400,1400,10),WHITE,rot=.06*j)
rod('Pencil pot',(-8400,15900,7770),(-8400,15900,8650),360,BLUE)
for j,tile in enumerate((YELLOW,RED,GREEN,BLUE)):rod('Pencil',(-8550+j*100,15900,8300),(-8600+j*140,15900,9700),42,tile,verts=8)

# Open wooden shelving sits against the wall, with the two landings unobstructed.
group('RoomShelves')
for x in (15100,21600):
 for y in (12700,18800):box('Shelf post',(x,y,10600),(350,400,21200),WOOD,40)
for z in (400,5000,10000,15000,20000):box('Shelf board',(18350,15750,z),(6900,6500,450),WOOD,45)
for level,z in enumerate((630,5230,15230)):
 for j in range(7):
  h=1900+j%3*370;x=15700+j*770
  box('Leaning book',(x,16700,z+h/2),(570,2700,h),[RED,BLUE,GREEN,YELLOW,PURPLE][j%5],25,rot=(j%3-1)*.12)
  text('Book spine title',['SPACE','STARS','ABC','TOYS','PLANETS','WEST','STORY'][j],(x,15330,z+h*.5),180,WHITE)
for z in (10225,20225):
 for j in range(3):box('Checkpoint rear book',(15700+j*480,18000,z+1100),(380,1500,2200),[BLUE,RED,GREEN][j],20)
# Game boxes are tucked onto the low shelves.
for z,label,tile in ((690,'OPERATION',RED),(1500,'MOUSE TRAP',YELLOW)):
 box('Board game',(18400,14400,z),(3900,2300,650),tile,30);text('Board game title',label,(18400,13220,z-100),360,WHITE)

# Molly's crib has turned rails, pastel beads, an arched end and a hanging mobile.
group('RoomCrib')
box('Crib mattress',(0,-14500,1900),(8600,4700,550),WHITE,220)
for x in (-4600,4600):
 for y in (-17100,-11900):turned('Crib corner',(x,y,0),6400,210,WHITE);ell('Crib finial',(x,y,6650),(230,230,260),WHITE)
for y in (-17000,-12000):
 box('Crib top rail',(0,y,5700),(9400,240,280),WHITE,80);box('Crib pink trim',(0,y,5860),(9400,220,45),RED)
 box('Crib bottom rail',(0,y,1100),(9300,250,260),WHITE,60)
 for j in range(17):
  x=-4200+j*525;turned('Crib spindle',(x,y,1250),4300,105,WHITE)
  for z in (1900,4900):ell('Pastel spindle bead',(x,y,z),(145,145,190),PURPLE,16,10);small_torus('Teal spindle ring',(x,y,z+260),110,35,BLUE)
for x in (-4500,4500):
 for j in range(9):turned('Crib end spindle',(x,-16800+j*575,1500),4500,110,WHITE)
 # End crown is built in XY then rotated to span the crib width.
 board=arch_board('Crib arch',0,0,5100,5000,8000,6100,260,WHITE,900)
 for vert in board.data.vertices:
  px,py,pz=vert.co;vert.co=(x+py,-14500+px,pz)
# Curved mobile boom and a few suspended shapes.
points=[(4000,-13500,6000),(4000,-13500,7800),(3600,-13700,8800),(2700,-14100,9250),(1600,-14500,9000),(900,-14700,8300)]
for a,b in zip(points,points[1:]):rod('Mobile boom',a,b,45,WHITE,verts=12)
for j,tile in enumerate((YELLOW,GREEN,BLUE,RED)):
 angle=j*math.tau/4;p=(900+1100*math.cos(angle),-14700+1100*math.sin(angle),7900)
 rod('Mobile spoke',(900,-14700,8300),p,30,WHITE,verts=8);rod('Mobile string',p,(p[0],p[1],6800),12,WHITE,verts=6);ell('Mobile toy',(p[0],p[1],6650),(220,180,350),tile,16,12)

# Bedside table and the baby's changing cabinet give each bed its own corner.
group('RoomNightstand')
box('Nightstand cabinet',(-11000,17100,1950),(3400,2600,3900),WHITE,90)
box('Nightstand top',(-11000,17100,3980),(3700,2900,260),WHITE,65)
box('Nightstand drawer',(-11000,15755,3100),(3000,130,1100),WHITE,60)
rod('Brass drawer pull',(-11500,15580,3100),(-10500,15580,3100),90,YELLOW,verts=16)
box('Nightstand lower inset',(-11000,15740,1350),(2800,90,1700),WOOD,50)
ell('Bedside lamp body',(-11000,17400,5100),(620,620,950),RED,24,16)
rod('Bedside lamp stem',(-11000,17400,5700),(-11000,17400,6400),100,YELLOW,verts=16)
rod('Bedside lamp shade',(-11000,17400,6100),(-11000,17400,8000),1400,WHITE,r2=750,verts=48)
group('RoomNurseryCabinet')
box('Changing cabinet',(-6900,-15900,2400),(3200,4700,4800),PURPLE,100)
box('Changing top',(-6900,-15900,4880),(3450,4900,260),WHITE,70)
for z in (950,2500,4050):
 box('Nursery drawer',(-6900,-13490,z),(2850,140,1300),PURPLE,50)
 ell('Nursery knob',(-6900,-13320,z),(160,130,160),WHITE,16,10)
ell('Changing pad',(-6900,-16000,5200),(1400,2050,240),GREEN,24,12)
rod('Baby bottle',(-7000,-17800,5300),(-7000,-17800,6600),250,WHITE,verts=24)
rod('Bottle collar',(-7000,-17800,6580),(-7000,-17800,6730),270,GREEN,verts=24)
ell('Bottle teat',(-7000,-17800,6840),(130,130,180),WHITE,16,10)

# Low-profile wall art: separate borders, lettering and graphic shapes.
group('RoomPosters')
# The left-wall poster sits beside, rather than over, the new bed window.
box('Deep space poster border',(-22910,14000,14000),(75,4400,7200),WHITE)
box('Deep space poster field',(-22860,14000,14000),(20,4100,6900),DENIM)
# Text on this wall faces positive X.
for label,z,size,tile in [('LIGHTYEAR',16500,520,WHITE),('DEEP SPACE',11700,470,WHITE),('CODE',10900,760,RED)]:
 text('Poster heading',label,(-22835,14000,z),size,tile,rotation=(math.pi/2,0,math.pi/2),extrude=0)
for j in range(12):
 for side in (-1,1):
  box('Space code line',(-22832,14000+side*1000,15700-j*300),(10,1100 if j%3 else 1400,45),WHITE)
# Framed rocket/star print on the desk wall, echoing the movie's space posters.
box('Rocket print border',(-15700,18900,16100),(5000,90,7300),WHITE)
box('Rocket print field',(-15700,18835,16100),(4700,25,7000),DENIM)
rod('Poster rocket body',(-15700,18795,14200),(-15700,18795,17700),370,WHITE,verts=20)
ell('Poster rocket nose',(-15700,18795,17900),(370,55,670),RED,20,12)
box('Poster rocket wings',(-15700,18730,14500),(2300,35,380),RED)
ell('Poster blue porthole',(-15700,18680,16900),(210,40,210),BLUE,20,12)
for x,z in ((-17400,18400),(-14100,17400),(-17300,15000),(-14200,13700)):
 for a in (0,math.pi/2):
  dx,dz=180*math.cos(a),180*math.sin(a)
  rod('Poster star',(x-dx,18780,z-dz),(x+dx,18780,z+dz),35,YELLOW,verts=6)
text('Rocket print caption','SPACE RANGER',(-15700,18765,13100),400,WHITE,extrude=0)
# Oversized wristwatch wall clock, a distinctive feature of Andy's wall.
group('RoomClock')
box('Watch strap',(-22900,-4100,14200),(140,950,10000),BLUE,180)
rod('Watch case',(-22900,-4100,14800),(-22450,-4100,14800),1750,BLUE,verts=64)
rod('Clock face',(-22445,-4100,14800),(-22410,-4100,14800),1500,WHITE,verts=64)
for j in range(12):
 a=j*math.tau/12;y=-4100+1200*math.sin(a);z=14800+1200*math.cos(a)
 ell('Clock hour',(-22380,y,z),(25,80,80),BLACK,12,8)
rod('Clock minute hand',(-22350,-4100,14800),(-22350,-3750,15700),45,BLACK,verts=8)
rod('Clock hour hand',(-22340,-4100,14800),(-22340,-4700,15100),65,BLACK,verts=8)
# A covered-wagon toy chest beside the crib and clear of the start approach.
group('RoomWagonChest')
box('Wagon chest',(7600,-15900,1450),(5600,3700,2800),DARKGREEN,70)
box('Wagon plinth',(7600,-15900,200),(5900,3900,400),BLUE,35)
verts=[];faces=[]
for y in (-17800,-14000):
 for j in range(33):
  a=j*math.pi/32;verts.append((7600+2800*math.cos(a),y,2850+1550*math.sin(a)))
for j in range(32):faces.append((j,j+1,34+j,33+j))
faces.extend([tuple(reversed(range(33))),tuple(range(33,66))]);mesh('Curved wagon canopy',verts,faces,WHITE)
for x in (5900,9300):
 rod('Painted wheel',(x,-13940,1250),(x,-13905,1250),1040,RED,verts=48)
 rod('Wheel center panel',(x,-13900,1250),(x,-13885,1250),900,BLUE,verts=48)
 for j in range(12):
  a=j*math.tau/12;rod('Painted spoke',(x,-13860,1250),(x+860*math.cos(a),-13860,1250+860*math.sin(a)),35,YELLOW,verts=6)
 rod('Wheel hub',(x,-13860,1250),(x,-13820,1250),180,RED,verts=24)
for y in (-17400,-15900,-14400):
 for j in range(32):
  a=j*math.pi/32;b=(j+1)*math.pi/32
  rod('Canopy hoop',(7600+2810*math.cos(a),y,2850+1560*math.sin(a)),(7600+2810*math.cos(b),y,2850+1560*math.sin(b)),45,WHITE,verts=8)

# Join per furniture item, keeping the character meshes unchanged.
changed=[]
for name,parts in ns['GROUPS'].items():
 if not parts:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 for f in o.data.polygons:f.material_index=0
 o.data.materials.clear();o.data.materials.append(mat);o['export_material']='RoomDecorAtlas'
 while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 if name=='RoomPosters':
  from room_poster_text import correct_poster_handedness
  correct_poster_handedness(o)
 changed.append(repair_mesh(o,1024 if name in ('RoomBed','RoomDesk','RoomWalls','RoomShelves','RoomCrib') else 512))
 print('Rebuilt',name,len(o.data.polygons),flush=True)
for n,sig in protected.items():assert surface_signature(bpy.data.objects[n])==sig,n
from room_mesh_parts import split_mesh
for n in list(ns['GROUPS']):
 o=bpy.data.objects.get(n)
 if o and len(o.data.polygons)>20000:split_mesh(o)
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()/'RoomFinish.blend'))
(out/'redesign.json').write_text(json.dumps({'changed':changed,'preserved_characters':protected,'pending':['Buzz print texture','wallpaper palette refinement','route clearance']},indent=2))
print('Reference room source saved',flush=True)
