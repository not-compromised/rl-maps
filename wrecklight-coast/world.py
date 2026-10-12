"""Connected haunted harbor. Original geometry; no Ice Rings assets."""
import lib_path  # noqa: F401  (puts the shared ../lib on sys.path)
import math,random
from course import *
from ue3 import Scene
R=random.Random(81024)

def merge(scene,prefix):
 groups={};keep=[]
 for m in scene.meshes:
  if m['name'].startswith(prefix):groups.setdefault((m['material'],m['collision'],m['smooth']),[]).append(m)
  else:keep.append(m)
 scene.meshes=keep
 for gi,((mat,coll,smooth),items) in enumerate(groups.items()):
  v=[];f=[];part=0
  for m in items:
   if sum(len(x)-2 for x in f)+sum(len(x)-2 for x in m['faces'])>45000:
    scene.mesh(f'{prefix}Batch{gi}_{part}',v,f,mat,coll,smooth);v=[];f=[];part+=1
   base=len(v);v.extend(m['vertices']);f.extend(tuple(base+i for i in face) for face in m['faces'])
  if f:scene.mesh(f'{prefix}Batch{gi}_{part}',v,f,mat,coll,smooth)

def beam(s,n,a,b,r,mat='WoodDark',segments=8):s.tube(n,[a,b],r,mat,segments)
def rock(s,n,p,size,mat='Rock',seed=0,rows=7,cols=13):
 rng=random.Random(seed);v=[];f=[]
 for i in range(rows+1):
  a=-math.pi/2+math.pi*i/rows
  for j in range(cols):
   b=math.tau*j/cols;t=1+rng.uniform(-.12,.12)
   v.append((p[0]+size[0]*math.cos(a)*math.cos(b)*t,p[1]+size[1]*math.cos(a)*math.sin(b)*t,p[2]+size[2]*math.sin(a)*t))
 for i in range(rows):
  for j in range(cols):f.append((i*cols+j,i*cols+(j+1)%cols,(i+1)*cols+(j+1)%cols,(i+1)*cols+j))
 s.mesh(n,v,f,mat,True,False)

def lantern(s,n,p):
 s.box(n+'Cage',add(p,(0,0,25)),(54,54,100),'Iron')
 s.box(n+'Glass',add(p,(0,0,30)),(58,58,58),'Gold',False)
 s.box(n+'Roof',add(p,(0,0,95)),(90,90,18),'Iron')

