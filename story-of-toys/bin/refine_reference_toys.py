"""Refine toy silhouettes, faces and molded details against the owner's reference images."""
import ast,bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin')]
from room_lightmaps import repair_mesh,surface_signature
from room_mesh_parts import split_mesh
SOURCE=ROOT/'output/room-detail-94';OUT=ROOT/'output/room-toys-94b';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
scene=bpy.context.scene;old={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
target_names=['RoomBuzz','RoomWoody','RoomSlinky','RoomRex','RoomHamm','RoomAliens','RoomCheckpointHat','RoomCheckpointPlane','RoomCheckpointStart','RoomCheckpointLowerShelf','RoomCheckpointUpperShelf']
targets={}
for name in target_names:
 o=bpy.data.objects[name];vs=[o.matrix_world@v.co for v in o.data.vertices];targets[name]=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]
# A purpose-made UV palette keeps pink vinyl, lime armor and blue cloth distinct from room paint.
colors=[(.40,.19,.065),(.46,.48,.22),(.70,.035,.025),(.035,.105,.32),(.78,.48,.30),(.84,.86,.79),(.34,.70,.045),(.29,.075,.47),(.095,.031,.01),(.009,.012,.018),(.025,.24,.59),(.95,.57,.075),(.90,.24,.035),(.105,.32,.035),(.77,.32,.37),(.50,.56,.61)]
N=256;pixels=np.ones((N,N,4),np.float32)
for i,c in enumerate(colors):pixels[(i//4)*64:(i//4+1)*64,(i%4)*64:(i%4+1)*64,:3]=c
im=bpy.data.images.new('RoomToyPalette94',width=N,height=N,alpha=False);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(OUT/'RoomToyPalette94.tga');im.file_format='TARGA_RAW';im.save();im.pack()
mat=bpy.data.materials.new('RoomToyPalette94');mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.58
source=(ROOT/'bin/build_room_blender.py').read_text();module=ast.parse(source);helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'finish','box','ell','rod','text','torus'}],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,Matrix=Matrix,scene=scene,mat=mat,GROUPS={},group='RoomBuzz',CLOUD=1)
for i,n in enumerate(['WOOD','CLOUD','RED','DENIM','SKIN','WHITE','GREEN','PURPLE','HAIR','BLACK','BLUE','YELLOW','ORANGE','DARKGREEN','FACE_SKIN','GLASS']):ns[n]=i
exec(compile(helpers,'toy-shapes','exec'),ns)
base_ell,base_box,base_rod,base_torus=ns['ell'],ns['box'],ns['rod'],ns['torus']
SKIP={'Woody hat brim','Woody hat crown','Woody smile','Sheriff badge','Rex mouth','Rex tooth','Slinky metal spring','Slinky tail','Hamm eye','Hamm pupil','Hamm ear','Buzz panel','Buzz chest button'}
def ell(name,p,s,tile,segments=24,rings=14,**kw):
 if name in SKIP:return None
 p=list(p);s=list(s)
 if name.startswith('Hamm') and tile==4:tile=14
 if name=='Hamm head':s=[880,730,780]
 if name=='Hamm snout':s=[560,210,380];p[1]=-2070
 if name=='Hamm nostril':p[1]=-2280;s=[85,28,85]
 if name=='Hamm hoof':tile=9
 if name=='Buzz face':s=[280,220,360];p[1]=-220
 if name=='Buzz eye':p[1]=-435;s=[80,30,75]
 if name=='Buzz iris':tile=10;s=[29,17,36];p[1]=-463
 if name=='Buzz nose':p[1]=-451
 if name=='Buzz chin':s=[220,180,145];p[1]=-280;p[2]=2780
 if name=='Buzz glove':s=[185,185,210]
 if name=='Woody head':s=[300,275,470]
 if name=='Woody eye':s=[88,38,115];p[1]=-267;p[2]+=15
 if name=='Woody pupil':s=[38,18,53];p[1]=-299;p[2]+=15
 if name=='Woody nose':s=[66,100,118];p[1]=-311
 if name=='Slinky head':s=[600,540,630]
 if name=='Slinky floppy ear':s=[190,200,720];p[2]=1150;p[1]=-1320
 if name=='Slinky eye':s=[185,95,255];p[1]=-1670;p[2]=1730
 if name=='Slinky pupil':s=[79,38,125];p[1]=-1753;p[2]=1720
 if name=='Slinky muzzle':s=[450,300,245];p[1]=-1780;p[2]=1330
 if name=='Rex belly':tile=1;s=[590,180,1040];p[1]=-850
 if name=='Rex head':s=[800,1160,610];p[2]=3940
 if name=='Rex muzzle':s=[760,670,280];p[2]=3670
 if name=='Rex eye':s=[200,170,245];p[2]=4250
 if name=='Rex pupil':s=[78,45,115];p[2]=4250
 if name=='Rex toe':s=[80,160,75];tile=0
 return base_ell(name,p,s,tile,segments=segments,rings=rings,**kw)
