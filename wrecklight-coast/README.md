# Wrecklight Coast

A rope-ring aerial course over a haunted coastal shipwreck: 54 rings in six
stages (The Hold, The Crags, North Ridge, Barge Cove, The Bones, Watchtower)
through a wrecked ghost ship, cliffs, coves and mountains. Package
`WrecklightTrial01`. Visual direction is in [STYLE.md](STYLE.md).

```sh
python3 build_map.py              # gray course: output/course.t3d, Voyage.kismet.txt, build.json
python3 build_map.py --full       # with materials, fog and lights
python3 verify_source.py          # checks gates, stages, sensors and Kismet references
python3 -m unittest discover -s tests
```

Texture inputs and the generated sky are described in
[assets/README.md](assets/README.md). The texture conversion step it names
(`tools/prepare_textures.py`) belongs to the separate workshop toolkit and is
not in this repository.
