"""Seven-stage route through the oversized bedroom. Calibration is preserved in output/calibration-01."""
import math
PACKAGE = 'AndysRoomRings03'
WORLD_ACTOR = 'WorldInfo_7'  # Stable actor in the saved room package.
ROOM_KILL_Z = -100000  # The guarded floor trigger owns course resets and unlocks exploration.
TITLE = "Andy's Room: Flight Time"
SIZES = {'easy': 620.0, 'medium': 470.0, 'hard': 340.0}
STAGE_NAMES = ('TOY BOX', 'BED AND DESK', 'REMOTE CONTROL', 'HAT TRICK', 'BOOKSHELF', 'HIGH FLYER', 'HOME')
STAGE_COUNTS = (10, 14, 13, 7, 15, 24, 17)
STAGE_STARTS = tuple(1+sum(STAGE_COUNTS[:i]) for i in range(len(STAGE_COUNTS)))
HAT_CHECKPOINT = 3
STAGE_COLORS = (('Orange', (1.0, .14, .015)), ('Cyan', (.015, .65, 1.0)),
                ('Pink', (1.0, .025, .32)), ('Lime', (.28, 1.0, .015)),
                ('Violet', (.32, .025, 1.0)), ('Yellow', (1.0, .85, .015)),
                ('White', (.95, .95, .95)))

def stage_material(stage):
 return 'Stage' + str(stage) + STAGE_COLORS[stage-1][0]

DECKS = [(-5000, -4500, 2000), (-17500, -12865, 4165), (-3200, 14200, 7750), (1500, -1400, 16340), (18350, 13900, 10425), (18350, 13900, 20425), (-4000, -3000, 22700), (-20225, -12865, 17220)]
SPAWNS = [(x,y,z+150) for x,y,z in DECKS[:-1]]
TARGETS = [(x,y,z+180) for x,y,z in DECKS[1:]]
from flight_path import curve, GUIDES

GATE_SIZES = []
for stage, count in enumerate(STAGE_COUNTS):
 hard_every = 4 if stage < 3 else 2
 sizes = ['hard' if stage > 0 and i % hard_every == hard_every-1 else 'medium' for i in range(count)]
 sizes[-1] = 'easy'
 if stage == 0:sizes[0] = 'easy'
 GATE_SIZES.extend(sizes)

PATHS = []
CURVE_GATES = []
for stage, first in enumerate(STAGE_STARTS):
 stop = STAGE_STARTS[stage+1]-1 if stage+1<len(STAGE_STARTS) else len(GATE_SIZES)
 gates_on_curve, path = curve([SPAWNS[stage]]+GUIDES[stage]+[TARGETS[stage]], GATE_SIZES[first-1:stop], departure=4500 if stage==2 else 4000 if stage in (1,5) else 3500, arrival=4600 if stage==1 else 4800 if stage==3 else 3800)
 CURVE_GATES.extend(gates_on_curve)
 PATHS.append(path)
POINTS = [(*p, size) for p, normal, size in CURVE_GATES]

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
   normal=CURVE_GATES[i][1]
   result.append({'index':i+1,'stage':stage,'center':p[:3],'normal':normal,'size':p[3],'radius':SIZES[p[3]]})
 return result

GATES=gates()

def local(g,x,y,z):
 n,s,u=basis(g['normal'])
 return add(g['center'],add(mul(n,x),add(mul(s,y),mul(u,z))))
