# Andy facial texture study

`face-study-01.png` was generated with the built-in image-generation tool on 2026-09-12 using the owner's supplied movie photo as the identity reference. It is an input texture, not a render of the map. No downloaded third-party character mesh is used.

`bin/build_room_blender.py` maps it onto the rebuilt head, eyes and mouth. The original file is preserved unchanged. Candidate40 uses Blender emission baking to combine it with the existing room atlas at4096square; use `BakedRoomAtlas.tga` for UDK, not the older1024 `RoomAtlas.tga` written during construction. BothUVchannels and the existing MI_RoomAtlas assignment remain.

Bake the saved Blender scene with `bin/bake_room_atlas.py -- NEW_OUTPUT_DIRECTORY`, then export geometry from `AndyDetail-baked.blend`. Import the baked texture as the existing `AndysRoomRings03.RoomAtlas` asset before replacing the head. The original room material and actor overrides can then remain in place. The helper refuses to overwrite an existing bake. It spot-checks colors in the other15tiles; it does not claim every interpolated pixel is identical after enlargement.
