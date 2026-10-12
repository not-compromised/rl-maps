"""Run inside the owned Blender scene; create a measured UDK import fixture."""
import bpy
import hashlib
import json
from mathutils import Quaternion
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'blender-probe-01'
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / 'ProbePlatform.fbx').exists():
    raise RuntimeError('Probe export already exists; inspect before creating another revision')
if any(obj.name.startswith('Probe') for obj in bpy.data.objects):
    raise RuntimeError('Probe geometry already exists; inspect before retrying')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01
scene.unit_settings.length_unit = 'CENTIMETERS'

parts = []
# Bounds are X [-1200,1200], Y [-900,900], top Z=0. Hole is X [100,700], Y [-350,350].
for name, center, size in [
    ('ProbeLeft', (-550, 0, -40), (1300, 1800, 80)),
    ('ProbeRight', (950, 0, -40), (500, 1800, 80)),
    ('ProbeFront', (400, -625, -40), (600, 550, 80)),
    ('ProbeBack', (400, 625, -40), (600, 550, 80)),
    ('ProbeBlock', (-700, 300, 200), (400, 500, 400)),
]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.object
obj.name = 'ProbePlatform'
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
obj.data.uv_layers[0].name = 'UVMap'
# Identical directional checker scale across adjoining coplanar faces.
for poly in obj.data.polygons:
    axis = max(range(3), key=lambda i: abs(poly.normal[i]))
    axes = [i for i in range(3) if i != axis]
    for loop_id in poly.loop_indices:
        co = obj.data.vertices[obj.data.loops[loop_id].vertex_index].co
        obj.data.uv_layers[0].data[loop_id].uv = ((co[axes[0]] + 1200) / 1200, (co[axes[1]] + 900) / 1200)
obj.data.uv_layers.new(name='LightmapUV')
obj.data.uv_layers.active_index = 1
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.1519173, island_margin=0.04)
bpy.ops.object.mode_set(mode='OBJECT')
obj.data.uv_layers.active_index = 0
obj.data.uv_layers[0].active_render = True
tri = obj.modifiers.new('ExportTriangles', 'TRIANGULATE')
bpy.ops.object.modifier_apply(modifier=tri.name)

size = 256
img = bpy.data.images.new('ProbeChecker', width=size, height=size, alpha=False)
pixels = []
for y in range(size):
    for x in range(size):
        base = (0.9, 0.27, 0.035) if x < size//2 else (0.035, 0.4, 0.8)
        if y >= size//2:
            base = tuple(v * 0.6 + 0.2 for v in base)
        factor = 0.35 if (x//32 + y//32) % 2 else 1
        pixels.extend([*(v*factor for v in base), 1])
img.pixels.foreach_set(pixels)
img.filepath_raw = str(OUT / 'ProbeChecker.tga')
img.file_format = 'TARGA_RAW'
img.save()
img.pack()
mat = bpy.data.materials.new('ProbeChecker')
mat.use_nodes = True
nodes = mat.node_tree.nodes
tex = nodes.new('ShaderNodeTexImage')
tex.image = img
mat.node_tree.links.new(tex.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])
nodes.get('Principled BSDF').inputs['Roughness'].default_value = 0.7
obj.data.materials.clear()
obj.data.materials.append(mat)
bpy.ops.export_scene.fbx(filepath=str(OUT / 'ProbePlatform.fbx'), use_selection=True,
    object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Y', axis_up='Z',
    use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True,
    bake_anim=False, add_leaf_bones=False, path_mode='STRIP', embed_textures=False)

vertices = [list(obj.matrix_world @ v.co) for v in obj.data.vertices]
report = {'blender': bpy.app.version_string, 'object': obj.name,
    'vertices': len(vertices), 'triangles': len(obj.data.polygons),
    'bounds': [[min(v[i] for v in vertices), max(v[i] for v in vertices)] for i in range(3)],
    'opening': {'x': [100,700], 'y': [-350,350], 'clear_width':600, 'clear_depth':700},
    'uv_channels': [uv.name for uv in obj.data.uv_layers],
    'scene_unit_meters': scene.unit_settings.scale_length,
    'collision': 'Not exported; configure and test in UDK',
    'lighting': 'Not baked; configure and build in UDK',
    'files': {p.name: {'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in OUT.iterdir() if p.suffix in ('.fbx','.tga')}}
(OUT / 'source-report.json').write_text(json.dumps(report, indent=2)+'\n')
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.clip_end = 100000
        space.shading.type = 'MATERIAL'
        space.region_3d.view_distance = 3700
        space.region_3d.view_location = (0,0,100)
        space.region_3d.view_rotation = Quaternion((0.820, 0.425, 0.176, 0.340)).normalized()
print(json.dumps(report))
