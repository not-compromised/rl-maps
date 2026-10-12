"""Build the current character while retaining the room's preview scene."""
import bpy, sys
from pathlib import Path

out = Path(sys.argv[sys.argv.index('--')+1])
if (out / 'AndyParts.blend').exists() or (out / 'AndyDetail.blend').exists():
    raise RuntimeError('Choose a new character output directory')
root = Path(__file__).resolve().parents[1]
source = root / 'bin/build_room_blender.py'
code = source.read_text()
namespace = {'__file__': str(source), '__name__': '__main__'}
for section in [code[:code.index('# Small plank pieces')], code[code.index('# Frozen boy:'):code.index('# Buzz stands on the floor')]]:
    exec(compile(section, str(source), 'exec'), namespace)
out = namespace['OUT']
if (out / 'AndyParts.blend').exists():
    raise RuntimeError('Choose a new character output directory')
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'AndyParts.blend'))
exec(compile(code[code.index('# Join by furniture/character'):code.index('# Preview scene stays')], str(source), 'exec'), namespace)
partial = out / 'AndyOnly.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(partial))
bpy.ops.wm.open_mainfile(filepath=str(root / 'output/room-art-11/AndyDetail.blend'))
names = ['RoomAndy', 'RoomAndyHead', 'RoomAndyHat']
for name in names:
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
with bpy.data.libraries.load(str(partial), link=False) as (available, loaded):
    loaded.objects = names
for obj in loaded.objects:
    bpy.context.scene.collection.objects.link(obj)
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'AndyDetail.blend'))
print('Finished revised Andy', flush=True)
