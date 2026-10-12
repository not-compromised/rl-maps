# Asset inputs

The current material set uses weathered_planks, seaside_rock, hessian_230, rusty_metal and snow_02 from Poly Haven. [Credits](TEXTURE-CREDITS.md) provide source pages and license. Download metadata is retained in `sources/`; full source textures remain locally in ignored `textures/`.

For each set acquire 2K PNG diffuse, DirectX normal and roughness images from the recorded source and save them as `<asset>_diff_2k.png`, `<asset>_nor_dx_2k.png`, `<asset>_rough_2k.png` under `assets/textures/`. The metadata contains original download URLs and hashes. Verify downloaded bytes against the source metadata rather than trusting filenames. OpenGL normals are useful for Blender but the editor recipe uses DirectX normals.

Then run `python3 tools/prepare_textures.py` from the repository root. It writes fifteen RGB TGA images and a manifest under output/textures. Snow uses 1024-square output to limit package size; other sets use 2048-square output.

The generated sky is retained as `assets/ghost_sky.png`, with its original prompt in `sky-prompt.txt`. For UDK convert it to 24-bit RGB TGA and import as `T_GhostSky` in the map package. This sky has no asset-download prerequisite. Preserve its prompt/provenance when changing it.

`THIRD_PARTY_NOTICES.md` distinguishes licensed inputs from proprietary reference extractions. Texture files are outside Git by default to keep source history small; the local workspace is not missing them. A fresh clone must acquire the documented inputs before texture conversion.
