import unittest
from testing.verify_highlights import verify
from testing.build_tour import build
from course import GATES, PACKAGE


def snapshot(expected=1, stage=1, finished=0, visible=(1,), component_hidden=()):
    prefix = PACKAGE.lower()+'.TheWorld:PersistentLevel.'
    rows = [prefix+f'Main_Sequence.Voyage.{name}.{prop} = {value}'
            for name, prop, value in [('Expected', 'IntValue', expected),
                                     ('Stage', 'IntValue', stage),
                                     ('Finished', 'bValue', finished)]]
    for gate in GATES:
        i = gate['index']
        name = f'Gate{i:02}Light_Actor'
        rows += [prefix+f'{name}.bHidden = {i not in visible}',
                 prefix+f'{name}.Gate{i:02}Light_Component.HiddenGame = {i in component_hidden}']
    return '\n'.join(rows)


class RuntimeEvidenceTests(unittest.TestCase):
    def test_launch_and_checkpoint_guidance(self):
        self.assertTrue(verify(snapshot())['passed'])
        self.assertTrue(verify(snapshot(4, 1, visible=()))['passed'])
        self.assertTrue(verify(snapshot(4, 2, visible=(4,)))['passed'])

    def test_stale_highlight_and_component_hidden_fail(self):
        self.assertFalse(verify(snapshot(7, 2, 1))['passed'])
        self.assertFalse(verify(snapshot(component_hidden=(1,)))['passed'])

    def test_incomplete_and_mixed_snapshots_rejected(self):
        for text in [snapshot().rsplit('\n', 1)[0], snapshot()+'\n'+snapshot(4, 2, visible=(4,))]:
            with self.assertRaises(ValueError):
                verify(text)

    def test_invalid_progression_rejected(self):
        for text in [snapshot(stage=99, visible=()), snapshot(finished=1, visible=())]:
            with self.assertRaises(ValueError):
                verify(text)

    def test_tour_is_finite_and_every_chain_target_exists(self):
        files, manifest = build('test', suite_prefix='suite')
        self.assertLess(manifest['seconds'], 60)
        self.assertGreater(len(files), 1)
        visited = set()
        name = 'test-tour.cfg'
        while name:
            self.assertNotIn(name, visited)
            visited.add(name)
            content = files[name]
            self.assertLessEqual(len(content), 2000)
            tail = content.strip().split('; ')[-1]
            name = tail[5:]+'.cfg' if tail.startswith('exec test-tour-') else None
        self.assertEqual(visited, set(files))