def ship(s):
 # Lofted hull: separate courses of planking, with visible thickness at the breach.
 stations=[(-4930,880),(-4500,1040),(-3650,1140),(-2750,1100),(-1850,900),(-950,620),(-250,45)]
 for side in [-1,1]:
  for row in range(15):
   z0=430+row*137;z1=z0+130;v=[]
   for x,w in stations:
    for z in (z0,z1):
     a=(z-430)/2200;v.append((x,side*w*(.18+.82*math.sin(a*math.pi/2)),z))
   f=[]
   for k in range(len(stations)-1):
    q=(2*k,2*k+2,2*k+3,2*k+1);f.append(q if side<0 else q[::-1])
   count=len(v);v+= [(x,y-side*45,z) for x,y,z in v]
   outside=list(f);f += [tuple(i+count for i in reversed(face)) for face in outside]
   for k in range(len(stations)-1):
    a=2*k;b=2*k+2
    f.extend([(a,a+count,b+count,b),(a+1,b+1,b+1+count,a+1+count)])
   s.mesh(f'ArtHull{side}_{row}',v,f,'WoodLight' if row%4==0 else 'Wood',True)
  # Inner side skin gives solid appearance from hold; ribs stand proud of it.
  for k,(x,w) in enumerate(stations[:-1]):
   pts=[(x,side*(w*(.18+.82*math.sin((z-430)/2200*math.pi/2))-38),z) for z in [650,950,1300,1700,2150,2600]]
   s.tube(f'ArtRib{side}_{k}',pts,48,'WoodDark',8)
  s.tube(f'ArtGunwale{side}',[(x,side*w,2630) for x,w in stations],48,'WoodDark',10)
  s.tube(f'ArtRail{side}',[(x,side*w,2950) for x,w in stations],28,'WoodLight',8)
  for k in range(22):
   x=-4800+k*202;w=next(w0+(w1-w0)*(x-x0)/(x1-x0) for (x0,w0),(x1,w1) in zip(stations,stations[1:]) if x0<=x<=x1)
   beam(s,f'ArtRailPost{side}_{k}',(x,side*w,2610),(x,side*w,2940),23)
 # Solid hold and upper deck. Large framed fore hatch is the intended flight exit.
 s.box('ArtHoldFloor',(-2800,0,950),(4250,1750,100),'WoodDark')
 for j in range(24):
  y=-1100+j*94
  for k in range(21):
   x=-4830+k*211
   w=next((w0+(w1-w0)*(x-x0)/(x1-x0) for (x0,w0),(x1,w1) in zip(stations,stations[1:]) if x0<=x<=x1),0)
   if abs(y)>w-35:continue
   if -2750<x<-560 and abs(y)<780:continue
   s.box(f'ArtDeckPlank{j}_{k}',(x,y,2540),(205,88,65),'WoodLight' if (j+k)%6==0 else 'Wood')
 for side in [-1,1]:beam(s,f'ArtHatchSide{side}',(-2750,side*790,2570),(-560,side*790,2570),50,'WoodDark')
 for x in [-2750,-560]:beam(s,f'ArtHatchEnd{x}',(x,-790,2570),(x,790,2570),50,'WoodDark')
 # Stern wall around the first ring. Irregular radial boundary reveals a cannon impact.
 gate=GATES[0];v=[];faces=[];n=48
 for j in range(n):
  a=math.tau*j/n;inner=gate['radius']+104+R.uniform(0,65)
  # Rectangular outer panel in the ring plane, complete above/beside/below its hole.
  outer=min(970/max(abs(math.cos(a)),.001),1060/max(abs(math.sin(a)),.001))
  for x,r in [(-60,inner),(-60,outer),(75,inner),(75,outer)]:v.append(local(gate,x,r*math.cos(a),r*math.sin(a)))
 for j in range(n):
  a=j*4;b=((j+1)%n)*4
  faces.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b)])
 s.mesh('ArtCannonBreach',v,faces,'Wood',True)
 for j in range(28):
  a=math.tau*j/28;r=gate['radius']+140
  p=local(gate,-95,r*math.cos(a),r*math.sin(a));q=local(gate,-180-R.uniform(0,130),(r+R.uniform(60,160))*math.cos(a),(r+R.uniform(60,160))*math.sin(a))
  beam(s,f'ArtSplinter{j}',p,q,18,'WoodLight',5)
 # Raised stern deck and stairs retain a complete vessel silhouette.
 s.box('ArtQuarterDeck',(-4420,0,3240),(1120,1880,100),'Wood')
 for side in [-1,1]:
  for i in range(9):s.box(f'ArtStair{side}_{i}',(-3760+i*65,side*935,3150-i*70),(100,250,70),'WoodLight')
  beam(s,f'ArtQuarterRail{side}',(-4950,side*930,3580),(-3900,side*930,3580),30)
  for i in range(6):beam(s,f'ArtQuarterPost{side}_{i}',(-4900+i*190,side*930,3250),(-4900+i*190,side*930,3580),22)
 # Masts on the solid deck, yards, curved ragged canvas, rope stays.
 for mi,(x,h,width) in enumerate([(-4000,6500,1350),(-2950,7500,1700)]):
  beam(s,f'ArtMast{mi}',(x,0,2550),(x+90,0,h),72,'WoodDark',14)
  for yi,z in enumerate([h-450,h-1800]):
   beam(s,f'ArtYard{mi}_{yi}',(x,-width,z),(x,width,z+110),38,'WoodDark')
   v=[];f=[];nx=16;ny=8
   for row in range(ny+1):
    for col in range(nx+1):
     t=col/nx;u=row/ny
     y=(t*2-1)*width*(1-.18*u);zz=z-u*1250+110*t
     if row==ny:zz+=R.uniform(-150,160)
     v.append((x+260*math.sin(math.pi*t)*math.sin(math.pi*u),y,zz))
   for row in range(ny):
    for col in range(nx):
     if row>4 and (col+mi*3+yi)%9==0:continue
     a=row*(nx+1)+col;f.append((a,a+1,a+nx+2,a+nx+1))
   # Shipped material is single-sided. Give the canvas physical thickness so
   # the reverse view and torn edges render without relying on a new shader.
   count=len(v);front=list(f);v.extend((px-4,py,pz) for px,py,pz in v[:count])
   f.extend(tuple(index+count for index in reversed(face)) for face in front)
   edges={}
   for face in front:
    for a,b in zip(face,face[1:]+face[:1]):
     key=tuple(sorted((a,b)))
     if key in edges:del edges[key]
     else:edges[key]=(a,b)
   f.extend((a,a+count,b+count,b) for a,b in edges.values())
   s.mesh(f'ArtCanvas{mi}_{yi}',v,f,'Sail',True,True)
  for side in [-1,1]:
   for offset in [-300,0,300]:beam(s,f'ArtStay{mi}_{side}_{offset}',(x+offset,side*940,2670),(x+65,0,h-900),12,'Rope',6)
 beam(s,'ArtBowsprit',(-700,0,2680),(650,0,3300),52,'WoodDark',12)
 for j,p in enumerate([(-4850,-850,2670),(-4850,850,2670),(-2900,-1000,2670),(-2900,1000,2670),(-500,0,2800)]):lantern(s,f'ArtShipLamp{j}',p)
 # Helm wheel on raised deck.
 pts=[(-4460,180*math.cos(j*math.tau/24),3530+180*math.sin(j*math.tau/24)) for j in range(25)]
 s.tube('ArtHelmWheel',pts,22,'WoodLight',8)
 beam(s,'ArtHelmStand',(-4460,0,3290),(-4460,0,3540),32)
 for j in range(8):beam(s,f'ArtHelmSpoke{j}',(-4460,0,3530),(-4460,210*math.cos(j*math.tau/8),3530+210*math.sin(j*math.tau/8)),15,'WoodLight',6)
 for j in range(16):
  x=R.uniform(-4600,-3100);y=R.choice([-1,1])*R.uniform(680,790)
  s.box(f'ArtHoldCargo{j}',(x,y,1070),(R.uniform(90,180),120,180),'WoodDark')
 merge(s,'Art')

