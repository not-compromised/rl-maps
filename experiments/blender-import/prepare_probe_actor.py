from pathlib import Path
from ue3 import actor,box_volume
from course import PACKAGE
out=Path(__file__).parent/'output'/'blender-probe-01'
text=f'''Begin Map Name={PACKAGE}
Begin MapPackage
Begin PackageObject ParentPackage={PACKAGE} Class=MaterialInstanceConstant Name=MI_Probe Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'
Parent=Material'EngineDebugMaterials.TexturePaint_2Tex_Color'
TextureParameterValues(0)=(ParameterName="Diffuse",ParameterValue=Texture2D'{PACKAGE}.ProbeChecker')
TextureParameterValues(1)=(ParameterName="Diffuse2",ParameterValue=Texture2D'{PACKAGE}.ProbeChecker')
ScalarParameterValues(0)=(ParameterName="EmissiveMultiply",ParameterValue=0)
ScalarParameterValues(1)=(ParameterName="SpecularMultValue",ParameterValue=0.1)
End PackageObject
End MapPackage
Begin Level Name=PersistentLevel
'''
text+=actor('StaticMeshActor','ProbePlatform_Actor',f'''Begin Object Class=StaticMeshComponent Name=StaticMeshComponent0 ObjName=ProbePlatform_Component Archetype=StaticMeshComponent'Engine.Default__StaticMeshActor:StaticMeshComponent0'
StaticMesh=StaticMesh'{PACKAGE}.ProbePlatform'
Materials(0)=MaterialInstanceConstant'{PACKAGE}.MI_Probe'
bDisableAllRigidBody=False
bUsePrecomputedShadows=True
CastShadow=True
LightingChannels=(bInitialized=True,Static=True,Dynamic=True)
BlockRigidBody=True
CollideActors=True
End Object
StaticMeshComponent=StaticMeshComponent'ProbePlatform_Component'
Components(0)=StaticMeshComponent'ProbePlatform_Component'
CollisionComponent=StaticMeshComponent'ProbePlatform_Component'
BlockRigidBody=True
bCollideActors=True
bBlockActors=True
Location=(X=0,Y=0,Z=0)''')
text+=box_volume('ProbeLightingBounds',(0,0,800),(4000,4000,3000)).replace('TriggerVolume','LightmassImportanceVolume').replace('CollideActors=True','CollideActors=False')
text+='End Level\nEnd Map\n'
(out/'probe-actor.t3d').write_text(text)
