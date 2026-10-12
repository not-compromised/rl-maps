"""Check a complete runtime visibility snapshot; never connects to a game."""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course import GATES, PACKAGE


def verify(text):
    text = '\n'.join(line for line in text.splitlines() if PACKAGE.lower() + '.theworld:' in line.lower())
    def unique(pattern):
        rows = re.findall(pattern, text)
        result = dict(rows)
        if len(rows) != len(result):
            raise ValueError('Mixed or duplicate snapshots; provide exactly one record per property')
        return result

    state = {name: int(value) for name, value in unique(
        r'Voyage\.(Expected|Stage|Finished)\.(?:IntValue|bValue) = (\d+)').items()}
    actor = {int(i): value == 'True' for i, value in unique(
        r'Gate(\d+)Light_Actor\.bHidden = (True|False)').items()}
    component = {int(i): value == 'True' for i, value in unique(
        r'Gate(\d+)Light_Actor\.Gate\d+Light_Component\.HiddenGame = (True|False)').items()}
    ids = {gate['index'] for gate in GATES}
    if set(state) != {'Expected', 'Stage', 'Finished'} or set(actor) != ids or set(component) != ids:
        raise ValueError('Incomplete snapshot: require Expected, Stage, Finished and both visibility flags for every ring')
    if state['Expected'] not in range(1, len(GATES)+2) or state['Stage'] not in {gate['stage'] for gate in GATES} or state['Finished'] not in (0, 1):
        raise ValueError('Progression values are outside the course state domain')
    if state['Finished'] and state['Expected'] != len(GATES)+1:
        raise ValueError('Finished state requires every gate to have passed')
    wanted = {gate['index'] for gate in GATES if gate['index'] == state['Expected'] and gate['stage'] == state['Stage'] and not state['Finished']}
    visible = {i for i in ids if not actor[i] and not component[i]}
    return {'state': state, 'expected_visible': sorted(wanted), 'actual_visible': sorted(visible), 'passed': wanted == visible}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    args = parser.parse_args()
    result = verify(args.log.read_text())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
