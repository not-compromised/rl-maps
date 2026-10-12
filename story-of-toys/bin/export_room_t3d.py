"""Export Blender geometry and both UV channels with UDK collision settings."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ue3 import static_mesh,actor
from course import PACKAGE
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]);prefix=args[1];names=args[2:]
addon=None
if '--actors' in names:
 i=names.index('--actors');addon=Path(names[i+1]).read_text();del names[i:i+2]
 assert addon.startswith(f'Begin Map Name={PACKAGE}\nBegin MapPackage\n')
 assert not names,'Actor supplement requires every room mesh'
if out.exists():raise RuntimeError('Choose a new geometry export path')
objects=[bpy.data.objects[n] for n in names] if names else [o for o in bpy.data.objects if o.type=='MESH']
rows=[]
with out.open('w') as f:
 f.write(f'Begin Map Name={PACKAGE}\nBegin MapPackage\n')
 if addon:f.write(addon.split('Begin MapPackage\n',1)[1].split('End MapPackage\n',1)[0])
 for o in objects:
  assert len(o.data.uv_layers)==2,o.name
  groups=None
  if o.get('export_sharp_edges',False):
   groups,_=o.data.calc_smooth_groups(use_bitflags=True)
   assert all(g for g,p in zip(groups,o.data.polygons) if p.use_smooth),f'{o.name}: smoothing group overflow'
  vertices=[];faces=[];uvs=[];lightmaps=[];smoothing=[]
  for poly in o.data.polygons:
   assert len(poly.loop_indices)==3,(o.name,poly.index)
   face=[];lm=[]
   for li in poly.loop_indices:
    face.append(len(vertices));vertices.append(tuple(o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co))
    u,v=o.data.uv_layers[0].data[li].uv
    uvs.append((u,1-v));lm.append(tuple(o.data.uv_layers[1].data[li].uv))
   smoothing.append(groups[poly.index] if groups is not None else (1 if poly.use_smooth else 0))
   faces.append(tuple(face));lightmaps.append([lm[0],lm[2],lm[1]])
  m=dict(name=prefix+o.name,vertices=vertices,faces=faces,uvs=uvs,lightmap_uvs=lightmaps,material=o.get('export_material','RoomAtlas'),collision=o.get('export_collision',True),smooth=False,smoothing_groups=smoothing,lightmap_resolution=o.get('lightmap_resolution',512 if o.name in ('RoomAndy','RoomBed','RoomToys') else 256))
  f.write(static_mesh(m).replace(' LightMapCoordinateIndex=1',' UseFullPrecisionUVs=True\n LightMapCoordinateIndex=1'))
  rows.append(dict(name=m['name'],triangles=len(faces),bounds=[[min(v[i] for v in vertices),max(v[i] for v in vertices)] for i in range(3)]))
 f.write('End MapPackage\n'+addon.split('End MapPackage\n',1)[1] if addon else 'End MapPackage\nBegin Level Name=PersistentLevel\n'+actor('WorldInfo','ReservedWorld','')+actor('Brush','ReservedBrush','')+'End Level\nEnd Map\n')
out.with_suffix('.json').write_text(json.dumps(dict(package=PACKAGE,meshes=rows,sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=2))
print('Geometry export',out,len(rows),'meshes')
