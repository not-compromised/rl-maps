"""Evaluate generated checkpoint decisions using UE3 integer comparison pins.

This checks the emitted control graph. Physics, ball spawning and rendering
still require the real game and are deliberately outside this interpreter.
"""
import re
import unittest
from course import STAGE_STARTS
from logic import generate


def run_decisions(graph, event, **state):
    values = {name: int(node['props']['IntValue'])
              for name, node in graph.nodes.items() if node['class'] == 'SeqVar_Int'}
    values.update({name:int(node['props']['bValue']) for name,node in graph.nodes.items() if node['class']=='SeqVar_Bool'})
    values.update(state)
    pending = [event]
    while pending:
        name = pending.pop(0)
        node = graph.nodes[name]
        props = node['props']
        def variable(pin):
            return re.search(r"LinkedVariables=\(\w+'([^']+)'", props[f'VariableLinks({pin})'])[1]
        kind = node['class']
        output = 0
        if kind == 'SeqCond_CompareInt':
            a, b = values[variable(0)], values[variable(1)]
            output = 0 if a < b else 1 if a > b else 2
        elif kind in ('SeqAct_SetInt','SeqAct_SetBool'):
            values[variable(1)] = values[variable(0)]
        elif kind == 'SeqAct_SetObject':
            values[variable(1)] = props['DefaultValue'].split('.')[-1].rstrip("'")
        elif kind not in ('SeqEvent_Touch',):
            continue
        pending.extend(re.findall(r"LinkedOp=\w+'([^']+)'", props.get(f'OutputLinks({output})', '')))
    return values


class CheckpointProgression(unittest.TestCase):
    def setUp(self):
        self.graph = generate()

    def test_each_stage_resets_to_its_own_first_ring(self):
        for stage, first in enumerate(STAGE_STARTS, 1):
            with self.subTest(stage=stage):
                state = run_decisions(self.graph, 'ChooseSpawn', Stage=stage, Expected=999)
                self.assertEqual(state['Expected'], first)
                self.assertEqual(state['Armed'], 0)

    def test_checkpoint_changes_both_destinations_once(self):
        for stage in range(2, 7):
            event = f'Checkpoint{stage}Touch'
            state = run_decisions(self.graph, event, Stage=stage-1, Expected=STAGE_STARTS[stage-1])
            self.assertEqual(state['Stage'], stage)
            self.assertEqual(state['Respawn'], f'Spawn{stage}')
            self.assertEqual(state['CameraDestination'], f'Camera{stage}')
            # A completed checkpoint cannot regress a later stage.
            repeated = run_decisions(self.graph, event, Stage=6, Expected=STAGE_STARTS[stage-1])
            self.assertEqual(repeated['Stage'], 6)
            self.assertNotIn('CameraDestination', repeated)

    def test_future_rings_require_the_checkpoint_even_with_matching_ring_number(self):
        for first in STAGE_STARTS[1:]:
            state = run_decisions(self.graph, f'Gate{first:02}Entry', Stage=1, Expected=first)
            self.assertEqual(state['Armed'], 0)

    def test_finish_requires_every_ring_and_the_final_stage(self):
        for stage, expected in [(1,55),(5,55),(6,54)]:
            state=run_decisions(self.graph,'FinishTouch',Stage=stage,Expected=expected)
            self.assertEqual(state['Finished'],0)
        state=run_decisions(self.graph,'FinishTouch',Stage=6,Expected=55)
        self.assertEqual(state['Finished'],1)

    def test_missing_ring_cannot_activate_checkpoint(self):
        for stage in range(2, 7):
            state = run_decisions(self.graph, f'Checkpoint{stage}Touch', Stage=stage-1,
                                  Expected=STAGE_STARTS[stage-1]-1)
            self.assertEqual(state['Stage'], stage-1)
            self.assertNotIn('Respawn', state)


if __name__ == '__main__':
    unittest.main()