def box(name,p,s,tile,bevel=0,rot=0):
 if name in SKIP:return None
 if name=='Buzz chest':return base_ell(name,(0,-320,2370),(615,240,460),tile,24,16)
 if name=='Cowhide vest':s=(250,90,850);bevel=80
 return base_box(name,p,s,tile,bevel,rot)
def rod(name,a,b,r,tile,r2=None,verts=16):
 if name in SKIP:return None
 if name.startswith('Hamm') and tile==4:tile=14
 if name in ('Buzz eyebrow','Buzz smile'):a=(a[0],-446,a[2]);b=(b[0],-446,b[2])
 return base_rod(name,a,b,r,tile,r2,verts)
def torus(name,p,major,minor,tile,rotation=(0,0,0)):
 if name in SKIP:return None
 if name.startswith('Hamm') and tile==4:tile=14
 return base_torus(name,p,major,minor,tile,rotation)
ns.update(ell=ell,box=box,rod=rod,torus=torus)
# Build in the original authoring frames, then fit each toy to its retained placement.
code=source[source.index("group='RoomBuzz';buzzstart"):source.index('# Toy companions sit beside')]
# Existing surface text would be mirrored by UE3; the new panel names use molded marks instead.
code=code.replace("text('Buzz name','LIGHTYEAR',(-180,-487,2520),72,BLACK,extrude=1)","")
exec(compile(code,'reference-toys','exec'),ns)
# Remove original placement transforms so additional molded details share a local frame.
placements={'RoomBuzz':((6600,-4300,0),-.35),'RoomWoody':((-5200,-9500,55),-.45),'RoomRex':((11900,4700,0),.65),'RoomHamm':((17000,-5400,0),-.6),'RoomSlinky':((-8200,3000,0),-.6)}
for name,(p,a) in placements.items():
 inverse=(Matrix.Translation(Vector(p))@Matrix.Rotation(a,4,'Z')).inverted()
 for o in ns['GROUPS'][name]:o.matrix_world=inverse@o.matrix_world

def group(n):ns['group']=n

def tube(name,points,radius,tile,sides=8):
 verts=[]
 for i,p in enumerate(points):
  p=Vector(p);n=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized();u=n.cross(Vector((0,0,1)) if abs(n.z)<.9 else Vector((0,1,0))).normalized();v=n.cross(u)
  for j in range(sides):verts.append(p+radius*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides)))
 faces=[tuple(reversed(range(sides))),tuple(range(len(verts)-sides,len(verts)))];faces += [(i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j) for i in range(len(points)-1) for j in range(sides)]
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);ns['finish'](o,name,tile,True);return o

def patch(name,points,tile):
 m=bpy.data.meshes.new(name);m.from_pydata(points,[],[tuple(range(len(points)))]);m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);ns['finish'](o,name,tile);return o
