# Asset inputs

The course generator builds from Python source without downloaded textures.
The room and probe modeling scripts require Blender. The saved, lit game
packages are separate release artifacts; source checks do not reconstruct
those packages.

The older coast-template material recipe is listed in [TEXTURE-CREDITS.md](TEXTURE-CREDITS.md).
Acquire any needed images from those Poly Haven source pages. Source textures,
download metadata and the private workshop's texture conversion helpers are
not included in this folder. Convert editor inputs to RGB TGA externally,
using DirectX normals for UDK and OpenGL normals for Blender.

The generated coast sky is available in the repository's Wrecklight Coast
assets folder with its prompt. It is not a prerequisite for the course.
Story of Toys includes its generated face texture beside its provenance note.
