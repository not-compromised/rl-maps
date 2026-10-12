"""Rebuild the shelf Buzz with fitted armor and a modeled expressive face."""
import ast,bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'bin')]
from room_lightmaps import repair_mesh,surface_signature
from room_palette_uv import fit_palette_uv
from room_mesh_parts import split_mesh
SOURCE=ROOT/'output/room-details-96';OUT=ROOT/'output/room-models-96';OUT.mkdir(exist_ok=True)
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
old={o.name:surface_signature(o) for o in bpy.data.objects if o.type=='MESH'}
targets=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='RoomBuzz' or o.name.startswith('RoomBuzzPart'))]
ps=[o.matrix_world@v.co for o in targets for v in o.data.vertices];bounds=[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)]
mat=bpy.data.materials['RoomToyPalette94'];module=ast.parse((ROOT/'bin/build_room_blender.py').read_text());helpers=ast.Module(body=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'finish','box','ell','rod','torus','text'}],type_ignores=[])
ns=dict(bpy=bpy,bmesh=bmesh,math=math,Vector=Vector,mat=mat,GROUPS={},group='RoomBuzz',CLOUD=1);exec(compile(helpers,'buzz96-shapes','exec'),ns)
# Reuse only pure shape helpers, not the room-building operations.
extra=ast.parse((ROOT/'bin/improve_room96.py').read_text());exec(compile(ast.Module(body=[n for n in extra.body if isinstance(n,ast.FunctionDef) and n.name in {'mesh','tube','label'}],type_ignores=[]),'buzz96-extra','exec'),ns)
ns['ns']=ns;ns['labels']=[];box,ell,rod,torus,tube,mesh,label=[ns[n] for n in ('box','ell','rod','torus','tube','mesh','label')]
# Boots have distinct soles, heel cups and a projecting rounded toe.
for side in (-1,1):
 x=side*265
 box('Green rubber boot sole',(x,-135,75),(485,705,150),6,65)
 ell('White boot shell',(x,-170,275),(240,325,215),5,32,20)
 box('Purple ankle cuff',(x,10,465),(400,410,130),7,65)
 box('White shin armor',(x,0,840),(410,400,660),5,105)
 box('Green shin inset',(x,-211,740),(235,36,350),6,55)
 ell('Purple knee joint',(x,0,1210),(205,220,170),7,28,16)
 ell('White knee shield',(x,-192,1235),(180,85,150),5,28,16)
 box('White thigh armor',(x,10,1530),(465,460,490),5,110)
 box('Hip plate',(side*310,5,1810),(380,475,255),5,85)
box('Pelvis shell',(0,0,1810),(670,510,330),5,95)
box('Green belt',(0,-15,1950),(985,595,175),6,65)
box('Purple belt buckle',(0,-328,1970),(200,70,130),7,30)
for z in range(2030,2281,58):
 e=torus('Flexible ribbed waist',(0,0,z),390,30,9);e.scale.y=.65
# White torso and green chest yoke are flatter, layered injection-molded armor.
box('White torso armor',(0,35,2510),(1120,635,690),5,190)
box('Green chest yoke',(0,-235,2700),(1110,220,425),6,135)
box('Lower white breast plate',(0,-320,2410),(770,170,225),5,85)
box('Chest center seam',(0,-413,2470),(20,20,150),15,5)
for j,tile in enumerate((10,6,12)):
 box('Chest control socket',(-365+j*105,-357,2650),(89,45,210),9,34)
 box('Chest colored control',(-365+j*105,-385,2650),(66,45,174),tile,28)
