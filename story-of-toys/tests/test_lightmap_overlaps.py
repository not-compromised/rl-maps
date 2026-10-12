import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
from room_lightmaps import overlapping_triangle_indices

class LightmapOverlapTests(unittest.TestCase):
    def test_contained_triangle_is_an_overlap(self):
        outer=((0,0),(1,0),(0,1))
        inner=((.1,.1),(.2,.1),(.1,.2))
        self.assertEqual(overlapping_triangle_indices([outer,inner]),[0,1])

    def test_coincident_reversed_triangle_is_an_overlap(self):
        triangle=((.1,.1),(.8,.1),(.1,.8))
        self.assertEqual(overlapping_triangle_indices([triangle,triangle[::-1]]),[0,1])

    def test_shared_chart_edges_are_allowed(self):
        self.assertEqual(overlapping_triangle_indices([
            ((0,0),(1,0),(0,1)), ((1,0),(1,1),(0,1))]),[])

    def test_bounding_boxes_alone_do_not_prove_overlap(self):
        self.assertEqual(overlapping_triangle_indices([
            ((0,0),(.8,0),(0,.8)), ((1,1),(1,.3),(.3,1))]),[])
