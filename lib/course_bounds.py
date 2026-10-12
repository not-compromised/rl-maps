"""Failure bounds belong to the selected course, including its lowest landing."""
from course import DECKS, GATES, SPAWNS, TARGETS


def sea_reset():
    points = list(DECKS) + list(SPAWNS) + list(TARGETS) + [g['center'] for g in GATES]
    low = [min(p[i] for p in points) - 5000 for i in range(2)]
    high = [max(p[i] for p in points) + 5000 for i in range(2)]
    top = min(d[2] for d in DECKS) - 350
    bottom = top - 3050
    return ((low[0]+high[0])/2, (low[1]+high[1])/2, (top+bottom)/2), (high[0]-low[0], high[1]-low[1], top-bottom)


def verify_landings():
    center, size = sea_reset()
    top = center[2] + size[2]/2
    protected = [d[2]-180 for d in DECKS] + [p[2]-100 for p in SPAWNS] + [p[2] for p in TARGETS]
    assert all(z > top for z in protected), 'Landing or camera target overlaps SeaReset'
    return top
