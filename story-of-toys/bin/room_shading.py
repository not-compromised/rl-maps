"""Export rounded surfaces without blending across manufactured creases."""
from collections import defaultdict
import math


def smooth_with_creases(obj, angle=60):
    mesh = obj.data
    neighbors = defaultdict(list)
    formerly_flat = sum(not f.use_smooth for f in mesh.polygons)
    for face in mesh.polygons:
        face.use_smooth = True
        for edge in face.edge_keys:
            neighbors[tuple(sorted(edge))].append(face)
    threshold = math.cos(math.radians(angle))
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        edge.use_edge_sharp = len(faces) != 2 or faces[0].normal.dot(faces[1].normal) < threshold
    mesh.update()
    obj['export_sharp_edges'] = True
    groups, count = mesh.calc_smooth_groups(use_bitflags=True)
    assert all(groups), (obj.name, 'smoothing-group overflow')
    isolated = set()
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        if edge.use_edge_sharp and len(faces) == 2 and groups[faces[0].index] & groups[faces[1].index]:
            isolated.update(f.index for f in faces)
    for index in isolated:
        mesh.polygons[index].use_smooth = False
    groups, count = mesh.calc_smooth_groups(use_bitflags=True)
    for edge in mesh.edges:
        faces = neighbors[tuple(sorted(edge.vertices))]
        if edge.use_edge_sharp and len(faces) == 2:
            assert not groups[faces[0].index] & groups[faces[1].index], (obj.name, edge.index)
    return dict(name=obj.name, formerly_flat=formerly_flat, hard_edges=sum(e.use_edge_sharp for e in mesh.edges), isolated_flat=len(isolated), groups=count)
