"""Shared surface coordinates and shipped UE3 texture material parameters."""
import math

SURFACES = {
    'Wood': ('weathered_planks', 1800, .22, 18),
    'WoodLight': ('weathered_planks', 1800, .22, 18),
    'WoodDark': ('weathered_planks', 1800, .15, 12),
    'Rock': ('seaside_rock', 2800, .28, 24),
    'RockLight': ('seaside_rock', 2800, .28, 24),
    'RockDark': ('seaside_rock', 2800, .28, 24),
    'Snow': ('snow_02', 900, .18, 42),
    'Sail': ('hessian_230', 450, .06, 8),
    'SailShade': ('hessian_230', 450, .06, 8),
    'Rope': ('hessian_230', 200, .06, 8),
    'Iron': ('rusty_metal', 800, .6, 38),
}

def face_uvs(m, face):
    """Project onto the face plane; align timber grain along its long edge."""
    vertices = [m['vertices'][i] for i in face]
    a, b, c = vertices[:3]
    e = [b[i]-a[i] for i in range(3)]
    f = [c[i]-a[i] for i in range(3)]
    n = (e[1]*f[2]-e[2]*f[1], e[2]*f[0]-e[0]*f[2], e[0]*f[1]-e[1]*f[0])
    axis = max(range(3), key=lambda i: abs(n[i]))
    axes = [i for i in range(3) if i != axis]
    scale = SURFACES.get(m['material'], ('', 1024))[1]
    if m['material'].startswith('Wood'):
        edges = [[vertices[(j+1)%len(vertices)][i]-p[i] for i in range(3)] for j,p in enumerate(vertices)]
        v = max(edges, key=lambda v: sum(x*x for x in v))
        length = math.sqrt(sum(x*x for x in v)) or 1
        v = [x/length for x in v]
        nl = math.sqrt(sum(x*x for x in n)) or 1
        n = [x/nl for x in n]
        u = (v[1]*n[2]-v[2]*n[1],v[2]*n[0]-v[0]*n[2],v[0]*n[1]-v[1]*n[0])
        return [(sum(p[i]*u[i] for i in range(3))/scale,
                 sum(p[i]*v[i] for i in range(3))/scale) for p in vertices]
    return [(p[axes[0]]/scale,p[axes[1]]/scale) for p in vertices]

def material_instance(package, name):
    asset, _, specular, power = SURFACES[name]
    result = [f"Begin PackageObject ParentPackage={package} Class=MaterialInstanceConstant Name=MI_{name} Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'",
              " Parent=Material'EngineDebugMaterials.TexturePaint_2Tex_Color'"]
    for i,(parameter,channel) in enumerate([('Diffuse','diff'),('Diffuse2','diff'),('Normal','nor_dx'),('Normal2','nor_dx'),('Spec','spec')]):
        result.append(f' TextureParameterValues({i})=(ParameterName="{parameter}",ParameterValue=Texture2D\'{package}.T_{asset}_{channel}\')')
    for i,(parameter,value) in enumerate([('EmissiveMultiply',0),('SpecularMultValue',specular),('SpecPower',power)]):
        result.append(f' ScalarParameterValues({i})=(ParameterName="{parameter}",ParameterValue={value})')
    result.append('End PackageObject\n')
    return '\n'.join(result)


def water_instance(package):
    """Use the shipped liquid shader; new base shaders do not work in the game."""
    result = [f"Begin PackageObject ParentPackage={package} Class=MaterialInstanceConstant Name=MI_Water Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'",
              " Parent=Material'Engine_MI_Shaders.M_ES_Phong_Translucent_Liquid_Master_01'"]
    for i, (name, value) in enumerate([
        ('Speed', .045), ('Scale', 1.4), ('Opacity', .88),
        ('SpecPower', 48), ('ReflectionOpacityContribution', .35),
    ]):
        result.append(f' ScalarParameterValues({i})=(ParameterName="{name}",ParameterValue={value})')
    for i, (name, rgba) in enumerate([
        ('DiffuseTexColor', (.025, .105, .12, 2)),
        ('CubeColor', (.22, .40, .43, .45)),
        ('SpecColor', (.42, .65, .66, 1)),
        ('NormalIntensity', (.5, .5, 1, 1)),
        ('DistortionIntensity', (.2, .2, 0, 1)),
    ]):
        color = ','.join(f'{channel}={value}' for channel, value in zip('RGBA', rgba))
        result.append(f' VectorParameterValues({i})=(ParameterName="{name}",ParameterValue=({color}))')
    result.append('End PackageObject\n')
    return '\n'.join(result)
