"""Apply the owner's detail pass to the accepted revision 93 source."""
import ast,bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin'),str(ROOT)]
from room_lightmaps import repair_mesh,surface_signature
from room_mesh_parts import split_mesh
SOURCE=ROOT/'output/room-repair-93';OUT=ROOT/'output/room-detail-94'
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
scene=bpy.context.scene;original={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
changed={'RoomPlane','RoomPosters','RoomWindow','RoomDesk','RoomBuzz','RoomWoody','RoomSlinky'}
removed={'RoomCheckpointDesk','RoomCheckpointBed','RoomCheckpointFinish'}
mat=bpy.data.materials['RoomEnvironment91']
module=ast.parse((ROOT/'bin/build_room_blender.py').read_text())
helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'finish','box','ell','rod','text','torus'}],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,scene=scene,mat=mat,GROUPS={},group='RoomPosters',CLOUD=1)
exec(compile(helpers,'room-shapes','exec'),ns)
box,ell,rod,text,torus=[ns[n] for n in ('box','ell','rod','text','torus')]
WOOD,CLOUD,RED,DENIM,SKIN,WHITE,GREEN,PURPLE,HAIR,BLACK,BLUE,YELLOW,ORANGE,DARKGREEN,FACE_SKIN,GLASS=range(16)

def components(bm):
 left=set(bm.verts)
 while left:
  seed=left.pop();vs={seed};todo=[seed]
  while todo:
   for e in todo.pop().link_edges:
    for v in e.verts:
     if v in left:left.remove(v);vs.add(v);todo.append(v)
  yield vs

def edit_components(name,fn):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);count=0
 for vs in list(components(bm)):
  lo=[min(v.co[k] for v in vs) for k in range(3)];hi=[max(v.co[k] for v in vs) for k in range(3)]
  count+=bool(fn(bm,vs,lo,hi))
 bm.to_mesh(o.data);bm.free();o.data.update();return count

