"""Refine fabric, the hat transition, furniture surfaces and the bedside globe."""
import ast
import bpy
import bmesh
import hashlib
import json
import math
import sys
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from room_shading import smooth_with_creases
from room_lightmaps import overlapping_faces
SOURCE=ROOT/'output/room-surfaces-97'
OUT=Path(sys.argv[sys.argv.index('--')+1]).resolve() if '--' in sys.argv else ROOT/'output/room-polish-98'
assert Path(bpy.data.filepath).resolve()==SOURCE/'RoomFinish.blend'
assert not (OUT/'RoomFinish.blend').exists()
OUT.mkdir(exist_ok=True)


def digest(obj):
    m=obj.data
    data=([tuple(v.co) for v in m.vertices], [tuple(f.vertices) for f in m.polygons],
          [[tuple(v.uv) for v in uv.data] for uv in m.uv_layers],
          [f.use_smooth for f in m.polygons], [e.use_edge_sharp for e in m.edges],
          list(obj.matrix_world), obj.get('export_material'), obj.get('export_collision'))
    return hashlib.sha256(repr(data).encode()).hexdigest()


def components(mesh):
    parents=list(range(len(mesh.vertices)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for face in mesh.polygons:
        r=find(face.vertices[0])
        for v in face.vertices[1:]:parents[find(v)]=r
    groups=defaultdict(list)
    for face in mesh.polygons:groups[find(face.vertices[0])].append(face)
    return list(groups.values())


def bounds(obj,faces):
    pts=[obj.matrix_world@obj.data.vertices[v].co for v in {v for f in faces for v in f.vertices}]
    return [[min(p[k] for p in pts),max(p[k] for p in pts)] for k in range(3)]


def subset(obj,keep):
    old=obj.data
    mesh=bpy.data.meshes.new(obj.name+'_98')
    ids=sorted({v for f in keep for v in f.vertices});remap={v:i for i,v in enumerate(ids)}
    mesh.from_pydata([tuple(old.vertices[v].co) for v in ids],[],[tuple(remap[v] for v in f.vertices) for f in keep])
    for material in old.materials:mesh.materials.append(material)
    for a,b in zip(keep,mesh.polygons):b.use_smooth=a.use_smooth;b.material_index=a.material_index
    for layer in old.uv_layers:
        uv=mesh.uv_layers.new(name=layer.name)
        for a,b in zip(keep,mesh.polygons):
            for i,j in zip(a.loop_indices,b.loop_indices):uv.data[j].uv=layer.data[i].uv
    obj.data=mesh;mesh.update()


original={o.name:digest(o) for o in bpy.data.objects if o.type=='MESH'}
changed={'RoomBed','RoomCrib','RoomCribPart2','RoomCribPart3','RoomCribPart4','RoomDesk',
         'RoomDresser','RoomNightstand','RoomWindow','RoomDoor','RoomWagonChest',
         'RoomAndyHat','RoomAndyHatPart2','RoomGlobe','RoomGlobePart2'}

# Extend the transition beyond the protected 1,100-unit flat band. The old
# 200-unit shoulder made the curled brim rise abruptly beside the driving strip.
hat_moves=[]
for name in ('RoomAndyHat','RoomAndyHatPart2'):
    obj=bpy.data.objects[name];mesh=obj.data
    selected=[]
    for faces in components(mesh):
        b=bounds(obj,faces)
        if len(faces)>1000 or len(faces)==92:selected.extend({v for f in faces for v in f.vertices})
    moved=0;largest=0
    for i in set(selected):
        vertex=mesh.vertices[i];p=obj.matrix_world@vertex.co;x,y=p.x-1500,p.y-1000
        distance=abs(y+2400)
        def weight(width):
            t=max(0,min(1,(550+width-distance)/width));return t*t*(3-2*t)
        radius=math.sqrt((x/3900)**2+(y/3800)**2)
        edge=max(0,min(1,(radius-.82)/.18));edge=edge*edge*(3-2*edge)
        delta=edge*(1050*(abs(x)/3900)**3-300*max(0,-y/3800)**4+180*max(0,y/3800)**3)
        shift=(weight(200)-weight(500))*delta
        if abs(shift)>.001:
            p.z+=shift;vertex.co=obj.matrix_world.inverted()@p;moved+=1;largest=max(largest,abs(shift))
    mesh.update();hat_moves.append(dict(name=name,moved_vertices=moved,max_displacement=largest))

# Retain the pillow's footprint but replace the flat box profile with a soft
# superellipsoid. Subdivision interpolates the existing UV charts.
obj=bpy.data.objects['RoomBed'];candidates=[]
for faces in components(obj.data):
    b=bounds(obj,faces)
    if b[2][0]>4100 and b[2][1]<4800 and b[0][0]<-21000:candidates.append(faces)
assert len(candidates)==1
indices={f.index for f in candidates[0]}
bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table()
faces=[bm.faces[i] for i in indices];edges=list({e for f in faces for e in f.edges})
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True)
center=Vector((-20725,-13115,4440));radii=Vector((1300,4050,310));pillow_count=0
for v in bm.verts:
    p=obj.matrix_world@v.co
    if -22026<=p.x<=-19424 and -17166<=p.y<=-9064 and 4129<=p.z<=4751:
        q=Vector(tuple((p[k]-center[k])/radii[k] for k in range(3)))
        length=sum(abs(t)**4 for t in q)**.25
        if length>0:
            q/=length;p=Vector(tuple(center[k]+q[k]*radii[k] for k in range(3)));p.z=4780+q.z*650
            v.co=obj.matrix_world.inverted()@p;pillow_count+=1
bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
assert pillow_count>100

# Convert the globe's printed ocean, land and fine grid to one mipmapped map.
# Keep the existing brass base/meridian geometry and its position on the dresser.
obj=bpy.data.objects['RoomGlobe'];keep=[]
for faces in components(obj.data):
    uv=obj.data.uv_layers[0].data
    tile=tuple(int(sum(uv[i].uv[k] for i in faces[0].loop_indices)/3*4) for k in range(2))
    if tile==(3,2) and len(faces) in (28,92,960):keep.extend(faces)
assert len(keep)==3740,len(keep)
subset(obj,keep)
module=ast.parse((ROOT/'bin/refine_room_layout.py').read_text())
assignment=next(n for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='land' for t in n.targets))
ns=dict(GREEN=6,YELLOW=11,ORANGE=12,RED=2,WHITE=5)
exec(compile(ast.Module(body=[assignment],type_ignores=[]),'globe outlines','exec'),ns)
colors={6:(.21,.43,.09),11:(.70,.49,.18),12:(.60,.21,.065),2:(.48,.055,.048),5:(.70,.69,.62)}
size=2048;yy,xx=np.mgrid[0:size,0:size];lon=(xx+.5)/size*360-180;lat=(yy+.5)/size*180-90
pixels=np.ones((size,size,4),np.float32);pixels[:,:,:3]=(.06,.24,.37)
for _,outline,tile in ns['land']:
    inside=np.zeros((size,size),bool)
    for (x1,y1),(x2,y2) in zip(outline,outline[1:]+outline[:1]):
        if y1==y2:continue
        inside ^= ((y1>lat)!=(y2>lat)) & (lon<(x2-x1)*(lat-y1)/(y2-y1)+x1)
    pixels[inside,:3]=colors[tile]
