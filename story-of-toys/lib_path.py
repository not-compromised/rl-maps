"""Put the repository's shared lib/ folder on sys.path.

The modules in lib/ import this map's own course, world and ue3 by name, so
lib/ is appended after this map's folder and the map's own modules win.
"""
import sys
from pathlib import Path

LIB = str(Path(__file__).resolve().parents[1] / 'lib')
if LIB not in sys.path:
    sys.path.append(LIB)
