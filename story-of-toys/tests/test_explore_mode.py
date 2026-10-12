"""Exercise finish/hazard/restart paths in the emitted Kismet graph."""
import lib_path  # noqa: F401  (puts the shared ../lib on sys.path)
import re,unittest
from logic import generate
from course import GATES,STAGE_STARTS

def dispatch(graph,event,**state):
 values={n:int(v['props'].get('bValue',v['props'].get('IntValue',0))) for n,v in graph.nodes.items() if v['class'] in ('SeqVar_Int','SeqVar_Bool')};values.update(state)
 effects=[];queue=[event];steps=0
 while queue:
  steps+=1
  if steps>1000:raise AssertionError('Unexpected event cycle')
  n=queue.pop(0);node=graph.nodes[n];p=node['props'];kind=node['class'];pin=0
  def var(i):return re.search(r"LinkedVariables=\(\w+'([^']+)'",p[f'VariableLinks({i})'])[1]
  if kind=='SeqCond_CompareBool':pin=0 if values[var(0)] else 1
  elif kind=='SeqCond_CompareInt':
   a,b=values[var(0)],values[var(1)];pin=0 if a<b else 1 if a>b else 2
  elif kind in ('SeqAct_SetInt','SeqAct_SetBool'):values[var(1)]=values[var(0)]
  elif kind=='SeqAct_AddInt':values[var(2)]=values[var(0)]+values[var(1)]
  elif kind=='SeqAct_ModifyProperty':effects.append((n,dict(p)))
  elif kind in ('SeqAct_Teleport','SeqAct_SetVelocity'):effects.append((n,dict(p)))
  elif kind in ('SeqAct_Delay','SeqAct_DrawText','SeqAct_AddGameBall_TA'):continue
  elif kind not in ('SeqEvent_Touch','SeqEvent_CarSpawned_TA','SeqAct_SetObject','SeqAct_GiveBoost_TA'):continue
  queue+=re.findall(r"LinkedOp=\w+'([^']+)'",p.get(f'OutputLinks({pin})',''))
 return values,effects

class ExploreMode(unittest.TestCase):
 def setUp(self):self.g=generate()
 def test_finish_enables_exploration_and_freezes_score(self):
  v,e=dispatch(self.g,'FinishTouch',Stage=7,Expected=len(GATES)+1,Running=1,Seconds=90,Deaths=4)
  self.assertEqual((v['Finished'],v['Seconds'],v['Deaths']),(1,90,4))
  after_tick,_=dispatch(self.g,'ClockRunning',**v)
  self.assertEqual(after_tick['Seconds'],90)
  active_tick,_=dispatch(self.g,'ClockRunning',Running=1,Finished=0,Seconds=90)
  self.assertEqual(active_tick['Seconds'],91)
 def test_all_reset_entries_are_inert_after_finish(self):
  for event in ['SeaTouch','CanReset','CarSpawned']+[f'Gate{i:02}Miss00' for i in range(1,len(GATES)+1)]:
   with self.subTest(event=event):
    v,e=dispatch(self.g,event,Finished=1,Running=1,Stage=7,Expected=len(GATES)+1,Deaths=4)
    self.assertFalse(e,'Exploration must not teleport or stop the car');self.assertEqual(v['Deaths'],4)
 def test_revisiting_finish_does_not_stop_exploration(self):
  v,e=dispatch(self.g,'FinishTouch',Finished=1,Stage=7,Expected=len(GATES)+1)
  self.assertFalse(e)
 def test_active_run_still_resets_on_sea_and_missed_rings(self):
  for stage,first in enumerate(STAGE_STARTS,1):
   for event in ['SeaTouch',f'Gate{first:02}Miss00']:
    with self.subTest(stage=stage,event=event):
     v,e=dispatch(self.g,event,Finished=0,Running=1,Stage=stage,Expected=first,Deaths=4)
     self.assertEqual(v['Deaths'],5);self.assertIn('TeleportToDeck',[n for n,p in e])
 def test_restart_toy_does_nothing_during_an_unfinished_run(self):
  initial=dict(Finished=0,Running=1,Stage=4,Expected=40,Deaths=3,Seconds=75)
  values,effects=dispatch(self.g,'RestartTouch',**initial)
  self.assertFalse(effects)
  self.assertEqual({k:values[k] for k in initial},initial)
 def test_restart_restores_course_hazards_and_initial_state(self):
  v,e=dispatch(self.g,'RestartTouch',Finished=1,Running=1,Stage=7,Expected=len(GATES)+1,Deaths=4,Seconds=90)
  self.assertEqual((v['Finished'],v['Running'],v['Stage'],v['Expected'],v['Deaths'],v['Seconds']),(0,0,1,1,0,0))
  v['Running']=1
  reset,e=dispatch(self.g,'SeaTouch',**v)
  self.assertEqual(reset['Deaths'],1)
  self.assertIn('TeleportToDeck',[n for n,p in e])

 def test_floor_reset_covers_room_and_native_kill_floor_is_outside_it(self):
  from course import ROOM_KILL_Z
  from course_bounds import sea_reset
  center,size=sea_reset()
  self.assertLess(ROOM_KILL_Z,-32000)
  for axis,extent in enumerate((23000,19000)):
   self.assertLess(center[axis]-size[axis]/2,-extent)
   self.assertGreater(center[axis]+size[axis]/2,extent)
  self.assertLess(center[2]-size[2]/2,0)
  self.assertGreater(center[2]+size[2]/2,150)
