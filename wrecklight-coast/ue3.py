"""UE3 text export. Source winding remains right-handed until serialization."""
import lib_path  # noqa: F401  (puts the shared ../lib on sys.path)
import math,struct
from course import PACKAGE,add,sub,cross,dot,unit
from surface_materials import face_uvs

def vec(v): return '(X=%.6f,Y=%.6f,Z=%.6f)'%tuple(v)
def actor(cls,name,body):
 owner='TAGame' if cls.endswith('_TA') else 'Engine'
 return f"Begin Actor Class={cls} Name={name} Archetype={cls}'{owner}.Default__{cls}'\n{body}\nEnd Actor\n"

def brush(name,vertices,faces):
 polygons=''.join('Begin Polygon Flags=0\n'+''.join('Vertex %.6f,%.6f,%.6f\n'%tuple(vertices[i]) for i in face)+'End Polygon\n' for face in faces)
 return actor('TriggerVolume',name,f"""Begin Object Class=BrushComponent Name=BrushComponent0 ObjName={name}Brush Archetype=BrushComponent'Engine.Default__TriggerVolume:BrushComponent0'
 Brush=Model'{name}Model'
 CollideActors=True
 BlockActors=False
 BlockRigidBody=False
 bDisableAllRigidBody=False
End Object
Begin Brush Name={name}Model
Begin PolyList
{polygons}End PolyList
End Brush
Brush=Model'{name}Model'
BrushComponent=BrushComponent'{name}Brush'
CollisionComponent=BrushComponent'{name}Brush'
Components(0)=BrushComponent'{name}Brush'
bCollideActors=True
bBlockActors=False
""")

def prism(name,polygon,transform,depth=70):
 # polygon is counterclockwise in local Y/Z. Extrusion runs along local X.
 size=len(polygon);v=[transform(x,y,z) for x in [-depth/2,depth/2] for y,z in polygon]
 f=[tuple(reversed(range(size))),tuple(range(size,2*size))]
 f.extend((i,(i+1)%size,(i+1)%size+size,i+size) for i in range(size))
 return brush(name,v,f)

def box_volume(name,center,size):
 x,y,z=[a/2 for a in size]
 return prism(name,[(-y,-z),(y,-z),(y,z),(-y,z)],lambda a,b,c:add(center,(a,b,c)),x*2)

class Scene:
 def __init__(self):self.meshes=[]
 def mesh(self,name,v,f,material,collision=True,smooth=False):
  if any(m['name']==name for m in self.meshes):raise ValueError(name)
  self.meshes.append(dict(name=name,vertices=v,faces=f,material=material,collision=collision,smooth=smooth))
 def box(self,name,center,size,mat,collision=True):
  x,y,z=[a/2 for a in size]
  v=[add(center,(sx*x,sy*y,sz*z)) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  self.mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,collision)
 def tube(self,name,points,radius,mat,segments=10,collision=True):
  v=[]
  for i,p in enumerate(points):
   tangent=sub(points[min(i+1,len(points)-1)],points[max(0,i-1)])
   n=unit(tangent);s=unit(cross((1,0,0) if abs(n[2])>.9 else (0,0,1),n));u=cross(n,s)
   for j in range(segments):
    a=2*math.pi*j/segments;v.append(add(p,add(tuple(x*radius*math.cos(a) for x in s),tuple(x*radius*math.sin(a) for x in u))))
  f=[tuple(reversed(range(segments))),tuple(range((len(points)-1)*segments,len(points)*segments))]
  f.extend((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j) for i in range(len(points)-1) for j in range(segments))
  self.mesh(name,v,f,mat,collision,True)

