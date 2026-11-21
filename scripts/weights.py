"""Limit every vertex to 4 bone influences and normalize the weights (Roblox reads at most 4).

blender --background --python scripts/weights.py -- work/rigged.blend --out work/weighted.blend [--max 4]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morphtools import common as c  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--max", type=int, default=c.MAX_INFLUENCES, help="influences to keep per vertex (default 4)")


args = c.parse("weights.py", __doc__.splitlines()[0], configure)
c.load(args.input)
arm = c.the_armature()
bones = set(arm.data.bones.keys())

for obj in c.meshes():
    bone_groups = {g.index for g in obj.vertex_groups if g.name in bones}
    if not bone_groups:
        print(f"skip {obj.name}: no bone vertex groups")
        continue
    trimmed = unweighted = 0
    for v in obj.data.vertices:
        weights = sorted(((g.weight, g.group) for g in v.groups if g.group in bone_groups and g.weight > 1e-6), reverse=True)
        if not weights:
            unweighted += 1
            continue
        keep, drop = weights[:args.max], weights[args.max:]
        for _, index in drop:
            obj.vertex_groups[index].remove([v.index])
        total = sum(w for w, _ in keep)
        for w, index in keep:
            obj.vertex_groups[index].add([v.index], w / total, "REPLACE")
        trimmed += bool(drop)
    print(f"WEIGHTS {obj.name}: trimmed {trimmed} vertices to {args.max} influences, normalized all; {unweighted} unweighted")
    if unweighted:
        print(f"WARNING {obj.name}: {unweighted} vertices have no bone weight; weight-paint them before export")
c.save(args.out, args.input)
