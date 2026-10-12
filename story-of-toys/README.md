# Story of Toys

An unofficial, non-commercial fan map: a 100-ring aerial course in seven
stages (Toy Box, Bed and Desk, Remote Control, Hat Trick, Bookshelf, High
Flyer, Home) through a child's bedroom full of toys, with an explore mode
after the finish. Package `AndysRoomRings03`. Not affiliated with Disney or
Pixar; see [the notices](../THIRD_PARTY_NOTICES.md).

```sh
python3 build_map.py              # course: output/course.t3d, Voyage.kismet.txt, build.json
python3 verify_source.py
python3 -m unittest discover -s tests
```

There is no `--full` build: the room art is modelled in Blender and imported
as FBX after the course (`bin/prepare_room_import.py`). `bin/` holds those
room and character modelling steps (most run inside Blender) and the editor
helpers used while building the map; the `editor_*` helpers need the
separate workshop toolkit. Visual direction is in
[STYLE.md](STYLE.md); asset inputs in [docs/assets.md](docs/assets.md).
