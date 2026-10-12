"""Revision 96: readable lettering, stable surfaces and recognizable small props."""
import ast,bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'bin')]
from room_lightmaps import repair_mesh,surface_signature
from room_palette_uv import fit_palette_uv
from room_mesh_parts import split_mesh
from course import DECKS
from checkpoint_props import SUPPORT_TOPS
SOURCE=ROOT/'output/room-checkpoints-95';OUT=ROOT/'output/room-details-96';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
old={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
changed=set();removed=set();reports=[];labels=[]
mat=bpy.data.materials['RoomToyPalette94'];module=ast.parse((ROOT/'bin/build_room_blender.py').read_text())
helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'finish','box','ell','rod','torus','text'}],type_ignores=[])
ns=dict(bpy=bpy,math=math,Vector=Vector,mat=mat,GROUPS={},group='',CLOUD=1);exec(compile(helpers,'detail96-shapes','exec'),ns)
box,ell,rod,torus=[ns[n] for n in ('box','ell','rod','torus')]
def group(name):ns['group']=name

def mesh(name,vertices,faces,tile,smooth=False):
 m=bpy.data.meshes.new(name);m.from_pydata(vertices,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(o);return ns['finish'](o,name,tile,smooth)

def tube(name,points,radius,tile,sides=12):
 # Bezier bevel gives curved, round fingers and cables with closed ends.
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=5;d.bevel_depth=radius;d.bevel_resolution=2;d.use_fill_caps=True
 s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for v,p in zip(s.bezier_points,points):v.co=p;v.handle_left_type=v.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');return ns['finish'](bpy.context.object,name,tile,True)

def label(body,p,size,tile=5,rotation=(math.pi/2,0,0),width=None):
 o=ns['text'](body,body,p,size,tile,rotation=rotation,extrude=2)
 # XYZ stays fixed during UE3 export, whose camera basis is left-handed.
 # Reflect glyphs in their own horizontal axis, preserving the baseline and normal.
 for v in o.data.vertices:v.co.x=-v.co.x
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 if width and o.dimensions.x>width and abs(rotation[2])<.01:o.scale.x*=width/o.dimensions.x
 labels.append(dict(text=body,position=list(p),rotation=list(rotation),mirrored_for_ue3=True));return o

def components(o):
 bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);result=[]
 while left:
  v=left.pop();vs={v};todo=[v]
  while todo:
   for e in todo.pop().link_edges:
    for w in e.verts:
     if w in left:left.remove(w);vs.add(w);todo.append(w)
  ps=[o.matrix_world@v.co for v in vs];lo=Vector([min(p[k] for p in ps) for k in range(3)]);hi=Vector([max(p[k] for p in ps) for k in range(3)])
  result.append((vs,lo,hi))
 return bm,result

def drop_components(name,predicate):
 o=bpy.data.objects[name];bm,rows=components(o);drop=[v for vs,lo,hi in rows if predicate(lo,hi) for v in vs]
 if drop:bmesh.ops.delete(bm,geom=drop,context='VERTS');bm.to_mesh(o.data);o.data.update();changed.add(name)
 bm.free();return len(drop)

def remove(name):
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True);removed.add(name)

# Book spines: replace oversize horizontal words that cross adjacent books.
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.startswith('RoomShelves'):
  drop_components(o.name,lambda lo,hi:hi.y-lo.y<15)
  if not o.data.polygons:remove(o.name)
group('RoomBookLettering96')
for z in (630,5230,15230):
 for j,title in enumerate(('SPACE','STARS','ABC','TOYS','PLANETS','WEST','STORY')):
  x=15700+j*770;h=1900+j%3*370;angle=(j%3-1)*.12
  # Titles run up each spine, rotated with that book. Slightly forward of the cover.
  p=Vector((x,16700,z+h/2))+Matrix.Rotation(angle,3,'Z')@Vector((0,-1380,0))
  o=label(title,p,155,rotation=(math.pi/2,math.pi/2,angle));o.scale.x=.9
