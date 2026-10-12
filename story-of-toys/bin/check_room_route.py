"""Blender geometry clearance, separate from game flight proof."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course import route_segments,GATES,local
out=Path(sys.argv[sys.argv.index('--')+1]); dg=bpy.context.evaluated_depsgraph_get()
trees=[(o.name,BVHTree.FromObject(o,dg)) for o in bpy.data.objects if o.type=='MESH']
hits=[];near=[]
for i,(a,b) in enumerate(route_segments()):
 a,b=Vector(a),Vector(b);d=b-a
 for name,tree in trees:
  hit=tree.ray_cast(a,d.normalized(),d.length)
  if hit[0] is not None:hits.append({'segment':i,'mesh':name,'point':list(hit[0])})
 for j in range(1,max(2,math.ceil(d.length/200))):
  p=a+d*j/max(2,math.ceil(d.length/200))
  for name,tree in trees:
   n=tree.find_nearest(p,100)
   if n and n[0] is not None:near.append({'segment':i,'mesh':name,'point':list(p),'distance':n[3]})
rims=[]
for g in GATES:
 for j in range(48):
  a=math.tau*j/48;p=Vector(local(g,0,(g['radius']+44)*math.cos(a),(g['radius']+44)*math.sin(a)))
  for name,tree in trees:
   n=tree.find_nearest(p,70)
   if n and n[0] is not None:rims.append({'gate':g['index'],'mesh':name,'distance':n[3]})
out.write_text(json.dumps({'ray_intersections':hits,'within_100_units':near,'rim_intersections':rims},indent=2));print(json.dumps({'hits':hits,'near_count':len(near),'rim_hits':rims}))
