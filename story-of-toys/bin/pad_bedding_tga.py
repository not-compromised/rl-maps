"""Pad uncompressed TGA scanlines for UE3's four-pixel DXT block requirement."""
from pathlib import Path
import struct,hashlib,json,sys
source,target=map(Path,sys.argv[1:]);b=source.read_bytes();header=list(struct.unpack('<BBBHHBHHHHBB',b[:18]))
assert header[:3]==[0,0,2] and header[10]==24
w,h=header[8:10];new_w=(w+3)//4*4;new_h=(h+3)//4*4
assert h==new_h,'This reference only needs horizontal padding'
pixels=b[18:18+w*h*3];assert len(pixels)==w*h*3
rows=[pixels[y*w*3:(y+1)*w*3] for y in range(h)]
padded=[row+row[-3:]*(new_w-w) for row in rows]
assert all(a==c[:w*3] for a,c in zip(rows,padded))
header[8]=new_w;target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(struct.pack('<BBBHHBHHHHBB',*header)+b''.join(padded))
target.with_suffix('.json').write_text(json.dumps({'original_size':[w,h],'padded_size':[new_w,h],'unchanged_original_pixels':True,'added_columns':new_w-w,'source_sha256':hashlib.sha256(b).hexdigest(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))
