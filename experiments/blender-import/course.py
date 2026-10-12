"""Two-stage calibration route; expand only after engine playtesting."""
import math
PACKAGE = 'BlenderImportProbe01'
TITLE = 'Blender import probe'
SIZES = {'easy': 620.0, 'medium': 470.0, 'hard': 340.0}
STAGE_NAMES = ('LAUNCH', 'CONTROL')
STAGE_STARTS = (1, 4)
DECKS = [(0,0,0), (4200,600,0), (4200,4800,0)]
SPAWNS = [(x,y,z+150) for x,y,z in DECKS[:-1]]
TARGETS = [(x,y,z+180) for x,y,z in DECKS[1:]]
POINTS = [(1000,0,1000,'easy'), (2100,180,1150,'easy'), (3200,600,1000,'medium'),
          (4700,1800,1000,'medium'), (4900,2900,1200,'medium'), (4500,3900,1000,'hard')]

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
 length=math.sqrt(dot(a,a))
 if length<1e-9: raise ValueError('Zero direction')
 return mul(a,1/length)
def basis(normal):
 n=unit(normal); side=unit(cross((0,0,1),n)); up=unit(cross(n,side))
 return n,side,up

def stage_gates(stage):
 first=STAGE_STARTS[stage-1]-1
 stop=STAGE_STARTS[stage]-1 if stage<len(STAGE_STARTS) else len(POINTS)
 return GATES[first:stop]

def route_segments():
 result=[]
 for stage,start in enumerate(SPAWNS,1):
  points=[start]+[g['center'] for g in stage_gates(stage)]+[TARGETS[stage-1]]
  result.extend(zip(points,points[1:]))
 return result

def gates():
 result=[]
 for stage,first in enumerate(STAGE_STARTS,1):
  stop=STAGE_STARTS[stage]-1 if stage<len(STAGE_STARTS) else len(POINTS)
  for i in range(first-1,stop):
   p=POINTS[i]
   before=SPAWNS[stage-1] if i==first-1 else POINTS[i-1][:3]
   after=TARGETS[stage-1] if i==stop-1 else POINTS[i+1][:3]
   normal=unit(add(unit(sub(p[:3],before)),unit(sub(after,p[:3]))))
   result.append({'index':i+1,'stage':stage,'center':p[:3],'normal':normal,'size':p[3],'radius':SIZES[p[3]]})
 return result

GATES=gates()

def local(g,x,y,z):
 n,s,u=basis(g['normal'])
 return add(g['center'],add(mul(n,x),add(mul(s,y),mul(u,z))))
