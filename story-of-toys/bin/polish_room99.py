"""Join the globe meridian and finish the crib's open spindle connections."""
import bpy
import bmesh
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bin'))
from room_lightmaps import overlapping_faces
from room_shading import smooth_with_creases


def digest(obj):
    m = obj.data
    values = ([tuple(v.co) for v in m.vertices], [tuple(f.vertices) for f in m.polygons],
              [[tuple(v.uv) for v in uv.data] for uv in m.uv_layers],
              [f.use_smooth for f in m.polygons], [e.use_edge_sharp for e in m.edges],
              list(obj.matrix_world), obj.get('export_material'), obj.get('export_collision'))
    return hashlib.sha256(repr(values).encode()).hexdigest()


def components(obj):
    parents = list(range(len(obj.data.vertices)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    for face in obj.data.polygons:
        root = find(face.vertices[0])
        for v in face.vertices[1:]:
            parents[find(v)] = root
    groups = defaultdict(list)
    for face in obj.data.polygons:
        groups[find(face.vertices[0])].append(face)
    return list(groups.values())


def bounds(obj, faces):
    points = [obj.matrix_world @ obj.data.vertices[v].co for v in {v for f in faces for v in f.vertices}]
    return [[min(p[k] for p in points), max(p[k] for p in points)] for k in range(3)]


def crib_parts():
    arches, spindles = [], []
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or not obj.name.startswith('RoomCrib'):
            continue
        for faces in components(obj):
            b = bounds(obj, faces)
            if len(faces) == 388 and b[2][1] == 8000:
                arches.append((obj, faces))
            if len(faces) == 412 and b[2][0] == 1500 and abs(abs(sum(b[0])/2)-4500) < 1:
                spindles.append((obj, faces))
    assert len(arches) == 2 and len(spindles) == 18, (len(arches), len(spindles))
    return arches, spindles


def spindle_gaps():
    arches, spindles = crib_parts()
    vertices, polygons = [], []
    for obj, faces in arches:
        for face in faces:
            polygons.append(tuple(range(len(vertices), len(vertices)+3)))
            vertices.extend(obj.matrix_world @ obj.data.vertices[i].co for i in face.vertices)
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=True)
    rows = []
    for obj, faces in spindles:
        b = bounds(obj, faces)
        x, y = sum(b[0])/2, sum(b[1])/2
        hit, _, _, _ = tree.ray_cast(Vector((x,y,5000)), Vector((0,0,1)), 3500)
        assert hit is not None, (x,y)
        rows.append(dict(object=obj.name, x=x, y=y, top=b[2][1], arch_bottom=hit.z, gap=hit.z-b[2][1]))
    return rows


def retain(obj, faces):
    old = obj.data
    m = bpy.data.meshes.new(obj.name + '_99')
    indices = sorted({v for f in faces for v in f.vertices})
    remap = {v:i for i,v in enumerate(indices)}
    m.from_pydata([tuple(old.vertices[v].co) for v in indices], [],
                  [tuple(remap[v] for v in f.vertices) for f in faces])
    for mat in old.materials:
        m.materials.append(mat)
    for src,dst in zip(faces,m.polygons):
        dst.material_index=src.material_index
        dst.use_smooth=src.use_smooth
    sharp={tuple(sorted(e.vertices)):e.use_edge_sharp for e in old.edges}
    for edge in m.edges:
        edge.use_edge_sharp=sharp[tuple(sorted(indices[v] for v in edge.vertices))]
    for layer in old.uv_layers:
        uv=m.uv_layers.new(name=layer.name)
        for src,dst in zip(faces,m.polygons):
            for a,b in zip(src.loop_indices,dst.loop_indices):
                uv.data[b].uv=layer.data[a].uv
    obj.data=m
    m.update()


def closed_meridian(obj):
    center=Vector((-20875,-215,8220))
    rot=Matrix.Rotation(math.radians(23),3,'Y')
    n,k=192,12
    vertices=[]
    for i in range(n):
        a=i*math.tau/n
        for j in range(k):
            b=j*math.tau/k
            vertices.append(center+rot@Vector(((1750+55*math.cos(b))*math.cos(a),
                                               55*math.sin(b),(1750+55*math.cos(b))*math.sin(a))))
    faces=[]
    coords=[]
    for i in range(n):
        for j in range(k):
            a=i*k+j;b=((i+1)%n)*k+j;c=((i+1)%n)*k+(j+1)%k;d=i*k+(j+1)%k
            faces.extend([(a,b,c),(a,c,d)])
            coords.extend([((i/n,j/k),((i+1)/n,j/k),((i+1)/n,(j+1)/k)),
                           ((i/n,j/k),((i+1)/n,(j+1)/k),(i/n,(j+1)/k))])
    old=obj.data
    m=bpy.data.meshes.new('Continuous brass meridian99')
    base=len(old.vertices)
    m.from_pydata([tuple(v.co) for v in old.vertices]+[tuple(obj.matrix_world.inverted()@v) for v in vertices],[],
                 [tuple(f.vertices) for f in old.polygons]+[tuple(base+v for v in f) for f in faces])
    for mat in old.materials:m.materials.append(mat)
    for layer_index,layer in enumerate(old.uv_layers):
        uv=m.uv_layers.new(name=layer.name)
        for src,dst in zip(old.polygons,m.polygons):
            for a,b in zip(src.loop_indices,dst.loop_indices):
                u,v=layer.data[a].uv
                uv.data[b].uv=(u,v) if layer_index==0 else (.01+.97*u,.01+.70*v)
        for face,chart in zip(list(m.polygons)[len(old.polygons):],coords):
            for li,(u,v) in zip(face.loop_indices,chart):
                uv.data[li].uv=(.79+.17*u,.54+.17*v) if layer_index==0 else (.025+.95*u,.75+.22*v)
    obj.data=m
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update()
    smooth_with_creases(obj)


def mobile_support():
    changed=set()
    removed=0
    for obj in list(bpy.data.objects):
        if obj.type!='MESH' or not obj.name.startswith('RoomCrib'):continue
        groups=components(obj)
        rods=[fs for fs in groups if len(fs)==44]
        if rods:
            removed+=len(rods)
            retain(obj,[f for fs in groups if len(fs)!=44 for f in fs])
            changed.add(obj.name)
    assert removed==5,removed
    points=[Vector(p) for p in [(4500,-13500,7000),(4050,-13500,7100),(4000,-13500,7800),
            (3600,-13700,8800),(2700,-14100,9250),(1600,-14500,9000),(900,-14700,8300)]]
    curve=[]
    for i in range(len(points)-1):
        a=points[max(0,i-1)];b=points[i];c=points[i+1];d=points[min(len(points)-1,i+2)]
        for j in range(10):
            t=j/10
            curve.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    curve.append(points[-1])
    k=12;vertices=[];faces=[];charts=[]
    for i,p in enumerate(curve):
        tangent=(curve[min(i+1,len(curve)-1)]-curve[max(0,i-1)]).normalized()
        u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
        vertices.extend(p+45*(u*math.cos(j*math.tau/k)+v*math.sin(j*math.tau/k)) for j in range(k))
    for i in range(len(curve)-1):
        for j in range(k):
            a=i*k+j;b=i*k+(j+1)%k;c=(i+1)*k+(j+1)%k;d=(i+1)*k+j
            faces.extend([(a,b,c),(a,c,d)])
            x=i/(len(curve)-1);xx=(i+1)/(len(curve)-1);y=j/k;yy=(j+1)/k
            charts.extend([((x,y),(x,yy),(xx,yy)),((x,y),(xx,yy),(xx,y))])
    for end in (0,len(curve)-1):
        base=len(vertices);vertices.append(curve[end])
        for j in range(k):
            faces.append((base,end*k+j,end*k+(j+1)%k))
            offset=0 if end==0 else .5
            charts.append(((offset+.24,.5),(offset+.24+.21*math.cos(j*math.tau/k),.5+.45*math.sin(j*math.tau/k)),
                          (offset+.24+.21*math.cos((j+1)*math.tau/k),.5+.45*math.sin((j+1)*math.tau/k))))
    obj=bpy.data.objects['RoomCribPart4'];old=obj.data;base=len(old.vertices)
    m=bpy.data.meshes.new('Crib with continuous mounted mobile99')
    m.from_pydata([tuple(v.co) for v in old.vertices]+[tuple(obj.matrix_world.inverted()@v) for v in vertices],[],
                 [tuple(f.vertices) for f in old.polygons]+[tuple(base+v for v in f) for f in faces])
    for material in old.materials:m.materials.append(material)
    for layer_index,layer in enumerate(old.uv_layers):
        uv=m.uv_layers.new(name=layer.name)
        for src,dst in zip(old.polygons,m.polygons):
            for a,b in zip(src.loop_indices,dst.loop_indices):
                u,v=layer.data[a].uv
                uv.data[b].uv=(u,v) if layer_index==0 else (.01+.98*u,.01+.66*v)
        for i,(face,chart) in enumerate(zip(list(m.polygons)[len(old.polygons):],charts)):
            cap=i>=(len(curve)-1)*k*2
            for li,(u,v) in zip(face.loop_indices,chart):
                uv.data[li].uv=(.29+.17*u,.29+.17*v) if layer_index==0 else ((.02+.96*u,.69+.18*v) if not cap else (.02+.20*u,.90+.08*v))
    obj.data=m
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();m.update()
    smooth_with_creases(obj)
    return changed


def main():
    source=ROOT/'output/room-polish-98c'
    out=ROOT/'output/room-finish-99b'
    assert Path(bpy.data.filepath).resolve()==source/'RoomFinish.blend'
    assert hashlib.sha256((source/'RoomFinish.blend').read_bytes()).hexdigest()=='6e164034d4b1c80ca132087bb74e04c76a51d96f4077a9336dbff0f5e033210d'
    assert not out.exists()
    out.mkdir()
    original={o.name:digest(o) for o in bpy.data.objects if o.type=='MESH'}
    before=spindle_gaps()
    arches,spindles=crib_parts()
    changed={'RoomGlobe'}
    for (obj,faces),row in zip(spindles,before):
        target=row['arch_bottom']+140
        for v in {v for f in faces for v in f.vertices}:
            p=obj.matrix_world@obj.data.vertices[v].co
            # Extend the top neck into the board; retain the lower turned profile.
            if p.z>4965:
                p.z=4965+(p.z-4965)*(target-4965)/(6000-4965)
                obj.data.vertices[v].co=obj.matrix_world.inverted()@p
        obj.data.update();changed.add(obj.name)
    globe=bpy.data.objects['RoomGlobe']
    groups=components(globe)
    rods=[fs for fs in groups if len(fs)==28]
    assert len(rods)==96
    retain(globe,[f for fs in groups if len(fs)!=28 for f in fs])
    closed_meridian(globe)
    changed.update(mobile_support())
    for name in changed:
        obj=bpy.data.objects[name]
        assert len(obj.data.loops)<65536,name
        assert not overlapping_faces(obj),name
    after=spindle_gaps()
    assert all(row['gap']<=0 for row in after),after
    for name,value in original.items():
        if name not in changed:assert digest(bpy.data.objects[name])==value,name
    manifest=json.loads((source/'room-manifest.json').read_text())
    for row in manifest['meshes']:
        obj=bpy.data.objects[row['name']]
        row.update(triangles=len(obj.data.polygons),bounds=bounds(obj,list(obj.data.polygons)))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
    manifest.update(source=str(out/'RoomFinish.blend'),source_sha256=hashlib.sha256((out/'RoomFinish.blend').read_bytes()).hexdigest(),triangles=sum(r['triangles'] for r in manifest['meshes']))
    (out/'room-manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'asset-prefixes.json').write_bytes((source/'asset-prefixes.json').read_bytes())
    report=dict(source=manifest['source'],source_sha256=manifest['source_sha256'],changed=sorted(changed),
                protected={n:d for n,d in original.items() if n not in changed},spindles_before=before,spindles_after=after,
                meridian_components_before=len(rods),meridian_components_after=1)
    (out/'room99.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='protected'}))

if __name__=='__main__':main()
