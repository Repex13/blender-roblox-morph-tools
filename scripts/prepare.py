"""Clean and normalize a model for Roblox: drop helper objects, reset to rest pose,
apply transforms, scale to a target height in studs and stand it on the ground.

blender --background --python scripts/prepare.py -- model.glb --out work/prepared.blend
    [--height 5.3] [--remove "Book|Helper"] [--rotate-z 180]
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from morphtools import common as c  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--out", required=True, help="new .blend to write (the input is never overwritten)")
    p.add_argument("--height", type=float, default=5.3, help="target height in studs (default 5.3)")
    p.add_argument("--remove", help="regex; objects whose names match are deleted (props, helpers, duplicates)")
    p.add_argument("--rotate-z", type=float, default=0.0, help="degrees to turn the model so it faces -Y")


def transform_top_level(matrix):
    for obj in bpy.context.scene.objects:
        if obj.parent is None:
            obj.matrix_world = matrix @ obj.matrix_world
    bpy.context.view_layer.update()


def apply_all():
    objs = [o for o in bpy.context.scene.objects if o.type in {"ARMATURE", "MESH", "EMPTY"}]
    c.select_only(objs, c.the_armature())
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)


args = c.parse("prepare.py", __doc__.splitlines()[0], configure)
c.load(args.input)

if args.remove:
    pattern = re.compile(args.remove, re.IGNORECASE)
    doomed = [o for o in bpy.context.scene.objects if pattern.search(o.name)]
    names = [o.name for o in doomed]
    for obj in doomed:
        bpy.data.objects.remove(obj, do_unlink=True)
    print(f"removed {len(names)} objects: {names[:20]}")

arm = c.the_armature()
c.rest_pose(arm)
if args.rotate_z:
    transform_top_level(Matrix.Rotation(math.radians(args.rotate_z), 4, "Z"))
apply_all()

lo, hi = c.world_bounds(c.meshes())
height = hi.z - lo.z
if height <= 0:
    c.fail("model has no height; is the mesh empty?")
scale = args.height / height
center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
transform_top_level(Matrix.Diagonal((scale, scale, scale, 1)) @ Matrix.Translation(-center))
apply_all()

lo, hi = c.world_bounds(c.meshes())
print(f"PREPARED height {hi.z - lo.z:.3f} studs (scale x{scale:.4f}), lowest point z={lo.z:.4f}")
c.save(args.out, args.input)
