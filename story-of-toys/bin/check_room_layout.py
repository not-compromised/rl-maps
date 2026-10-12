"""Check furniture relationships from the saved Blender manifest."""
import json,sys
from pathlib import Path
rows=json.loads((Path(sys.argv[1])/'room-manifest.json').read_text())['meshes']
b={m['name']:m['bounds'] for m in rows}
bed,table=b['RoomBed'],b['RoomNightstand']
assert 0<=bed[1][0]-(-18755)<=150, 'Bed side must meet the corner wall'
for name in ('RoomBed','RoomNightstand','RoomDresser'):
 gap=b[name][0][0]-(-22815)
 assert 0<=gap<=150, (name,'back must meet left wall molding',gap)
assert table[1][0]>bed[1][1], 'Nightstand overlaps the side of the bed'
assert table[1][0]-bed[1][1]<=500, 'Nightstand must stay beside the headboard'
assert table[0][1]<sum(bed[0])/2, 'Nightstand belongs near the pillow end'
assert b['RoomDresser'][1][0]>table[1][1], 'Dresser overlaps the nightstand'
assert b['RoomDresser'][1][0]-table[1][1]<=800, 'Dresser belongs alongside the nightstand'
assert b['RoomGlobe'][0][0]>-22815, 'Globe intersects wall'
assert b['RoomGlobe'][2][0]>b['RoomDresser'][2][1]-160, 'Globe base must sit on dresser'
for first,second in [('RoomDresser','RoomSlinky'),('RoomWagonChest','RoomDesk'),('RoomWagonChest','RoomAliens')]:
 a,c=b[first],b[second]
 assert any(a[i][1]<c[i][0] or c[i][1]<a[i][0] for i in range(3)), (first,second,'overlap')
assert b['RoomWagonChest'][1][0]>10000, 'Wagon belongs near the desk'
assert b['RoomBedPrint'][2]==[4155,4155], 'Keep the flat landing height'
assert abs(b['RoomShelfBasket'][2][0]-630)<1, 'Basket rests on the lower shelf'
print('PASS: bedside relationships, dresser/globe support, prop separation, wagon position and flat bedding')

# Main furnishings and the launch deck need full footprints clear, not just route rays.
furniture=['RoomBed','RoomNightstand','RoomDresser','RoomNurseryCabinet','RoomCrib','RoomDesk','RoomWagonChest','RoomShelvesPart3']
for i,first in enumerate(furniture):
 for second in furniture[i+1:]:
  a,c=b[first],b[second]
  assert any(a[k][1]<c[k][0] or c[k][1]<a[k][0] for k in range(3)),(first,second,'furniture footprints overlap')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course import DECKS
x,y,z=DECKS[0];deck=[[x-1100,x+1100],[y-1100,y+1100],[z-180,z]]
for name in furniture:
 c=b[name]
 assert any(deck[k][1]<c[k][0] or c[k][1]<deck[k][0] for k in range(3)),('Start deck',name,'overlap')
assert 0<=b['RoomNurseryCabinet'][1][0]-(-18755)<=150,'Changing cabinet back must meet front wall'
print('PASS: all major furniture footprints and launch deck clear')
