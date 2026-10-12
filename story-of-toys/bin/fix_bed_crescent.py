"""Repair crown normals before cutting the bed's crescent opening."""
import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from room_lightmaps import repair_mesh
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
assert not (out/'RoomFinish.blend').exists()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/room-reference-79/RoomFinish.blend'))
scene=bpy.context.scene;o=bpy.data.objects['RoomBed'];before=len(o.data.polygons)
# Discard the old malformed crown/cutter components, retaining posts and spindles.
bm=bmesh.new();bm.from_mesh(o.data);seen=set();discard=[]
for seed in bm.verts:
 if seed in seen:continue
 todo=[seed];component=[];seen.add(seed)
 while todo:
  v=todo.pop();component.append(v)
  for edge in v.link_edges:
   q=edge.other_vert(v)
   if q not in seen:seen.add(q);todo.append(q)
 if min(v.co.y for v in component)>13000 and max(v.co.y for v in component)<14500 and min(v.co.z for v in component)>4500 and (max(v.co.x for v in component)-min(v.co.x for v in component)>5000 or -16500<sum(v.co.x for v in component)/len(component)<-15000):
  discard.extend(component)
assert discard
bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(o.data);bm.free()
mat=o.data.materials[0]
def finish(obj,name,tile):
 obj.data.materials.append(mat);uv=obj.data.uv_layers.new(name='UVMap')
 for f in obj.data.polygons:
  for li in f.loop_indices:
   co=obj.data.vertices[obj.data.loops[li].vertex_index].co
   uv.data[li].uv=(.005+.24*(co.x+21000)/10500,.005+.24*co.z/10000)
 return obj
code=(ROOT/'bin/redesign_room.py').read_text();start=code.index('def mesh(');end=code.index('# Cream paneling',start)
exec(code[start:end]);crown=arch_board('Replacement crown',-15750,13700,10500,4600,9900,6200,340,0,2100)
crescent_cut(crown,-15750,13700,8850)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);crown.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
bpy.context.view_layer.objects.active=o;o.select_set(True)
o.data.uv_layers.active_index=1
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
mod=o.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
repair_mesh(o,1024)
tree=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get())
hole=tree.ray_cast(Vector((-16100,13000,8850)),Vector((0,1,0)),1400)[0]
assert hole is None,('Crescent remained filled',hole)
solid=tree.ray_cast(Vector((-15750,13000,9650)),Vector((0,1,0)),1400)[0]
assert solid is not None,'Crown missing'
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()/'RoomFinish.blend'))
(out/'crescent.json').write_text(json.dumps({'before_triangles':before,'after_triangles':len(o.data.polygons),'hole_ray_clear':True,'crown_ray_solid':True},indent=2))
