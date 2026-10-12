"""Render the reference-driven furniture revision from useful inspection views."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(exist_ok=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=1000;s.render.resolution_percentage=100
views=[('bed',(-8500,-6000,11000),(-16300,6500,5700),26),('nursery',(8500,-6000,11000),(0,-15000,3800),24),('desk',(-11000,4000,10500),(-2500,14000,8500),24),('overview',(21000,-18000,17000),(-2000,3500,10500),19)]
for name,pos,target,lens in views:
 if len(sys.argv)>sys.argv.index('--')+2 and name not in sys.argv[sys.argv.index('--')+2:]:continue
 c=s.camera;c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;c.data.clip_end=150000
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
