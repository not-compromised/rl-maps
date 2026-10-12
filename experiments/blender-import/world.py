"""Small calibration backdrop; replace this module when designing the world."""
import lib_path  # noqa: F401  (puts the shared ../lib on sys.path)
from course import DECKS, add
from course_bounds import sea_reset


def build_world(scene):
    center, size = sea_reset()
    water_z = center[2] + size[2]/2 - 100
    scene.box('CalibrationWater', (center[0], center[1], water_z), (size[0], size[1], 20), 'Water', False)
    for i, deck in enumerate(DECKS):
        # Supports stop at the landing underside; the approach remains clear.
        scene.box(f'CalibrationPier{i}', add(deck, (0,0,-350)), (900,900,340), 'Rock')
