import math
import unittest
from course import DECKS, POINTS, STAGE_STARTS, STAGE_COLORS, stage_material
from build_map import material, gray_scene, sensors
from logic import generate

class RouteReadability(unittest.TestCase):
 def test_checkpoint_approaches_have_room_and_at_least_100_degrees(self):
  for checkpoint,first in enumerate(STAGE_STARTS[1:],1):
   p=DECKS[checkpoint]
   incoming=[POINTS[first-2][i]-p[i] for i in range(2)]
   outgoing=[POINTS[first-1][i]-p[i] for i in range(2)]
   a,b=math.hypot(*incoming),math.hypot(*outgoing)
   with self.subTest(checkpoint=checkpoint):
    self.assertGreaterEqual(min(a,b),3000)
    angle=math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(incoming,outgoing))/(a*b)))))
    self.assertGreaterEqual(angle,100)
    incoming3=[POINTS[first-2][i]-p[i] for i in range(3)]
    outgoing3=[POINTS[first-1][i]-p[i] for i in range(3)]
    cosine=sum(x*y for x,y in zip(incoming3,outgoing3))/(math.hypot(*incoming3)*math.hypot(*outgoing3))
    self.assertGreaterEqual(math.degrees(math.acos(max(-1,min(1,cosine)))),100)
 def test_no_manual_camera_controls_remain(self):
  self.assertFalse(any('Camera' in m['name'] for m in gray_scene().meshes))
  self.assertNotIn('CameraOn',''.join(sensors()))
  self.assertNotIn('CameraOff',''.join(sensors()))
  graph=generate()
  for name in ('CameraEnabled','WantCamera','EnableCamera','DisableCamera'):
   self.assertNotIn(name,graph.nodes)
  self.assertIn('CameraDelay',str(graph.nodes['ClearCamera']))
  self.assertIn('AddCamera',str(graph.nodes['CameraDelay']))
 def test_colored_checkpoint_surfaces_have_valid_nonoverlapping_lightmaps(self):
  import runpy
  overlap=runpy.run_path('bin/room_lightmaps.py')['overlapping_triangle_indices']
  for mesh in gray_scene().meshes:
   self.assertIn('lightmap_uvs',mesh)
   if mesh['name'].startswith('Gate'):continue
   self.assertEqual(overlap(mesh['lightmap_uvs']),[],mesh['name'])
   self.assertTrue(all(0<=x<=1 for triangle in mesh['lightmap_uvs'] for uv in triangle for x in uv))
 def test_stage_rings_receive_lighting(self):
  for i in range(1,len(STAGE_COLORS)+1):
   source=material(stage_material(i))
   self.assertIn('TexturePaint_2Tex_Color',source)
   self.assertNotIn('Unlit',source)
   self.assertIn('ParameterName="EmissiveMultiply",ParameterValue=0',source)