# Woody: curved stitched brim, pinched crown, hair, expressive mouth and a five-point badge.
group('RoomWoody');NSEG=64;vertices=[]
for down in (False,True):
 for r in (.38,1):
  for i in range(NSEG):
   a=i*math.tau/NSEG;x=760*r*math.cos(a);y=560*r*math.sin(a);z=3500+115*(abs(x)/760)**3-40*max(0,-y/560)-(35 if down else 0);vertices.append((x,y,z))
faces=[]
for i in range(NSEG):
 j=(i+1)%NSEG
 faces.extend([(i,j,NSEG+j,NSEG+i),(2*NSEG+i,3*NSEG+i,3*NSEG+j,2*NSEG+j),(NSEG+i,NSEG+j,3*NSEG+j,3*NSEG+i),(i,2*NSEG+i,2*NSEG+j,j)])
m=bpy.data.meshes.new('Stitched cowboy brim');m.from_pydata(vertices,[],faces);m.update();o=bpy.data.objects.new('Stitched cowboy brim',m);scene.collection.objects.link(o);ns['finish'](o,o.name,0,True)
base_ell('Pinched cowboy crown',(0,25,3695),(390,310,260),0,40,20)
base_ell('Crown pinch',(0,25,3925),(220,140,14),8,24,12)
base_torus('Hat band',(0,0,3570),340,30,8)
for i in range(40):
 a=i*math.tau/40;b=a+.045
 tube('Brim stitch',[(710*math.cos(t),515*math.sin(t),3530+105*abs(math.cos(t))**3-35*max(0,-math.sin(t))) for t in (a,b)],7,11,6)
base_ell('Hair cap',(0,70,3400),(307,237,185),8,24,14)
for side in (-1,1):
 base_ell('Sideburn',(side*260,-100,3210),(55,70,150),8,16,10)
 tube('Woody eyebrow',[(side*115-88+j*22,-292,3325+30*math.sin(j*math.pi/8)) for j in range(9)],15,8)
 base_ell('Eye catchlight',(side*115-12,-321,3220),(12,8,17),5,12,8)
base_ell('Open friendly smile',(0,-260,2940),(145,42,86),8,24,12)
base_box('Woody smile teeth',(0,-300,2980),(235,14,31),5,10)
tube('Lower smile lip',[(-120+30*j,-287,2900-17*math.sin(j*math.pi/8)) for j in range(9)],10,4)
star=[(-290+math.cos(math.pi/2+j*math.pi/5)*(110 if j%2==0 else 46),-325,2450+math.sin(math.pi/2+j*math.pi/5)*(110 if j%2==0 else 46)) for j in range(10)];patch('Sheriff star',star,11)
for side in (-1,1):patch('Shirt collar',[(side*200,-231,2700),(side*30,-300,2650),(side*210,-300,2480)],5)
# Buzz: armor seams, ribbed waist, wrist control, insignia and the chin curl.
group('RoomBuzz')
for z in range(1670,1931,65):base_torus('Black waist rib',(0,0,z),410,32,9)
for side in (-1,1):
 base_torus('Buzz ankle joint',(side*250,0,460),195,35,7)
 base_box('Boot sole',(side*250,-160,75),(460,640,90),6,35)
 base_ell('Elbow insert',(side*900,-310,1890),(120,70,125),7,16,10)
 base_ell('Knee armor',(side*250,-188,950),(155,70,175),6,20,12)
