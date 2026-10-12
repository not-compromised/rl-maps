"""Accept baked-lighting coordinates only for unchanged source geometry."""
import json


def apply_lightmaps(meshes, cached_scene):
    cached = {mesh['name']: mesh for mesh in cached_scene['meshes']}
    if len(cached) != len(cached_scene['meshes']):
        raise ValueError('Duplicate cached mesh names')
    current = {mesh['name'] for mesh in meshes}
    selected = {name: mesh for name, mesh in cached.items() if 'lightmap_uvs' in mesh}
    if not selected or selected.keys() - current:
        raise ValueError('Lightmap scene must contain known meshes with generated charts')
    for mesh in meshes:
        if mesh['name'] not in selected:
            continue
        old = selected[mesh['name']]
        geometry = {key: value for key, value in old.items()
                    if key not in ('lightmap_uvs', 'lightmap_resolution')}
        if json.loads(json.dumps(mesh)) != geometry:
            raise ValueError('Stale lightmap geometry: ' + mesh['name'])
    for mesh in meshes:
        if mesh['name'] in selected:
            old = selected[mesh['name']]
            mesh['lightmap_uvs'] = old['lightmap_uvs']
            mesh['lightmap_resolution'] = old['lightmap_resolution']
    vertices = [vertex for mesh in meshes if mesh['name'] in selected for vertex in mesh['vertices']]
    low = [min(v[axis] for v in vertices) - 500 for axis in range(3)]
    high = [max(v[axis] for v in vertices) + 500 for axis in range(3)]
    return dict(meshes=sorted(selected), center=[(a+b)/2 for a,b in zip(low,high)],
                size=[b-a for a,b in zip(low,high)])
