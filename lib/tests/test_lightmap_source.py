import copy
import json
import unittest

from build_map import key_light
from lightmap_source import apply_lightmaps
from ue3 import Scene, mesh_actor


class LightmapSourceTests(unittest.TestCase):
    def scene_and_cache(self):
        scene = Scene()
        scene.box('DeckA', (0, 0, 0), (200, 200, 20), 'Wood')
        scene.box('DeckB', (500, 0, 0), (200, 200, 20), 'Wood')
        cache = json.loads(json.dumps({'meshes': scene.meshes}))
        cache['meshes'][0].update(lightmap_uvs=[[(0, 0), (.5, 0), (0, .5)]]*12,
                                  lightmap_resolution=512)
        return scene.meshes, cache

    def test_stale_geometry_is_rejected_before_applying_charts(self):
        meshes, cache = self.scene_and_cache()
        cache['meshes'][0]['vertices'][0][0] += 1
        before = copy.deepcopy(meshes)
        with self.assertRaisesRegex(ValueError, 'Stale lightmap geometry: DeckA'):
            apply_lightmaps(meshes, cache)
        self.assertEqual(meshes, before)

    def test_only_charted_meshes_enable_baked_lighting(self):
        meshes, cache = self.scene_and_cache()
        lighting = apply_lightmaps(meshes, cache)
        self.assertEqual(lighting['meshes'], ['DeckA'])
        self.assertEqual(lighting['size'], [1200, 1200, 1020])
        self.assertIn('bUsePrecomputedShadows=True', mesh_actor(meshes[0]))
        self.assertIn('bUsePrecomputedShadows=False', mesh_actor(meshes[1]))
        sun = key_light(baked=True)
        self.assertIn('Class=DominantDirectionalLight Name=Sun', sun)
        self.assertIn('bForceDynamicLight=False', sun)
        self.assertNotIn('DominantDirectionalLightMovable', sun)


if __name__ == '__main__':
    unittest.main()