ell('Round red chest button',(315,-373,2680),(110,43,110),2,32,18)
box('Lightyear name plate',(-250,-363,2845),(390,24,91),5,10)
label('LIGHTYEAR',(-250,-386,2818),65,9,width=355)
# Wings and badge are broad shapes that remain readable from a distance.
mesh('Space ranger badge',[(-65,-373,2810),(90,-373,2770),(245,-373,2810),(170,-373,2810),(90,-373,2793),(10,-373,2810)],[(0,1,2,3,4,5)],10)
# Articulated upper arms and gauntlets, with shoulder caps instead of green spheres.
for side in (-1,1):
 x=side*780
 ell('Purple shoulder joint',(side*630,10,2670),(200,220,230),7,28,18)
 e=ell('Shoulder white shell',(side*680,0,2780),(280,315,245),5,32,20)
 e=ell('Shoulder lime panel',(side*700,-55,2850),(252,280,145),6,32,20)
 rod('Upper arm white armor',(side*790,0,2630),(side*850,-70,2260),195,5,175,32)
 ell('Purple elbow joint',(side*855,-90,2180),(178,175,155),7,28,18)
 box('Forearm gauntlet',(side*875,-125,1945),(355,440,470),5,95)
 box('Gauntlet green panel',(side*875,-356,2050),(230,30,180),6,35)
 if side==1:
  box('Wrist laser red button',(side*875,-378,2050),(130,25,80),2,18)
 else:
  for j in range(3):box('Wrist readout',(side*875-65+j*65,-380,2050),(38,20,80),10,9)
 box('Purple glove cuff',(side*875,-145,1660),(315,355,100),7,35)
 ell('White glove palm',(side*875,-155,1520),(165,175,180),5,28,18)
 for j in range(4):ell('Molded glove finger',(side*875-105+j*70,-277,1490),(38,63,115),5,18,12)
 ell('Glove thumb',(side*1040,-180,1545),(72,115,92),5,20,14)
# Jet pack with swept purple wing panels and diagonal red tip stripes.
box('Jet pack',(0,330,2640),(830,430,710),5,105)
for side in (-1,1):
 box('Jet green pod',(side*420,330,2650),(190,340,780),6,65)
 vertices=[(side*470,410,2780),(side*2050,410,2890),(side*2100,410,2660),(side*490,410,2420),
           (side*470,540,2780),(side*2050,540,2890),(side*2100,540,2660),(side*490,540,2420)]
 mesh('Swept wing',vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],7)
 tube('Green wing leading edge',[(side*470,400,2780),(side*1300,400,2840),(side*2050,400,2890)],36,6)
 for j in range(5):
  x=850+j*235;top=2780+(x-470)*110/1580;bottom=2420+(x-490)*240/1610
  mesh('White diagonal wing stripe',[(side*x,395,bottom+12),(side*(x+92),395,bottom+26),(side*(x+205),395,top-16),(side*(x+112),395,top-22)],[(0,1,2,3)],5)
 ell('Red wingtip light',(side*2050,420,2780),(65,85,145),2,24,16)
# Hood and modeled head: broad jaw, small ears, compact nose, confident eyebrows.
ell('Purple fitted cowl',(0,30,3180),(375,295,420),7,48,28)
# Closed loft gives the face a flatter front and a distinct square chin.
sections=[(2825,150,110,-125),(2880,245,155,-120),(2990,285,185,-100),(3150,286,220,-65),(3340,292,240,-40),(3470,245,210,-15),(3510,125,130,0)]
verts=[];faces=[];N=48
for z,rx,ry,y in sections:
 for i in range(N):
  a=i*math.tau/N;verts.append((rx*math.copysign(abs(math.cos(a))**.65,math.cos(a)),y+ry*math.sin(a),z))
for j in range(len(sections)-1):
 for i in range(N):k=j*N+i;n=j*N+(i+1)%N;faces.append((k,n,n+N,k+N))
faces.extend([tuple(reversed(range(N))),tuple(range((len(sections)-1)*N,len(sections)*N))]);mesh('Square jaw face',verts,faces,4,True)
for side in (-1,1):
 ell('Buzz eye',(side*122,-285,3295),(92,25,67),5,32,20)
 ell('Buzz blue iris',(side*120,-309,3292),(34,14,45),10,24,16)
 ell('Buzz pupil',(side*120,-322,3292),(18,8,29),9,20,14)
 ell('Buzz eye glint',(side*120-10,-330,3308),(10,5,13),5,12,8)
 tube('Sculpted brow',[(side*40,-290,3393),(side*117,-297,3410),(side*212,-263,3370)],27,8)
 ell('Nose wing',(side*47,-297,3185),(50,42,32),4,24,16)