base_box('Wrist red control',(950,-486,1590),(180,30,190),2,20)
for j,tile in enumerate((10,6,12)):base_box('Colored suit control',(-315+j*90,-552,2395),(52,35,180),tile,22)
base_ell('Red chest button',(300,-555,2420),(108,36,108),2,24,12)
patch('Space ranger wings',[(-230,-557,2640),(-85,-557,2550),(70,-557,2640),(-15,-557,2590),(-85,-557,2620),(-155,-557,2590)],10)
base_box('Chest name panel',(-170,-557,2585),(280,14,80),5,9)
for j in range(4):base_box('Nameplate mark',(-260+j*56,-572,2585),(25,12,38),9,3)
tube('Buzz chin curl',[(32*math.cos(a),-446,2805+32*math.sin(a)) for a in [j*.14 for j in range(37)]],8,8,6)
# Slinky has one continuous helical wire instead of separate hoops.
group('RoomSlinky')
points=[(510*math.cos(t),-900+1800*i/416,800+510*math.sin(t)) for i in range(417) for t in [i/416*math.tau*13]];tube('Continuous spring',points,27,15,6)
base_torus('Green collar',(0,-1260,1300),430,60,6)
base_ell('Open dog mouth',(0,-1830,1180),(285,90,150),9,20,12)
base_ell('Pink dog tongue',(0,-1900,1080),(110,50,130),14,20,12)
for side in (-1,1):base_ell('Dog eye highlight',(side*200-24,-1790,1780),(26,14,36),5,12,8)
tube('Coiled tail',[(110*math.cos(t),1320+i*8,1100+110*math.sin(t)+i*5) for i in range(81) for t in [i*.35]],18,15,8)
base_ell('Tail tip',(110*math.cos(80*.35),1960,1500+110*math.sin(80*.35)),(90,90,90),0,16,10)
# Hamm's eyes are black beads, with pink inner ears and split black hooves.
group('RoomHamm')
for side in (-1,1):
 base_ell('Pig black eye',(side*450,-1980,1460),(95,44,122),9,20,12)
 base_ell('Pig eye highlight',(side*450-22,-2017,1500),(22,12,28),5,12,8)
 e=base_ell('Pink pig ear',(side*690,-1180,1880),(250,120,360),14,20,12);e.rotation_euler[1]=side*-.28
 e=base_ell('Pig ear inside',(side*690,-1280,1910),(150,30,235),14,20,12);e.rotation_euler[1]=side*-.28
 tube('Pig eyebrow',[(side*450-115+j*28,-1932,1650+35*math.sin(j*math.pi/8)) for j in range(9)],18,8)
for x in (-720,720):
 for y in (-850,850):base_box('Hoof split',(x,y-285,120),(22,20,145),14,4)
# Rex: a continuous smiling jaw, teeth on both sides, and molded scale/belly detail.
group('RoomRex')
base_ell('Rex open mouth',(0,-1710,3550),(640,310,170),9,24,14)
base_ell('Rex lower jaw',(0,-1700,3350),(650,420,190),13,24,14)
for side in (-1,1):
 for i in range(7):
  x=side*(120+i*75);y=-1970+90*(i/6)**2
  base_rod('Rex upper tooth',(x,y,3655),(x,y,3485),45,5,1,12)
  base_rod('Rex lower tooth',(x,y,3410),(x,y,3510),36,5,1,12)
for z in range(1050,2530,150):
 width=490*math.sqrt(max(.05,1-((z-1750)/1040)**2));tube('Belly scale row',[(x,-860-180*math.sqrt(max(.01,1-(x/590)**2-((z-1750)/1040)**2)),z) for j in range(17) for x in [-width+j*width/8]],8,13,6)
for j in range(12):
 for i in range(13):
  a=i*math.tau/13;z=800+j*240;r=math.sqrt(max(.05,1-((z-1850)/1550)**2));x=945*r*math.cos(a);y=945*r*math.sin(a)
  if y< -450:continue
  base_ell('Molded dinosaur scale',(x,y,z),(30,30,23),13,10,6)
# Suit collars, sleeve cuffs and the planet badge make all three-eyed aliens read as toys.
group('RoomAliens')
# Aliens already sit in their original three placements; detail each in that same frame.
for n,(x,y) in enumerate(((7000,10500),(9600,12400),(7200,14500))):
 before=len(ns['GROUPS']['RoomAliens']);base_torus('Alien purple collar',(0,0,1310),340,65,7)
 base_ell('Planet badge',(180,-312,970),(100,30,70),11,16,10)
 ring=base_torus('Planet orbit',(180,-335,970),112,12,11,rotation=(math.pi/2,0,.3))
 for side in (-1,1):base_ell('Alien cuff',(side*615,-99,840),(155,130,70),7,16,10)
 transform=Matrix.Translation(Vector((x,y,0)))@Matrix.Rotation((n-1)*.4,4,'Z')
 for o in ns['GROUPS']['RoomAliens'][before:]:o.matrix_world=transform@o.matrix_world