grid=np.minimum(abs((lon+15)%30-15),abs((lat+15)%30-15))
alpha=np.clip((.32-grid)/.12,0,1)*.50
pixels[:,:,:3]=pixels[:,:,:3]*(1-alpha[:,:,None])+np.array((.52,.63,.61))*alpha[:,:,None]
image=bpy.data.images.new('RoomGlobePrint98',width=size,height=size,alpha=False)
image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(OUT/'RoomGlobePrint98.tga');image.file_format='TARGA_RAW';image.save();image.pack()
mat=bpy.data.materials.new('RoomGlobePrint98');mat.use_nodes=True
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.75
obj=bpy.data.objects['RoomGlobePart2'];center=Vector((-20875,-215,8220));rotation=Matrix.Rotation(math.radians(23),3,'Y')
verts=[];uvs=[];faces=[];segments=96;rings=48
for j in range(rings+1):
    b=-math.pi/2+j*math.pi/rings
    for i in range(segments+1):
        a=-math.pi+i*math.tau/segments
        verts.append(tuple(center+rotation@Vector((1550*math.cos(b)*math.cos(a),1550*math.cos(b)*math.sin(a),1550*math.sin(b)))))
        uvs.append((i/segments,j/rings))
for j in range(rings):
    for i in range(segments):
        a=j*(segments+1)+i;b=a+1;c=a+segments+1;d=c+1
        if j>0:faces.append((a,b,c))
        if j<rings-1:faces.append((b,d,c))
