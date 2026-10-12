import bpy,sys,json
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);manifest=json.loads((root/'room-manifest.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
bpy.ops.import_scene.fbx(filepath=str(root/'Room.fbx'))
rows=[]
for expected in manifest['meshes']:
 o=bpy.data.objects.get(expected['name']);assert o and o.type=='MESH',expected['name']
 verts=[o.matrix_world@v.co for v in o.data.vertices]
 bounds=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)]
 wanted=expected['bounds'];wanted[1]=[-wanted[1][1],-wanted[1][0]]
 err=max(abs(a-b) for pair,goal in zip(bounds,wanted) for a,b in zip(pair,goal))
 assert err<.1,(o.name,err,bounds,wanted)
 assert len(o.data.uv_layers)==2,(o.name,len(o.data.uv_layers))
 assert len(o.data.polygons)==expected['triangles']
 rows.append({'mesh':o.name,'triangles':len(o.data.polygons),'uv_channels':len(o.data.uv_layers),'max_bounds_error':err})
assert len([o for o in bpy.data.objects if o.type=='MESH'])==len(rows)
(root/'fbx-roundtrip.json').write_text(json.dumps({'passed':True,'meshes':rows},indent=2));print('FBX roundtrip passed',len(rows),'meshes')
