"""Prepare the empty UDK test level; its tested mesh must come from Blender FBX."""
from pathlib import Path
from ue3 import actor
from build_map import key_light
from course import PACKAGE
out=Path(__file__).parent/'output'/'blender-probe-01'
parts=[f'Begin Map Name={PACKAGE}\nBegin Level Name=PersistentLevel\n']
parts.append(actor('WorldInfo','WorldInfo_0', '''Begin Object Class=MapInfo_TA Name=MapSettings
MirrorFieldType=MFT_None
MinStadiumBrightness=0.3
End Object
MyMapInfo=MapInfo_TA'MapSettings'
Title="Blender import probe"
KillZ=-4000
GlobalGravityZ=-650
bForceNoPrecomputedLighting=False
bUseGlobalIllumination=True'''))
parts.append(actor('Brush','BuilderBrush',''))
parts.append(actor('PlayerStart_TA','InitialPlayer','Location=(X=-700,Y=400,Z=150)\nRotation=(Yaw=0)\nTeamIndex=1\nbDestinationOnly=True'))
parts.append(actor('Pylon_Soccar_TA','FlightArea',"Location=(X=0,Y=0,Z=100)\nFieldCenter=(X=0,Y=0,Z=0)\nFieldExtent=(X=6000,Y=6000,Z=4000)\nSpawnPoints(0)=PlayerStart_TA'InitialPlayer'"))
parts.append(actor('SkyLight','Ambient',"Begin Object Class=SkyLightComponent Name=SkyLightComponent0 ObjName=AmbientComponent Archetype=SkyLightComponent'Engine.Default__SkyLight:SkyLightComponent0'\nBrightness=0.4\nEnd Object\nLightComponent=SkyLightComponent'AmbientComponent'\nComponents(1)=SkyLightComponent'AmbientComponent'\nLocation=(X=0,Y=0,Z=2500)"))
parts.append(key_light(baked=True))
parts.append('End Level\nEnd Map\n')
(out/'empty-probe.t3d').write_text(''.join(parts))
print(out/'empty-probe.t3d')
