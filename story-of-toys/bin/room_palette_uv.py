"""Keep color swatches uniform without collapsing the UV tangent basis."""
from collections import defaultdict
from mathutils import Vector


def fit_palette_uv(mesh):
    uv = mesh.uv_layers[0].data
    lightmap = mesh.uv_layers[1].data
    records = []
    extents = defaultdict(float)
    for face in mesh.polygons:
        coords = [uv[i].uv.copy() for i in face.loop_indices]
        average = sum(coords, Vector((0, 0))) / len(coords)
        tile = tuple(max(0, min(3, int(v * 4))) for v in average)
        center = Vector(tuple((v + .5) / 4 for v in tile))
        valid = abs((coords[1] - coords[0]).cross(coords[2] - coords[0])) > 0
        records.append((face, tile, center, coords if valid else None))
        if valid:
            extents[tile] = max(extents[tile], max(abs(c[k] - center[k]) for c in coords for k in range(2)))
    for face, tile, center, coords in records:
        if coords is not None:
            scale = min(.75, .09 / extents[tile])
            mapped = [center + (c - center) * scale for c in coords]
        else:
            mapped = [center + (lightmap[i].uv - Vector((.5, .5))) * .18 for i in face.loop_indices]
        for i, c in zip(face.loop_indices, mapped):
            uv[i].uv = c
        a, b, c = [uv[i].uv for i in face.loop_indices]
        assert abs((b - a).cross(c - a)) > 0, (mesh.name, face.index)
        assert all(abs(uv[i].uv[k] - center[k]) <= .090001 for i in face.loop_indices for k in range(2))
