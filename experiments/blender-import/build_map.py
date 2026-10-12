"""Build the course import and Kismet separately; no guest or game mutations."""
import lib_path  # noqa: F401  (puts the shared ../lib on sys.path)
from pathlib import Path
import argparse,gzip,json,math,hashlib
from course import *
from ue3 import Scene,actor,vec,prism,box_volume,static_mesh,mesh_actor
from logic import generate
from course_bounds import sea_reset, verify_landings

PALETTE={'Wood':(.19,.105,.045),'WoodLight':(.34,.23,.13),'WoodDark':(.065,.04,.025),'Iron':(.055,.075,.08),'Rock':(.20,.26,.28),'RockDark':(.09,.15,.17),'Snow':(.73,.83,.84),'Ghost':(.18,.9,.55),'Gold':(.95,.63,.18),'Violet':(.6,.3,.88),'Sky':(.045,.105,.13),'Water':(.055,.24,.26),'Sail':(.54,.57,.41),'Rope':(.25,.19,.12)}

def ring(scene,g):
 for label,tube,offset,material in [('Rim',44,0,'Iron'),('Light',10,-46,'Ghost')]:
  major=g['radius']+44 if label=='Rim' else g['radius']+12
  v=[];f=[];n=96;m=8
  for j in range(n):
   theta=2*math.pi*j/n
   for k in range(m):
    phi=2*math.pi*k/m;r=major+tube*math.cos(phi);v.append(local(g,offset+tube*math.sin(phi),r*math.cos(theta),r*math.sin(theta)))
  for j in range(n):
   for k in range(m):f.append((j*m+k,((j+1)%n)*m+k,((j+1)%n)*m+(k+1)%m,j*m+(k+1)%m))
  scene.mesh(f'Gate{g["index"]:02}{label}',v,f,material,label=='Rim',True)
  if label=='Rim':scene.meshes[-1]['hidden']=True
 from rope_rings import braided_ring
 braided_ring(scene,g)

def sensors():
 out=[]
 for g in GATES:
  i=g['index'];r=g['radius'];name=f'Gate{i:02}'
  polygon=[((r-85)*math.cos(a*math.tau/32),(r-85)*math.sin(a*math.tau/32)) for a in range(32)]
  # Keep passage checks beside the rim so recovery at the opening can still arm it.
  for label,offset in [('Entry',-90),('Exit',90)]:out.append(prism(name+label+'Volume',polygon,lambda x,y,z,g=g,o=offset:local(g,x+o,y,z),70))
  for j in range(16):
   a,b=math.tau*j/16,math.tau*(j+1)/16
   # Circumscribed opening leaves the visible rim collidable before the miss boundary.
   inner=(r+110)/math.cos(math.pi/16);outer=4500
   poly=[(inner*math.cos(a),inner*math.sin(a)),(outer*math.cos(a),outer*math.sin(a)),(outer*math.cos(b),outer*math.sin(b)),(inner*math.cos(b),inner*math.sin(b))]
   out.append(prism(name+f'MissVolume{j:02}',poly,lambda x,y,z,g=g:local(g,x,y,z),90))
 verify_landings()
 out.append(box_volume('SeaReset',*sea_reset()))
 for stage,deck in enumerate(DECKS[1:-1],2):out.append(box_volume(f'Checkpoint{stage}Volume',add(deck,(0,0,230)),(1300,1300,450)))
 out.append(box_volume('FinishVolume',add(DECKS[-1],(0,0,230)),(1300,1300,450)))
 out.append(box_volume('RestartVolume',add(DECKS[-1],(-1250,0,200)),(340,340,300)))
 for i in range(len(SPAWNS)):
  for switch,side in [('On',1),('Off',-1)]:out.append(box_volume(f'Camera{switch}{i+1}Volume',add(DECKS[i],(0,side*770,170)),(340,340,280)))
 return out

def gray_scene():
 scene=Scene()
 for i,p in enumerate(DECKS):
  scene.box(f'Deck{i}',add(p,(0,0,-90)),(2200,2200,180),'Wood')
  for side in [-1,1]:scene.box(f'Deck{i}Stripe{side}',add(p,(side*1000,0,5)),(24,1900,10),'Ghost',False)
  if i<len(SPAWNS):
   from camera_stations import camera_station
   for side in (1,-1):camera_station(scene,f'Deck{i}Camera{side}',add(p,(0,side*770,0)),side)
 scene.box('RestartPad',add(DECKS[-1],(-1250,0,-10)),(500,500,100),'Gold')
 for g in GATES:ring(scene,g)
 # The sky has inward faces. It never participates in collision.
 v=[];f=[];rows=16;cols=48
 for i in range(rows+1):
  a=-math.pi/2+math.pi*i/rows
  for j in range(cols):
   b=math.tau*j/cols;v.append((80000*math.cos(a)*math.cos(b),80000*math.cos(a)*math.sin(b),80000*math.sin(a)))
 for i in range(rows):
  for j in range(cols):f.append((i*cols+j,(i+1)*cols+j,(i+1)*cols+(j+1)%cols,i*cols+(j+1)%cols))
 scene.mesh('SkyDome',v,f,'Sky',False,True)
 return scene

