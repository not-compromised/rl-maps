"""Run the shared tests in lib/tests against this map's own modules.

`python3 -m unittest discover -s tests` from the map folder picks this file
up. The shared tests import this map's build_map and ue3, because the map
folder comes first on sys.path.
"""
import sys
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / 'lib'
SHARED = ('test_lightmap_source', 'test_surface_export')


def load_tests(loader, tests, pattern):
    if str(LIB) not in sys.path:
        sys.path.append(str(LIB))
    suite = unittest.TestSuite()
    for name in SHARED:
        suite.addTests(unittest.TestLoader().discover(
            str(LIB / 'tests'), pattern=name + '.py', top_level_dir=str(LIB / 'tests')))
    return suite
