# Texture sources

Powered by Poly Haven. The downloaded texture sets are free, public-domain CC0 assets. Original metadata and source images are retained in textures/.

- [Weathered planks](https://polyhaven.com/a/weathered_planks)
- [Seaside rock](https://polyhaven.com/a/seaside_rock)
- [Hessian canvas](https://polyhaven.com/a/hessian_230), used for sails and rope.
- [Rusty metal](https://polyhaven.com/a/rusty_metal)
- [Snow 02](https://polyhaven.com/a/snow_02), by Rob Tuytel.
- [License](https://polyhaven.com/license)

Run `python3 tools/prepare_textures.py` to prepare 24-bit RGB TGA images, 1024-square for snow and 2048-square for the other sets. Grayscale specular TGA fails UDK import; force true-color output. Specular is inverse roughness, scaled down by the material. This is a practical UE3 approximation, not a physically based roughness workflow. DirectX normal maps go to UDK; OpenGL normal maps go to Blender.

API responses retain download URLs and source hashes. Current prepared-image hashes are written to output/textures/manifest.json.

The cloudy sky texture, `textures/ghost_sky.png`, was created with the built-in image_gen tool. The exact prompt and import conversion are recorded in `sky-prompt.txt`. It is an environment texture, not a rendered substitute for the ship geometry.
