# Blender import probe

A technical test asset, not a map: one checker-textured platform with an
off-centre opening and a raised block, used to prove geometry, UVs, collision
and lighting survive the Blender to UDK import path. Package
`BlenderImportProbe01`. See [STYLE.md](STYLE.md).

```sh
python3 build_map.py
python3 verify_source.py
python3 -m unittest discover -s tests
```

`create_probe.py` runs inside Blender; the `prepare_*.py` scripts write the
probe's import and runtime files under `output/`.
