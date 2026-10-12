"""Grounded ridge buttresses that join the tunnel to the eastern mountain."""
import math
import random
from course import GATES, add, cross, local, mul, sub, unit
from world import clear


def tunnel_ridge(scene):
    # Unequal ridges overlap the outer bore and descend into the existing coast.
    anchors = [
        (1700, -4400, 3650, 1250, 950, .3),
        (2550, -3300, 4550, 1650, 1200, -.4),
        (3650, -2250, 4950, 1600, 1450, .7),
        (4350, -1050, 5400, 1400, 1350, -.2),
    ]
    groups = {name: ([], []) for name in ('Rock', 'RockDark', 'Snow')}
    rng = random.Random(20260909)
    levels, sides = 18, 27
    for index, (cx, cy, peak, rx, ry, turn) in enumerate(anchors):
        vertices = []
        for row in range(levels + 1):
            t = row / levels
            # Retreating shelves and several narrow ribs break the cone outline.
            envelope = (.12 + .88 * (1 - t) ** .62)
            shelf = 1 + .09 * math.sin(t * math.pi * 11 + index)
            for col in range(sides):
                angle = math.tau * col / sides
                fluting = 1 + .16 * math.cos(5 * angle + .7 * index)
                fluting += .055 * math.sin(11 * angle + row * .28)
                radius = envelope * shelf * fluting
                x = rx * radius * math.cos(angle)
                y = ry * radius * math.sin(angle)
                z = -450 + (peak + 450) * t
                z += (25 + 45 * t) * math.sin(3 * angle + row * .4)
                z += rng.uniform(-24, 24)
                vertices.append((cx + x * math.cos(turn) - y * math.sin(turn) + 210 * t,
                                 cy + x * math.sin(turn) + y * math.cos(turn) - 130 * t, z))
        triangles = []
        for row in range(levels):
            for col in range(sides):
                a = row * sides + col
                b = row * sides + (col + 1) % sides
                triangles.extend(((a, b, b + sides), (a, b + sides, a + sides)))
        top = len(vertices)
        vertices.append((cx + 210, cy - 130, peak + 100))
        triangles.extend((levels * sides + col, levels * sides + (col + 1) % sides, top)
                         for col in range(sides))
        for face in triangles:
            points = [vertices[k] for k in face]
            center = tuple(sum(p[axis] for p in points) / 3 for axis in range(3))
            bound = max(math.dist(center, p) for p in points)
            # A whole-triangle bounding sphere preserves the flight corridor,
            # including triangle interiors; vertex-only checks can miss a wall.
            if not clear(center, 1100 + bound):
                continue
            normal = unit(cross(sub(points[1], points[0]), sub(points[2], points[0])))
            snowline = 3850 + 170 * math.sin(center[0] / 370 + center[1] / 510)
            material = 'Snow' if center[2] > snowline and normal[2] > .32 else 'RockDark' if normal[2] < .18 else 'Rock'
            v, f = groups[material]
            base = len(v)
            v.extend(points)
            f.append((base, base + 1, base + 2))
    for material, (vertices, faces) in groups.items():
        if faces:
            scene.mesh('TunnelRidge' + material, vertices, faces, material, True, False)


def tunnel_fractures(scene):
    """Buried, faceted rock plates give the bore visible relief at car scale."""
    gates = GATES[13:17]
    centers = [local(gates[0], -650, 0, 0)]
    centers += [g['center'] for g in gates]
    centers += [local(gates[-1], 650, 0, 0)]
    rng = random.Random(70924)
    groups = {name: ([], []) for name in ('Rock', 'RockDark')}
    for segment, (start, end) in enumerate(zip(centers, centers[1:])):
        tangent = unit(sub(end, start))
        side = unit(cross((0, 0, 1), tangent))
        up = cross(tangent, side)
        for row in range(6):
            t = (row + .5) / 6
            centerline = add(start, mul(sub(end, start), t))
            for col in range(11):
                if rng.random() < .28:
                    continue
                angle = math.tau * (col + .22 * math.sin(row)) / 11
                radial = add(mul(side, math.cos(angle)), mul(up, math.sin(angle)))
                across = cross(radial, tangent)
                center = add(centerline, mul(radial, 1060 + rng.uniform(-15, 45)))
                lengths = (rng.uniform(95, 180), rng.uniform(80, 155), rng.uniform(110, 170))
                vertices = []
                # Five staggered rings produce chipped plates, not round pebbles.
                for ring in range(5):
                    latitude = -.5 * math.pi + (ring + .25) / 4.5 * math.pi
                    for edge in range(7):
                        longitude = math.tau * (edge + .13 * ring) / 7
                        wobble = rng.uniform(.85, 1.12)
                        point = add(center, mul(tangent, lengths[0] * math.cos(latitude) * math.cos(longitude) * wobble))
                        point = add(point, mul(across, lengths[1] * math.cos(latitude) * math.sin(longitude) * wobble))
                        point = add(point, mul(radial, lengths[2] * math.sin(latitude)))
                        vertices.append(point)
                faces = []
                for ring in range(4):
                    for edge in range(7):
                        a = ring * 7 + edge
                        b = ring * 7 + (edge + 1) % 7
                        faces.extend(((a, b, b + 7), (a, b + 7, a + 7)))
                bottom, top = len(vertices), len(vertices) + 1
                vertices.extend((add(center, mul(radial, -lengths[2])),
                                 add(center, mul(radial, lengths[2]))))
                for edge in range(7):
                    following = (edge + 1) % 7
                    faces.append((bottom, following, edge))
                    faces.append((top, 28 + edge, 28 + following))
                # Keep or discard the complete rock so clearance trimming cannot
                # leave open surfaces. Its sphere encloses every triangle.
                if not clear(center, 800 + max(math.dist(center, p) for p in vertices)):
                    continue
                material = 'Rock' if (col + row + segment) % 3 == 0 else 'RockDark'
                out_v, out_f = groups[material]
                for face in faces:
                    points = [vertices[k] for k in face]
                    index = len(out_v)
                    out_v.extend(points)
                    out_f.append((index, index + 1, index + 2))
    for material, (vertices, faces) in groups.items():
        if faces:
            scene.mesh('TunnelFracture' + material, vertices, faces, material, True, False)
