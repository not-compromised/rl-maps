"""Closed rope strands follow the hoop; a separate torus owns collision."""
import math
from course import local,sub,cross,unit,add

TURNS=24
# Twelve samples per twist keep the strand-center chord error below one unit.
STEPS=TURNS*12
SIDES=8

def strand_point(theta,phase,major):
    twist=TURNS*theta+phase
    radial=major+25*math.cos(twist)
    return (25*math.sin(twist),radial*math.cos(theta),radial*math.sin(theta))

def braided_ring(scene,gate):
    major=gate['radius']+44
    vertices=[];faces=[];uvs=[]
    for strand in range(3):
        phase=math.tau*strand/3
        base=len(vertices)
        for j in range(STEPS+1):
            theta=math.tau*j/STEPS
            p=strand_point(theta,phase,major)
            tangent=unit(sub(strand_point(theta+.00001,phase,major),strand_point(theta-.00001,phase,major)))
            radial=(0,math.cos(theta),math.sin(theta))
            side=unit(cross(tangent,radial));up=cross(side,tangent)
            for k in range(SIDES+1):
                angle=math.tau*k/SIDES
                q=add(p,tuple(19*(math.cos(angle)*side[a]+math.sin(angle)*up[a]) for a in range(3)))
                vertices.append(local(gate,*q))
                uvs.append((j/STEPS*TURNS,k/SIDES))
        for j in range(STEPS):
            for k in range(SIDES):
                a=base+j*(SIDES+1)+k;b=a+SIDES+1
                faces.append((a,b,b+1,a+1))
    scene.mesh(f'Gate{gate["index"]:02}Braid',vertices,faces,'Rope',False,True)
    scene.meshes[-1]['uvs']=uvs
