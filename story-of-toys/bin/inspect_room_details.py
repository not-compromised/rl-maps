"""Measure the reported poster, propeller and duplicate-toy defects in the live source."""
import bpy,json,sys
from pathlib import Path

def pieces(obj):
 m=obj.data;parent=list(range(len(m.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in m.edges:
  a,b=map(root,e.vertices);parent[b]=a
 groups={}
 for v in m.vertices:groups.setdefault(root(v.index),[]).append(v)
 result=[]
 for vs in groups.values():
  world=[obj.matrix_world@v.co for v in vs];bounds=[[min(v[k] for v in world),max(v[k] for v in world)] for k in range(3)]
  result.append(dict(vertices=len(vs),bounds=bounds,center=[sum(b)/2 for b in bounds],size=[b-a for a,b in bounds]))
 return result
out=Path(sys.argv[sys.argv.index('--')+1]);out.parent.mkdir(parents=True,exist_ok=True)
names=['RoomPlane','RoomPosters','RoomWindow','RoomDesk','RoomBed','RoomToys']
rows={n:pieces(bpy.data.objects[n]) for n in names}
plane=rows['RoomPlane'];fuselage=max((p for p in plane if p['size'][1]>5000 and p['size'][2]<2000),key=lambda p:p['vertices']);prop=[p for p in plane if p['bounds'][1][0]>500]
post=[p for p in rows['RoomPosters'] if -16500<p['center'][0]<-14900 and 14100<p['center'][2]<18800 and p['vertices']>20]
counts={k:sum(n in bpy.data.objects for n in names) for k,names in {'Buzz':['RoomBuzz','RoomCheckpointFinish'],'Woody':['RoomWoody','RoomCheckpointDesk'],'Slinky':['RoomSlinky','RoomCheckpointBed']}.items()}
checks={'one_of_each_named_toy':all(v==1 for v in counts.values()),'propeller_on_fuselage_axis':all(abs(p['center'][0]-fuselage['center'][0])<1 and abs(p['center'][2]-fuselage['center'][2])<1 for p in prop),'rocket_print_depth_under_10':(len(bpy.data.objects['RoomRocketPrint'].data.polygons)==2 and abs(bpy.data.objects['RoomRocketPrint'].dimensions.y)<.01) if 'RoomRocketPrint' in bpy.data.objects else bool(post) and all(p['size'][1]<=10 for p in post)}
result=dict(file=bpy.data.filepath,toy_counts=counts,checks=checks,fuselage=fuselage,propeller=prop,rocket_components=post,pieces=rows)
out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='pieces'},indent=2))
