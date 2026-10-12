"""Check the actual T3D corner stream against the loaded source sharp edges."""
import bpy,collections,json,re,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
text=(Path(args[0]) if args else root/'output/room-surfaces-97/Buzz97.t3d').read_text()
rows=[]
for name,body in re.findall(r'Begin StaticMesh Class=StaticMesh Name=(\w+).*?Begin StaticMeshTriangleBulkData(.*?)End StaticMeshTriangleBulkData',text,re.S):
 # Bulk bytes use comma-separated hex; metadata lines must stay excluded.
 lines=[line.strip() for line in body.splitlines() if re.fullmatch(r'(?:[0-9a-f]{2},)+',line.strip())]
 raw=bytes.fromhex(''.join(lines).replace(',',' '))
 obj=bpy.data.objects[name.removeprefix('Room09_')];mesh=obj.data
 assert len(raw)==len(mesh.polygons)*372,(name,len(raw))
 masks=[struct.unpack_from('<I',raw,i*372+248)[0] for i in range(len(mesh.polygons))]
 edges=collections.defaultdict(list)
 for face in mesh.polygons:
  for edge in face.edge_keys:edges[tuple(sorted(edge))].append(face)
 hard=0;smooth=0
 for faces in edges.values():
  if len(faces)!=2:continue
  a,b=faces;dot=a.normal.dot(b.normal)
  if dot<.5:
   hard+=1;assert masks[a.index]&masks[b.index]==0,(name,a.index,b.index)
  elif a.use_smooth and b.use_smooth:
   smooth+=1;assert masks[a.index]&masks[b.index],(name,a.index,b.index)
 rows.append(dict(mesh=name,sharp_edges_verified=hard,continuous_edges_verified=smooth,triangles=len(masks)))
assert len(rows)==4
(root/'evidence/surface97/export-shading-check.json').write_text(json.dumps(rows,indent=2));print(rows)
