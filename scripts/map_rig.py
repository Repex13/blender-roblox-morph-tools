"""Rename the rig's main bones to Roblox R15 names and make HumanoidRootPart the root.

blender --background --python scripts/map_rig.py -- work/prepared.blend --out work/rigged.blend
    [--preset auto|valve|mixamo|vrm|unity] [--map custom-map.json]

Extra bones (spine segments, fingers, hair, wings, tails) keep their names and keep deforming.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from morphtools import common as c, rigmaps  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--preset", default="auto", choices=["auto", *rigmaps.PRESETS])
    p.add_argument("--map", help='JSON file {"SourceBone": "R15Name", ...} used instead of a preset')


args = c.parse("map_rig.py", __doc__.splitlines()[0], configure)
c.load(args.input)
arm = c.the_armature()
names = list(arm.data.bones.keys())

if args.map:
    wanted = json.loads(Path(args.map).read_text(encoding="utf-8"))
    mapping = {src: dst for src, dst in wanted.items() if src in names}
else:
    preset = rigmaps.detect(names) if args.preset == "auto" else args.preset
    if not preset:
        c.fail("couldn't recognise this rig; pass --preset or a --map file")
    mapping = rigmaps.mapping_for(preset, names)
    print(f"preset: {preset}")

for src, dst in mapping.items():
    if src == dst:
        continue
    if dst in arm.data.bones:
        c.fail(f"can't rename {src} to {dst}: a bone called {dst} already exists")
    arm.data.bones[src].name = dst
    for obj in c.meshes():
        group = obj.vertex_groups.get(src)
        if group and dst not in obj.vertex_groups:
            group.name = dst

c.select_only([arm], arm)
bpy.ops.object.mode_set(mode="EDIT")
edit = arm.data.edit_bones
lower = edit.get("LowerTorso")
if lower is None:
    bpy.ops.object.mode_set(mode="OBJECT")
    c.fail("no LowerTorso after mapping; check the preset or --map")
root = edit.get("HumanoidRootPart")
if root is None:
    root = edit.new("HumanoidRootPart")
    root.head = lower.head.copy()
    root.tail = lower.head + Vector((0, 0, max(lower.length, 0.2)))
    root.use_deform = False
root.parent = None
lower.use_connect = False
lower.parent = root
orphans = [b.name for b in edit if b.parent is None and b.name != "HumanoidRootPart" and not b.children]
for name in orphans:
    edit.remove(edit[name])
bpy.ops.object.mode_set(mode="OBJECT")

present = set(arm.data.bones.keys())
missing = [b for b in c.R15 if b not in present]
print(f"MAPPED {len(mapping)} bones; removed empty root bones {orphans}; {len(present)} bones total")
if missing:
    print(f"WARNING missing R15 bones: {missing}")
c.save(args.out, args.input)
