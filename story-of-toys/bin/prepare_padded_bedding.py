import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'output/room-reference-82';assert not (out/'RoomFinish.blend').exists()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/room-reference-81/RoomFinish.blend'))
o=bpy.data.objects['RoomBedPrint']
for loop in o.data.uv_layers[0].data:loop.uv.x*=1441/1444
img=bpy.data.images.load(str(out/'RoomBuzzBedding.tga'));img.pack()
for node in o.data.materials[0].node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=img
bpy.ops.wm.save_as_mainfile(filepath=str(out/'RoomFinish.blend'))
