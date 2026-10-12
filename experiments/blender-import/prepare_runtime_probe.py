"""Generate finite offline checks. This script never launches or controls a game."""
from pathlib import Path
import sys

PREFIX = "rlmaps-blenderprobe03"
QUERY = f"exec {PREFIX}-query"
FLUSH = f"exec {PREFIX}-flush"


def build():
    probes = {
        "query": [
            'unreal_command "getall Car_TA Location"',
            'unreal_command "getall Car_TA Velocity"',
            'unreal_command "getall WorldInfo GlobalGravityZ"',
            'unreal_command "getall WorldInfo WorldGravityZ"',
        ],
        "flush": ['unreal_command "getall StaticMeshComponent StaticMesh"'],
        # Flat top is Z=0; car should settle above it, with zero vertical speed.
        "platform": ["player location -700 400 600", "player velocity 0 0 0",
                     "sleep 1600", QUERY, "sleep 500", QUERY, FLUSH],
        # FBX→UDK flips Blender Y. Imported block: Y[-550,-50], top Z=400.
        "block-top": ["player location -700 -300 1000", "player velocity 0 0 0",
                      "sleep 1600", QUERY, "sleep 500", QUERY, FLUSH],
        # Hole spans X[100,700], Y[-350,350]; sample before KillZ=-4000.
        "hole": ["player location 400 0 450", "player velocity 0 0 0",
                 "sleep 1500", QUERY, "sleep 500", QUERY, FLUSH],
        # From positive Y, strike the imported block's front face at Y=-50.
        "block-side": ["player location -700 500 180", "player velocity 0 -1200 0",
                       "sleep 350", QUERY, "sleep 350", QUERY, FLUSH],
        "gravity": ["player location -700 400 2200", "player velocity 0 0 0",
                    "sleep 100", QUERY, "sleep 500", QUERY, FLUSH],
        "fall-recovery": ["player location 400 0 450", "player velocity 0 0 0",
                          "sleep 6000", QUERY, "sleep 1500", QUERY, FLUSH],
    }
    probes["suite"] = []
    for name in ["platform", "block-top", "block-side", "gravity", "hole"]:
        probes["suite"] += [f"exec {PREFIX}-{name}", "sleep 3000"]
    probes["suite"] += [f"exec {PREFIX}-fall-recovery", "sleep 8500", FLUSH]
    return {f"{PREFIX}-{name}.cfg": "; ".join(commands) + "\n"
            for name, commands in probes.items()}


if __name__ == "__main__":
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    for name, content in build().items():
        (output / name).write_text(content)
    print(f"Prepared {len(build())} configs in {output}; no game commands executed.")
