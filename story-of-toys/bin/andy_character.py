"""Andy assembled from editable anatomical, clothing and controller parts."""
import math
import bpy
from mathutils import Vector, Matrix


def build_character(g):
    origin = g['origin']
    skin, denim, green, blue = g['SKIN'], g['DENIM'], g['DARKGREEN'], g['BLUE']
    white, red, hair, black = (g[k] for k in ('WHITE', 'RED', 'HAIR', 'BLACK'))
    groups = g['GROUPS']
    g['group'] = 'RoomAndy'

    def ell(name, p, scale, tile, segments=32, rings=20):
        return g['ell'](name, origin + Vector(p), scale, tile, segments, rings)

    def box(name, p, scale, tile, bevel=30):
        return g['box'](name, origin + Vector(p), scale, tile, bevel)

    def mesh(name, vertices, faces, tile):
        data = bpy.data.meshes.new(name)
        data.from_pydata([tuple(origin + Vector(v)) for v in vertices], [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        return g['finish'](obj, name, tile, True)

    def solid_uv(obj, tile):
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name='UVMap')
        for uv in obj.data.uv_layers[0].data:
            uv.uv = ((tile % 4 + .5) / 4, (tile // 4 + .5) / 4)

    def merge(name, parts, tile, voxel, budget):
        groups[g['group']] = [p for p in groups[g['group']] if p not in parts]
        bpy.ops.object.select_all(action='DESELECT')
        for p in parts:
            p.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = name
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        remesh = obj.modifiers.new('Blend sculpt forms', 'REMESH')
        remesh.mode = 'VOXEL'
        remesh.voxel_size = voxel
        remesh.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier=remesh.name)
        smooth = obj.modifiers.new('Relax transitions', 'SMOOTH')
        smooth.factor = .65
        smooth.iterations = 18 if tile == skin else 5
        bpy.ops.object.modifier_apply(modifier=smooth.name)
        count = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        if count > budget:
            decimate = obj.modifiers.new('Surface budget', 'DECIMATE')
            decimate.ratio = budget / count
            bpy.ops.object.modifier_apply(modifier=decimate.name)
        solid_uv(obj, tile)
        groups[g['group']].append(obj)
        return obj

    def tube(name, points, radii, tile, sides=16, squash=1):
        points = [Vector(p) for p in points]
        if len(points)>2:
            refined=[];sizes=[]
            for i in range(len(points)-1):
                p0,p1,p2,p3=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
                for step in range(5):
                    t=step/5
                    refined.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
                    sizes.append(radii[i]*(1-t)+radii[i+1]*t)
            points=refined+[points[-1]];radii=sizes+[radii[-1]]
        vertices, faces = [], []
        for i, (p, radius) in enumerate(zip(points, radii)):
            direction = points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]
            axis = direction.normalized()
            u = axis.cross(Vector((0, 1, 0)))
            if u.length < .1:
                u = axis.cross(Vector((1, 0, 0)))
            u.normalize()
            v = axis.cross(u).normalized()
            for j in range(sides):
                a = math.tau * j / sides
                vertices.append(p + radius * (u * math.cos(a) + v * math.sin(a) * squash))
        for i in range(len(points) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                faces.append((i * sides + j, i * sides + k, (i + 1) * sides + k, (i + 1) * sides + j))
        faces += [tuple(reversed(range(sides))), tuple(range((len(points) - 1) * sides, len(points) * sides))]
        return mesh(name, vertices, faces, tile)

    def curve(name, points, radius, tile):
        data = bpy.data.curves.new(name, 'CURVE')
        data.dimensions = '3D'
        data.resolution_u = 5
        data.bevel_depth = radius
        data.bevel_resolution = 2
        data.use_fill_caps = True
        spline = data.splines.new('BEZIER')
        spline.bezier_points.add(len(points) - 1)
        for p, co in zip(spline.bezier_points, points):
            p.co = origin + Vector(co)
            p.handle_left_type = p.handle_right_type = 'AUTO'
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target='MESH')
        return g['finish'](bpy.context.object, name, tile, True)

    def loft(name, sections, tile, sides=48, folds=0):
        vertices, faces = [], []
        for i, (cx, cy, z, rx, ry) in enumerate(sections):
            for j in range(sides):
                a = math.tau * j / sides
                wrinkle = folds * math.sin(5 * a + i * 1.4) * math.sin(math.pi * i / (len(sections) - 1))
                vertices.append((cx + (rx + wrinkle) * math.cos(a), cy + (ry + wrinkle) * math.sin(a), z))
        for i in range(len(sections) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                faces.append((i*sides+j, i*sides+k, (i+1)*sides+k, (i+1)*sides+j))
        faces += [tuple(reversed(range(sides))), tuple(range((len(sections)-1)*sides, len(sections)*sides))]
        return mesh(name, vertices, faces, tile)

    # The lower legs remain separate all the way up to the actual crotch.
    pants = []
    for side in (-1, 1):
        x = side * 880
        sole = loft('Rubber sneaker sole', [(x,-410,170,650,1180),(x,-450,300,710,1270),(x,-430,450,690,1240)], white)
        shoe = loft('Canvas sneaker upper', [(x,-430,440,670,1210),(x,-380,650,650,1130),(x,-200,880,520,880),(x,40,1040,450,650)], red)
        ell('Rubber toe cap', (x,-1240,520), (560,420,230), white)
        box('Canvas shoe tongue', (x,-500,890), (500,650,90), red, 65)
        for j in range(5):
            yy = -850+j*160
            curve('Crossed cotton lace', [(x-220,yy,900),(x,yy+75,940),(x+220,yy+130,930)], 25, white)
        sections = [(x,60,1050,540,540),(x,40,1280,565,560),(x,30,1420,545,550),(x,45,1540,580,572),(x,50,1730,565,560),
                    (x-side*35,70,2650,560,580),(x-side*55,-30,3620,590,580),(x-side*55,-40,3820,620,610),(x-side*55,-30,3980,595,590),
                    (x-side*60,-60,4100,630,620),(x-side*70,0,4500,610,650),
                    (x-side*90,50,5500,680,720),(x-side*100,60,6500,740,780),
                    (x-side*130,0,7400,770,790)]
        pants.append(loft('Left jean leg' if side<0 else 'Right jean leg', sections, denim, folds=14))
        curve('Outer leg seam', [(x+side*550,60,1250),(x+side*575,50,3900),(x+side*635,60,6100),(x+side*640,50,7400)], 13, blue)
        loft('Jean cuff', [(x,45,1090,560,555),(x,45,1230,575,570)], denim)
    pants.append(ell('Fitted jean pelvis', (0,100,7360), (1500,810,850), denim))
    merge('Tailored jeans', pants, denim, 80, 11000)
    loft('Denim waistband', [(0,50,7720,1470,810),(0,50,7900,1440,785)], denim)
    # A closed elliptical leather strap wraps the hips, with a hollow buckle.
    loft('Leather belt', [(0,50,7760,1488,826),(0,50,7870,1470,814)], hair)
    for a in (-2.75,-2.1,-1.0,-.35,.7,2.4):
        box('Belt loop', (1490*math.cos(a),50+835*math.sin(a),7820), (90,75,255), denim, 15)
    for x in (-130,130):
        box('Buckle side', (x,-807,7815), (38,50,220), g['GLASS'], 12)
    for z in (7720,7910):
        box('Buckle bar', (0,-807,z), (260,50,35), g['GLASS'], 10)
    box('Buckle tongue', (0,-845,7815), (190,25,25), g['GLASS'], 8)
    curve('Jean fly stitch', [(100,-751,7710),(125,-780,7480),(100,-790,7240)], 12, blue)
    for side in (-1,1):
        curve('Curved pocket opening', [(side*380,-745,7690),(side*700,-713,7500),(side*1190,-495,7340)], 15, blue)

    torso = loft('Cotton shirt torso', [(0,80,7860,1400,790),(0,60,8030,1450,810),
        (0,60,8350,1450,810),(0,70,9300,1470,830),(0,70,10400,1540,840),
        (0,90,11200,1550,780),(0,100,11600,1340,650),(0,80,12050,720,530),
        (0,65,12230,490,440)], green, folds=22)
    shoulders = [torso]
    for side in (-1,1):
        shoulders.append(ell('Cloth shoulder', (side*1250,30,11460), (620,650,600), green))
        shoulders.append(tube('Short sleeve', [(side*1330,10,11480),(side*1580,-10,11150),(side*1780,-50,10820)], [610,590,530], green, 32))
    shirt=merge('Cotton shirt', shoulders, green, 90, 10000)
    inverse=shirt.matrix_world.inverted()
    for v in shirt.data.vertices:
        co=shirt.matrix_world @ v.co-origin
        if co.y < -250:
            waist=math.exp(-((co.z-8290)/340)**2)*math.exp(-((abs(co.x)-1050)/340)**2)
            underarm=math.exp(-((co.z-10800)/360)**2)*math.exp(-((abs(co.x)-1200)/270)**2)
            co.y+=42*waist*math.sin((co.z-8000)/80+abs(co.x)/110)+30*underarm*math.sin(co.z/110+abs(co.x)/170)
            v.co=inverse @ (origin+co)
    shirt.data.update()
    loft('Shirt hem seam', [(0,75,7890,1410,800),(0,70,7990,1455,823)], green)
    collar = g['torus']('Ribbed crew collar', origin+Vector((0,65,12200)), 510, 48, green)
    collar.scale.y = .86
    tube('Neck', [(0,60,12080),(0,30,12600),(0,0,13360)], [440,420,490], skin, 40)
    for side in (-1,1):
        tube('Sleeve stitched cuff', [(side*1740,-50,10860),(side*1810,-60,10730)], [535,515], green, 32)
        curve('Shoulder fabric crease', [(side*1050,-540,11600),(side*1440,-560,11350),(side*1710,-495,10920)], 14, green)

    hand_pivot=Vector((550,-2220,10480))
    hand_rotation=Matrix.Rotation(math.radians(35),4,'Z')
    def pose_hand_point(p, weight=1, lift=None):
        p=Vector(p);return p.lerp(hand_pivot+hand_rotation @ (p-hand_pivot),weight)+Vector((0,0,hand_lift if lift is None else lift))
    def pose_hand_object(obj):
        pivot=origin+hand_pivot
        obj.matrix_world=Matrix.Translation(pivot+Vector((0,0,hand_lift))) @ hand_rotation @ Matrix.Translation(-pivot) @ obj.matrix_world
        return obj
    arms = [
        ('Left',[(-1730,-20,10830),(-1900,-140,10300),(-2120,-340,9640),(-1920,-800,9630),(-1150,-1690,10000),(-390,-2270,10480)], [295,285,270,260,220,145], (-300,-2370,10700)),
        ('Right',[(1730,-20,10830),(1930,-140,10100),(2190,-490,9370),(1900,-1120,9440),(1200,-1700,9280),(800,-2070,9300)], [295,285,270,250,215,145], (800,-2150,9460))]
    for name, points, radii, palm in arms:
        hand_lift=1400*max(0,min(1,(palm[2]-8000)/2000))
        posed=[]
        for point in points:
            w=max(0,min(1,(-point[1]-300)/1500));w=w*w*(3-2*w)
            posed.append(pose_hand_point(point,w,1400*max(0,min(1,(point[2]-8000)/2000))))
        if name=='Right':
            posed=[Vector(p) for p in [(1730,-20,12230),(1880,-150,11600),(2000,-380,10800),(1950,-650,10430),(1450,-1380,10430)]]+[pose_hand_point(points[-1])]
        else:
            posed=[Vector(p) for p in [(-1730,-20,12230),(-1860,-100,11650),(-1950,-400,11000),(-1650,-850,11050),(-850,-1750,11500)]]+[pose_hand_point(points[-1])]
        posed.append(pose_hand_point(palm))
        radii=[295,280,250,240,205,150,150]
        parts = [tube(name+' arm', posed, radii, skin, 32)]
        parts.append(pose_hand_object(ell(name+' palm', palm, (190,135,295), skin)))
        # Every finger has a knuckle, middle joint and rounded pad.
        for finger in range(4):
            if name == 'Left':
                yy = -2540+finger*105
                points = [(-430+finger*60,-2340+finger*70,10880),(-330+finger*40,-2380+finger*70,11020),(-130,-2400+finger*70,11010),(-80,-2400+finger*70,10890)]
                radii = [52,52,46,36]
            else:
                zz = 9690-finger*130
                points = [(790,-2260,zz),(680,-2410,zz),(430,-2410,zz-20),(360,-2220,zz-30)]
                radii = [65,60,53,47]
            parts.append(ell(name+' knuckle '+str(finger+1),pose_hand_point(points[0]),(68,68,72),skin,20,12))
            parts.append(tube(name+' finger '+str(finger+1), [pose_hand_point(p) for p in points], radii, skin, 16))
            parts.append(ell(name+' fingertip '+str(finger+1), pose_hand_point(points[-1]), (42,42,46), skin,20,12))
        thumb = [(-150,-2370,10680),(-170,-2480,10610),(-100,-2460,10590)] if name=='Left' else [(810,-2100,9650),(650,-2320,9860),(450,-2390,9800)]
        parts.append(tube(name+' opposable thumb', [pose_hand_point(p) for p in thumb], [75,65,48], skin,20))
        parts.append(ell(name+' thumb pad', pose_hand_point(thumb[-1]), (48,48,55), skin,20,12))
        merge(name+' arm and palm', [p for p in parts if 'finger' not in p.name], skin, 27, 7500)

    controller_start=len(groups['RoomAndy'])
    loft('Pistol grip handle',[(550,-2150,8880,185,235),(550,-2150,9020,165,215),(550,-2150,9740,175,225),(550,-2150,10040,220,255)],green)
    box('Green transmitter shell', (550,-2220,10480), (840,960,1130), g['GREEN'], 70)
    box('Transmitter rear shell seam', (550,-1770,10480), (820,100,1100), green, 38)
    # Thick cylindrical steering wheel on the left side, with a projecting hub.
    x=110
    g['rod']('Steering spindle',origin+Vector((x+25,-2260,10770)),origin+Vector((x-120,-2260,10770)),90,blue,verts=32)
    g['rod']('Blue steering wheel',origin+Vector((x-80,-2260,10770)),origin+Vector((x-195,-2260,10770)),235,blue,verts=48)
    g['rod']('Blue wheel center barrel',origin+Vector((x-195,-2260,10770)),origin+Vector((x-360,-2260,10770)),125,blue,verts=32)
    for j in range(24):
        a=math.tau*j/24
        tube('Wheel fine grip',[(x-80,-2260+234*math.cos(a),10770+234*math.sin(a)),(x-195,-2260+234*math.cos(a),10770+234*math.sin(a))],[5,5],blue,8)
    box('Small throttle recess',(340,-2705,10850),(105,12,230),green,12)
    tube('Front throttle lever',[(340,-2710,10880),(340,-2810,10970)],[29,29],blue,16)
    box('Throttle blue paddle',(340,-2810,10970),(125,65,75),blue,18)
    tube('Aerial socket',[(810,-2070,11015),(810,-2070,11120)],[47,42],green,20)
    tube('Silver aerial',[(810,-2070,11100),(900,-2020,13950)],[20,15],g['GLASS'],16)
    ell('Aerial red safety cap',(900,-2020,13980),(48,48,105),red,24,16)
    pivot_remote=origin+Vector((550,-2220,10480))
    rotation_remote=Matrix.Rotation(math.radians(35),4,'Z')
    for part in groups['RoomAndy']:
        is_controller=part in groups['RoomAndy'][controller_start:]
        if not is_controller:continue
        inv=part.matrix_world.inverted()
        for vertex in part.data.vertices:
            point=part.matrix_world @ vertex.co
            weight=1
            relative=point-pivot_remote
            rotated=rotation_remote @ relative
            vertex.co=inv @ (pivot_remote+relative.lerp(rotated,weight))
        part.data.update()

    g['group']='RoomAndyHead'
    forms=[]
    for name,p,scale in [
        ('Cranium',(0,100,14980),(1130,880,1190)),
        ('Facial plane',(0,-230,14380),(1000,700,1050)),
        ('Jaw',(0,-180,13800),(740,550,510)),
        ('Chin',(0,-300,13570),(460,390,260)),
        ('Left cheek',(-510,-320,14230),(380,380,390)),
        ('Right cheek',(510,-320,14230),(380,380,390)),
        ('Upper muzzle',(0,-540,14020),(460,300,240)),
        ('Nasal bridge',(0,-725,14600),(140,170,360)),
        ('Nose tip',(0,-905,14380),(210,260,175)),
        ('Left nose wing',(-165,-865,14350),(115,150,100)),
        ('Right nose wing',(165,-865,14350),(115,150,100))]:
        forms.append(ell(name,p,scale,skin))
    face=merge('Blended skull cheeks jaw and nose', forms, skin, 36, 14000)
    # Recess the smile into the face, instead of drawing it on the skin.
    cutter=ell('Smile cavity cutter',(0,-1030,13940),(420,350,95),black)
    for v in cutter.data.vertices:
        v.co.z += 75*(v.co.x/420)**2
    bpy.ops.object.select_all(action='DESELECT');face.select_set(True);bpy.context.view_layer.objects.active=face
    bpy.context.view_layer.update()
    boolean=face.modifiers.new('Recessed mouth','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    assert len(face.data.polygons)>5000, 'Mouth operation removed the head'
    groups[g['group']].remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)
    face=merge('Sculpted face with rounded mouth rim',[face],skin,24,18000)
    def pigment_uv(obj):
        for poly in obj.data.polygons:
            center=sum((obj.matrix_world @ obj.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)-origin
            if center.y >= -200:
                continue
            for i in poly.loop_indices:
                co=obj.matrix_world @ obj.data.vertices[obj.data.loops[i].vertex_index].co-origin
                u=.02+.96*(.5+co.x/2840);v=.02+.96*(.5+(co.z-14600)/3200)
                obj.data.uv_layers[0].data[i].uv=((2+u)/4,(3+v)/4)
        return obj
    solid_uv(face,skin);pigment_uv(face)
    ell('Mouth interior',(0,-710,13960),(350,100,80),hair)
    vertices=[];faces=[]
    for row in (0,1):
        for j in range(33):
            t=-1+2*j/32
            vertices.append((330*t,-825+80*t*t,13998+30*t*t-row*55*(1-t*t)))
    for j in range(32):faces.append((33+j,34+j,j+1,j))
    mesh('Curved upper teeth',vertices,faces,white)
    for side in (-1,1):
        # A shallow ear shell with an asymmetric helix, blended lobe and inner fold.
        vv=[];ff=[];n=48
        for row in range(9):
            r=row/8
            for j in range(n):
                a=math.tau*j/n
                x=side*(1050+145*r*math.cos(a)*(1+.15*math.sin(a)))
                z=14520+235*r*math.sin(a)
                y=5-48*(1-r*r)-40*math.exp(-((r-.82)/.16)**2)
                vv.append((x,y,z))
        for row in range(8):
            for j in range(n):
                k=(j+1)%n;ff.append((row*n+j,row*n+k,(row+1)*n+k,(row+1)*n+j))
        ear=mesh('Ear sculpted shell',vv,ff,skin)
        solid_uv(ear,skin)
        ell('Ear soft lobe',(side*1050,0,14320),(95,62,95),skin)
        curve('Ear inner fold',[(side*1055,-64,14395),(side*1100,-67,14505),(side*1070,-65,14615)],13,skin)
        ex=side*440;ez=14950
        from mathutils.bvhtree import BVHTree
        if side == -1:
            bvh=BVHTree.FromPolygons([face.matrix_world @ v.co for v in face.data.vertices], [list(p.vertices) for p in face.data.polygons])
        def surface_y(x,z):
            hit=bvh.ray_cast(origin+Vector((x,-5000,z)),Vector((0,1,0)),10000)[0]
            return hit.y-origin.y if hit else -600
        def eye_y(x,z):
            return surface_y(x,z)-8-65*max(0,1-((x-ex)/270)**2-((z-ez)/185)**2)
        def cap(name,cx,cz,rx,rz,tile,offset=0):
            vv=[(cx,eye_y(cx,cz)-offset,cz)];ff=[];segments=40
            for row in range(1,7):
                r=row/6
                for j in range(segments):
                    a=math.tau*j/segments;x=cx+rx*r*math.cos(a);z=cz+rz*r*math.sin(a)
                    vv.append((x,eye_y(x,z)-offset,z))
            for j in range(segments):ff.append((0,j+1,(j+1)%segments+1))
            for row in range(5):
                for j in range(segments):
                    a=1+row*segments+j;b=1+row*segments+(j+1)%segments
                    ff.append((a,a+segments,b+segments,b))
            return mesh(name,vv,ff,tile)
        # The diffuse eye opening and sculpt must share one outline.
        # A broad continuous bulge avoids a second elliptical rim across the painted lid.
        vv=[];ff=[];n=64
        for row in range(13):
            r=row/12
            for j in range(n):
                a=math.tau*j/n;x=ex+360*r*math.cos(a);z=ez+260*r*math.sin(a)
                y=surface_y(x,z)-2-32*(1-r*r)**2
                vv.append((x,y,z))
        for row in range(12):
            for j in range(n):
                k=(j+1)%n;ff.append((row*n+j,row*n+k,(row+1)*n+k,(row+1)*n+j))
        pigment_uv(mesh('Continuous eye surface',vv,ff,skin))
        curve('Soft eyebrow',[(ex-285,-695,15300),(ex-120,-770,15410),(ex+110,-780,15425),(ex+275,-700,15370)],14,hair)
    # A separate scalp and tapered swept locks sit on the rounded skull.
    vertices=[];faces=[];around=64;rows=20
    for row in range(rows+1):
        for j in range(around):
            a=math.tau*j/around;front=max(0,-math.sin(a))
            limit=1.60-1.18*front
            t=.001+(limit-.001)*row/rows
            relief=7*math.sin(40*a+t*3)
            vertices.append(((1160+relief)*math.sin(t)*math.cos(a),100+(915+relief)*math.sin(t)*math.sin(a),14980+1220*math.cos(t)))
    for row in range(rows):
        for j in range(around):
            k=(j+1)%around;faces.append((row*around+j,row*around+k,(row+1)*around+k,(row+1)*around+j))
    mesh('Scalp cap',vertices,faces,hair)
    # Project facial color only after the geometric forms and openings exist.
    import numpy as np
    heights=[13150,13730,13860,13940,14005,14380,14765,14950,15135,15300,16150]
    image_y=[.95,.85,.81,.78,.718,.635,.48,.417,.352,.245,.01]
    for part in list(groups['RoomAndyHead']):
        if part.name.startswith('Soft eyebrow'):
            groups['RoomAndyHead'].remove(part);bpy.data.objects.remove(part,do_unlink=True);continue
        if part.name.startswith(('Ear','Scalp')):continue
        for poly in part.data.polygons:
            center=sum((part.matrix_world @ part.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)-origin
            if center.y>=-200:continue
            for i in poly.loop_indices:
                co=part.matrix_world @ part.data.vertices[part.data.loops[i].vertex_index].co-origin
                mouth_weight=math.exp(-((co.z-13950)/250)**2)
                x_scale=.000371*(1+.25*mouth_weight)
                u=.49+co.x*x_scale;v=1-float(np.interp(co.z,heights,image_y))
                part.data.uv_layers[0].data[i].uv=((2+u)/4,(3+v)/4)
    pivot=origin+Vector((0,0,14500))
    pose=Matrix.Translation(pivot+Vector((0,-100,620))) @ Matrix.Rotation(math.radians(11),4,'X') @ Matrix.Rotation(math.radians(-6),4,'Y') @ Matrix.Translation(-pivot)
    for part in groups['RoomAndyHead']:
        part.matrix_world=pose @ part.matrix_world
    for part in groups['RoomAndy']:
        if part.name.startswith(('Left arm','Right arm','Left finger','Right finger')):continue
        inverse = part.matrix_world.inverted()
        for vertex in part.data.vertices:
            point = part.matrix_world @ vertex.co
            height = point.z - origin.z
            point.z += 1400 * max(0, min(1, (height-8000)/2000))
            vertex.co = inverse @ point
        part.data.update()
    # Preserve named groups and the hat/course coordinates used by the importer.
    g['group']='RoomAndy'
