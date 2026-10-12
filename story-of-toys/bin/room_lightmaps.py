"""Keep tiny decorative faces from folding over their lighting charts."""
import hashlib
import math

from collections import defaultdict


def surface_signature(obj):
    return combined_surface_signature([obj])


def combined_surface_signature(objects):
    rows = []
    for obj in objects:
        uv = obj.data.uv_layers[0].data
        for face in obj.data.polygons:
            if face.area < 1e-6:
                continue
            corners = tuple(tuple(obj.data.vertices[obj.data.loops[i].vertex_index].co)
                            + tuple(uv[i].uv) for i in face.loop_indices)
            corners = min(corners[i:] + corners[:i] for i in range(len(corners)))
            rows.append(hashlib.sha256(repr((corners, face.use_smooth, face.material_index)).encode()).digest())
    return hashlib.sha256(b''.join(sorted(rows))).hexdigest()


def cross2(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def intersection_area(first, second):
    polygon = list(first)
    sign = 1 if cross2(*second) > 0 else -1
    for a, b in zip(second, second[1:] + second[:1]):
        clipped = []
        if not polygon:
            return 0
        previous = polygon[-1]
        distance = sign * cross2(a, b, previous)
        for current in polygon:
            next_distance = sign * cross2(a, b, current)
            if (distance >= 0) != (next_distance >= 0):
                t = distance / (distance - next_distance)
                clipped.append(tuple(previous[i] + t*(current[i]-previous[i]) for i in (0, 1)))
            if next_distance >= 0:
                clipped.append(current)
            previous, distance = current, next_distance
        polygon = clipped
    return abs(sum(a[0]*b[1]-a[1]*b[0]
                   for a, b in zip(polygon, polygon[1:] + polygon[:1]))) / 2


def overlapping_triangle_indices(triangles):
    # A 3D BVH can miss coplanar containment. UVs need a 2D broad phase.
    cells = defaultdict(list)
    bounds = []
    invalid = set()
    for i, triangle in enumerate(triangles):
        xmin = min(p[0] for p in triangle)
        xmax = max(p[0] for p in triangle)
        ymin = min(p[1] for p in triangle)
        ymax = max(p[1] for p in triangle)
        occupied = [(x, y)
                    for x in range(math.floor(xmin*64), math.floor(xmax*64)+1)
                    for y in range(math.floor(ymin*64), math.floor(ymax*64)+1)]
        candidates = {j for cell in occupied for j in cells[cell]}
        for j in candidates:
            left, right, bottom, top = bounds[j]
            if right < xmin or left > xmax or top < ymin or bottom > ymax:
                continue
            if intersection_area(triangle, triangles[j]) > 1e-12:
                invalid.update((i, j))
        bounds.append((xmin, xmax, ymin, ymax))
        for cell in occupied:
            cells[cell].append(i)
    return sorted(invalid)


def overlapping_faces(obj):
    # Entering Blender edit mode merges duplicate faces. Read raw triangles
    # instead, and reject positive-area intersections rather than shared edges.
    uv = obj.data.uv_layers[1].data
    triangles, indices, invalid = [], [], set()
    for face in obj.data.polygons:
        if face.area < 1e-6:
            continue
        # UDK's diagnostic OBJ rounds to six decimals. Keep lighting charts
        # valid at that precision too, rather than retaining near-zero slivers.
        triangle = tuple(tuple(round(x, 6) for x in uv[i].uv) for i in face.loop_indices)
        assert len(triangle) == 3
        if abs(cross2(*triangle)) < 2e-12:
            invalid.add(face.index)
            continue
        triangles.append(triangle)
        indices.append(face.index)
    invalid.update(indices[i] for i in overlapping_triangle_indices(triangles))
    return sorted(invalid)


def repair_mesh(obj, resolution):
    import bpy
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    before = surface_signature(obj)
    affected = overlapping_faces(obj)
    uv = obj.data.uv_layers[1].data
    original_uvs = [tuple(loop.uv) for loop in uv]
    # Packing the main charts into the strip can expose additional tiny faces
    # through float rounding. Include them, always starting from the same UVs.
    for repair_pass in range(4):
        if not affected:
            break
        resolution = max(resolution, 1024)
        columns = max(2, math.ceil(math.sqrt(len(affected) * .18 / .98)))
        rows = math.ceil(len(affected) / columns)
        cell_width = .18 / columns
        cell_height = .98 / rows
        padding = 5 / resolution
        if min(cell_height, cell_width) <= 3 * padding:
            raise ValueError(f'{obj.name}: too many faces for the reserved lighting strip')
        for loop, (u, v) in zip(uv, original_uvs):
            loop.uv = (.01 + .78 * u, .01 + .98 * v)
        for index, face_index in enumerate(affected):
            x = .81 + (index % columns) * cell_width
            y = .01 + (index // columns) * cell_height
            triangle = [(x + padding, y + padding),
                        (x + cell_width - padding, y + padding),
                        (x + padding, y + cell_height - padding)]
            face = obj.data.polygons[face_index]
            assert len(face.loop_indices) == 3
            for loop, coordinate in zip(face.loop_indices, triangle):
                uv[loop].uv = coordinate
        remaining = overlapping_faces(obj)
        if not remaining:
            break
        affected = sorted(set(affected).union(remaining))
    original = obj.data
    kept = [face for face in original.polygons if face.area >= 1e-6]
    removed = len(original.polygons) - len(kept)
    if removed:
        # BMesh merges duplicate faces during conversion. Preserve every real
        # triangle and its corner UVs, including deliberately coincident faces.
        mesh = bpy.data.meshes.new(original.name + '_clean')
        mesh.from_pydata([tuple(v.co) for v in original.vertices], [],
                         [tuple(face.vertices) for face in kept])
        for material in original.materials:
            mesh.materials.append(material)
        for source, target in zip(kept, mesh.polygons):
            target.use_smooth = source.use_smooth
            target.material_index = source.material_index
        for layer in original.uv_layers:
            target = mesh.uv_layers.new(name=layer.name)
            for source_face, target_face in zip(kept, mesh.polygons):
                for source_loop, target_loop in zip(source_face.loop_indices, target_face.loop_indices):
                    target.data[target_loop].uv = layer.data[source_loop].uv
        obj.data = mesh
        mesh.update()
    assert surface_signature(obj) == before, f'{obj.name}: visible geometry or diffuse UVs changed'
    assert not overlapping_faces(obj), f'{obj.name}: lighting charts still overlap'
    obj.data.uv_layers.active_index = 0
    obj.data.uv_layers[0].active_render = True
    obj['lightmap_resolution'] = resolution
    return dict(name=obj.name, removed_degenerate_faces=removed,
                isolated_faces=len(affected), lightmap_resolution=resolution,
                surface_sha256=before, triangles=len(obj.data.polygons))
