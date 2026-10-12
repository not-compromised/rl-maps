#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
for map in wrecklight-coast haunted-hold story-of-toys experiments/blender-import; do
    (
        cd "$map"
        python3 -m unittest discover -s tests
        python3 build_map.py
        python3 verify_source.py
    )
done
