import math
import unittest
from course import GATES, PATHS, TARGETS

class FinishSeparation(unittest.TestCase):
 def test_white_route_does_not_pass_through_blue_rings(self):
  for g in (g for g in GATES if g['stage']==2):
   c,n=g['center'],g['normal']
   for a,b in zip(PATHS[6],PATHS[6][1:]):
    da=sum((a[k]-c[k])*n[k] for k in range(3));db=sum((b[k]-c[k])*n[k] for k in range(3))
    if da*db<0:
     p=tuple(a[k]+(b[k]-a[k])*da/(da-db) for k in range(3))
     self.assertGreater(math.dist(p,c),g['radius']+180,f'White path crosses blue ring {g["index"]}')
 def test_blue_and_white_corridors_have_distinct_space(self):
  closest=min(math.dist(a,b) for a in PATHS[6] for b in PATHS[1])
  self.assertGreaterEqual(closest,3000)
 def test_finish_is_above_the_bed(self):
  x,y,z=TARGETS[6]
  self.assertTrue(-22775<x<-6275 and -18715<y<-7515)
  self.assertGreater(z,15000)