def flat_polygon(label,points,tile):
 data=bpy.data.meshes.new(label);data.from_pydata(points,[],[tuple(range(len(points)))]);data.update()
 o=bpy.data.objects.new(label,data);scene.collection.objects.link(o);ns['finish'](o,label,tile)
 # A flat pigment samples its palette center, avoiding stray neighboring tiles.
 for uv in o.data.uv_layers[0].data:uv.uv=((tile%4+.5)/4,(tile//4+.5)/4)
 return o

def label(body,p,size,tile=WHITE,rotation=(math.pi/2,0,0)):
 o=text(body,body,p,size,tile,rotation=rotation,extrude=0)
 # UE3's reflected viewing convention needs the same lettering correction as the existing posters.
 for v in o.data.vertices:v.co.x=-v.co.x
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 return o

# Retain the checkpoint poses and remove their floor duplicates.
for name,checkpoint in [('RoomBuzz','RoomCheckpointFinish'),('RoomWoody','RoomCheckpointDesk'),('RoomSlinky','RoomCheckpointBed')]:
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True);bpy.data.objects[checkpoint].name=name
 bpy.data.objects[name]['character_identity']=name.removeprefix('Room')

# The print is now planar artwork, with no cylinder protruding through its backing.
def remove_rocket(bm,vs,lo,hi):
 if lo[0]>-18500 and hi[0]<-12800 and lo[1]>18000:
  bmesh.ops.delete(bm,geom=list(vs),context='VERTS');return True
rocket_removed=edit_components('RoomPosters',remove_rocket);assert rocket_removed>10
ns['group']='RoomPosters'
box('Rocket print border',(-15700,18900,16100),(5000,90,7300),WHITE)
box('Rocket print field',(-15700,18840,16100),(4700,25,7000),DENIM)
def ink(label_,xz,tile,depth=18820):return flat_polygon(label_,[(x,depth,z) for x,z in xz],tile)
ink('Printed rocket body',[(-16100,14300),(-15300,14300),(-15300,17500),(-16100,17500)],WHITE)
ink('Printed red nose',[(-16100,17500),(-15300,17500),(-15700,18600)],RED)
ink('Printed left fin',[(-16100,15100),(-16800,14000),(-16100,14400)],RED)
ink('Printed right fin',[(-15300,15100),(-15300,14400),(-14600,14000)],RED)
ink('Printed flame',[(-15980,14300),(-15700,13450),(-15420,14300)],YELLOW)
ink('Printed porthole',[(-15700+225*math.cos(a*math.tau/32),16650+225*math.sin(a*math.tau/32)) for a in range(32)],BLUE,18818)
for x,z in ((-17400,18400),(-14100,17400),(-17300,15000),(-14200,13700)):
 ink('Printed star',[(x+math.cos(j*math.pi/4)*(190 if j%2==0 else 55),z+math.sin(j*math.pi/4)*(190 if j%2==0 else 55)) for j in range(8)],YELLOW)
label('SPACE RANGER',(-15700,18816,13050),360)

# Window joints meet at their edges. Blinds hang forward of the sash, clear of the casing.
bpy.data.objects.remove(bpy.data.objects['RoomWindow'],do_unlink=True);ns['group']='RoomWindow';window_solids=[]
def window(center,width,height,side=False):
 cx,cy,cz=center
 def B(name,p,s,tile=WHITE,bevel=14):
  x,y,z=p;sx,sy,sz=s
  o=box(name,(cx-y,cy+x,cz+z) if side else (cx+x,cy+y,cz+z),(sy,sx,sz) if side else s,tile,bevel)
  if tile!=GLASS:window_solids.append(dict(window=list(center),part=name,center=list(p),size=list(s)))
  return o
 for x in (-width/2-140,width/2+140):B('Outside jamb',(x,-170,0),(280,440,height+560))
 for z in (-height/2-140,height/2+140):B('Outside casing rail',(0,-170,z),(width,440,280))
 # Two sash frames within the opening; bars terminate at rails instead of passing through them.
 inner=width-300
 for x in (-width/2+75,width/2-75):B('Sash side',(x,95,0),(150,160,height))
 for z in (-height/2+75,0,height/2-75):B('Sash horizontal',(0,95,z),(inner,160,150))
 for x in (-width/6,width/6):
  for sign in (-1,1):B('Sash glazing bar',(x,95,sign*(height/4-37.5)),(75,160,height/2-225))
 B('Window sill',(0,-425,-height/2-390),(width+800,950,220),WHITE,28)
 sky=B('Distant neighborhood',(0,380,0),(width,60,height),GLASS,0)
 uv=sky.data.uv_layers[0]
 for poly in sky.data.polygons:
  for li in poly.loop_indices:
   p=sky.matrix_world@sky.data.vertices[sky.data.loops[li].vertex_index].co
   u=((p.y-cy) if side else (p.x-cx))/width+.5;v=(p.z-cz)/height+.5
   uv.data[li].uv=((3+.005+.99*u)/4,(3+.005+.99*v)/4)
 B('Blind headrail',(0,-485,height/2-110),(width-500,160,160),WHITE,18)
 for j in range(12):B('Blind slat',(0,-475,height/2-350-j*290),(width-550,190,75),WHITE,12)
 for x in (-width*.32,width*.32):B('Blind tape',(x,-573,height/2-1900),(45,20,3550),WHITE,0)
window((-2800,19000,16000),12000,14500)
window((-23040,6500,14600),9000,13000,True)
# For all solid rectangular pieces, positive-volume AABB overlap is forbidden except tape attachment.
for i,a in enumerate(window_solids):
 for b in window_solids[i+1:]:
  if a['window']!=b['window'] or 'tape' in a['part'] or 'tape' in b['part']:continue
  overlap=[(a['size'][k]+b['size'][k])/2-abs(a['center'][k]-b['center'][k]) for k in range(3)]
  assert min(overlap)<=.001,(a['part'],b['part'],overlap)

# Correct the shared propeller axis and close the tiny gap at the nose.
def align_prop(bm,vs,lo,hi):
 if lo[1]>500:
  for v in vs:v.co.z-=350
  if hi[1]<800:
   for v in vs:
    if v.co.y<700:v.co.y=550
  return True
propeller_components=edit_components('RoomPlane',align_prop);assert propeller_components==2

# Open only the upper left drawer and build a hollow pedestal around it.
def open_drawer(bm,vs,lo,hi):
 if abs((lo[0]+hi[0])/2+6800)<1 and hi[1]>16900 and abs(hi[2]-7250)<1:
  bmesh.ops.delete(bm,geom=list(vs),context='VERTS');return True
 if lo[0]>-8600 and hi[0]<-5000 and lo[1]>11900 and hi[1]<12500 and lo[2]>=4990 and hi[2]<=7010:
  for v in vs:v.co.y-=1150
  return True
count=edit_components('RoomDesk',open_drawer);assert count==18,count
ns['group']='RoomDesk'
box('Pedestal lower case',(-6800,14700,2525),(3900,4600,4950),WHITE,65)
for x in (-8650,-4950):box('Pedestal side',(x,14700,6100),(200,4600,2300),WHITE,28)
box('Pedestal rear',(-6800,16900,6100),(3500,200,2300),WHITE,28)
box('Drawer interior bottom',(-6800,13100,5100),(3250,3740,150),WOOD,15)
for x in (-8475,-5125):box('Drawer side',(x,13100,5575),(150,3740,1100),WOOD,15)
box('Drawer rear',(-6800,14900,5575),(3250,140,1100),WOOD,15)
for x in (-8555,-5045):box('Drawer runner',(x,14100,5140),(50,2500,60),HAIR,8)

# Small hidden scenes have solid visible surfaces but no tiny collision wedges.
ns['group']='RoomSecretDrawer'
# A UFO has parked inside a drawer. A tiny parking ticket carries the room-number reference.
ell('Saucer dish',(-6800,11650,5310),(570,410,105),GLASS,24,12)
ell('Saucer dome',(-6800,11650,5440),(270,220,170),BLUE,24,12)
for x in (-7130,-6470):ell('Saucer foot',(x,11650,5220),(60,60,55),HAIR,12,8)
for j in range(8):
 a=j*math.tau/8;ell('Saucer running light',(-6800+460*math.cos(a),11650+315*math.sin(a),5340),(35,35,25),YELLOW,12,8)
box('Parking ticket',(-5880,11700,5185),(540,770,14),WHITE,0,rot=-.16)
o=label('A113',(-5880,11700,5194),165,RED,rotation=(0,0,-.16))
label('NO PARKING',(-6800,11203,5730),150,WHITE)
# A tiny alien face is visible through the cockpit.
ell('Pilot head',(-6800,11500,5480),(130,100,100),GREEN,16,10)
for x in (-6870,-6800,-6730):ell('Pilot eye',(x,11415,5500),(27,15,27),WHITE,12,8);ell('Pilot pupil',(x,11400,5500),(11,8,15),BLACK,12,8)

ns['group']='RoomSecretUnderBed'
# An open-front cardboard clubhouse, set back from the bed's open side.
cx,cy=-14400,-11200
box('Clubhouse back',(cx,cy-1100,730),(2700,100,1420),WOOD,18)
for x in (cx-1300,cx+1300):box('Clubhouse side',(x,cy,730),(100,2200,1420),WOOD,18)
box('Clubhouse roof',(cx,cy,1480),(2750,2250,80),WOOD,16)
box('Welcome mat',(cx,cy+1450,20),(1800,650,35),DENIM,20)
label('THE CLAW CLUB',(cx,cy+1132,1180),180,YELLOW,rotation=(math.pi/2,0,math.pi))
# A bottle-cap table and a pizza with one missing slice.
rod('Bottle cap stand',(cx,cy,25),(cx,cy,310),160,BLUE,verts=20)
rod('Bottle cap tabletop',(cx,cy,310),(cx,cy,350),620,BLUE,verts=32)
rod('Pizza crust',(cx,cy,365),(cx,cy,405),430,YELLOW,verts=32)
for j in range(6):
 a=j*math.tau/6;ell('Pepperoni',(cx+240*math.cos(a),cy+240*math.sin(a),414),(65,65,12),RED,12,8)
# A toy alien sitting on a spool, scaled to fit beneath the bed.
def mini_alien(p,scale=1):
 x,y,z=p
 def E(n,d,s,t):return ell(n,(x+d[0]*scale,y+d[1]*scale,z+d[2]*scale),tuple(v*scale for v in s),t,16,10)
 E('Alien suit',(0,0,280),(170,125,200),BLUE);E('Alien head',(0,0,575),(245,150,165),GREEN)
 for side in (-1,1):E('Alien ear',(side*255,0,620),(100,70,60),GREEN);E('Alien boot',(side*100,65,80),(95,145,80),PURPLE)
 for dx in (-130,0,130):E('Alien eye',(dx,135,595),(57,32,65),WHITE);E('Alien pupil',(dx,164,595),(24,13,32),BLACK)
 rod('Alien antenna',(x,y,z+720*scale),(x,y,z+875*scale),25*scale,GREEN,verts=10);E('Antenna tip',(0,0,900),(50,50,50),GREEN)
mini_alien((cx-870,cy-320,40),.9)
mini_alien((cx+880,cy-350,40),.85)
# The claw shrine is a tiny suspended three-prong claw over a rubber duck.
for j in range(3):
 a=j*math.tau/3;p=(cx+140*math.cos(a),cy-750+140*math.sin(a),1050);q=(cx+210*math.cos(a),cy-750+210*math.sin(a),810)
 rod('Mini claw finger',p,q,24,GLASS,verts=10)
rod('Claw string',(cx,cy-750,1420),(cx,cy-750,1060),10,HAIR,verts=8)
ell('Duck body',(cx,cy-750,140),(145,190,110),YELLOW,16,10);ell('Duck head',(cx,cy-590,260),(95,90,95),YELLOW,16,10);ell('Duck bill',(cx,cy-500,250),(90,65,35),ORANGE,12,8)
for side in (-1,1):ell('Duck eye',(cx+side*65,cy-535,280),(16,12,18),BLACK,12,8)

ns['group']='RoomSecretShelf'
# Behind the low shelf's books: a little cheese moon and a flag planted by an alien.
base=(16800,17400,650)
box('Secret moon base',(base[0],base[1],base[2]),(1600,1300,100),DENIM,25)
ell('Cheese moon',(16800,17400,1050),(530,510,370),YELLOW,24,14)
for x,y,z,s in [(16570,17060,1140,100),(16980,17010,1000,95),(16870,17200,1370,90)]:ell('Cheese crater',(x,y,z),(s,s,28),ORANGE,12,8)
rod('Flagpole',(16800,17400,1380),(16800,17400,2210),18,GLASS,verts=10)
box('Moon flag',(17040,17400,2070),(450,24,270),BLUE,8)
label('42',(17040,17381,1990),180,WHITE)

reports=[];changed_export=set(changed);new_names=[]
for name,parts in ns['GROUPS'].items():
 if name in bpy.data.objects:parts=[bpy.data.objects[name]]+parts
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 for p in o.data.polygons:p.material_index=0
 o.data.materials.clear();o.data.materials.append(mat)
 while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.016);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 o['export_material']='RoomDecorAtlas';o['export_collision']=not name.startswith('RoomSecret')
 if name.startswith('RoomSecret'):new_names.append(name)
 for piece in split_mesh(o):reports.append(dict(mesh=piece.name,lightmap=repair_mesh(piece,1024)));changed_export.add(piece.name)
