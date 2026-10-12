"""Verify the actual packed UE3 masks for every revision 98 replacement."""
import bpy,collections,json,re,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=Path(bpy.data.filepath).parent
expected=set(json.loads((source/'room98.json').read_text())['changed'])
rows=[]
for path in sorted(source.glob('Room*_Assets98.t3d')):
 for name,body in re.findall(r'Begin StaticMesh Class=StaticMesh Name=(\w+).*?Begin StaticMeshTriangleBulkData(.*?)End StaticMeshTriangleBulkData',path.read_text(),re.S):
  raw=bytes.fromhex(' '.join(line.strip().replace(',',' ') for line in body.splitlines() if re.fullmatch(r'(?:[0-9a-f]{2},)+',line.strip())))
  local=re.sub(r'^Room\d+_','',name);obj=bpy.data.objects[local];mesh=obj.data
  assert len(raw)==len(mesh.polygons)*372,(name,len(raw))
  masks=[struct.unpack_from('<I',raw,i*372+248)[0] for i in range(len(mesh.polygons))]
  neighbors=collections.defaultdict(list)
  for face in mesh.polygons:
   for edge in face.edge_keys:neighbors[tuple(sorted(edge))].append(face)
  sharp={tuple(sorted(e.vertices)) for e in mesh.edges if e.use_edge_sharp}
  hard=smooth=0
  for edge,faces in neighbors.items():
   if len(faces)!=2:continue
   a,b=faces
   if edge in sharp or not(a.use_smooth and b.use_smooth):
    hard+=1;assert not masks[a.index]&masks[b.index],(name,edge,'hard')
   else:
    smooth+=1;assert masks[a.index]&masks[b.index],(name,edge,'smooth')
  assert smooth>100,(name,smooth)
  rows.append(dict(mesh=local,hard_edges=hard,smooth_edges=smooth,triangles=len(masks)))
assert {r['mesh'] for r in rows}==expected
(root/'evidence/room98/export-shading-check.json').write_text(json.dumps(rows,indent=2))
print('PASS',len(rows),'exported meshes;',sum(r['hard_edges'] for r in rows),'hard and',sum(r['smooth_edges'] for r in rows),'smooth joins')
