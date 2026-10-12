"""Arc-length sampled cubic flight paths; normals follow their analytical tangents."""
import math,bisect

def curve(anchors, sizes, departure=3300, arrival=3500):
    lengths=[0.]
    for a,b in zip(anchors,anchors[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    slopes=[]
    for i,p in enumerate(anchors):
        lo=max(0,i-1);hi=min(len(anchors)-1,i+1)
        slopes.append(tuple((anchors[hi][k]-anchors[lo][k])/(lengths[hi]-lengths[lo]) for k in range(3)))
    def at(segment,t):
        a,b=anchors[segment:segment+2];h=lengths[segment+1]-lengths[segment];m,n=slopes[segment:segment+2]
        p=tuple((2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*h*m[k]+(-2*t**3+3*t*t)*b[k]+(t**3-t*t)*h*n[k] for k in range(3))
        d=tuple((6*t*t-6*t)*a[k]+(3*t*t-4*t+1)*h*m[k]+(-6*t*t+6*t)*b[k]+(3*t*t-2*t)*h*n[k] for k in range(3))
        return p,tuple(v/math.hypot(*d) for v in d)
    samples=[(0,0,0.,anchors[0])];distance=0
    for j in range(len(anchors)-1):
        for n in range(1,201):
            p,_=at(j,n/200);distance+=math.dist(p,samples[-1][3]);samples.append((distance,j,n/200,p))
    arc=[s[0] for s in samples]
    gates=[]
    for i,size in enumerate(sizes):
        s=departure+(distance-departure-arrival)*i/(len(sizes)-1)
        hi=bisect.bisect_left(arc,s);a,b=samples[hi-1:hi+1];f=(s-a[0])/(b[0]-a[0]);t=b[2]-(1-f)/200
        p,d=at(b[1],t);gates.append((p,d,size))
    return gates, [s[3] for s in samples]

GUIDES=[
 [(-10000,-2200,4400),(-15300,-2700,6100),(-18400,-6200,6700)],
 [(-10000,-16700,10000),(-5000,-15000,11500),(-5300,-9500,11700),(-11000,-3000,11800),(-12000,6000,12200),(-9600,12400,12200),(-6700,14300,11300)],
 [(1700,14000,10800),(3300,9900,12800),(-1100,6000,14500),(-5400,1500,17000),(-5000,-3100,18000),(-1900,-3800,17700)],
 [(6100,-1000,16900),(10500,4700,15700),(13200,10100,12800)],
 [(22100,10700,12000),(21100,5700,15300),(16700,5100,19500),(12200,11000,21900),(12800,15700,22900),(15400,16600,22200)],
 [(21100,9500,24000),(18200,5000,25300),(16000,1500,26000),(14600,-1800,26500),(11700,-3800,27000),(8900,-1600,27400),(9400,2300,27600),(9000,6500,27500),(-1500,11000,27800),(-10500,8000,26500),(-13500,500,25200),(-10300,-4800,24300),(-6300,-4700,23500)],
 [(0,-6000,24100),(300,-12000,23600),(-4300,-15700,22300),(-10500,-14100,20700),(-13300,-8200,19400),(-16600,-7900,18300)]
]
