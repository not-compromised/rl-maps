"""Orient raised poster lettering for this map's XYZ-preserving UE3 export."""
import bmesh

def correct_poster_handedness(obj):
    if obj.get('ue3_poster_text_corrected'):
        return []
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    unseen = set(bm.verts)
    counts = [0, 0]
    rules = [(0, -22835, 1, 14000), (1, 18765, 0, -15700)]
    while unseen:
        seed = unseen.pop()
        component, stack = {seed}, [seed]
        while stack:
            for edge in stack.pop().link_edges:
                for v in edge.verts:
                    if v in unseen:
                        unseen.remove(v)
                        component.add(v)
                        stack.append(v)
        world = {v: obj.matrix_world @ v.co for v in component}
        for index, (plane_axis, plane, horizontal, center) in enumerate(rules):
            if not all(abs(p[plane_axis] - plane) < 1.1 for p in world.values()):
                continue
            inverse = obj.matrix_world.inverted()
            for v, p in world.items():
                p[horizontal] = 2 * center - p[horizontal]
                v.co = inverse @ p
            faces = set(f for v in component for f in v.link_faces)
            bmesh.ops.reverse_faces(bm, faces=list(faces))
            counts[index] += len(faces)
            break
    assert all(counts), ('Poster lettering not found', counts)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj['ue3_poster_text_corrected'] = True
    return counts
