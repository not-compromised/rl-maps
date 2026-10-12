"""Check visible hoop continuity/clearance, independent of the editor renderer."""
import math
import unittest
from collections import Counter
from build_map import ring
from course import GATES, sub, dot, basis
from ue3 import Scene


class RopeGeometryTests(unittest.TestCase):
    def test_each_ring_keeps_its_opening_and_has_no_open_seam(self):
        for gate in GATES:
            with self.subTest(gate=gate['index']):
                scene = Scene()
                ring(scene, gate)
                braid = next(m for m in scene.meshes if m['material'] == 'Rope')
                collision = [m for m in scene.meshes if m['collision']]
                self.assertEqual(len(collision), 1)
                self.assertTrue(collision[0]['hidden'])
                self.assertFalse(braid['collision'])
                self.assertEqual(len(braid['uvs']), len(braid['vertices']))
                n, side, up = basis(gate['normal'])
                # Weld by physical location; UV seam duplicates must close geometrically.
                welded = [tuple(round(c, 5) for c in p) for p in braid['vertices']]
                edges = Counter()
                for face in braid['faces']:
                    for a, b in zip(face, face[1:] + face[:1]):
                        self.assertNotEqual(welded[a], welded[b])
                        edges[tuple(sorted((welded[a], welded[b])))] += 1
                self.assertTrue(all(count == 2 for count in edges.values()), 'Open or nonmanifold rope seam')
                for p in braid['vertices']:
                    delta = sub(p, gate['center'])
                    radius = math.hypot(dot(delta, side), dot(delta, up))
                    self.assertGreaterEqual(radius, gate['radius'] - 1e-5)
                    self.assertLessEqual(radius, gate['radius'] + 88 + 1e-5)
                    self.assertLessEqual(abs(dot(delta, n)), 44 + 1e-5)


if __name__ == '__main__':
    unittest.main()
