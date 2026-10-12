"""Check the UV coordinates actually delivered to UE3's mesh importer."""
import struct
import unittest

from ue3 import static_mesh


def exported_vertices(material, vertices, uvs=None, lightmap_uvs=None, channel=0):
    mesh = dict(name='SurfaceProbe', material=material, vertices=vertices,
                faces=[tuple(range(len(vertices)))], collision=False, smooth=False)
    if uvs is not None:
        mesh['uvs'] = uvs
    if lightmap_uvs is not None:
        mesh['lightmap_uvs'] = lightmap_uvs
    text = static_mesh(mesh)
    binary = text.split(' Begin Binary\n', 1)[1].split(' End Binary', 1)[0]
    raw = bytes.fromhex(binary.replace(',', ' '))
    result = {}
    for base in range(0, len(raw), 372):
        for corner in range(3):
            position = struct.unpack_from('<3f', raw, base + corner * 12)
            result[position] = struct.unpack_from('<2f', raw, base + 36 + corner * 64 + channel * 8)
    return result


class SurfaceExportTests(unittest.TestCase):
    def test_timber_grain_follows_long_edge_in_both_deck_directions(self):
        for vertices, endpoint in [
            ([(0, 0, 0), (1800, 0, 0), (1800, 180, 0), (0, 180, 0)], (1800, 0, 0)),
            ([(0, 0, 0), (180, 0, 0), (180, 1800, 0), (0, 1800, 0)], (0, 1800, 0)),
        ]:
            with self.subTest(endpoint=endpoint):
                uv = exported_vertices('Wood', vertices)
                self.assertAlmostEqual(uv[endpoint][0], 0)
                self.assertAlmostEqual(abs(uv[endpoint][1]), 1)

    def test_snow_repeats_once_per_900_units(self):
        uv = exported_vertices('Snow', [(0, 0, 0), (900, 0, 0), (0, 900, 0)])
        self.assertEqual(uv[(900, 0, 0)], (1, 0))
        self.assertEqual(uv[(0, 900, 0)], (0, 1))

    def test_authored_rope_coordinates_survive_export(self):
        vertices = [(0, 0, 0), (100, 0, 0), (0, 100, 0)]
        authored = [(0.25, 18), (0.5, 19), (0.75, 20)]
        self.assertEqual(exported_vertices('Rope', vertices, authored), dict(zip(vertices, authored)))

    def test_sky_retains_spherical_coordinates(self):
        uv = exported_vertices('Sky', [(100, 0, 0), (0, 100, 0), (0, 0, 100)])
        self.assertEqual(uv[(100, 0, 0)], (0.5, 0.5))
        self.assertEqual(uv[(0, 100, 0)], (0.75, 0.5))
        self.assertEqual(uv[(0, 0, 100)], (0.5, 0))

    def test_sky_seam_does_not_stretch_a_triangle_across_the_panorama(self):
        vertices = [(-100, 1, 0), (-100, -1, 0), (-100, 0, 10)]
        uv = exported_vertices('Sky', vertices)
        horizontal = [coord[0] for coord in uv.values()]
        self.assertLess(max(horizontal) - min(horizontal), 0.01)

    def test_lightmap_coordinates_are_independent_of_surface_tiling(self):
        vertices = [(0, 0, 0), (900, 0, 0), (0, 900, 0)]
        lightmap = [[(0.25, 0.25), (0.25, 0.75), (0.75, 0.25)]]
        surface = exported_vertices('Snow', vertices, lightmap_uvs=lightmap)
        lighting = exported_vertices('Snow', vertices, lightmap_uvs=lightmap, channel=1)
        self.assertEqual(surface[(900, 0, 0)], (1, 0))
        self.assertEqual(lighting[(900, 0, 0)], (0.75, 0.25))
        self.assertEqual(lighting[(0, 900, 0)], (0.25, 0.75))


if __name__ == '__main__':
    unittest.main()
