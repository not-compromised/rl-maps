"""Checkpoints use room surfaces without invisible replacement platforms."""
import unittest
from build_map import gray_scene
from course import DECKS, SPAWNS
from checkpoint_props import SUPPORT_TOPS, MARKER_SUPPORT_TOPS, MARKER_TOPS, BOOK_CHECKPOINTS, PROP_HEIGHT, RESTART_CENTER, RESTART_SIZE

class CheckpointSurfaceTests(unittest.TestCase):
 def test_only_rings_have_course_mesh_collision(self):
  scene=gray_scene()
  self.assertEqual(sum(m['collision'] for m in scene.meshes),100)
  for m in scene.meshes:
   if not m['name'].startswith('Gate'):
    self.assertFalse(m['collision'])
    self.assertLess(max(v[2] for v in m['vertices'])-min(v[2] for v in m['vertices']),20)
 def test_markers_clear_support_without_obstructing_landings(self):
  for i,z in enumerate(MARKER_TOPS):
   support=MARKER_SUPPORT_TOPS[i]+(PROP_HEIGHT if i in BOOK_CHECKPOINTS else 28 if i == 2 else 0)
   self.assertGreater(z,support)
   self.assertLessEqual(z-support,20)
   if i<len(SPAWNS):self.assertGreater(SPAWNS[i][2]-support,70)
 def test_finish_arrival_cannot_touch_restart(self):
  self.assertTrue(any(abs(RESTART_CENTER[a]-DECKS[-1][a])>RESTART_SIZE[a]/2+650+100 for a in (0,1)), 'Restart must remain outside the finish arrival box, including car clearance')
