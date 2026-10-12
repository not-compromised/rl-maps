"""Check the intended curved approaches, including a car-sized clearance envelope."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course import PATHS,GATES,dot,sub
out=Path(sys.argv[sys.argv.index('--')+1]);dg=bpy.context.evaluated_depsgraph_get()
trees=[(o.name,BVHTree.FromObject(o,dg)) for o in bpy.data.objects if o.type=='MESH']
hits=[];near=[];planes=[]
for stage,points in enumerate(PATHS,1):
 for i,(a,b) in enumerate(zip(points,points[1:])):
  a,b=Vector(a),Vector(b);d=b-a
  for name,tree in trees:
   hit=tree.ray_cast(a,d.normalized(),d.length)
   if hit[0] is not None:hits.append({'stage':stage,'mesh':name,'point':list(hit[0])})
   n=tree.find_nearest(a,120)
   if n and n[0] is not None:near.append({'stage':stage,'mesh':name,'distance':n[3],'point':list(a)})
 for g in [g for g in GATES if g['stage']==stage]:
  crossings=[]
  for a,b in zip(points,points[1:]):
   da=dot(sub(a,g['center']),g['normal']);db=dot(sub(b,g['center']),g['normal'])
   if da*db<0:
    p=tuple(x+(y-x)*(-da)/(db-da) for x,y in zip(a,b));r=math.dist(p,g['center'])
    if r<4500:crossings.append({'radius':r,'forward':db>da})
  planes.append({'gate':g['index'],'crossings_within_miss_boundary':crossings})
result={'curve_hits':hits,'within_120_units':near,'ring_plane_crossings':planes}
out.write_text(json.dumps(result,indent=2));print(json.dumps({'curve_hits':hits,'near_count':len(near),'bad_ring_crossings':[p for p in planes if len(p['crossings_within_miss_boundary'])!=1 or not p['crossings_within_miss_boundary'][0]['forward'] or p['crossings_within_miss_boundary'][0]['radius']>5]}))