# Terrain stays outside the flight corridor. Detail is tested again after import.
def distance_segment(p,a,b):
 d=sub(b,a);t=max(0,min(1,dot(sub(p,a),d)/max(dot(d,d),1)))
 return math.sqrt(dot(sub(p,add(a,tuple(t*x for x in d))),sub(p,add(a,tuple(t*x for x in d)))))
ROUTE_SEGMENTS=route_segments()
def clear(p,padding=800):
 return min(distance_segment(p,a,b) for a,b in ROUTE_SEGMENTS)>padding

def terrain(s):
 # Connected horseshoe coast. Peaks use several frequencies plus sharp ridges.
 def height(x,y):
  lumps=[(5200,-2400,3000,3400,4300),(2800,2500,3700,2600,5200),(-1800,3900,3200,2200,2800),(-5700,-3900,1750,2400,1300)]
  h=-350
  for cx,cy,sx,sy,z in lumps:h=max(h,z*math.exp(-1.8*((x-cx)**2/sx**2+(y-cy)**2/sy**2))-350)
  h+=100*math.sin(x/230)*math.cos(y/310)+90*math.sin(x/95+y/150)
  return h
 step=230;nx=82;ny=66;v=[]
 for j in range(ny):
  for i in range(nx):
   x=-8500+i*step;y=-7000+j*step;z=height(x,y)
   # Carve broad valleys along route. The tunnel is a separate enclosed bore.
   while z>30 and not clear((x,y,z),1050):z-=110
   v.append((x,y,z))
 bymat={'Rock':[],'RockDark':[],'Snow':[]}
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i
   for face in [(a,a+1,a+nx+1),(a,a+nx+1,a+nx)]:
    pts=[v[k] for k in face];z=sum(p[2] for p in pts)/3;normal=unit(cross(sub(pts[1],pts[0]),sub(pts[2],pts[0])))
    mat='Snow' if z>3500+140*math.sin(pts[0][0]/440) and normal[2]>.46 else ('RockDark' if normal[2]<.48 else 'Rock')
    bymat[mat].append(face)
 for mat,faces in bymat.items():s.mesh('Coast'+mat,v,faces,mat,True,True)
 # Low, stacked outcrops follow the coast's slope instead of scattered spheres.
 strata=random.Random(9147)
 for i in range(95):
  x=strata.uniform(-7500,8500);y=strata.uniform(-6200,6500);z=height(x,y)
  if z<80 or z>3200 or not clear((x,y,z),1650):continue
  dx=height(x+100,y)-height(x-100,y);dy=height(x,y+100)-height(x,y-100)
  if math.hypot(dx,dy)<95:continue
  angle=math.atan2(dy,dx)+math.pi/2
  for layer in range(3):
   center=(x+layer*35,y-layer*20,z-110+layer*120)
   rock(s,f'TerrainDetailStrata{i}_{layer}',center,
        (strata.uniform(360,620),230-layer*25,105),
        'RockLight' if layer==2 else 'RockDark',i*3+layer,rows=4,cols=9)
   mesh=s.meshes[-1]
   mesh['vertices']=[(center[0]+(px-center[0])*math.cos(angle)-(py-center[1])*math.sin(angle),
                      center[1]+(px-center[0])*math.sin(angle)+(py-center[1])*math.cos(angle),pz)
                     for px,py,pz in mesh['vertices']]
 for i in range(220):
  x=R.uniform(-7800,9000);y=R.uniform(-6500,7000);z=height(x,y)
  size=R.uniform(65,340)
  if z<0 or not clear((x,y,z),size+1000):continue
  rock(s,f'TerrainDetail{i}',(x,y,z),(size,size*.72,size*1.4),'Snow' if z>3700 else 'RockDark',i)
 merge(s,'TerrainDetail')
 # Water is a broad tessellated surface with wave crests, no collision.
 v=[];f=[];n=65
 for j in range(n):
  for i in range(n):
   x=-17000+i*530;y=-16000+j*530
   v.append((x,y,18*math.sin(x/180+y/420)+9*math.cos(y/90)))
 for j in range(n-1):
  for i in range(n-1):a=j*n+i;f.append((a,a+1,a+n+1,a+n))
 s.mesh('HarborWater',v,f,'Water',False,True)
 # Explicit curved tunnel, with continuous inner walls and thick rocky mouths.
 gates=GATES[13:17];centers=[local(gates[0],-650,0,0)]+[g['center'] for g in gates]+[local(gates[-1],650,0,0)]
 v=[];inner=[];outer=[];ends=[];segments=64
 for i,p in enumerate(centers):
  n=unit(sub(centers[min(i+1,len(centers)-1)],centers[max(i-1,0)]));side=unit(cross((0,0,1),n));up=cross(n,side)
  for layer in [0,1]:
   for j in range(segments):
    a=j*math.tau/segments
    # Broad irregular lobes and smaller fractures, rather than a repeated sawtooth.
    r=(1060+55*math.sin(3*a+i*.6)+24*math.sin(7*a-i*.35)) if layer==0 else (1900+130*math.sin(3*a+i*.4)+60*math.sin(5*a-i*.3))
    along=0
    if i in (0,len(centers)-1):
     along=(1 if i==0 else -1)*(110*math.sin(2*a+.4)+55*math.sin(5*a))
    v.append(add(add(p,mul(n,along)),add(mul(side,r*math.cos(a)),mul(up,r*math.sin(a)))))
 stride=segments*2
 for i in range(len(centers)-1):
  for j in range(segments):
   a=i*stride+j;b=i*stride+(j+1)%segments
   inner.append((a,a+stride,b+stride,b));outer.append((a+segments,b+segments,b+stride+segments,a+stride+segments))
 for i in [0,len(centers)-1]:
  p=centers[i];n=unit(sub(centers[min(i+1,len(centers)-1)],centers[max(i-1,0)]))
  # Recessed rock courses turn the flat annulus into a thick, weathered mouth.
  previous=[i*stride+j for j in range(segments)]
  for layer in range(1,4):
   t=layer/4;current=[]
   for j in range(segments):
    a=j*math.tau/segments;near=v[i*stride+j];far=v[i*stride+segments+j]
    point=add(mul(near,1-t),mul(far,t))
    relief=(160*math.sin(math.pi*t)+35*math.sin(5*a+layer*.8))*(1 if i==0 else -1)
    current.append(len(v));v.append(add(point,mul(n,relief)))
   for j in range(segments):
    k=(j+1)%segments;q=(previous[j],previous[k],current[k],current[j]);ends.append(q if i==0 else q[::-1])
   previous=current
  for j in range(segments):
   k=(j+1)%segments;q=(previous[j],previous[k],i*stride+segments+k,i*stride+segments+j);ends.append(q if i==0 else q[::-1])
 s.mesh('MountainTunnelInner',v,inner,'RockDark',True,True)
 s.mesh('MountainTunnelOuter',v,outer+ends,'Rock',True,False)
 for i,p in enumerate(centers[1:-1]):
  for side in [-1,1]:lantern(s,f'TunnelLamp{i}_{side}',add(p,(side*740,0,-600)))
 merge(s,'TunnelLamp')

