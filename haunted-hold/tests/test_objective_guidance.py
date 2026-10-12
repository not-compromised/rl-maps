"""Exercise emitted objective branches. Engine rendering/ball physics need runtime tests."""
import re
import unittest
from course import GATES
from logic import generate


def decisions(event, **overrides):
    graph=generate(); values={}; visible=set(range(1,len(GATES)+1)); effects=[]
    for name,node in graph.nodes.items():
        p=node['props']
        if node['class']=='SeqVar_Int':values[name]=int(p['IntValue'])
        if node['class']=='SeqVar_Bool':values[name]=int(p['bValue'])
    values.update(overrides)
    pending=[(event,0)]; steps=0
    while pending:
        name,input_pin=pending.pop(0);steps+=1
        if steps>500:raise AssertionError('Unexpected graph cycle')
        node=graph.nodes[name];p=node['props'];kind=node['class'];output=0
        def variables(pin):return re.findall(r"\w+'([^']+)'",p.get(f'VariableLinks({pin})',''))
        if kind=='SeqCond_CompareInt':
            a,b=(values[variables(pin)[0]] for pin in (0,1));output=0 if a<b else 1 if a>b else 2
        elif kind=='SeqCond_CompareBool':output=0 if values[variables(0)[0]] else 1
        elif kind in ('SeqAct_SetInt','SeqAct_SetBool'):
            values[variables(1)[0]]=values[variables(0)[0]]
        elif kind=='SeqAct_SetObject':values[variables(1)[0]]=p['DefaultValue'].split('.')[-1].rstrip("'")
        elif kind=='SeqAct_ToggleHiddenGame':
            for variable in variables(0):
                i=int(re.search(r'Gate(\d+)Highlight',variable)[1])
                if input_pin==0:visible.discard(i)
                elif input_pin==1:visible.add(i)
                else:raise AssertionError('Unexpected visibility input')
        elif kind=='SeqAct_AddGameBall_TA':
            effects.append((name,input_pin));continue
        elif kind not in ('SeqEvent_Touch','SeqAct_Teleport','SeqAct_SetVelocity','SeqAct_GiveBoost_TA','SeqAct_DrawText'):
            continue
        pending.extend((target,int(pin)) for target,pin in re.findall(r"LinkedOp=\w+'([^']+)',InputLinkIdx=(\d+)",p.get(f'OutputLinks({output})','')))
    return values,visible,effects


class ObjectiveGuidance(unittest.TestCase):
    def test_each_active_ring_owns_highlight_and_camera(self):
        for gate in GATES:
            with self.subTest(gate=gate['index']):
                state,visible,effects=decisions('HideGateHighlights',Stage=gate['stage'],Expected=gate['index'])
                self.assertEqual(visible,{gate['index']})
                self.assertEqual(state['CameraDestination'],f"CameraGate{gate['index']:02}")
                self.assertEqual(effects,[('ClearCamera',2)])

    def test_checkpoint_landing_is_required_before_next_ring_lights(self):
        state,visible,_=decisions('Gate03Disarm',Stage=1,Expected=4)
        self.assertEqual(visible,set())
        self.assertEqual(state['CameraDestination'],'Camera1')
        state,visible,_=decisions('Checkpoint2Touch',Stage=1,Expected=4)
        self.assertEqual(visible,{4})
        self.assertEqual(state['CameraDestination'],'CameraGate04')

    def test_reset_restores_section_first_ring_and_guide(self):
        for stage,first in [(1,1),(2,4)]:
            state,visible,_=decisions('ChooseSpawn',Stage=stage,Expected=6,Armed=6)
            self.assertEqual(state['Expected'],first)
            self.assertEqual(state['Armed'],0)
            self.assertEqual(visible,{first})
            self.assertEqual(state['CameraDestination'],f'CameraGate{first:02}')

    def test_finish_landing_then_completed_run_has_no_highlight(self):
        state,visible,_=decisions('Gate06Disarm',Stage=2,Expected=7)
        self.assertEqual(visible,set())
        self.assertEqual(state['CameraDestination'],'Camera2')
        state,visible,effects=decisions('FinishTouch',Stage=2,Expected=7)
        self.assertTrue(state['Finished'])
        self.assertEqual(visible,set())
        self.assertIn(('RemoveCamera',2),effects)
        self.assertNotIn(('ClearCamera',2),effects)

    def test_restart_rebuilds_first_objective(self):
        state,visible,_=decisions('RestartTouch',Stage=2,Expected=7,Finished=1,Seconds=99,Deaths=3)
        self.assertEqual((state['Stage'],state['Expected'],state['Finished'],state['Seconds'],state['Deaths']),(1,1,0,0,0))
        self.assertEqual(visible,{1})
        self.assertEqual(state['CameraDestination'],'CameraGate01')


if __name__=='__main__':unittest.main()
