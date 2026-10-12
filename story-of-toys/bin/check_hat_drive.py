"""Check the actual Blender hat supports a car-width driving corridor."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(sys.argv[sys.argv.index('--')+1]);dg=bpy.context.evaluated_depsgraph_get()
trees={o.name:BVHTree.FromObject(o,dg) for o in bpy.data.objects if o.type=='MESH'}
rows=[]
for x in range(-500,4201,150):
 for y in (-1650,-1400,-1150):
  hit=trees['RoomAndyHat'].ray_cast(Vector((x,y,17000)),Vector((0,0,-1)),1000)
  assert hit[0] is not None,('Hat support missing',x,y)
  assert abs(hit[0].z-16340)<1,('Hat is not a smooth driving strip',x,y,hit[0].z)
  center=Vector((x,y,16423))
  for name,tree in trees.items():
   if name=='RoomAndyHat':continue
   nearest=tree.find_nearest(center,130)
   assert nearest[0] is None,('Driving corridor obstructed',name,x,y,nearest[3])
  rows.append((x,y,hit[0].z))
for x in range(4150,4401,25):
 for y in (-1500,-1400,-1300):
  hit=trees['RoomAndyHat'].ray_cast(Vector((x,y,17000)),Vector((0,0,-1)),1000)
  assert hit[0] is not None and abs(hit[0].z-16340)<1,('Launch run unsupported',x,y)
out.write_text(json.dumps({'passed':True,'car_center_z':16423,'corridor_width':500,'support_samples':len(rows),'x_range':[-500,4150],'y_center':-1400},indent=2))
print('Hat driving corridor passed',len(rows),'support samples')