for z,title in ((690,'OPERATION'),(1500,'MOUSE TRAP')):label(title,(18400,13200,z-95),300,width=3300)
# Mirror remaining original alphabet/chest geometry about its own label center.
o=bpy.data.objects['RoomToys'];bm,rows=components(o);flipped=0
for vs,lo,hi in rows:
 if hi.y-lo.y>12 or hi.z-lo.z<30:continue
 # Text lies on front-facing planes; collect all glyphs by the original label plane.
 y=(lo.y+hi.y)/2
 centers={-7040:-2500,-8040:-300,-7540:-1400,-5540:-5000,-16196:17875}
 match=min(centers,key=lambda k:abs(k-y))
 if abs(match-y)>15:continue
 for v in vs:v.co.x=2*centers[match]-v.co.x
 bmesh.ops.reverse_faces(bm,faces=list({f for v in vs for f in v.link_faces}));flipped+=1
bm.to_mesh(o.data);bm.free();o.data.update();changed.add(o.name)
# Flat rug uses adjacent color regions, never floating overlapping strips.
count=drop_components('RoomToys',lambda lo,hi:hi.z<60 and lo.x>=-7010 and hi.x<=7010 and lo.y>=-14760 and hi.y<=-5240)
assert count>0
group('RoomRug96');xs=sorted(set([-7000,-6590,-6410,6410,6590,7000]+[a for i in range(7) for a in (-6050+i*1800,-4950+i*1800)]));ys=[-14750,-14290,-14110,-13400,-6600,-5890,-5710,-5250]
verts=[(x,y,48) for y in ys for x in xs];faces=[];tiles=[]
for j in range(len(ys)-1):
 for i in range(len(xs)-1):
  x=(xs[i]+xs[i+1])/2;y=(ys[j]+ys[j+1])/2;tile=10
  if (6410<abs(x)<6590 and -14500<y<-5500) or (-14290<y<-14110 or -5890<y<-5710) and abs(x)<6500:tile=11
  if -13400<y<-6600:
   for k in range(7):
    if -6050+k*1800<x<-4950+k*1800:tile=(2,6,11)[k%3]
  a=j*len(xs)+i;faces.append((a,a+1,a+1+len(xs),a+len(xs)));tiles.append(tile)