# Join the authored figures before making their positioned copies.
models={}
for name,parts in ns['GROUPS'].items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='DetailModel_'+name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 models[name]=o
# A single alien model comes from the first fully assembled member of the group.
aliens=models['RoomAliens'];single=aliens.copy();single.data=aliens.data.copy();scene.collection.objects.link(single);single.name='DetailModel_SingleAlien'
bm=bmesh.new();bm.from_mesh(single.data);drop=[v for v in bm.verts if v.co.y>11600];bmesh.ops.delete(bm,geom=drop,context='VERTS');bm.to_mesh(single.data);bm.free();single.data.update()
reports=[];replacement=[];new_rows=[]
angles={'RoomBuzz':math.pi/2-.35,'RoomWoody':-.45,'RoomSlinky':math.pi/2-.6,'RoomRex':.65,'RoomHamm':-.6,'RoomCheckpointLowerShelf':-.6,'RoomCheckpointUpperShelf':.65}
for name in target_names:
 source_name={'RoomCheckpointLowerShelf':'RoomHamm','RoomCheckpointUpperShelf':'RoomRex'}.get(name,name)
 model=single if name.startswith('RoomCheckpoint') and name not in ('RoomCheckpointLowerShelf','RoomCheckpointUpperShelf') else models[source_name]
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 o=model.copy();o.data=model.data.copy();scene.collection.objects.link(o);o.name=name
 if name in angles:
  R=Matrix.Rotation(angles[name],4,'Z')
  for v in o.data.vertices:v.co=R@v.co
 # Uniform fit preserves the repaired proportions while retaining all old clearance bounds.
 vs=o.data.vertices;lo=[min(v.co[k] for v in vs) for k in range(3)];hi=[max(v.co[k] for v in vs) for k in range(3)];bounds=targets[name]
 scale=min((bounds[k][1]-bounds[k][0])/(hi[k]-lo[k]) for k in range(3))
 center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]));dest=Vector(((bounds[0][0]+bounds[0][1])/2,(bounds[1][0]+bounds[1][1])/2,bounds[2][0]))
 for v in vs:v.co=dest+(v.co-center)*scale
 o.data.update();o['export_material']='RoomToyPalette94';o['export_collision']=True
 while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 for piece in split_mesh(o,triangle_limit=9000):
  reports.append(dict(mesh=piece.name,lightmap=repair_mesh(piece,2048)));replacement.append(piece.name)
  vs=[piece.matrix_world@v.co for v in piece.data.vertices];new_rows.append(dict(name=piece.name,material='RoomToyPalette94',collision=True,triangles=len(piece.data.polygons),lightmap_resolution=piece.get('lightmap_resolution',2048),bounds=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]))
for o in [*models.values(),single]:bpy.data.objects.remove(o,do_unlink=True)
for n,sig in old.items():
 if n not in target_names:assert surface_signature(bpy.data.objects[n])==sig,n
manifest=json.loads((SOURCE/'room-manifest.json').read_text());manifest['meshes']=[r for r in manifest['meshes'] if r['name'] not in target_names]+new_rows
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'))
manifest['source_sha256']=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest();manifest['triangles']=sum(m['triangles'] for m in manifest['meshes']);(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
previous=json.loads((SOURCE/'detail.json').read_text());previous['changed']=sorted(set(previous['changed'])|set(replacement));previous['preserved']=sorted(set(previous['preserved'])-set(target_names));previous['toys']=dict(replaced=target_names,parts=replacement,placement_envelopes=targets,lightmaps=reports);(OUT/'detail.json').write_text(json.dumps(previous,indent=2))
print('Saved refined reference toys:',len(manifest['meshes']),'room parts')
