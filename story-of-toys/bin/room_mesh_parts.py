"""Keep disconnected scenery pieces within UDK's 16-bit render index limit."""
from collections import defaultdict
from room_lightmaps import combined_surface_signature, surface_signature


def split_mesh(obj, triangle_limit=20000):
    import bpy
    mesh = obj.data
    parent = list(range(len(mesh.vertices)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for face in mesh.polygons:
        assert len(face.vertices) == 3
        a = root(face.vertices[0])
        for b in face.vertices[1:]:
            parent[root(b)] = a
    components = defaultdict(list)
    for face in mesh.polygons:
        components[root(face.vertices[0])].append(face)
    batches = []
    for component in sorted(components.values(), key=len, reverse=True):
        if len(component) > triangle_limit:
            raise ValueError(f'{obj.name}: connected piece requires a deliberate seam')
        for batch in batches:
            if len(batch) + len(component) <= triangle_limit:
                batch.extend(component)
                break
        else:
            batches.append(list(component))
    before = surface_signature(obj)
    result = []
    for i, faces in enumerate(batches):
        target = obj if i == 0 else obj.copy()
        if i:
            target.name = obj.name + f'Part{i+1}'
            obj.users_collection[0].objects.link(target)
        source_vertices = sorted({v for face in faces for v in face.vertices})
        remap = {v: j for j, v in enumerate(source_vertices)}
        data = bpy.data.meshes.new(target.name + '_indexed')
        data.from_pydata([tuple(mesh.vertices[v].co) for v in source_vertices], [],
                         [tuple(remap[v] for v in face.vertices) for face in faces])
        for material in mesh.materials:
            data.materials.append(material)
        for old, new in zip(faces, data.polygons):
            new.use_smooth = old.use_smooth
            new.material_index = old.material_index
        for layer in mesh.uv_layers:
            uv = data.uv_layers.new(name=layer.name)
            for old, new in zip(faces, data.polygons):
                for a, b in zip(old.loop_indices, new.loop_indices):
                    uv.data[b].uv = layer.data[a].uv
        target.data = data
        data.update()
        data.uv_layers.active_index = 0
        data.uv_layers[0].active_render = True
        assert len(data.polygons) * 3 <= 65535
        result.append(target)
    assert combined_surface_signature(result) == before, obj.name
    return result
