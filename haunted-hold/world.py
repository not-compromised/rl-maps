"""Compact ship hold. Structural detail stays outside the six-gate flight lane."""
import math
from course import add


def build_world(scene):
    # A low bilge catches light below the failure plane; landing decks stay distinct.
    scene.box('HoldBilge',(2150,1100,-730),(7700,6500,100),'Water',False)
    for row in range(19):
        y=-1940+row*330
        scene.box(f'FloorPlank{row:02}',(2150,y,-650),(7700,316,90),'Wood' if row%3 else 'WoodDark')
    # Cross-section bends outward above the bilge and inward toward roof knees.
    section=[(-2180,-650),(-2350,200),(-2260,1800),(-1880,3200),(-1100,3850),
             (3350,3850),(4230,3200),(4550,1800),(4600,200),(4350,-650)]
    for bay in range(12):
        x=-1600+bay*700
        points=[(x,y,z) for y,z in section]
        scene.tube(f'HullRib{bay:02}',points,95,'WoodDark',8)
        # Long roof beams and transverse knees read as ship construction.
        scene.tube(f'RoofTie{bay:02}',[(x,-1900,3280),(x,1100,3470),(x,4200,3280)],65,'Wood',8)
        for side in (-1,1):
            y=-2210 if side<0 else 4490
            scene.box(f'RibBand{bay:02}_{side}',(x,y,1550),(210,110,140),'Iron')
    # Individual side planks follow the curved hull profile; dark seams stay visible.
    for side in ('Port','Starboard'):
        for row in range(14):
            z=-520+row*260
            t=(z+520)/3380
            y=(-2250+380*t*t) if side=='Port' else (4490-260*t*t)
            scene.box(f'{side}Plank{row:02}',(2150,y,z),(7800,76,244),'Wood' if row%4 else 'WoodLight')
    for end,x in [('Stern',-1780),('Bow',6100)]:
        for row in range(15):
            scene.box(f'{end}Plank{row:02}',(x,1120,-500+row*265),(120,6600,245),'WoodDark' if row%4==0 else 'Wood')
        # Massive inner braces leave the central approach clear.
        for y in (-1800,4000):scene.box(f'{end}Post{y}',(x-80,y,1500),(180,210,4150),'WoodDark')
    for beam,y in enumerate((-1900,-1100,3300,4220)):
        scene.box(f'RoofLongitudinal{beam}',(2150,y,3620),(7900,180,180),'WoodDark')
    # Open central hatch above the route. No ceiling crosses a ring aperture.
    for side,y in [('Port',-1250),('Starboard',3570)]:
        for row in range(5):scene.box(f'UpperDeck{side}{row}',(2150,y+row*155,3900),(7900,145,100),'Wood')
    for i,x in enumerate((1700,3650)):
        scene.tube(f'Mast{i}',[(x,900,-620),(x,900,4100)],135,'Wood',14)
        for band,z in enumerate((-200,450,2500,3100)):
            scene.tube(f'MastBand{i}_{band}',[(x,900,z),(x,900,z+110)],145,'Iron',14)
        scene.tube(f'MastBrace{i}A',[(x-480,900,-580),(x,900,400)],75,'WoodDark',8)
        scene.tube(f'MastBrace{i}B',[(x+480,900,-580),(x,900,400)],75,'WoodDark',8)
    # Cargo is fixed below the flying height or against the hull.
    positions=[(-950,-1570,-400),(500,-1650,-350),(1950,-1670,-360),(3450,-1630,-350),
               (5050,-1540,-320),(5500,3380,-350),(3600,4070,-350),(2150,4080,-350)]
    for i,center in enumerate(positions):
        crate(scene,f'Crate{i:02}',center, (440,420,470) if i%2 else (540,420,560))
    for i,x in enumerate((-900,400,1700,3000,4300,5600)):
        for side,y in [('Port',-1960),('Starboard',4190)]:
            lantern(scene,f'Lantern{i}{side}',(x,y,2550))
    # Rope cargo slings high enough to preserve flight clearance.
    for i,x in enumerate((600,2600,4900)):
        scene.tube(f'CargoSling{i}',[(x,-1700,3500),(x,-1400,2930),(x,-900,3500)],18,'Rope',8,False)


def crate(scene,name,p,size):
    scene.box(name+'Body',p,size,'WoodDark')
    for side in (-1,1):
        scene.box(name+f'Band{side}',add(p,(side*size[0]*.33,0,0)),(44,size[1]+12,size[2]+12),'WoodLight')
        scene.box(name+f'Iron{side}',add(p,(0,0,side*size[2]*.35)),(size[0]+16,size[1]+16,24),'Iron')


def lantern(scene,name,p):
    scene.box(name+'Bracket',add(p,(0,0,130)),(180,75,45),'Iron',False)
    scene.box(name+'Glow',p,(80,80,135),'Gold',False)
    for z in (-90,90):scene.box(name+f'Cap{z}',add(p,(0,0,z)),(135,135,34),'Iron',False)
    for x,y in [(-52,-52),(52,-52),(52,52),(-52,52)]:
        scene.box(name+f'Bar{x}_{y}',add(p,(x,y,0)),(16,16,175),'Iron',False)