ell('Nose bridge',(0,-285,3240),(49,60,110),4,32,20)
ell('Rounded nose tip',(0,-334,3195),(70,72,52),4,32,20)
tube('Confident half smile',[(-128,-278,3070),(-50,-300,3050),(55,-300,3058),(135,-274,3100)],13,8)
tube('Lower lip',[(-75,-293,3018),(5,-308,3000),(93,-283,3025)],10,4)
tube('Chin curl',[(30*math.cos(a),-276,2910+30*math.sin(a)) for a in [j*.15 for j in range(36)]],8,8)
# Neck seal and open helmet rails leave the face visible, avoiding fake opaque glass.
e=torus('Purple pressure seal',(0,15,2830),400,55,7);e.scale.y=.76
e=torus('White helmet collar',(0,15,2890),440,42,5);e.scale.y=.76
for side in (-1,1):
 tube('Helmet side hinge rail',[(side*415,40,2890),(side*450,120,3130),(side*340,225,3430)],34,15)
 ell('Helmet hinge',(side*425,70,2940),(55,85,80),7,24,16)
# Fit to the original occupied envelope; collision and route clearance are preserved.
parts=ns['GROUPS']['RoomBuzz'];R=Matrix.Rotation(math.pi/2-.35,4,'Z')
for o in parts:o.matrix_world=R@o.matrix_world
ps=[o.matrix_world@v.co for o in parts for v in o.data.vertices];lo=Vector([min(p[k] for p in ps) for k in range(3)]);hi=Vector([max(p[k] for p in ps) for k in range(3)]);scale=min((bounds[k][1]-bounds[k][0])/(hi[k]-lo[k]) for k in range(3));center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));dest=Vector(((bounds[0][0]+bounds[0][1])/2,(bounds[1][0]+bounds[1][1])/2,bounds[2][0]))
for o in parts:
 for v in o.data.vertices:v.co=dest+(o.matrix_world@v.co-center)*scale
 o.matrix_world.identity()
removed=[o.name for o in targets]
for o in targets:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='RoomBuzz';o['export_material']='RoomToyPalette94';o['export_collision']=True
while len(o.data.uv_layers)>1:o.data.uv_layers.remove(o.data.uv_layers[-1])
o.data.uv_layers.new(name='LightmapUV');o.data.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
reports=[];names=[]
for piece in split_mesh(o,18000):reports.append(dict(name=piece.name,lightmap=repair_mesh(piece,1024)));fit_palette_uv(piece.data);names.append(piece.name)
for n,sig in old.items():
 if n not in removed:assert surface_signature(bpy.data.objects[n])==sig,n
manifest=json.loads((SOURCE/'room-manifest.json').read_text());manifest['meshes']=[r for r in manifest['meshes'] if r['name'] not in removed]
for n in names:
 o=bpy.data.objects[n];ps=[o.matrix_world@v.co for v in o.data.vertices];manifest['meshes'].append(dict(name=n,material='RoomToyPalette94',collision=True,triangles=len(o.data.polygons),lightmap_resolution=o['lightmap_resolution'],bounds=[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)]))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'));manifest.update(source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest(),triangles=sum(r['triangles'] for r in manifest['meshes']));(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
prefix=json.loads((SOURCE/'asset-prefixes.json').read_text());prefix={n:p for n,p in prefix.items() if n not in removed};prefix.update({n:'Room09_' for n in names});(OUT/'asset-prefixes.json').write_text(json.dumps(prefix,indent=2))
detail=json.loads((SOURCE/'details96.json').read_text());detail['changed']=sorted(set(detail['changed'])|set(names));detail['removed']=sorted(set(detail['removed'])|set(removed)-set(names));detail['buzz']=dict(previous_bounds=bounds,scale=scale,parts=names,lightmaps=reports);(OUT/'details96.json').write_text(json.dumps(detail,indent=2));print('Buzz rebuilt',names,scale)