def material(name, full=False):
 if full:
  from surface_materials import SURFACES,material_instance,water_instance
  if name=='Water':return water_instance(PACKAGE)
  if name in SURFACES:return material_instance(PACKAGE,name)
  if name=='Sky':
   return f"""Begin PackageObject ParentPackage={PACKAGE} Class=MaterialInstanceConstant Name=MI_Sky Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'
 Parent=Material'EngineDebugMaterials.TexturePaint_2Tex_Color'
 TextureParameterValues(0)=(ParameterName="Diffuse",ParameterValue=Texture2D'{PACKAGE}.T_GhostSky')
 TextureParameterValues(1)=(ParameterName="Diffuse2",ParameterValue=Texture2D'{PACKAGE}.T_GhostSky')
 TextureParameterValues(2)=(ParameterName="Emissive",ParameterValue=Texture2D'{PACKAGE}.T_GhostSky')
 ScalarParameterValues(0)=(ParameterName="EmissiveMultiply",ParameterValue=0.55)
 ScalarParameterValues(1)=(ParameterName="SpecularMultValue",ParameterValue=0)
End PackageObject
"""
 color=','.join(f'{c}={v}' for c,v in zip('RGB',PALETTE[name]))
 return f"""Begin PackageObject ParentPackage={PACKAGE} Class=MaterialInstanceConstant Name=MI_{name} Archetype=MaterialInstanceConstant'Engine.Default__MaterialInstanceConstant'
 Parent=Material'EngineDebugMaterials.LevelColorationUnlitMaterial'
 VectorParameterValues(0)=(ParameterName="Color",ParameterValue=({color},A=1.0))
End PackageObject
"""

def key_light(baked=False):
 # Static lights accompany charted meshes; retain the movable baseline otherwise.
 light_class='DominantDirectionalLight' if baked else 'DominantDirectionalLightMovable'
 return actor(light_class,'Sun',f"""Begin Object Class=DominantDirectionalLightComponent Name=DominantDirectionalLightComponent0 ObjName=SunComponent Archetype=DominantDirectionalLightComponent'Engine.Default__{light_class}:DominantDirectionalLightComponent0'
Brightness=1.4
LightColor=(R=230,G=235,B=220,A=255)
WholeSceneDynamicShadowRadius=14000
NumWholeSceneDynamicShadowCascades=3
CascadeDistributionExponent=3
CastShadows=True
CastDynamicShadows=True
bForceDynamicLight={str(not baked)}
End Object
LightComponent=DominantDirectionalLightComponent'SunComponent'
Components(2)=DominantDirectionalLightComponent'SunComponent'
Rotation=(Pitch=-9000,Yaw=-17000)""")

