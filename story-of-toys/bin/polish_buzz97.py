"""Separate armor caps from rounded sides without changing the fitted toy."""
import collections
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'output/room-release-96d'
OUT = ROOT / 'output/room-surfaces-97'
assert Path(bpy.data.filepath).resolve() == SOURCE / 'RoomFinish.blend'
assert not (OUT / 'RoomFinish.blend').exists()
OUT.mkdir(exist_ok=True)


def geometry_digest(obj):
    mesh = obj.data
    data = ([tuple(v.co) for v in mesh.vertices],
            [tuple(p.vertices) for p in mesh.polygons],
            [[tuple(loop.uv) for loop in layer.data] for layer in mesh.uv_layers],
            list(obj.matrix_world), obj.get('export_collision'))
    return hashlib.sha256(repr(data).encode()).hexdigest()


before = {o.name: geometry_digest(o) for o in bpy.data.objects if o.type == 'MESH'}
reports = []
for obj in bpy.data.objects:
    if obj.type != 'MESH' or not obj.name.startswith('RoomBuzz'):
        continue
    mesh = obj.data
    neighbors = collections.defaultdict(list)
    formerly_flat = sum(not p.use_smooth for p in mesh.polygons)
    for face in mesh.polygons:
        for edge in face.edge_keys:
            neighbors[tuple(sorted(edge))].append(face)
        face.use_smooth = True
    hard = 0
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        edge.use_edge_sharp = len(faces) != 2 or faces[0].normal.dot(faces[1].normal) < .5
        hard += edge.use_edge_sharp
    mesh.update()
    obj['export_sharp_edges'] = True
    groups, count = mesh.calc_smooth_groups(use_bitflags=True)
    assert all(groups), (obj.name, 'smoothing group overflow')
    isolated = set()
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        if edge.use_edge_sharp and len(faces) == 2 and groups[faces[0].index] & groups[faces[1].index]:
            isolated.update(f.index for f in faces)
    # A hard edge inside one connected smoothing region cannot be encoded by
    # one face bitmask. Keep those few crease triangles flat.
    for index in isolated:
        mesh.polygons[index].use_smooth = False
    groups, count = mesh.calc_smooth_groups(use_bitflags=True)
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        if edge.use_edge_sharp and len(faces) == 2:
            assert not groups[faces[0].index] & groups[faces[1].index], (obj.name, edge.index)
    reports.append(dict(name=obj.name,formerly_flat_faces=formerly_flat,
                        hard_edges=hard,smoothing_groups=count,isolated_crease_faces=len(isolated),
                        geometry_sha256=before[obj.name]))

assert all(geometry_digest(bpy.data.objects[name]) == digest for name,digest in before.items())
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'RoomFinish.blend'))
manifest = json.loads((SOURCE / 'room-manifest.json').read_text())
manifest['source_sha256'] = hashlib.sha256((OUT / 'RoomFinish.blend').read_bytes()).hexdigest()
(OUT / 'room-manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT / 'asset-prefixes.json').write_bytes((SOURCE / 'asset-prefixes.json').read_bytes())
report = dict(baseline_source=str(SOURCE / 'RoomFinish.blend'),
              baseline_source_sha256=hashlib.sha256((SOURCE / 'RoomFinish.blend').read_bytes()).hexdigest(),
              source=str(OUT / 'RoomFinish.blend'),source_sha256=manifest['source_sha256'],
              geometry_uvs_collision_unchanged=True,meshes=reports)
(OUT / 'surfaces97.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
