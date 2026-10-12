# lib

Generator modules shared by the ring maps (Wrecklight Coast, The Haunted
Hold, Story of Toys and the Blender import probe), kept once instead of as
identical copies in every map folder.

These modules import the calling map's own `course`, `world` and `ue3` by
name, so they only work with a map folder first on `sys.path`. Each map's
`lib_path.py` appends this folder after the map's own; run the map's scripts
from its folder. The tests in `tests/` run once per map through that map's
`tests/test_shared_lib.py`.
