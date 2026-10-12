"""One route definition drives geometry, sensors, state and verification."""
import math

PACKAGE = 'WrecklightTrial01'
TITLE = 'Wrecklight Coast - First Voyage'
SIZES = {'easy': 620.0, 'medium': 470.0, 'hard': 340.0}
# A checkpoint deck is the next stage's start. The final deck is completion.
STAGE_NAMES = ('THE HOLD', 'THE CRAGS', 'NORTH RIDGE', 'BARGE COVE', 'THE BONES', 'WATCHTOWER')
STAGE_STARTS = (1, 11, 23, 31, 39, 47)
DECKS = [(-6200,0,900), (-3400,-5300,600), (-1250,2100,2450),
         (-5400,4000,1150), (-8000,500,700), (-1400,-3500,900),
         (-1250,2100,3900)]
SPAWNS = [(x,y,z+150) for x,y,z in DECKS[:-1]]
TARGETS = [(x,y,z+180) for x,y,z in DECKS[1:]]
POINTS = [
 (-4800,0,1740,'easy'),(-3900,60,1740,'easy'),(-2900,-80,1850,'medium'),
 (-2050,0,2100,'medium'),(-1200,0,3000,'easy'),(-700,-950,3450,'easy'),
 (-1600,-2000,3300,'easy'),(-2850,-2450,2700,'medium'),(-4000,-3000,1800,'easy'),
 (-4300,-4000,1350,'easy'),
 (-2400,-5900,1350,'medium'),(-1400,-6000,1600,'medium'),(-400,-5400,1950,'medium'),
 (100,-4300,2350,'medium'),(600,-3350,2700,'medium'),(1550,-2550,3000,'medium'),
 (2600,-1700,3450,'medium'),(3600,-650,4200,'medium'),(3100,800,4700,'medium'),
 (1750,1550,4250,'medium'),(500,1200,3500,'medium'),(-500,1000,3000,'medium'),
 # Traverse the north shoulder, then descend toward the western wreck cove.
 (-1400,2950,3250,'medium'),(-700,3850,3850,'medium'),
 (-1500,4650,4000,'medium'),(-2550,4900,3700,'medium'),
 (-3500,4550,3200,'hard'),(-4100,3850,2500,'medium'),
 (-4900,3150,2100,'medium'),(-5700,3250,1800,'hard'),
 # Low flight around the barge, with a tighter turn around its broken stern.
 (-6600,4400,1450,'medium'),(-6900,3100,1400,'medium'),
 (-7400,2400,1200,'hard'),(-6950,1750,1150,'medium'),
 (-6100,1750,1150,'medium'),(-5550,1200,1300,'hard'),
 (-6300,650,1250,'medium'),(-7250,50,1200,'hard'),
 # Approach the main ship from seaward and thread the exposed ribs below it.
 (-7800,-450,1350,'hard'),(-7150,-1250,1500,'hard'),
 (-6400,-1950,1450,'medium'),(-5550,-2400,1350,'hard'),
 (-4700,-2100,1400,'hard'),(-3900,-2100,1250,'medium'),
 (-2850,-2100,1200,'hard'),(-2100,-2800,1350,'hard'),
 # Climb around the stern and return above the northern face of the lookout.
 (-2300,-4800,1800,'hard'),(-3600,-4700,2350,'hard'),
 (-4600,-3750,3000,'hard'),(-5550,-2250,3650,'hard'),
 (-5550,-300,4350,'hard'),(-4750,1350,4650,'medium'),
 (-3600,2350,4650,'hard'),(-2450,2950,4400,'hard')]

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
