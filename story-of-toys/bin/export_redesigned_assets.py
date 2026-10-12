"""Export only the changed room meshes, including shifted shelf companions."""
import bpy,sys,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[sys.argv.index('--')+1])
names=[o.name for o in bpy.data.objects if o.type=='MESH' and (o.get('export_material') or o.name in ('RoomCheckpointLowerShelf','RoomCheckpointUpperShelf'))]
sys.argv=['blender','--',str(out),'Room05_']+names
runpy.run_path(str(ROOT/'bin/export_room_t3d.py'),run_name='__main__')
