"""Build a small Source-style (ValveBiped) humanoid for smoke tests: boxy weighted mesh,
some vertices with 5 bone influences, a stray helper prop, an alpha texture, and an
off-center, rotated, wrongly scaled placement.

blender --background --python tests/make_test_rig.py -- tests/out/source.blend
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

out = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
P = "ValveBiped.Bip01_"
BONES = [  # name, head, tail, parent
    ("Pelvis", (0, 0, 1.0), (0, 0, 1.1), None),
    ("Spine", (0, 0, 1.1), (0, 0, 1.25), "Pelvis"),
    ("Spine1", (0, 0, 1.25), (0, 0, 1.4), "Spine"),
    ("Spine2", (0, 0, 1.4), (0, 0, 1.55), "Spine1"),
    ("Neck1", (0, 0, 1.55), (0, 0, 1.65), "Spine2"),
    ("Head1", (0, 0, 1.65), (0, 0, 1.85), "Neck1"),
]
for side, sx in (("L", 1), ("R", -1)):
    BONES += [
        (f"{side}_UpperArm", (0.2 * sx, 0, 1.5), (0.5 * sx, 0, 1.5), "Spine2"),
        (f"{side}_Forearm", (0.5 * sx, 0, 1.5), (0.75 * sx, 0, 1.5), f"{side}_UpperArm"),
        (f"{side}_Hand", (0.75 * sx, 0, 1.5), (0.85 * sx, 0, 1.5), f"{side}_Forearm"),
        (f"{side}_Thigh", (0.1 * sx, 0, 1.0), (0.1 * sx, 0, 0.55), "Pelvis"),
        (f"{side}_Calf", (0.1 * sx, 0, 0.55), (0.1 * sx, 0, 0.1), f"{side}_Thigh"),
        (f"{side}_Foot", (0.1 * sx, 0, 0.1), (0.1 * sx, -0.15, 0.0), f"{side}_Calf"),
    ]

arm_data = bpy.data.armatures.new("Rig")
arm = bpy.data.objects.new("Rig", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for name, head, tail, parent in BONES:
    b = arm_data.edit_bones.new(P + name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = arm_data.edit_bones[P + parent]
bpy.ops.object.mode_set(mode="OBJECT")

verts, faces, owner = [], [], []
for name, head, tail, _ in BONES:
    h, t = Vector(head), Vector(tail)
    lo = Vector(map(min, h, t)) - Vector((0.06, 0.06, 0.06))
    hi = Vector(map(max, h, t)) + Vector((0.06, 0.06, 0.06))
    base = len(verts)
    verts += [(x, y, z) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    faces += [[base + i for i in f] for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    owner += [name] * 8
mesh = bpy.data.meshes.new("Body")
mesh.from_pydata(verts, [], faces)
body = bpy.data.objects.new("Body", mesh)
bpy.context.scene.collection.objects.link(body)
for name, *_ in BONES:
    body.vertex_groups.new(name=P + name)
for i, name in enumerate(owner):
    body.vertex_groups[P + name].add([i], 1.0, "REPLACE")
    if name in ("Spine", "Spine1"):  # 5 influences on the torso to exercise weights.py
        for extra in ("Pelvis", "Spine2", "Neck1", "Spine1" if name == "Spine" else "Spine"):
            body.vertex_groups[P + extra].add([i], 0.2, "REPLACE")
body.parent = arm
body.modifiers.new("Armature", "ARMATURE").object = arm

img = bpy.data.images.new("FaceOverlay", 8, 8, alpha=True)
img.pixels = [1.0, 0.0, 0.0, 0.5] * 64
img.pack()
mat = bpy.data.materials.new("Face")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
bsdf = mat.node_tree.nodes["Principled BSDF"]
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
mat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
body.data.materials.append(mat)

helper = bpy.data.objects.new("Helper_Prop", bpy.data.meshes.new("Helper_Prop"))
helper.data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
bpy.context.scene.collection.objects.link(helper)

arm.location = (3, 2, 0.5)
arm.rotation_euler.z = math.radians(90)
arm.scale = (40, 40, 40)
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print(f"built {out}")
