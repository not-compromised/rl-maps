"""Deck-mounted camera controls; existing trigger footprints stay unchanged."""
import math

from course import add
from ue3 import Scene


LETTERS = {
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'N': ('10001', '11001', '11001', '10101', '10011', '10011', '10001'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
}


def camera_station(scene, name, center, side):
    """Two assets: colliding iron plate and noncolliding luminous inlay."""
    def point(u, v, z):
        return add(center, (side*u, side*v, z))

    outline = [(-145,-170),(145,-170),(170,-145),(170,145),
               (145,170),(-145,170),(-170,145),(-170,-145)]
    vertices = [point(u,v,z) for z in (0,24) for u,v in outline]
    faces = [tuple(reversed(range(8))), tuple(range(8,16))]
    faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    scene.mesh(name, vertices, faces, 'Iron')

    parts = Scene()
    color = 'Ghost' if side == 1 else 'Violet'
    def bar(label, u, v, width, height):
        parts.box(label, point(u,v,28), (width,height,4), color, False)

    for u in (-148,148):
        bar('Rail'+str(u),u,0,5,260)
    for v in (-148,148):
        bar('Edge'+str(v),0,v,260,5)
    word = 'ON' if side == 1 else 'OFF'
    cell = 11
    span = (len(word)*6-1)*cell
    for letter_index, letter in enumerate(word):
        for row, pixels in enumerate(LETTERS[letter]):
            for column, value in enumerate(pixels):
                if value == '1':
                    bar(f'Letter{letter_index}_{row}_{column}',
                        -span/2+(letter_index*6+column+.5)*cell,
                        -40-row*cell,8,8)
    # Camera silhouette, circular lens and removable-target motif.
    for label,u,v,w,h in [('BodyTop',0,103,126,5),('BodyBottom',0,19,126,5),
                          ('BodyLeft',-63,61,5,84),('BodyRight',63,61,5,84),
                          ('Prism',-25,114,42,12)]:
        bar(label,u,v,w,h)
    lens = [point(26*math.cos(i*math.tau/32),61+26*math.sin(i*math.tau/32),28)
            for i in range(33)]
    parts.tube('Lens',lens,3,color,6,False)
    if side == -1:
        parts.tube('Strike',[point(-46,15,31),point(46,108,31)],4,color,6,False)
    v,f=[],[]
    for mesh in parts.meshes:
        offset=len(v);v.extend(mesh['vertices'])
        f.extend(tuple(offset+i for i in face) for face in mesh['faces'])
    scene.mesh(name+'Inlay',v,f,color,False)
