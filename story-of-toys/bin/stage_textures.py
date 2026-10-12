"""Write the seven flat-color diffuse textures used by the lit course rings."""
import json, struct, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course import STAGE_COLORS, stage_material

def write(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 assets=[]
 for stage,(_,linear) in enumerate(STAGE_COLORS,1):
  rgb=[round(255*(12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055)) for c in linear]
  path=output/f'T_{stage_material(stage)}.tga'
  header=struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,16,16,24,32)
  path.write_bytes(header+bytes(reversed(rgb))*256)
  assets.append({'file':path.name,'srgb':rgb,'linear':linear,'SRGB':True})
 (output/'textures.json').write_text(json.dumps(assets,indent=2))
 return assets
if __name__=='__main__':write(sys.argv[1])