def make(full=False,lightmap_scene=None,output_dir=None):
 root=Path(__file__).parent;out=Path(output_dir) if output_dir else root/'output';out.mkdir(parents=True,exist_ok=True)
 scene=gray_scene()
 if full:
  from world import build_world
  build_world(scene)
 lighting=None
 if lightmap_scene:
  from lightmap_source import apply_lightmaps
  lighting=apply_lightmaps(scene.meshes,json.loads(Path(lightmap_scene).read_text()))
 parts=[f"Begin Map Name={PACKAGE}\nBegin MapPackage\nBegin TopLevelPackage Class=Package Name={PACKAGE} Archetype=Package'Core.Default__Package'\nEnd TopLevelPackage\n"]
 parts.extend(material(n,full) for n in sorted(set(PALETTE)|{m['material'] for m in scene.meshes}))
 parts.append(f"""Begin PackageObject ParentPackage={PACKAGE} Class=PhysicalMaterial Name=SurfacePhysics Archetype=PhysicalMaterial'Engine.Default__PhysicalMaterial'
 Begin Object Class=PhysicalMaterialProperty_TA Name=CarSurface Archetype=PhysicalMaterialProperty_TA'TAGame.Default__PhysicalMaterialProperty_TA'
 bStickyWheels=True
 End Object
 PhysicalMaterialProperty=PhysicalMaterialProperty_TA'CarSurface'
End PackageObject
""")
 parts.extend(static_mesh(m) for m in scene.meshes)
 parts.append('End MapPackage\nBegin Level NAME=PersistentLevel\n')
 parts.append(actor('WorldInfo','WorldInfo_0',f'''Begin Object Class=MapInfo_TA Name=MapSettings
 MirrorFieldType=MFT_None
 MinStadiumBrightness=0.3
End Object
MyMapInfo=MapInfo_TA'MapSettings'
Title="{TITLE}"
Author="{globals().get('AUTHOR', '')}"
KillZ={sea_reset()[0][2]-sea_reset()[1][2]/2-1000}
GlobalGravityZ=-650.0
bForceNoPrecomputedLighting={str(not bool(lighting))}
bUseGlobalIllumination=True
'''))
 parts.append(actor('Brush','BuilderBrush',''))
 parts.extend(mesh_actor(m) for m in scene.meshes)
 parts.append(actor('PlayerStart_TA','InitialPlayer',f'Location={vec(SPAWNS[0])}\nRotation=(Yaw=0)\nTeamIndex=1\nbDestinationOnly=True'))
 parts.append(actor('Pylon_Soccar_TA','FlightArea',"Location=(X=-6000,Y=0,Z=1100)\nFieldCenter=(X=0,Y=0,Z=0)\nFieldExtent=(X=40000,Y=40000,Z=20000)\nSpawnPoints(0)=PlayerStart_TA'InitialPlayer'"))
 for i,p in enumerate(SPAWNS):
  d=sub(GATES[STAGE_STARTS[i]-1]['center'],p);yaw=round(math.atan2(d[1],d[0])*32768/math.pi)
  parts.append(actor('TargetPoint',f'Spawn{i+1}',f'Location={vec(p)}\nRotation=(Yaw={yaw})'))
 for i,p in enumerate(TARGETS):parts.append(actor('TargetPoint',f'Camera{i+1}',f'Location={vec(p)}'))
 parts.extend(sensors())
 parts.append(actor('SkyLight','Ambient',"Begin Object Class=SkyLightComponent Name=SkyLightComponent0 ObjName=AmbientComponent Archetype=SkyLightComponent'Engine.Default__SkyLight:SkyLightComponent0'\nBrightness=0.65\nLightColor=(R=150,G=185,B=215,A=255)\nEnd Object\nLightComponent=SkyLightComponent'AmbientComponent'\nComponents(1)=SkyLightComponent'AmbientComponent'\nLocation=(X=0,Y=0,Z=6000)"))
 parts.append(key_light(baked=bool(lighting)))
 if lighting:
  bounds=box_volume('BakeProbeBounds',lighting['center'],lighting['size'])
  parts.append(bounds.replace('TriggerVolume','LightmassImportanceVolume').replace('CollideActors=True','CollideActors=False'))
 if full:parts.append(actor('ExponentialHeightFog','CoastalFog',"Begin Object Class=ExponentialHeightFogComponent Name=HeightFogComponent0 ObjName=CoastalFogComponent Archetype=ExponentialHeightFogComponent'Engine.Default__ExponentialHeightFog:HeightFogComponent0'\nFogDensity=0.003\nFogHeightFalloff=0.4\nFogMaxOpacity=0.6\nStartDistance=1600\nLightInscatteringColor=(R=100,G=160,B=155)\nLightInscatteringBrightness=0.5\nOppositeLightColor=(R=55,G=95,B=105)\nOppositeLightBrightness=0.35\nEnd Object\nComponent=ExponentialHeightFogComponent'CoastalFogComponent'\nComponents(1)=ExponentialHeightFogComponent'CoastalFogComponent'\nLocation=(X=0,Y=0,Z=1300)"))
 parts.append('End Level\nEnd Map\n')
 data=''.join(parts).encode();(out/'course.t3d').write_bytes(data);(out/'course.t3d.gz').write_bytes(gzip.compress(data,compresslevel=6))
 graph=generate();kismet=graph.serialize().encode();(out/'Voyage.kismet.txt').write_bytes(kismet)
 (out/'scene.json').write_text(json.dumps({'meshes':scene.meshes,'gates':GATES,'decks':DECKS}))
 report={'package':PACKAGE,'full_art':full,'gates':GATES,'meshes':len(scene.meshes),'triangles':sum(len(f)-2 for m in scene.meshes for f in m['faces']),'nodes':len(graph.nodes),'trigger_volumes':len(sensors()),'source_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 report['stages']=[{'number':i+1,'name':name,'first_gate':STAGE_STARTS[i],'spawn':SPAWNS[i],'target':TARGETS[i]} for i,name in enumerate(STAGE_NAMES)]
 report['baked_lighting']=lighting
 report['lightmap_scene_sha256']=hashlib.sha256(Path(lightmap_scene).read_bytes()).hexdigest() if lightmap_scene else None
 report['scene_sha256']=hashlib.sha256((out/'scene.json').read_bytes()).hexdigest()
 report['kismet_sha256']=hashlib.sha256(kismet).hexdigest()
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='gates'},indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--lightmap-scene',type=Path)
 parser.add_argument('--output-dir',type=Path,help='Keep each course revision in a separate build directory')
 parser.add_argument('--sensors-only',type=Path,help='Export a named sensor supplement; replace existing sensors and reconnect Kismet before saving')
 args=parser.parse_args()
 if args.sensors_only:
  if args.full or args.lightmap_scene:parser.error('--sensors-only cannot be combined with full scene options')
  args.sensors_only.write_text(f'Begin Map Name={PACKAGE}\nBegin Level Name=PersistentLevel\n'+''.join(sensors())+'End Level\nEnd Map\n')
  print(f'Exported {len(sensors())} sensors to {args.sensors_only}; no editor changes made.')
 else:make(args.full,args.lightmap_scene,args.output_dir)
