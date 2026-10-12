# Hold asset inputs

This map uses three Poly Haven texture sets: weathered_planks, hessian_230 and rusty_metal. Source download metadata lives in `assets/sources/`. Original 2K PNG files live in ignored `assets/textures/`. The generated sky and its prompt live in `assets/ghost_sky.png` and `assets/sky-prompt.txt`.

From this map workspace, prepare a fresh import directory:

```sh
python3 prepare_assets.py output/textures-next --download
```

The helper verifies each source against its recorded MD5 before conversion, refuses an existing output directory, and writes ten 24-bit RGB TGA files plus a SHA256 manifest. It downloads missing inputs only from the recorded Poly Haven host. Omit `--download` to require existing local sources. ImageMagick `magick` must be installed.

Diffuse, DirectX normal and inverted roughness maps are 1024 square. The sky is 2048 by 1024. Inverted roughness approximates the specular input expected by this legacy material; it is not a physically accurate metalness conversion. The material bindings are in `surface_materials.py`.

Import into package CargoHold01 with these settings:

| Channel | Compression | SRGB |
|---|---|---|
| Diffuse and sky | TC_Default | True |
| DirectX normal | TC_Normalmap | False |
| Specular | TC_Default | False |

The manifest states required settings, not verified engine state. Query Texture2D CompressionSettings and SRGB after import, save, reopen, and query again. Current package status belongs in TASK.md. Ten reproduced textures matched the original prepared files byte for byte on 2026-09-11.

Poly Haven publishes these inputs under CC0. Source pages: [weathered planks](https://polyhaven.com/a/weathered_planks), [hessian](https://polyhaven.com/a/hessian_230), [rusty metal](https://polyhaven.com/a/rusty_metal). Preserve metadata and generated-sky provenance when moving the workspace. Proprietary reference-map extractions are not distributable assets; see the repository THIRD_PARTY_NOTICES.md.

## Observed editor procedure

Content Browser search `spec` narrows CargoHold01 to its three specular textures. Double-click each texture to open its Texture Properties viewer, search `srgb`, and clear the visible checkbox. Close the viewer before saving the map. Search text and checkbox state need screenshot/readback verification. A native bridge click dismissed a context menu without invoking Properties; a QEMU double-click opened the viewer correctly. The editor-input helper exits after a native click, so native click and subsequent keys must be separate calls.