o=mesh('Single rug top',verts,faces,10)
for f,tile in zip(o.data.polygons,tiles):
 for li in f.loop_indices:o.data.uv_layers[0].data[li].uv=((tile%4+.5)/4,(tile//4+.5)/4)
box('Rug backing',(0,-10000,20),(14000,9500,40),10)
# Existing title-free closed books become larger, thicker volumes lying flat.
for i in (4,5,7):
 remove('RoomCheckpointBook'+str(i));group('RoomCheckpointBook'+str(i));x,y,_=DECKS[i];z=SUPPORT_TOPS[i];color={4:7,5:3,7:10}[i]
 # Covers and page block sit entirely above the supporting shelf.
 box('Lower book cover',(x,y,z+23),(2260,2740,26),color,10)
 box('Page block',(x+18,y,z+143),(2170,2650,212),5,12)
 box('Top book cover',(x,y,z+257),(2260,2740,26),color,10)
 box('Rounded cloth spine',(x-1100,y,z+140),(100,2740,240),color,40)
 for dy in (-1050,1050):box('Spine gold band',(x-1154,y+dy,z+140),(12,75,215),11,4)
 # Embossed design is outside the star/arrival corridor.
 for dy in (-920,920):box('Cover gold rule',(x,y+dy,z+275),(1640,26,10),11,3)
 title={4:'SPACE',5:'STORIES',7:'FLIGHT'}[i];label(title,(x,y+570,z+283),250,11,rotation=(0,0,0),width=1550)
# Plane: keep accepted wing/collision and replace only nose fittings.
assert drop_components('RoomPlane',lambda lo,hi:lo.y>500)>=30
group('RoomPlaneDetails96');cx,cy,cz=-4000,800,22050
rod('Propeller shaft',(cx,500,cz),(cx,960,cz),125,15,verts=32)
ell('Spinner',(cx,985,cz),(245,235,245),2,40,20)
# Swept airfoil section with thick root, broad middle and rounded narrow tip.
for side in (-1,1):
 vertices=[];faces=[];rings=12;segments=12
 for r in range(rings):
  t=r/(rings-1);distance=180+1330*t;width=55+155*math.sin(math.pi*t)**.65;thick=45*(1-.65*t);sweep=160*t*t;pitch=math.radians(26-14*t)
  for j in range(segments):
   a=j*math.tau/segments;xx=side*distance;zz=sweep+width*math.cos(a);yy=thick*math.sin(a)
   zz,yy=zz*math.cos(pitch)-yy*math.sin(pitch),zz*math.sin(pitch)+yy*math.cos(pitch)
   angle=math.radians(32);vertices.append((cx+xx*math.cos(angle)-side*zz*math.sin(angle),cy+yy,cz+xx*math.sin(angle)+side*zz*math.cos(angle)))
 for r in range(rings-1):
  for j in range(segments):k=r*segments+j;n=r*segments+(j+1)%segments;faces.append((k,n,n+segments,k+segments))
 faces.extend([tuple(reversed(range(segments))),tuple(range((rings-1)*segments,rings*segments))]);mesh('Pitched propeller blade',vertices,faces,8,True)
# Windows follow the elliptical fuselage, keeping white rims outside its skin.
for side in (-1,1):
 for yy in (-4100,-3000,-1900):
  xx=620*math.sqrt(1-((yy+3000)/3600)**2)
  ell('Cabin window rim',(cx+side*(xx+4),yy,22100),(32,270,245),5,24,16)
  ell('Blue cabin glass',(cx+side*(xx+34),yy,22100),(22,220,197),10,24,16)
# Remove old UFO and its ticket. The open drawer becomes a 2319 incident scene.
remove('RoomSecretDrawer');group('RoomSecretDrawer');mx,my,mz=-6870,11870,5555
ell('Mike round green body',(mx,my,mz),(325,245,340),6,40,28)
ell('Mike eye white',(mx,my-225,mz+85),(235,60,225),5,40,24)
ell('Mike iris blue',(mx,my-280,mz+85),(108,28,120),10,32,20)
ell('Mike pupil',(mx,my-304,mz+85),(52,16,73),9,24,16)
ell('Mike eye glint',(mx-26,my-319,mz+130),(24,9,30),5,16,12)
ell('Mike mouth',(mx,my-224,mz-180),(165,32,70),9,28,16)
box('Mike grin',(mx,my-253,mz-160),(255,18,31),5,12)
for side in (-1,1):
 rod('Mike ivory horn',(mx+side*235,my,mz+235),(mx+side*285,my+5,mz+385),70,5,4,20)
 tube('Mike arm',[(mx+side*300,my,mz),(mx+side*430,my-10,mz+140),(mx+side*440,my-150,mz+70)],35,6)
 ell('Mike hand',(mx+side*440,my-150,mz+95),(55,36,70),6,20,12)
 tube('Mike leg',[(mx+side*160,my,mz-280),(mx+side*175,my-15,5210)],40,6)
 ell('Mike toes',(mx+side*175,my-70,5210),(85,130,43),6,20,12)
# Blue Monsters Inc hard hat and a sock: an unmistakable incident gag.
ell('Mike hard hat',(mx,my,mz+310),(220,200,105),10,28,16)
ell('Hat rim',(mx,my-35,mz+285),(265,240,22),10,32,12)
box('Incident sign',(-5850,11960,5490),(610,70,540),11,25)
label('2319',(-5850,11915,5490),210,9,width=540)
label('SOCK ALERT',(-5850,11915,5340),72,9,width=540)
box('Lost white sock',(-5850,11600,5210),(180,350,40),5,20)
ell('Sock toe',(-5760,11465,5210),(160,100,32),5,20,12)
# Claw: cable, actuator, three pivoted curved metal fingers with inward hooks.
assert drop_components('RoomSecretUnderBed',lambda lo,hi:lo.x>-14700 and hi.x<-14100 and lo.y>-12200 and hi.y<-11700 and lo.z>700 and hi.z<1450)>0
group('RoomClaw96');cx,cy=-14400,-11950
rod('Claw cable',(cx,cy,1440),(cx,cy,1250),18,9,verts=16)
rod('Claw motor housing',(cx,cy,1150),(cx,cy,1260),112,15,90,32)
ell('Claw actuator',(cx,cy,1135),(135,135,75),15,28,16)
for i in range(3):
 a=i*math.tau/3;u=Vector((math.cos(a),math.sin(a),0));v=Vector((-math.sin(a),math.cos(a),0));p=Vector((cx,cy,1100))+u*100
 rod('Claw hinge pin',p-v*50,p+v*50,36,9,verts=20)
 points=[Vector((cx,cy,z))+u*r for r,z in [(100,1100),(210,1000),(265,820),(220,670),(85,590)]]
 tube('Curved gripping finger',points,31,15)
 rod('Claw finger link',Vector((cx,cy,1180))+u*75,points[1],17,15,verts=16)
 ell('Rubber gripping tip',points[-1],(40,40,45),9,16,12)
# Hair uses the solid brown swatch with real UV derivatives, independent of face atlas.
for o in list(bpy.data.objects):
 if o.type!='MESH' or not o.name.startswith('RoomAndyHead'):continue
 bm=bmesh.new();bm.from_mesh(o.data);uv=bm.loops.layers.uv[0];hair=[f for f in bm.faces if all(int(l[uv].uv.x*4)==0 and int(l[uv].uv.y*4)==2 for l in f.loops)]
 if not hair:bm.free();continue
 # Copy just scalp faces; preserve the accepted fitted silhouette under the hat.
 ids=sorted({v.index for f in hair for v in f.verts});bm.verts.ensure_lookup_table();remap={v:i for i,v in enumerate(ids)}
 group('RoomAndyHair96');h=mesh('Clean scalp', [tuple(o.matrix_world@bm.verts[i].co) for i in ids],[tuple(remap[v.index] for v in f.verts) for f in hair],8,True)
 bmesh.ops.delete(bm,geom=hair,context='FACES');bm.to_mesh(o.data);bm.free();o.data.update();changed.add(o.name)
 # The old scalloped relief is smoothed at a scale below its silhouette.
 bpy.context.view_layer.objects.active=h;mod=h.modifiers.new('Quiet scalp relief','SMOOTH');mod.factor=.32;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)

# Finalize newly authored groups, retaining separate material and collision metadata.
for name,parts in ns['GROUPS'].items():
 if not parts:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
 o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 o['export_material']='RoomToyPalette94';o['export_collision']=not name.startswith(('RoomSecret','RoomClaw','RoomBookLettering'))
 for piece in split_mesh(o,18000):
  reports.append(dict(name=piece.name,lightmap=repair_mesh(piece,512 if len(piece.data.polygons)<6000 else 1024)));fit_palette_uv(piece.data);changed.add(piece.name)
for name in changed:
 if name in old and name not in removed:
  o=bpy.data.objects[name]
  if name not in ns['GROUPS']:reports.append(dict(name=name,lightmap=repair_mesh(o,o.get('lightmap_resolution',512))))
for name,sig in old.items():
 if name not in changed and name not in removed:assert surface_signature(bpy.data.objects[name])==sig,name
manifest=json.loads((SOURCE/'room-manifest.json').read_text());original={r['name']:r for r in manifest['meshes']};rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 ps=[o.matrix_world@v.co for v in o.data.vertices];rows.append(dict(name=o.name,material=o.get('export_material',original.get(o.name,{}).get('material','RoomAtlas')),collision=o.get('export_collision',True),triangles=len(o.data.polygons),lightmap_resolution=o.get('lightmap_resolution',256),bounds=[[min(v[k] for v in ps),max(v[k] for v in ps)] for k in range(3)]))
assert all(r['triangles']*3<65535 for r in rows)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(meshes=rows,triangles=sum(r['triangles'] for r in rows),source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest());(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix={n:p for n,p in prefix.items() if n not in removed};prefix.update({n:'Room09_' for n in changed});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2))
(OUT/'details96.json').write_text(json.dumps(dict(changed=sorted(changed),removed=sorted(removed-set(ns['GROUPS'])),labels=labels,flipped_toy_text_components=flipped,lightmaps=reports),indent=2));print('Revision 96 details source saved',len(rows),'meshes; mirrored toy glyph components',flipped)