# Plane edits preserve UV charts; cloned characters retain their accepted geometry and charts.
for name in ('RoomPlane','RoomBuzz','RoomWoody','RoomSlinky'):
 o=bpy.data.objects[name];o['export_material']='RoomDecorAtlas';reports.append(dict(mesh=name,lightmap=repair_mesh(o,o.get('lightmap_resolution',1024))))
for name,sig in original.items():
 if name not in changed|removed:assert surface_signature(bpy.data.objects[name])==sig,name
manifest=json.loads((SOURCE/'room-manifest.json').read_text());manifest['meshes']=[m for m in manifest['meshes'] if m['name'] not in removed]
known={m['name'] for m in manifest['meshes']}
for name in changed_export-known:manifest['meshes'].append(dict(name=name,material='RoomDecorAtlas',collision=bpy.data.objects[name].get('export_collision',True)))
for row in manifest['meshes']:
 o=bpy.data.objects[row['name']];vs=[o.matrix_world@v.co for v in o.data.vertices]
 row.update(triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',256),collision=o.get('export_collision',True),bounds=[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'))
manifest['source_sha256']=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest();manifest['triangles']=sum(m['triangles'] for m in manifest['meshes']);(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'detail.json').write_text(json.dumps(dict(changed=sorted(changed_export),removed=sorted(removed),preserved=sorted(set(original)-changed-removed),new_secrets=new_names,lightmaps=reports,window_solids=window_solids,drawer_open_offset=1150,propeller_axis_z=22050),indent=2))
print('Saved detail94:',len(manifest['meshes']),'meshes;',len(changed_export),'changed/new; character duplicates removed')
