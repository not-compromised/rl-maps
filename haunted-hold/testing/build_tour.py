"""Generate a bounded car-position walkthrough for visual inspection, not flight proof."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course import SPAWNS, TARGETS, stage_gates, sub, mul, add


def vector_command(action, value):
    return 'player ' + action + ' ' + ' '.join(f'{x:.3f}' for x in value)


def build(prefix, speed=900, suite_prefix=None):
    suite_prefix = suite_prefix or prefix
    commands = [f'exec {suite_prefix}-restart', 'sleep 1000', 'togglemenu console2', 'sleep 3000']
    duration = 4.0
    points = []
    for stage, spawn in enumerate(SPAWNS, 1):
        route = [spawn] + [g['center'] for g in stage_gates(stage)] + [TARGETS[stage-1]]
        for start, stop in zip(route, route[1:]):
            delta = sub(stop, start)
            distance = math.sqrt(sum(x*x for x in delta))
            count = max(1, math.ceil(distance / speed / .05))
            velocity = mul(delta, 1 / (count * .05))
            for step in range(1, count+1):
                point = add(start, mul(delta, step/count))
                points.append(point)
                commands += [vector_command('velocity', velocity), vector_command('location', point), 'sleep 50']
            duration += count*.05
        commands += [vector_command('velocity', (0, 0, 0)), 'sleep 1200']
        duration += 1.2
    commands += [f'exec {suite_prefix}-query', f'exec {suite_prefix}-flush']
    if duration > 60:
        raise ValueError('Tour exceeds 60 seconds; split into sections')
    chunks = [commands[i:i+30] for i in range(0, len(commands), 30)]
    names = [prefix+'-tour.cfg'] + [f'{prefix}-tour-{i:02}.cfg' for i in range(1, len(chunks))]
    files = {}
    for i, chunk in enumerate(chunks):
        if i+1 < len(chunks):
            chunk = chunk + ['exec '+names[i+1][:-4]]
        content = '; '.join(chunk)+'\n'
        if len(content) > 2000:
            raise ValueError('Console line exceeds 2000 characters')
        files[names[i]] = content
    return files, {'seconds': duration, 'points': points, 'method': 'scripted position/velocity; not ordinary flight'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--suite-prefix')
    args = parser.parse_args()
    if any(not value.replace('-', '').isalnum() for value in (args.prefix, args.suite_prefix or args.prefix)):
        parser.error('Prefix must contain letters, numbers or hyphens')
    files, manifest = build(args.prefix, suite_prefix=args.suite_prefix)
    args.output.mkdir(exist_ok=False)
    name = args.prefix+'-tour.cfg'
    for filename, content in files.items():
        (args.output/filename).write_text(content)
    manifest['files'] = {filename: hashlib.sha256(content.encode()).hexdigest() for filename,content in files.items()}
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'seconds': manifest['seconds'], 'samples': len(manifest['points']), 'file': name}))