mesh=bpy.data.meshes.new('Printed classroom globe98');mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update();obj.data=mesh;obj.matrix_world=Matrix.Identity(4)
for layer_name in ('UVMap','LightmapUV'):
    uv=mesh.uv_layers.new(name=layer_name)
    for face in mesh.polygons:
        face.use_smooth=True
        for li in face.loop_indices:
            u,v=uvs[mesh.loops[li].vertex_index]
            uv.data[li].uv=(u,v) if layer_name=='UVMap' else (.02+.96*u,.02+.96*v)
obj['export_material']='RoomGlobePrint98';obj['lightmap_resolution']=512;obj['export_collision']=True

shading=[]
for name in sorted(changed-{'RoomGlobePart2'}):shading.append(smooth_with_creases(bpy.data.objects[name]))
# The crown is one continuous fabric surface. Its dented top is triangulated;
# treating those triangle angles as manufactured creases leaves flat wedges.
hat=bpy.data.objects['RoomAndyHat'];crowns=[fs for fs in components(hat.data) if len(fs)==508]
assert len(crowns)==1
crown_vertices={v for f in crowns[0] for v in f.vertices}
for face in crowns[0]:face.use_smooth=True
for edge in hat.data.edges:
    if all(v in crown_vertices for v in edge.vertices):edge.use_edge_sharp=False
hat.data.update()
for name in changed:
    obj=bpy.data.objects[name]
    assert len(obj.data.loops)<=65535,(name,len(obj.data.loops))
    assert not overlapping_faces(obj),name
for name,value in original.items():
    if name not in changed:assert digest(bpy.data.objects[name])==value,name
assert len([o for o in bpy.data.objects if o.type=='MESH'])==len(original)
manifest=json.loads((SOURCE/'room-manifest.json').read_text())
for row in manifest['meshes']:
    obj=bpy.data.objects[row['name']]
    row.update(material=obj.get('export_material','RoomAtlas'),triangles=len(obj.data.polygons),bounds=bounds(obj,list(obj.data.polygons)),lightmap_resolution=obj.get('lightmap_resolution',256))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RoomFinish.blend'))
manifest.update(source=str(OUT/'RoomFinish.blend'),source_sha256=hashlib.sha256((OUT/'RoomFinish.blend').read_bytes()).hexdigest(),triangles=sum(r['triangles'] for r in manifest['meshes']))
(OUT/'room-manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'asset-prefixes.json').write_bytes((SOURCE/'asset-prefixes.json').read_bytes())
report=dict(source=manifest['source'],source_sha256=manifest['source_sha256'],changed=sorted(changed),protected={n:v for n,v in original.items() if n not in changed},hat=hat_moves,pillow_vertices=pillow_count,shading=shading,globe_grid_rods_removed=792,globe_triangles_before=20060,globe_triangles_after=sum(len(bpy.data.objects[n].data.polygons) for n in ('RoomGlobe','RoomGlobePart2')),bed_print_preserved=True)
(OUT/'room98.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
