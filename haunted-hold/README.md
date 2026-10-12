# The Haunted Hold

A compact aerial trainer inside a haunted ship's cargo hold: a U-shaped
route of six braided rope gates in two stages (Outbound, Return), with a
highlight on the current gate. Package `CargoHold01`. Visual direction is in
[STYLE.md](STYLE.md).

```sh
python3 build_map.py              # gray course: output/course.t3d, Voyage.kismet.txt, build.json
python3 build_map.py --full       # with materials, fog and lights
python3 verify_source.py
python3 -m unittest discover -s tests
python3 prepare_assets.py output/textures-next --download   # Poly Haven inputs to TGA (needs ImageMagick)
```

`testing/build_tour.py` and `testing/verify_highlights.py` generate a
walkthrough and check a runtime visibility snapshot; neither connects to the
game. Asset inputs: [docs/assets.md](docs/assets.md).
