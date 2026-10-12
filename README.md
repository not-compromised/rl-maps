# rl-maps

Source generators for custom Rocket League maps. Each map is a set of Python
scripts that write Unreal Engine 3 text (course geometry, materials, Kismet
logic) for import into the Rocket League UDK editor. No game files, editor
files or built map packages are kept here.

Downloads: https://pmserver.us/rocket-league/downloads.

## Maps

| Folder | Map |
|---|---|
| [wrecklight-coast/](wrecklight-coast/) | Wrecklight Coast: a 54-ring, six-stage rope-ring course through a haunted shipwreck coast |
| [haunted-hold/](haunted-hold/) | The Haunted Hold: a compact six-gate aerial trainer inside a haunted ship's cargo hold |
| [story-of-toys/](story-of-toys/) | Story of Toys: a 100-ring, seven-stage course through a toy-filled bedroom (unofficial fan map) |
| [experiments/blender-import/](experiments/blender-import/) | Blender import probe: a small test asset for the Blender to UDK path |

[lib/](lib/) holds the generator modules the ring maps share (rock and
geology, rope rings, camera stations, lightmap reuse, course bounds, surface
materials) and their tests. Each map loads it through its own `lib_path.py`;
nothing needs installing.

## Build a map from a clone

You need Python 3 (standard library only for the generators).
Run `./scripts/check.sh` from the repository root to test and build every map.
GitHub Actions runs the same command on pushes and pull requests. These are
source checks; they do not open UDK or prove the saved game packages playable.

```sh
git clone https://github.com/not-compromised/rl-maps.git
cd rl-maps/haunted-hold          # or any map folder
python3 build_map.py             # writes output/course.t3d, output/Voyage.kismet.txt, output/build.json
python3 verify_source.py         # checks the generated source without opening the editor
python3 -m unittest discover -s tests
```

Run the commands from the map's own folder. Textured builds need the Poly
Haven texture sets each map's credits list, converted to TGA; the images are
not stored here. Importing the text into UDK, baking lighting and packaging
the map for the game are done in the Rocket League UDK editor and are not
automated by this repository.

The public test suites cover the map generators and shared library. Editor
transport, asset-update and lightmap-tool tests depend on the separate private
workshop toolkit and remain outside this public export.

## Licence

The original code is released under the [MIT licence](LICENSE). Third-party
material, which keeps its own terms, is described in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
