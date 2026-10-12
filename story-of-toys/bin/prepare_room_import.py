"""One-time placed room supplement after FBX and texture import into this map."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from course import PACKAGE
from ue3 import actor,box_volume
art=Path(sys.argv[1]);out=Path(sys.argv[2]);prefix=sys.argv[3] if len(sys.argv)>3 else 'Room_'
manifest=json.loads((art/'room-manifest.json').read_text())
parts=[f'Begin Map Name={PACKAGE}\nBegin MapPackage\n']
parts.append(f'''Begin PackageObject ParentPackage={PACKAGE} Class=MaterialInstanceConstant Name=MI_RoomAtlas Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'
Parent=Material'EngineDebugMaterials.TexturePaint_2Tex_Color'
TextureParameterValues(0)=(ParameterName="Diffuse",ParameterValue=Texture2D'{PACKAGE}.RoomAtlas')
TextureParameterValues(1)=(ParameterName="Diffuse2",ParameterValue=Texture2D'{PACKAGE}.RoomAtlas')
ScalarParameterValues(0)=(ParameterName="EmissiveMultiply",ParameterValue=0)
ScalarParameterValues(1)=(ParameterName="SpecularMultValue",ParameterValue=0.08)
End PackageObject
''')
parts.append('End MapPackage\nBegin Level Name=PersistentLevel\n')
parts.append(actor('WorldInfo','ReservedWorld',''));parts.append(actor('Brush','ReservedBrush',''))
for mesh in manifest['meshes']:
 n=mesh['name'];asset=prefix+n
 parts.append(actor('StaticMeshActor',n+'_Actor',f'''Begin Object Class=StaticMeshComponent Name=StaticMeshComponent0 ObjName={n}_Component Archetype=StaticMeshComponent'Engine.Default__StaticMeshActor:StaticMeshComponent0'
StaticMesh=StaticMesh'{PACKAGE}.{asset}'
Materials(0)=MaterialInstanceConstant'{PACKAGE}.MI_RoomAtlas'
PhysMaterialOverride=PhysicalMaterial'{PACKAGE}.SurfacePhysics'
bDisableAllRigidBody=False
bUsePrecomputedShadows=True
CastShadow=True
LightingChannels=(bInitialized=True,Static=True,Dynamic=True)
BlockRigidBody=True
CollideActors=True
bOverrideLightMapRes=False
OverriddenLightMapRes={mesh['lightmap_resolution']}
End Object
StaticMeshComponent=StaticMeshComponent'{n}_Component'
Components(0)=StaticMeshComponent'{n}_Component'
CollisionComponent=StaticMeshComponent'{n}_Component'
BlockRigidBody=True
bCollideActors=True
bBlockActors=True
Location=(X=0,Y=0,Z=0)'''))
parts.append(box_volume('RoomLightingBounds',(0,0,16000),(46500,38500,32500)).replace('TriggerVolume','LightmassImportanceVolume').replace('CollideActors=True','CollideActors=False'))
# Broad soft window light. Static lights are baked in UDK, never in Blender.
for i,(x,y,z,brightness,radius) in enumerate([(-1000,15500,22000,2.2,42000),(0,-11000,18000,.65,35000)]):
 parts.append(actor('PointLight',f'RoomFill{i}',f'''Begin Object Class=PointLightComponent Name=PointLightComponent0 ObjName=RoomFillComponent{i} Archetype=PointLightComponent'Engine.Default__PointLight:PointLightComponent0'
Brightness={brightness}
Radius={radius}
LightmassSettings=(LightSourceRadius=3000)
LightColor=(R=255,G=235,B=208,A=255)
CastShadows=True
CastStaticShadows=True
UseDirectLightMap=True
End Object
LightComponent=PointLightComponent'RoomFillComponent{i}'
Components(1)=PointLightComponent'RoomFillComponent{i}'
Location=(X={x},Y={y},Z={z})'''))
parts.append('End Level\nEnd Map\n');out.write_text(''.join(parts));print(out)
# Set imported mesh collision in the Static Mesh Editor. A properties-only
# PackageObject import discards the existing geometry in this UDK build.