def static_mesh(m):
 triangles=[];triangle_uvs=[]
 for face in m['faces']:
  projected=face_uvs(m,face) if 'uvs' not in m else None
  for i in range(1,len(face)-1):
   corners=(0,i+1,i);indices=[face[j] for j in corners]
   triangles.append([m['vertices'][j] for j in indices])
   triangle_uvs.append([m['uvs'][j] for j in indices] if 'uvs' in m else [projected[j] for j in corners])
 count=len(triangles)
 if count>60000:raise ValueError('Split collision mesh '+m['name'])
 lightmap=m.get('lightmap_uvs')
 if lightmap is not None:
  if len(lightmap)!=count or any(len(t)!=3 or any(len(uv)!=2 or any(not math.isfinite(x) or not 0<=x<=1 for x in uv) for uv in t) for t in lightmap):
   raise ValueError('Invalid lightmap coordinates for '+m['name'])
 raw=bytearray(count*372)
 for k,tri in enumerate(triangles):
  uvs=triangle_uvs[k]
  if m['material']=='Sky':
   uvs=[(math.atan2(v[1],v[0])/math.tau+.5,.5-math.asin(v[2]/math.sqrt(dot(v,v)))/math.pi) for v in tri]
   if max(u for u,v in uvs)-min(u for u,v in uvs)>.5:
    uvs=[(u+1 if u<.5 else u,v) for u,v in uvs]
  for i,v in enumerate(tri):
   struct.pack_into('<3f',raw,k*372+i*12,*v)
   uv=uvs[i]
   for channel in range(2):
    coords=lightmap[k][i] if channel==1 and lightmap is not None else uv
    struct.pack_into('<2f',raw,k*372+36+i*64+channel*8,*coords)
  struct.pack_into('<3I',raw,k*372+228,*([0xffffffff]*3));struct.pack_into('<4I',raw,k*372+240,0,0,1 if m['smooth'] else 0,2)
 hexlines='\n'.join(','.join(f'{b:02x}' for b in raw[i:i+32])+',' for i in range(0,len(raw),32))
 n=m['name'];collision=str(m['collision']);lightmap_resolution=m.get('lightmap_resolution',32)
 return f"""Begin PackageStaticMesh ParentPackage={PACKAGE}
 Begin StaticMesh Class=StaticMesh Name={n} ObjName={n} Archetype=StaticMesh'Engine.Default__StaticMesh'
 LightMapCoordinateIndex=1
 LightMapResolution={lightmap_resolution}
 UseSimpleRigidBodyCollision=False
 UseSimpleBoxCollision=False
 UseSimpleLineCollision=False
 Begin SMData
 Version=0.0
 LODDistanceRatio=1.0
 LODMaxRange=2000.0
 StreamingDistanceMultiplier=1.0
 LightMapResolution={lightmap_resolution}
 LightMapCoordinateIndex=1
 UseSimpleLineCollision=False
 UseSimpleBoxCollision=False
 UseSimpleRigidBodyCollision=False
 InternalVersion=18
 Begin SMRenderData
 NumVertices={count*3}
 Begin Elements
 Count=1
 Begin StaticMeshElement
 Material={PACKAGE}.MI_{m['material']}
 EnableCollision={collision}
 OldEnableCollision={collision}
 bEnableShadowCasting=True
 FirstIndex=0
 NumTriangles={count}
 MinVertexIndex=0
 MaxVertexIndex={count*3-1}
 MaterialIndex=0
 Begin Fragments
 0,{count}
 End Fragments
 End StaticMeshElement
 End Elements
 Begin StaticMeshTriangleBulkData
 Begin UntypedBulkData
 ElementCount={count}
 ElementSize=372
 Begin BinaryBlob
 Size={len(raw)}
 Begin Binary
{hexlines}
 End Binary
 End BinaryBlob
 End UntypedBulkData
 End StaticMeshTriangleBulkData
 End SMRenderData
 End SMData
 End StaticMesh
End PackageStaticMesh
"""

def mesh_actor(m):
 n=m['name'];solid=str(m['collision'])
 return actor('StaticMeshActor',n+'_Actor',f"""Begin Object Class=StaticMeshComponent Name=StaticMeshComponent0 ObjName={n}_Component Archetype=StaticMeshComponent'Engine.Default__StaticMeshActor:StaticMeshComponent0'
 StaticMesh=StaticMesh'{PACKAGE}.{n}'
 PhysMaterialOverride=PhysicalMaterial'{PACKAGE}.SurfacePhysics'
 bDisableAllRigidBody={str(not m['collision'])}
 bUsePrecomputedShadows={str('lightmap_uvs' in m)}
 CastShadow={str(m['material'] not in ('Sky','Water'))}
 LightingChannels=(bInitialized=True,Static=True,Dynamic=True)
 BlockRigidBody={solid}
 CollideActors={solid}
End Object
StaticMeshComponent=StaticMeshComponent'{n}_Component'
Components(0)=StaticMeshComponent'{n}_Component'
CollisionComponent=StaticMeshComponent'{n}_Component'
BlockRigidBody={solid}
bHidden={str(m.get('hidden',False))}
bCollideActors={solid}
bBlockActors={solid}
""")