def harbor(s):
 # Different wreck silhouettes: an exposed rib keel and a low broken barge.
 for wi,(cx,cy,z) in enumerate([(-4200,-2100,400),(-6500,1800,120)]):
  if wi==0:
   for i in range(11):
    x=cx-850+i*170;w=850*math.sin(math.pi*(i+1)/12)
    # Broken end ribs leave entry and exit clear; the middle ribs retain height.
    height=600 if i in (0,10) else 1000
    pts=[(x,-w,z+height),(x,-w*.9,z+200),(x,0,z),
         (x,w*.9,z+200),(x,w,z+height)]
    s.tube(f'WreckRib{wi}_{i}',pts,26,'WoodDark',8)
  else:
   # Broad, shallow cargo barge with a broken stern and a surviving foredeck.
   for row in range(5):
    for side in [-1,1]:
     for part in range(8):
      if part>5 and (part+row)%3==0:continue
      s.box(f'WreckBargeSide{side}_{row}_{part}',
            (cx-820+part*230,cy+side*(450+row*22),z+row*65),
            (220,46,58),'Wood' if row%2 else 'WoodLight')
   for plank in range(10):
    length=1050+(plank%3)*160
    s.box(f'WreckBargeDeck{plank}',(cx+250,cy-460+plank*100,z+320),
          (length,92,48),'Wood')
   for side in [-1,1]:
    beam(s,f'WreckBargeRail{side}',(cx-220,cy+side*535,z+500),
         (cx+980,cy+side*535,z+500),22)
   for cargo in range(4):
    s.box(f'WreckBargeCargo{cargo}',(cx+120+cargo*180,cy+(-1)**cargo*160,z+425),
          (160,150,180),'WoodDark')
  beam(s,f'WreckKeel{wi}',(cx-1000,cy,z),(cx+1000,cy,z),60)
  # Move ribs to their local cove, then add broken mast and debris.
  for m in s.meshes:
   if m['name'].startswith(f'WreckRib{wi}_'):m['vertices']=[(x,y+cy,zz) for x,y,zz in m['vertices']]
  if wi==0:beam(s,f'WreckMast{wi}',(cx,cy,z+100),(cx+1100,cy+500,z+380),45)
  for i in range(8):rock(s,f'WreckRock{wi}_{i}',(cx+R.uniform(-1200,1200),cy+R.uniform(-550,550),z-180),(300,250,330),'RockDark',wi*20+i)
 # Tall lookout, seen at the end after circling the harbor.
 cx,cy,cz=DECKS[-1]
 for side in [-1,1]:
  for end in [-1,1]:
   a=(cx+side*980,cy+end*980,220);b=(cx+side*900,cy+end*900,cz)
   # The damaged southeast leg ends below the approach to the lower landing.
   if side==1 and end==-1:b=(b[0],b[1],1600)
   beam(s,f'LookoutPost{side}_{end}',a,b,90,'WoodDark')
   beam(s,f'LookoutBrace{side}_{end}',a,(cx+side*900,cy-end*900,cz-250),45,'Wood')
 for i in range(math.ceil((cz-500)/180)):beam(s,f'LookoutLadder{i}',(cx-1000,cy-220,500+i*180),(cx-1000,cy+220,500+i*180),28)
 for j,deck in enumerate(DECKS):
  for side in (-1,1):lantern(s,f'HarborLantern{j}_{side}',add(deck,(side*900,900,80)))
 merge(s,'Wreck');merge(s,'Lookout');merge(s,'HarborLantern')

def build_world(scene):
 ship(scene);terrain(scene);harbor(scene)
 from geology import tunnel_ridge,tunnel_fractures
 tunnel_ridge(scene)
 tunnel_fractures(scene)
