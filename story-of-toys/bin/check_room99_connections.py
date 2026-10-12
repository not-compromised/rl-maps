"""Check the visible joints independently in an opened candidate or baseline."""
import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from polish_room99 import components,bounds,spindle_gaps
obj=bpy.data.objects['RoomGlobe']
ring=[fs for fs in components(obj) if bounds(obj,fs)[2][1]>7000]
gaps=spindle_gaps()
report=dict(source=bpy.data.filepath,meridian_components=len(ring),spindle_gaps=gaps)
args=sys.argv[sys.argv.index('--')+1:]
Path(args[0]).write_text(json.dumps(report,indent=2))
assert len(ring)==1, f'Meridian has {len(ring)} disconnected pieces'
assert max(r['gap'] for r in gaps)<=0, 'Crib spindles do not reach their arch'
vertices={v for f in ring[0] for v in f.vertices}
edges={}
for face in ring[0]:
 for edge in face.edge_keys:edges[tuple(sorted(edge))]=edges.get(tuple(sorted(edge)),0)+1
assert set(edges.values())=={2},'Meridian has open or nonmanifold joints'
assert len(vertices)-len(edges)+len(ring[0])==0,'Meridian is not one closed loop'
print('PASS: continuous closed meridian, all 18 crib end spindles meet their arches')
