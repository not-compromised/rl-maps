"""Record room assets and source checks for a saved candidate."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from room_lightmaps import overlapping_faces
out=Path(sys.argv[sys.argv.index('--')+1]);meshes=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 corners=[o.matrix_world@Vector(c) for c in o.bound_box]
 invalid=overlapping_faces(o)
 assert not invalid,(o.name,len(invalid))
 meshes.append({'name':o.name,'triangles':len(o.data.polygons),'material':o.get('export_material','RoomAtlas'),'collision':o.get('export_collision',True),'lightmap_resolution':o.get('lightmap_resolution',512),'bounds':[[min(v[i] for v in corners),max(v[i] for v in corners)] for i in range(3)]})
(out/'room-manifest.json').write_text(json.dumps({'meshes':meshes,'source':bpy.data.filepath,'lightmap_errors':0},indent=2))
print('Manifest',len(meshes),'meshes',sum(x['triangles'] for x in meshes),'triangles',flush=True)
