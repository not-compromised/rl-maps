import math
import unittest
from course import GATES,STAGE_STARTS,SPAWNS,TARGETS,stage_gates,unit,sub,dot

def angle(a,b):
 return math.degrees(math.acos(max(-1,min(1,dot(unit(a),unit(b))))))

class FlightFlow(unittest.TestCase):
 def test_direction_changes_are_spread_over_multiple_rings(self):
  for stage in range(1,len(STAGE_STARTS)+1):
   gates=stage_gates(stage)
   points=[SPAWNS[stage-1]]+[g['center'] for g in gates]+[TARGETS[stage-1]]
   for gate,a,b,c in zip(gates,points,points[1:],points[2:]):
    with self.subTest(gate=gate['index']):
     self.assertLessEqual(angle(sub(b,a),sub(c,b)),35 if stage==1 else 65)
 def test_ring_faces_the_approach_and_exit(self):
  for stage in range(1,len(STAGE_STARTS)+1):
   gates=stage_gates(stage)
   points=[SPAWNS[stage-1]]+[g['center'] for g in gates]+[TARGETS[stage-1]]
   for gate,a,b,c in zip(gates,points,points[1:],points[2:]):
    with self.subTest(gate=gate['index']):
     self.assertLessEqual(angle(gate['normal'],sub(b,a)),45)
     self.assertLessEqual(angle(gate['normal'],sub(c,b)),45)
 def test_local_spacing_is_consistent_through_bends(self):
  for stage in range(1,len(STAGE_STARTS)+1):
   gates=stage_gates(stage)
   gaps=[math.dist(a['center'],b['center']) for a,b in zip(gates,gates[1:])]
   with self.subTest(stage=stage):
    self.assertLess(max(gaps)/min(gaps),1.2)
    self.assertGreater(min(gaps),1500)
 def test_requested_course_length_and_sizes_remain(self):
  self.assertEqual(len(GATES),100)
  self.assertEqual(len(STAGE_STARTS),7)
  self.assertEqual({g['radius'] for g in GATES},{340,470,620})

 def test_late_stage_has_one_compact_hairpin(self):
  gates=stage_gates(6)
  turns=[(a,b) for a in gates for b in gates if 2 <= b['index']-a['index'] <= 4 and angle(a['normal'],b['normal']) >= 145 and math.dist(a['center'],b['center']) < 7000]
  self.assertTrue(turns,'Yellow stage needs a clear near-180-degree turn across several aligned rings')
