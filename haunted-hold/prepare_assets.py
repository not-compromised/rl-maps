"""Verify licensed inputs and prepare the hold's texture import manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
ASSETS = ('weathered_planks', 'hessian_230', 'rusty_metal')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    sources = ROOT / 'assets/textures'
    sources.mkdir(parents=True, exist_ok=True)
    inputs = []
    for asset in ASSETS:
        metadata = json.loads((ROOT / 'assets/sources' / f'{asset}.json').read_text())
        for channel, key in (('diff', 'Diffuse'), ('nor_dx', 'nor_dx'), ('rough', 'Rough')):
            entry = metadata[key]['2k']['png']
            source = sources / f'{asset}_{channel}_2k.png'
            if not source.exists():
                if not args.download:
                    raise SystemExit(f'Missing {source}; use --download to acquire documented inputs')
                url = urlparse(entry['url'])
                if url.scheme != 'https' or url.netloc != 'dl.polyhaven.org':
                    raise ValueError('Unexpected asset host')
                with urlopen(entry['url'], timeout=60) as response:
                    data = response.read()
                if hashlib.md5(data).hexdigest() != entry['md5']:
                    raise ValueError(f'Download checksum mismatch: {asset}/{channel}')
                with source.open('xb') as output:
                    output.write(data)
            if hashlib.md5(source.read_bytes()).hexdigest() != entry['md5']:
                raise ValueError(f'Local source checksum mismatch: {source}')
            inputs.append((asset, channel, source, entry))
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    for asset, channel, source, entry in inputs:
        suffix = 'spec' if channel == 'rough' else channel
        target = args.output / f'T_{asset}_{suffix}.tga'
        command = ['magick', str(source), '-resize', '1024x1024!', '-depth', '8']
        if channel == 'rough':
            command += ['-negate']
        subprocess.run(command + ['-type', 'TrueColor', str(target)], check=True)
        records.append({'file': target.name, 'source_url': entry['url'],
                        'source_md5': entry['md5'],
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                        'compression': 'TC_Normalmap' if channel == 'nor_dx' else 'TC_Default',
                        'srgb': channel == 'diff'})
    target = args.output / 'T_GhostSky.tga'
    subprocess.run(['magick', str(ROOT / 'assets/ghost_sky.png'), '-resize', '2048x1024!',
                    '-depth', '8', '-type', 'TrueColor', str(target)], check=True)
    records.append({'file': target.name, 'source': 'assets/sky-prompt.txt',
                    'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                    'compression': 'TC_Default', 'srgb': True})
    (args.output / 'manifest.json').write_text(json.dumps({
        'files': records, 'imported': False,
        'note': 'Manifest settings are requirements, not evidence of editor state.'
    }, indent=2) + '\n')
    print(f'Prepared {len(records)} textures; editor import and readback remain separate.')


if __name__ == '__main__':
    main()
